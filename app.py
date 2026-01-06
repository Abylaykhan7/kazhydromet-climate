"""
Климатический Атлас Казахстана
Сглаженная интерактивная карта
РГП «Казгидромет»
"""

import streamlit as st
import geopandas as gpd
import folium
from folium import GeoJson
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from shapely.geometry import Point
import requests
import json

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
st.set_page_config(page_title="Климатический Атлас Казахстана", page_icon="🌡️", layout="wide", initial_sidebar_state="collapsed")

# Инициализация
for k, v in {'lang': 'ru', 'param': 'temp', 'month': 0, 'show_cities': True, 'show_stations': True, 'show_boundary': True, 'grid_size': 55, 'opacity': 0.8, 'basemap': 'light', 'chat_history': []}.items():
    if k not in st.session_state:
        st.session_state[k] = v

API_KEY = "sk-xquciybelqijbpxynvxppleljcwbbizelikzxvorrinirlqt"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# ============================================================================
# ГРАНИЦА КАЗАХСТАНА
# ============================================================================
KZ_GEOJSON = {"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"Kazakhstan"},"geometry":{"type":"MultiPolygon","coordinates":[[[[69.16,55.37],[70.08,55.17],[70.93,55.17],[71.21,54.59],[71.51,54.11],[72.18,54.19],[72.82,54.12],[73.68,54.07],[74.28,53.5],[75.23,53.89],[76.35,54.33],[76.94,54.43],[77.33,53.6],[78.54,52.64],[79.43,51.59],[80.09,50.85],[80.83,51.28],[81.45,50.79],[82.36,50.79],[83.21,50.99],[84.22,50.53],[85.0,50.05],[85.62,49.58],[86.36,49.61],[86.98,49.3],[87.3,49.1],[86.73,48.91],[86.59,48.54],[85.7,48.32],[85.59,47.74],[85.53,47.06],[84.83,46.83],[84.1,46.97],[83.31,47.18],[82.92,46.95],[82.51,46.02],[82.3,45.53],[82.07,45.19],[81.45,45.27],[80.83,45.14],[80.25,45.04],[79.84,44.89],[80.45,44.76],[80.37,44.08],[80.63,43.66],[80.68,43.29],[80.4,42.99],[80.17,42.64],[80.2,42.22],[79.48,42.49],[78.81,42.81],[78.01,42.87],[77.18,42.96],[76.48,42.89],[75.71,42.8],[74.87,42.99],[74.04,43.16],[73.45,42.7],[73.11,42.54],[72.46,42.7],[71.77,42.81],[71.17,42.59],[70.88,42.34],[70.56,42.02],[70.02,41.77],[69.39,41.46],[68.87,41.15],[68.35,40.61],[68.02,41.12],[66.81,41.24],[66.01,42.19],[65.71,43.15],[64.64,43.64],[62.9,43.61],[61.28,44.14],[59.41,45.14],[58.01,45.45],[56.0,44.94],[56.0,43.35],[55.93,41.32],[55.0,41.78],[54.24,42.33],[52.78,41.98],[52.44,42.04],[52.57,42.81],[51.76,43.04],[51.0,43.9],[50.24,44.44],[50.77,44.61],[51.3,44.55],[51.22,44.69],[51.0,45.0],[51.5,45.34],[52.36,45.43],[52.81,45.46],[52.83,45.59],[52.85,45.79],[52.91,46.02],[52.98,46.35],[53.03,46.59],[52.85,46.75],[52.52,46.86],[51.8,46.85],[51.57,46.86],[51.21,47.01],[50.7,46.89],[50.18,46.72],[49.81,46.41],[49.38,46.38],[49.18,46.47],[48.87,46.47],[48.52,46.74],[48.61,47.41],[47.46,47.8],[47.12,48.16],[46.58,48.41],[46.81,49.51],[47.26,50.2],[47.83,50.31],[48.22,49.87],[48.76,50.12],[49.0,50.71],[49.61,51.12],[50.51,51.5],[51.03,51.68],[51.62,51.48],[52.25,51.72],[52.77,51.51],[53.16,51.5],[53.62,51.37],[54.15,51.1],[54.47,50.86],[54.71,50.68],[55.06,50.83],[55.86,50.65],[56.46,51.03],[57.02,51.05],[57.75,51.08],[58.26,51.15],[58.8,50.77],[59.52,50.59],[60.19,50.8],[61.18,50.73],[61.55,51.34],[60.69,51.62],[60.08,51.9],[60.65,52.16],[60.97,52.5],[61.03,52.98],[61.78,53.0],[62.13,53.08],[61.26,53.27],[61.39,53.48],[61.02,53.65],[61.12,53.88],[61.31,54.07],[61.82,54.01],[62.18,54.03],[62.67,54.03],[63.25,54.2],[63.98,54.29],[64.62,54.4],[65.2,54.44],[65.74,54.6],[66.76,54.74],[67.75,54.88],[68.25,55.1],[68.89,55.32],[69.16,55.37]]]]}}]}

@st.cache_resource
def load_kz():
    gdf = gpd.read_file(json.dumps(KZ_GEOJSON), driver='GeoJSON')
    return gdf.geometry.iloc[0], gdf.total_bounds

KZ_POLYGON, KZ_BOUNDS = load_kz()

BASEMAPS = {
    'light': {'name_ru': 'Светлая', 'name_kk': 'Ашық', 'name_en': 'Light', 'tiles': 'CartoDB positron'},
    'dark': {'name_ru': 'Тёмная', 'name_kk': 'Қараңғы', 'name_en': 'Dark', 'tiles': 'CartoDB dark_matter'},
    'terrain': {'name_ru': 'Рельеф', 'name_kk': 'Бедер', 'name_en': 'Terrain', 'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'},
    'satellite': {'name_ru': 'Спутник', 'name_kk': 'Жерсерік', 'name_en': 'Satellite', 'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'},
}

# ============================================================================
# CSS
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root {
    --accent: #dc2626; --accent-light: #ef4444; --bg-dark: #0a0f1a; --bg-card: #141b2d;
    --text-primary: #f8fafc; --text-secondary: #94a3b8; --text-muted: #64748b;
    --border: #1e293b; --success: #10b981; --primary: #3b82f6;
}
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(160deg, var(--bg-dark) 0%, #0f172a 50%, #1a1a2e 100%); }
#MainMenu, footer, header, .stDeployButton { visibility: hidden; }

.main-header {
    background: linear-gradient(135deg, #b91c1c 0%, #dc2626 30%, #ea580c 70%, #f59e0b 100%);
    padding: 1.75rem 2.5rem; border-radius: 20px; margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(220, 38, 38, 0.4); position: relative; overflow: hidden;
}
.main-header::after {
    content: ''; position: absolute; top: -50%; right: -10%; width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
}
.main-header h1 { margin: 0; font-size: 1.9rem; font-weight: 700; color: white; position: relative; }
.main-header p { margin: 0.5rem 0 0 0; opacity: 0.92; font-size: 0.95rem; color: white; position: relative; }

.stat-card {
    background: linear-gradient(145deg, var(--bg-card), #1a2338);
    border-radius: 14px; padding: 1rem; text-align: center;
    border: 1px solid var(--border); margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: transform 0.2s, border-color 0.2s;
}
.stat-card:hover { transform: translateY(-2px); border-color: var(--primary); }
.stat-value {
    font-size: 1.5rem; font-weight: 700;
    background: linear-gradient(135deg, var(--primary), #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.stat-label { font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }

.legend-box {
    background: linear-gradient(145deg, var(--bg-card), #1a2338);
    border-radius: 14px; padding: 1.2rem; border: 1px solid var(--border);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3); margin-bottom: 12px;
}
.legend-title { font-size: 0.7rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; }
.legend-gradient { height: 140px; width: 18px; border-radius: 9px; margin: 0 auto; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3); }
.legend-labels { display: flex; flex-direction: column; justify-content: space-between; height: 140px; margin-left: 10px; }
.legend-label { font-size: 0.72rem; color: var(--text-secondary); font-weight: 500; }

.stTabs [data-baseweb="tab-list"] { background: var(--bg-card); padding: 6px; border-radius: 14px; border: 1px solid var(--border); }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%) !important; color: white !important; border-radius: 10px; }

.chat-box { background: linear-gradient(145deg, rgba(220,38,38,0.08), rgba(234,88,12,0.08)); border-radius: 14px; padding: 1.25rem; border: 1px solid rgba(220,38,38,0.2); }
.chat-msg { padding: 0.9rem 1.1rem; margin: 0.6rem 0; border-radius: 12px; color: var(--text-primary); line-height: 1.6; }
.chat-user { background: var(--bg-card); border-left: 4px solid var(--primary); }
.chat-ai { background: rgba(16,185,129,0.1); border-left: 4px solid var(--success); }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ПЕРЕВОДЫ
# ============================================================================
TR = {
    'ru': {
        'title': 'Климатический Атлас Казахстана', 'subtitle': 'Интерактивная визуализация • РГП «Казгидромет»',
        'temp': 'Температура', 'precip': 'Осадки', 'sun': 'Солнце', 'wind': 'Ветер',
        'months': ['Год', 'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
        'map': '🗺️ Карта', 'compare': '📊 Сравнение', 'chart': '📈 Графики', 'timeline': '📅 История', 'ai': '🤖 ИИ',
        'cities': 'Города', 'stations': 'Станции', 'boundary': 'Граница', 'period': 'Период', 'basemap': 'Подложка',
        'detail': 'Детализация', 'opacity': 'Насыщенность', 'max': 'Макс', 'min': 'Мин', 'avg': 'Сред',
        'region': 'Область', 'zone': 'Зона', 'cycle': 'Годовой ход',
        'forest_steppe': 'Лесостепь', 'steppe': 'Степь', 'semi_desert': 'Полупустыня', 'desert': 'Пустыня', 'foothill': 'Предгорье',
        'ai_title': 'Климатический ИИ-ассистент', 'ai_hint': 'Задайте вопрос о климате Казахстана', 'ask': 'Спросить', 'clear': 'Очистить',
        'q1': 'Сравни климат Астаны и Алматы', 'q2': 'Где самые холодные зимы?', 'q3': 'Самые засушливые области?', 'q4': 'Лучший климат для сельского хозяйства?',
        'hot': 'Тепло', 'cold': 'Холодно', 'high': 'Много', 'low': 'Мало', 'legend': 'Шкала',
        'timeline_title': 'Изменение климата за 50 лет', 'timeline_desc': 'Динамика климатических показателей 1975-2024',
        'select_city': 'Выберите город', 'select_param': 'Показатель', 'kz_avg': 'Среднее по Казахстану',
        'change': 'Изменение', 'trend': 'Тренд', 'warming': 'Потепление', 'cooling': 'Похолодание',
        'year_temp': 'Среднегодовая температура', 'jan_temp': 'Температура января', 'jul_temp': 'Температура июля', 'year_precip': 'Годовые осадки',
        'since_1975': 'с 1975 года', 'per_decade': 'за 10 лет',
    },
    'kk': {
        'title': 'Қазақстан Климаттық Атласы', 'subtitle': 'Интерактивті визуализация • «Қазгидромет» РМК',
        'temp': 'Температура', 'precip': 'Жауын-шашын', 'sun': 'Күн', 'wind': 'Жел',
        'months': ['Жыл', 'Қаң', 'Ақп', 'Нау', 'Сәу', 'Мам', 'Мау', 'Шіл', 'Там', 'Қыр', 'Қаз', 'Қар', 'Жел'],
        'map': '🗺️ Карта', 'compare': '📊 Салыстыру', 'chart': '📈 Графиктер', 'timeline': '📅 Тарих', 'ai': '🤖 ЖИ',
        'cities': 'Қалалар', 'stations': 'Станциялар', 'boundary': 'Шекара', 'period': 'Кезең', 'basemap': 'Негіз',
        'detail': 'Детализация', 'opacity': 'Қанықтық', 'max': 'Макс', 'min': 'Мин', 'avg': 'Орт',
        'region': 'Облыс', 'zone': 'Аймақ', 'cycle': 'Жылдық өзгеріс',
        'forest_steppe': 'Орманды дала', 'steppe': 'Дала', 'semi_desert': 'Шөлейт', 'desert': 'Шөл', 'foothill': 'Тау бөктері',
        'ai_title': 'Климаттық ЖИ-көмекші', 'ai_hint': 'Климат туралы сұрақ қойыңыз', 'ask': 'Сұрау', 'clear': 'Тазалау',
        'q1': 'Астана мен Алматы климатын салыстыр', 'q2': 'Ең суық қыс қайда?', 'q3': 'Ең құрғақ облыстар?', 'q4': 'Ауыл шаруашылығы үшін жақсы климат?',
        'hot': 'Жылы', 'cold': 'Суық', 'high': 'Көп', 'low': 'Аз', 'legend': 'Шкала',
        'timeline_title': '50 жылдағы климат өзгерісі', 'timeline_desc': '1975-2024 климаттық көрсеткіштер динамикасы',
        'select_city': 'Қаланы таңдаңыз', 'select_param': 'Көрсеткіш', 'kz_avg': 'Қазақстан бойынша орташа',
        'change': 'Өзгеріс', 'trend': 'Тренд', 'warming': 'Жылыну', 'cooling': 'Суыну',
        'year_temp': 'Жылдық орташа температура', 'jan_temp': 'Қаңтар температурасы', 'jul_temp': 'Шілде температурасы', 'year_precip': 'Жылдық жауын-шашын',
        'since_1975': '1975 жылдан бері', 'per_decade': '10 жылда',
    },
    'en': {
        'title': 'Climate Atlas of Kazakhstan', 'subtitle': 'Interactive visualization • RSE "Kazhydromet"',
        'temp': 'Temperature', 'precip': 'Precipitation', 'sun': 'Sunshine', 'wind': 'Wind',
        'months': ['Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'map': '🗺️ Map', 'compare': '📊 Compare', 'chart': '📈 Charts', 'timeline': '📅 History', 'ai': '🤖 AI',
        'cities': 'Cities', 'stations': 'Stations', 'boundary': 'Border', 'period': 'Period', 'basemap': 'Basemap',
        'detail': 'Detail', 'opacity': 'Intensity', 'max': 'Max', 'min': 'Min', 'avg': 'Avg',
        'region': 'Region', 'zone': 'Zone', 'cycle': 'Annual cycle',
        'forest_steppe': 'Forest-steppe', 'steppe': 'Steppe', 'semi_desert': 'Semi-desert', 'desert': 'Desert', 'foothill': 'Foothill',
        'ai_title': 'Climate AI Assistant', 'ai_hint': 'Ask about Kazakhstan climate', 'ask': 'Ask', 'clear': 'Clear',
        'q1': 'Compare Astana and Almaty climate', 'q2': 'Where are coldest winters?', 'q3': 'Driest regions?', 'q4': 'Best climate for agriculture?',
        'hot': 'Hot', 'cold': 'Cold', 'high': 'High', 'low': 'Low', 'legend': 'Scale',
        'timeline_title': 'Climate change over 50 years', 'timeline_desc': 'Climate indicators dynamics 1975-2024',
        'select_city': 'Select city', 'select_param': 'Parameter', 'kz_avg': 'Kazakhstan average',
        'change': 'Change', 'trend': 'Trend', 'warming': 'Warming', 'cooling': 'Cooling',
        'year_temp': 'Annual average temperature', 'jan_temp': 'January temperature', 'jul_temp': 'July temperature', 'year_precip': 'Annual precipitation',
        'since_1975': 'since 1975', 'per_decade': 'per decade',
    }
}
def t(key): return TR[st.session_state.lang].get(key, key)

# ============================================================================
# ДАННЫЕ
# ============================================================================
STATIONS = {
    'Петропавловск': {'lat': 54.88, 'lon': 69.14, 't_year': 1.8, 't_jan': -17.5, 't_jul': 19.8, 'temps': [-17.5, -16.5, -9.2, 3.5, 12.8, 18.8, 19.8, 17.8, 11.8, 3.2, -7.5, -15.2], 'precip': 345, 'sun': 2000, 'wind': 3.8},
    'Костанай': {'lat': 53.22, 'lon': 63.64, 't_year': 2.5, 't_jan': -16.8, 't_jul': 20.8, 'temps': [-16.8, -16.2, -8.5, 4.2, 13.5, 19.5, 20.8, 18.8, 12.5, 3.8, -6.5, -14.2], 'precip': 315, 'sun': 2100, 'wind': 4.3},
    'Кокшетау': {'lat': 53.28, 'lon': 69.39, 't_year': 2.2, 't_jan': -16.0, 't_jul': 19.5, 'temps': [-16.0, -15.5, -8.0, 4.0, 13.0, 18.5, 19.5, 17.5, 11.5, 3.0, -7.0, -14.0], 'precip': 330, 'sun': 2050, 'wind': 4.0},
    'Астана': {'lat': 51.17, 'lon': 71.45, 't_year': 3.5, 't_jan': -14.5, 't_jul': 21.0, 'temps': [-14.5, -14.0, -6.5, 5.5, 14.0, 20.0, 21.0, 19.0, 13.0, 4.5, -5.5, -12.5], 'precip': 310, 'sun': 2200, 'wind': 4.5},
    'Караганда': {'lat': 49.80, 'lon': 73.11, 't_year': 3.2, 't_jan': -15.2, 't_jul': 21.2, 'temps': [-15.2, -14.5, -7.5, 5.2, 14.2, 20.2, 21.2, 19.5, 12.8, 4.2, -6.2, -12.8], 'precip': 280, 'sun': 2380, 'wind': 4.6},
    'Жезказган': {'lat': 47.78, 'lon': 67.71, 't_year': 5.5, 't_jan': -13.5, 't_jul': 24.0, 'temps': [-13.5, -12.5, -4.5, 8.0, 17.0, 23.0, 24.0, 22.0, 15.0, 6.0, -4.0, -11.0], 'precip': 180, 'sun': 2500, 'wind': 4.8},
    'Балхаш': {'lat': 46.84, 'lon': 74.95, 't_year': 6.8, 't_jan': -11.5, 't_jul': 24.5, 'temps': [-11.5, -10.0, -2.0, 10.0, 18.0, 24.0, 24.5, 23.0, 16.0, 7.0, -2.0, -9.0], 'precip': 130, 'sun': 2650, 'wind': 5.0},
    'Семей': {'lat': 50.42, 'lon': 80.23, 't_year': 3.0, 't_jan': -16.5, 't_jul': 22.0, 'temps': [-16.5, -15.0, -6.0, 6.0, 15.0, 21.0, 22.0, 20.0, 13.5, 4.5, -6.0, -14.0], 'precip': 280, 'sun': 2350, 'wind': 3.5},
    'Усть-Каменогорск': {'lat': 49.95, 'lon': 82.61, 't_year': 3.8, 't_jan': -15.0, 't_jul': 21.5, 'temps': [-15.0, -13.5, -5.0, 6.5, 14.5, 20.5, 21.5, 19.5, 13.0, 5.0, -5.0, -12.5], 'precip': 420, 'sun': 2200, 'wind': 2.5},
    'Уральск': {'lat': 51.23, 'lon': 51.39, 't_year': 5.8, 't_jan': -12.2, 't_jul': 23.5, 'temps': [-12.2, -11.2, -3.5, 8.2, 16.5, 22.5, 23.5, 22.2, 15.5, 6.8, -2.8, -9.8], 'precip': 290, 'sun': 2200, 'wind': 4.5},
    'Актобе': {'lat': 50.28, 'lon': 57.17, 't_year': 5.2, 't_jan': -14.5, 't_jul': 23.2, 'temps': [-14.5, -13.8, -5.8, 7.2, 16.2, 22.2, 23.2, 21.8, 14.8, 5.8, -4.2, -12.2], 'precip': 270, 'sun': 2300, 'wind': 5.0},
    'Атырау': {'lat': 46.80, 'lon': 51.88, 't_year': 10.1, 't_jan': -8.2, 't_jul': 26.5, 'temps': [-8.2, -6.8, 1.5, 11.8, 19.5, 25.5, 26.5, 25.8, 18.8, 10.2, 1.8, -5.5], 'precip': 165, 'sun': 2600, 'wind': 4.8},
    'Актау': {'lat': 43.64, 'lon': 51.16, 't_year': 12.5, 't_jan': -2.5, 't_jul': 27.2, 'temps': [-2.5, -0.8, 5.8, 13.2, 20.2, 26.2, 27.2, 26.8, 21.2, 13.8, 6.5, 0.2], 'precip': 145, 'sun': 2900, 'wind': 5.5},
    'Шымкент': {'lat': 42.34, 'lon': 69.60, 't_year': 13.2, 't_jan': -1.5, 't_jul': 27.0, 'temps': [-1.5, 1.5, 8.5, 15.5, 21.5, 26.5, 27.0, 25.5, 19.5, 12.0, 5.0, 0.0], 'precip': 500, 'sun': 2700, 'wind': 2.0},
    'Туркестан': {'lat': 43.30, 'lon': 68.25, 't_year': 12.8, 't_jan': -3.0, 't_jul': 28.0, 'temps': [-3.0, 0.5, 8.0, 16.0, 22.0, 27.5, 28.0, 26.5, 20.0, 12.0, 4.0, -1.0], 'precip': 200, 'sun': 2800, 'wind': 2.5},
    'Кызылорда': {'lat': 44.85, 'lon': 65.51, 't_year': 11.2, 't_jan': -6.5, 't_jul': 27.8, 'temps': [-6.5, -4.2, 5.2, 14.5, 22.2, 27.2, 27.8, 26.5, 19.5, 11.2, 2.5, -4.2], 'precip': 130, 'sun': 2800, 'wind': 3.5},
    'Тараз': {'lat': 42.90, 'lon': 71.37, 't_year': 10.8, 't_jan': -5.5, 't_jul': 25.8, 'temps': [-5.5, -2.8, 5.2, 13.5, 19.2, 24.8, 25.8, 24.5, 18.2, 10.5, 2.8, -3.5], 'precip': 340, 'sun': 2650, 'wind': 2.5},
    'Алматы': {'lat': 43.22, 'lon': 76.85, 't_year': 10.2, 't_jan': -4.5, 't_jul': 24.5, 'temps': [-4.5, -2.5, 4.5, 12.5, 18.0, 23.5, 24.5, 23.5, 17.5, 10.0, 2.5, -2.5], 'precip': 550, 'sun': 2500, 'wind': 1.8},
    'Талдыкорган': {'lat': 45.02, 'lon': 78.37, 't_year': 8.5, 't_jan': -9.0, 't_jul': 24.0, 'temps': [-9.0, -7.0, 1.5, 11.0, 17.5, 23.0, 24.0, 22.5, 16.5, 8.0, 0.0, -6.5], 'precip': 400, 'sun': 2450, 'wind': 2.2},
    'Павлодар': {'lat': 52.29, 'lon': 76.95, 't_year': 2.9, 't_jan': -17.2, 't_jul': 21.5, 'temps': [-17.2, -16.2, -8.2, 4.8, 14.2, 20.2, 21.5, 19.5, 12.8, 3.5, -7.2, -14.5], 'precip': 260, 'sun': 2200, 'wind': 4.2},
    'Аральск': {'lat': 46.79, 'lon': 61.66, 't_year': 9.5, 't_jan': -10.0, 't_jul': 27.5, 'temps': [-10.0, -8.0, 2.0, 12.0, 20.0, 26.5, 27.5, 26.0, 19.0, 10.0, 0.5, -7.0], 'precip': 100, 'sun': 2750, 'wind': 4.5},
    'Форт-Шевченко': {'lat': 44.52, 'lon': 50.27, 't_year': 11.8, 't_jan': -4.0, 't_jul': 26.0, 'temps': [-4.0, -2.5, 4.0, 12.0, 19.0, 25.0, 26.0, 25.5, 20.0, 13.0, 5.5, -1.0], 'precip': 160, 'sun': 2850, 'wind': 5.8},
    'Бейнеу': {'lat': 45.32, 'lon': 55.20, 't_year': 10.5, 't_jan': -7.0, 't_jul': 27.0, 'temps': [-7.0, -5.0, 3.0, 12.5, 20.5, 26.0, 27.0, 26.0, 19.5, 11.0, 2.0, -4.5], 'precip': 120, 'sun': 2700, 'wind': 5.0},
}

CITIES = {'Астана': [51.17, 71.45], 'Алматы': [43.22, 76.85], 'Шымкент': [42.34, 69.60], 'Караганда': [49.80, 73.11], 'Актобе': [50.28, 57.17], 'Атырау': [46.80, 51.88], 'Актау': [43.64, 51.16], 'Костанай': [53.22, 63.64], 'Павлодар': [52.29, 76.95], 'Семей': [50.42, 80.23]}

# Исторические данные по десятилетиям (1970-2020)
CLIMATE_HISTORY = {
    'Астана': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [2.1, 2.3, 2.8, 3.2, 3.5, 3.8],
        't_jan': [-16.2, -15.8, -15.2, -14.8, -14.5, -14.0],
        't_jul': [19.5, 19.8, 20.2, 20.6, 21.0, 21.4],
        'precip': [330, 325, 318, 312, 310, 305],
    },
    'Алматы': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [8.8, 9.2, 9.5, 9.8, 10.2, 10.6],
        't_jan': [-6.2, -5.8, -5.2, -4.8, -4.5, -4.0],
        't_jul': [22.8, 23.2, 23.8, 24.2, 24.5, 25.0],
        'precip': [620, 600, 580, 560, 550, 530],
    },
    'Актау': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [11.2, 11.5, 11.9, 12.2, 12.5, 13.0],
        't_jan': [-4.0, -3.5, -3.0, -2.8, -2.5, -2.0],
        't_jul': [25.8, 26.2, 26.6, 27.0, 27.2, 27.8],
        'precip': [170, 165, 158, 152, 145, 138],
    },
    'Атырау': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [8.8, 9.2, 9.6, 9.9, 10.1, 10.5],
        't_jan': [-9.8, -9.2, -8.8, -8.5, -8.2, -7.8],
        't_jul': [25.2, 25.6, 26.0, 26.3, 26.5, 27.0],
        'precip': [190, 182, 175, 170, 165, 158],
    },
    'Караганда': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [1.8, 2.2, 2.6, 2.9, 3.2, 3.5],
        't_jan': [-16.8, -16.2, -15.8, -15.4, -15.2, -14.8],
        't_jul': [19.8, 20.2, 20.6, 21.0, 21.2, 21.6],
        'precip': [310, 300, 292, 285, 280, 272],
    },
    'Шымкент': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [12.0, 12.4, 12.7, 13.0, 13.2, 13.6],
        't_jan': [-2.8, -2.4, -2.0, -1.7, -1.5, -1.2],
        't_jul': [25.8, 26.2, 26.5, 26.8, 27.0, 27.5],
        'precip': [550, 535, 520, 508, 500, 485],
    },
    'Петропавловск': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [0.5, 0.9, 1.2, 1.5, 1.8, 2.2],
        't_jan': [-19.0, -18.5, -18.0, -17.7, -17.5, -17.0],
        't_jul': [18.5, 18.9, 19.2, 19.5, 19.8, 20.2],
        'precip': [365, 358, 352, 348, 345, 338],
    },
    'Кызылорда': {
        'years': [1975, 1985, 1995, 2005, 2015, 2024],
        't_year': [9.8, 10.2, 10.6, 10.9, 11.2, 11.6],
        't_jan': [-8.0, -7.5, -7.0, -6.7, -6.5, -6.0],
        't_jul': [26.5, 26.9, 27.2, 27.5, 27.8, 28.2],
        'precip': [150, 145, 140, 135, 130, 122],
    },
}

# Средние по Казахстану
KZ_AVERAGE = {
    'years': [1975, 1985, 1995, 2005, 2015, 2024],
    't_year': [5.2, 5.6, 6.0, 6.4, 6.8, 7.2],
    't_jan': [-12.5, -12.0, -11.5, -11.1, -10.8, -10.4],
    't_jul': [21.8, 22.2, 22.6, 23.0, 23.3, 23.8],
    'precip': [320, 310, 300, 292, 285, 275],
}

REGIONS = {
    'akmola': {'name_ru': 'Акмолинская', 'name_kk': 'Ақмола', 'name_en': 'Akmola', 't_year': 2.8, 't_jan': -16.5, 't_jul': 20.2, 'precip': 320, 'temps': [-16.5, -15.8, -8.2, 4.5, 13.2, 18.8, 20.2, 18.5, 12.2, 3.8, -6.2, -13.8], 'zone': 'steppe'},
    'aktobe': {'name_ru': 'Актюбинская', 'name_kk': 'Ақтөбе', 'name_en': 'Aktobe', 't_year': 5.2, 't_jan': -14.5, 't_jul': 23.2, 'precip': 270, 'temps': [-14.5, -13.8, -5.8, 7.2, 16.2, 22.2, 23.2, 21.8, 14.8, 5.8, -4.2, -12.2], 'zone': 'semi_desert'},
    'almaty': {'name_ru': 'Алматинская', 'name_kk': 'Алматы', 'name_en': 'Almaty', 't_year': 8.5, 't_jan': -6.2, 't_jul': 22.5, 'precip': 450, 'temps': [-6.2, -4.5, 3.2, 11.5, 17.2, 21.8, 22.5, 21.8, 16.5, 8.8, 1.2, -4.5], 'zone': 'foothill'},
    'atyrau': {'name_ru': 'Атырауская', 'name_kk': 'Атырау', 'name_en': 'Atyrau', 't_year': 10.1, 't_jan': -8.2, 't_jul': 26.5, 'precip': 165, 'temps': [-8.2, -6.8, 1.5, 11.8, 19.5, 25.5, 26.5, 25.8, 18.8, 10.2, 1.8, -5.5], 'zone': 'desert'},
    'mangystau': {'name_ru': 'Мангистауская', 'name_kk': 'Маңғыстау', 'name_en': 'Mangystau', 't_year': 12.5, 't_jan': -2.5, 't_jul': 27.2, 'precip': 145, 'temps': [-2.5, -0.8, 5.8, 13.2, 20.2, 26.2, 27.2, 26.8, 21.2, 13.8, 6.5, 0.2], 'zone': 'desert'},
    'turkestan': {'name_ru': 'Туркестанская', 'name_kk': 'Түркістан', 'name_en': 'Turkestan', 't_year': 13.5, 't_jan': -1.2, 't_jul': 27.5, 'precip': 420, 'temps': [-1.2, 2.2, 9.2, 16.5, 22.2, 27.2, 27.5, 26.2, 20.2, 12.8, 5.5, 0.5], 'zone': 'semi_desert'},
    'north_kz': {'name_ru': 'СКО', 'name_kk': 'СҚО', 'name_en': 'North KZ', 't_year': 1.8, 't_jan': -17.5, 't_jul': 19.8, 'precip': 345, 'temps': [-17.5, -16.5, -9.2, 3.5, 12.8, 18.8, 19.8, 17.8, 11.8, 3.2, -7.5, -15.2], 'zone': 'forest_steppe'},
    'kostanay': {'name_ru': 'Костанайская', 'name_kk': 'Қостанай', 'name_en': 'Kostanay', 't_year': 2.5, 't_jan': -16.8, 't_jul': 20.8, 'precip': 315, 'temps': [-16.8, -16.2, -8.5, 4.2, 13.5, 19.5, 20.8, 18.8, 12.5, 3.8, -6.5, -14.2], 'zone': 'forest_steppe'},
    'pavlodar': {'name_ru': 'Павлодарская', 'name_kk': 'Павлодар', 'name_en': 'Pavlodar', 't_year': 2.9, 't_jan': -17.2, 't_jul': 21.5, 'precip': 260, 'temps': [-17.2, -16.2, -8.2, 4.8, 14.2, 20.2, 21.5, 19.5, 12.8, 3.5, -7.2, -14.5], 'zone': 'steppe'},
    'karaganda': {'name_ru': 'Карагандинская', 'name_kk': 'Қарағанды', 'name_en': 'Karaganda', 't_year': 3.2, 't_jan': -15.2, 't_jul': 21.2, 'precip': 280, 'temps': [-15.2, -14.5, -7.5, 5.2, 14.2, 20.2, 21.2, 19.5, 12.8, 4.2, -6.2, -12.8], 'zone': 'steppe'},
    'west_kz': {'name_ru': 'ЗКО', 'name_kk': 'БҚО', 'name_en': 'West KZ', 't_year': 5.8, 't_jan': -12.2, 't_jul': 23.5, 'precip': 290, 'temps': [-12.2, -11.2, -3.5, 8.2, 16.5, 22.5, 23.5, 22.2, 15.5, 6.8, -2.8, -9.8], 'zone': 'steppe'},
    'east_kz': {'name_ru': 'ВКО', 'name_kk': 'ШҚО', 'name_en': 'East KZ', 't_year': 3.5, 't_jan': -16.2, 't_jul': 21.5, 'precip': 400, 'temps': [-16.2, -14.5, -6.2, 5.8, 14.2, 20.2, 21.5, 19.8, 13.5, 4.5, -5.8, -13.5], 'zone': 'foothill'},
}

# ============================================================================
# ФУНКЦИИ
# ============================================================================
def get_unit(p): return {'temp': '°C', 'precip': 'мм', 'sun': 'ч', 'wind': 'м/с'}[p]

def get_val(d, p, m):
    if m == 0: return {'temp': d['t_year'], 'precip': d['precip'], 'sun': d['sun'], 'wind': d['wind']}[p]
    return d['temps'][m-1] if p == 'temp' else {'precip': d['precip'], 'sun': d['sun'], 'wind': d['wind']}[p]

def get_colors(p):
    if p == 'temp': return ['#313695','#4575b4','#74add1','#abd9e9','#e0f3f8','#ffffbf','#fee090','#fdae61','#f46d43','#d73027','#a50026']
    if p == 'precip': return ['#fff7ec','#fee8c8','#fdd49e','#fdbb84','#fc8d59','#ef6548','#d7301f','#b30000','#7f0000']
    if p == 'sun': return ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#08519c','#08306b']
    return ['#f7f7f7','#d9d9d9','#bdbdbd','#969696','#737373','#525252','#252525']

def val2color(v, vmin, vmax, colors):
    if vmax == vmin: return colors[len(colors)//2]
    n = max(0, min(1, (v - vmin) / (vmax - vmin)))
    idx = n * (len(colors) - 1)
    i = int(idx)
    if i >= len(colors) - 1: return colors[-1]
    t = idx - i
    c1 = [int(colors[i][j:j+2], 16) for j in (1,3,5)]
    c2 = [int(colors[i+1][j:j+2], 16) for j in (1,3,5)]
    return f'#{int(c1[0]+(c2[0]-c1[0])*t):02x}{int(c1[1]+(c2[1]-c1[1])*t):02x}{int(c1[2]+(c2[2]-c1[2])*t):02x}'

@st.cache_data
def make_grid(param, month, grid_size):
    pts, vals = [], []
    for d in STATIONS.values():
        pts.append((d['lon'], d['lat']))
        vals.append(get_val(d, param, month))
    pts, vals = np.array(pts), np.array(vals)
    
    # Мелкая сетка + сглаживание
    lon_r = np.linspace(KZ_BOUNDS[0], KZ_BOUNDS[2], grid_size)
    lat_r = np.linspace(KZ_BOUNDS[1], KZ_BOUNDS[3], grid_size)
    lon_g, lat_g = np.meshgrid(lon_r, lat_r)
    
    z = griddata(pts, vals, (lon_g, lat_g), method='cubic')
    z_near = griddata(pts, vals, (lon_g, lat_g), method='nearest')
    z = np.where(np.isnan(z), z_near, z)
    z = gaussian_filter(z, sigma=1.2)  # Сглаживание!
    
    features = []
    cw = (KZ_BOUNDS[2] - KZ_BOUNDS[0]) / grid_size
    ch = (KZ_BOUNDS[3] - KZ_BOUNDS[1]) / grid_size
    
    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            cx, cy = lon_r[j] + cw/2, lat_r[i] + ch/2
            if not KZ_POLYGON.contains(Point(cx, cy)): continue
            coords = [[[lon_r[j], lat_r[i]], [lon_r[j+1], lat_r[i]], [lon_r[j+1], lat_r[i+1]], [lon_r[j], lat_r[i+1]], [lon_r[j], lat_r[i]]]]
            v = (z[i,j] + z[i+1,j] + z[i,j+1] + z[i+1,j+1]) / 4
            features.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": coords}, "properties": {"value": round(v, 1)}})
    
    vmin = min(f['properties']['value'] for f in features)
    vmax = max(f['properties']['value'] for f in features)
    return {"type": "FeatureCollection", "features": features}, vmin, vmax, vals

def make_map(param, month, grid_size, opacity, basemap, show_st, show_ct, show_bd):
    m = folium.Map(location=[48.0, 67.0], zoom_start=5, tiles=None)
    bm = BASEMAPS[basemap]
    folium.TileLayer(tiles=bm['tiles'] if not bm['tiles'].startswith('http') else bm['tiles'], attr='').add_to(m)
    
    grid, vmin, vmax, st_vals = make_grid(param, month, grid_size)
    colors = get_colors(param)
    
    def style(f):
        c = val2color(f['properties']['value'], vmin, vmax, colors)
        return {'fillColor': c, 'color': c, 'weight': 0, 'fillOpacity': opacity}
    
    GeoJson(grid, style_function=style, tooltip=folium.GeoJsonTooltip(fields=['value'], aliases=[f'{t(param)}: '])).add_to(m)
    
    if show_bd:
        GeoJson(KZ_GEOJSON, style_function=lambda x: {'fillColor': 'none', 'color': '#dc2626', 'weight': 2.5}).add_to(m)
    if show_st:
        for n, d in STATIONS.items():
            v = get_val(d, param, month)
            folium.CircleMarker([d['lat'], d['lon']], radius=6, color='#1e293b', fill=True, fillColor='white', fillOpacity=0.9, weight=2, tooltip=f"<b>{n}</b><br>{v:.1f}{get_unit(param)}").add_to(m)
    if show_ct:
        for c, (lat, lon) in CITIES.items():
            folium.CircleMarker([lat, lon], radius=4, color='#3b82f6', fill=True, fillColor='#1e293b', fillOpacity=1, weight=2, tooltip=c).add_to(m)
    Fullscreen().add_to(m)
    return m, vmin, vmax, st_vals

def make_chart(rk):
    d = REGIONS[rk]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t('months')[1:], y=d['temps'], fill='tozeroy', fillcolor='rgba(220,38,38,0.15)', line=dict(color='#dc2626', width=3), mode='lines+markers', marker=dict(size=8, color='#dc2626', line=dict(color='white', width=2))))
    fig.add_hline(y=0, line_dash="dash", line_color="#64748b")
    fig.update_layout(title=dict(text=f"{t('cycle')}: {d[f'name_{st.session_state.lang}']}", font=dict(size=15, color='#f1f5f9')), xaxis=dict(color='#94a3b8', gridcolor='#334155'), yaxis=dict(title="°C", color='#94a3b8', gridcolor='#334155'), template='plotly_dark', paper_bgcolor='#141b2d', plot_bgcolor='#141b2d', height=340, margin=dict(l=50, r=30, t=50, b=40))
    return fig

def make_compare(param):
    names = [REGIONS[k][f'name_{st.session_state.lang}'] for k in REGIONS]
    pk = {'temp': 't_year', 'precip': 'precip', 'sun': 'sun', 'wind': 'wind'}[param]
    vals = [REGIONS[k].get(pk, REGIONS[k].get('t_year')) for k in REGIONS]
    data = sorted(zip(names, vals), key=lambda x: x[1], reverse=True)
    ns, vs = zip(*data)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(vs), y=list(ns), orientation='h', marker=dict(color='#dc2626'), text=[f"{v}{get_unit(param)}" for v in vs], textposition='outside'))
    fig.update_layout(xaxis=dict(title=get_unit(param), color='#94a3b8', gridcolor='#334155'), yaxis=dict(autorange='reversed', color='#94a3b8'), template='plotly_dark', paper_bgcolor='#141b2d', plot_bgcolor='#141b2d', height=480, margin=dict(l=120, r=70, t=20, b=40))
    return fig

def make_timeline_chart(city, param_key):
    """График изменения климата за 50 лет"""
    if city == 'kz_avg':
        data = KZ_AVERAGE
        name = t('kz_avg')
    else:
        data = CLIMATE_HISTORY.get(city, CLIMATE_HISTORY['Астана'])
        name = city
    
    years = data['years']
    values = data[param_key]
    
    # Определяем цвета и единицы
    if param_key == 'precip':
        color = '#3b82f6'
        unit = 'мм'
        fill_color = 'rgba(59, 130, 246, 0.2)'
    else:
        color = '#dc2626'
        unit = '°C'
        fill_color = 'rgba(220, 38, 38, 0.2)'
    
    fig = go.Figure()
    
    # Основная линия
    fig.add_trace(go.Scatter(
        x=years, y=values,
        mode='lines+markers',
        line=dict(color=color, width=3),
        marker=dict(size=10, color=color, line=dict(color='white', width=2)),
        fill='tozeroy' if param_key == 'precip' else None,
        fillcolor=fill_color if param_key == 'precip' else None,
        name=name,
        hovertemplate=f'%{{x}}: %{{y:.1f}}{unit}<extra></extra>'
    ))
    
    # Линия тренда
    z = np.polyfit(years, values, 1)
    p = np.poly1d(z)
    fig.add_trace(go.Scatter(
        x=years, y=p(years),
        mode='lines',
        line=dict(color='#facc15', width=2, dash='dash'),
        name=t('trend'),
        hoverinfo='skip'
    ))
    
    # Вычисляем изменение
    change = values[-1] - values[0]
    change_per_decade = change / 5  # 5 десятилетий
    
    param_names = {'t_year': t('year_temp'), 't_jan': t('jan_temp'), 't_jul': t('jul_temp'), 'precip': t('year_precip')}
    
    fig.update_layout(
        title=dict(
            text=f"{param_names.get(param_key, param_key)}: {name}",
            font=dict(size=16, color='#f1f5f9')
        ),
        xaxis=dict(
            title="", color='#94a3b8', gridcolor='#334155',
            tickmode='array', tickvals=years, ticktext=[str(y) for y in years]
        ),
        yaxis=dict(title=unit, color='#94a3b8', gridcolor='#334155'),
        template='plotly_dark',
        paper_bgcolor='#141b2d',
        plot_bgcolor='#141b2d',
        height=380,
        margin=dict(l=60, r=30, t=60, b=50),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig, change, change_per_decade

def make_multi_city_chart(param_key):
    """Сравнение нескольких городов за 50 лет"""
    colors = ['#dc2626', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
    
    fig = go.Figure()
    
    for i, (city, data) in enumerate(CLIMATE_HISTORY.items()):
        fig.add_trace(go.Scatter(
            x=data['years'], y=data[param_key],
            mode='lines+markers',
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6),
            name=city
        ))
    
    # Среднее по КЗ
    fig.add_trace(go.Scatter(
        x=KZ_AVERAGE['years'], y=KZ_AVERAGE[param_key],
        mode='lines',
        line=dict(color='white', width=3, dash='dot'),
        name=t('kz_avg')
    ))
    
    unit = 'мм' if param_key == 'precip' else '°C'
    param_names = {'t_year': t('year_temp'), 't_jan': t('jan_temp'), 't_jul': t('jul_temp'), 'precip': t('year_precip')}
    
    fig.update_layout(
        title=dict(text=f"{param_names.get(param_key, param_key)} (1975-2024)", font=dict(size=16, color='#f1f5f9')),
        xaxis=dict(title="", color='#94a3b8', gridcolor='#334155'),
        yaxis=dict(title=unit, color='#94a3b8', gridcolor='#334155'),
        template='plotly_dark',
        paper_bgcolor='#141b2d',
        plot_bgcolor='#141b2d',
        height=420,
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5)
    )
    
    return fig

def ask_ai(q):
    # Исправленный промпт - отвечать на выбранном языке
    lang_map = {'ru': 'русском языке', 'kk': 'қазақ тілінде', 'en': 'English'}
    lang_instr = lang_map.get(st.session_state.lang, 'русском языке')
    
    data = "\n".join([f"{n}: среднегодовая {d['t_year']}°C, январь {d['t_jan']}°C, июль {d['t_jul']}°C, осадки {d['precip']}мм" for n, d in STATIONS.items()])
    
    system_prompt = f"""Ты - климатолог-эксперт РГП «Казгидромет» Казахстана. 
ВАЖНО: Отвечай ТОЛЬКО на {lang_instr}. Не используй китайский или другие языки.
Используй данные метеостанций для ответов. Будь точным и информативным.

Данные метеостанций Казахстана:
{data}"""

    try:
        r = requests.post(API_URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, 
            json={"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": q}
            ], "max_tokens": 1000, "temperature": 0.7}, timeout=60, verify=False)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return f"Ошибка API: {r.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"

# ============================================================================
# MAIN
# ============================================================================
def main():
    # Header
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f'<div class="main-header"><h1>🌡️ {t("title")}</h1><p>{t("subtitle")}</p></div>', unsafe_allow_html=True)
    with c2:
        st.write("")
        cols = st.columns(3)
        for i, (code, flag) in enumerate([('kk','🇰🇿'), ('ru','🇷🇺'), ('en','🇬🇧')]):
            if cols[i].button(flag, key=f"l_{code}", use_container_width=True, type="primary" if st.session_state.lang == code else "secondary"):
                st.session_state.lang = code
                st.rerun()
    
    # Controls
    cc = st.columns([1,1,1,1,3])
    for col, (p, icon) in zip(cc[:4], [('temp','🌡️'), ('precip','💧'), ('sun','☀️'), ('wind','💨')]):
        if col.button(f"{icon} {t(p)}", key=f"p_{p}", use_container_width=True, type="primary" if st.session_state.param == p else "secondary"):
            st.session_state.param = p
            st.rerun()
    with cc[4]:
        st.session_state.month = st.select_slider(t('period'), list(range(13)), st.session_state.month, format_func=lambda x: t('months')[x])
    
    # Tabs
    tabs = st.tabs([t('map'), t('compare'), t('chart'), t('timeline'), t('ai')])
    
    # MAP
    with tabs[0]:
        mc, ctrl = st.columns([4, 1])
        with ctrl:
            st.markdown(f"**{t('basemap')}**")
            bm = st.selectbox("", list(BASEMAPS.keys()), list(BASEMAPS.keys()).index(st.session_state.basemap), format_func=lambda k: BASEMAPS[k][f'name_{st.session_state.lang}'], label_visibility="collapsed")
            if bm != st.session_state.basemap: st.session_state.basemap = bm
            
            st.markdown(f"**{t('detail')}**")
            st.session_state.grid_size = st.slider("", 35, 75, st.session_state.grid_size, label_visibility="collapsed")
            
            st.markdown(f"**{t('opacity')}**")
            st.session_state.opacity = st.slider("", 0.4, 1.0, st.session_state.opacity, 0.05, label_visibility="collapsed")
            
            st.session_state.show_stations = st.checkbox(t('stations'), st.session_state.show_stations)
            st.session_state.show_cities = st.checkbox(t('cities'), st.session_state.show_cities)
            st.session_state.show_boundary = st.checkbox(t('boundary'), st.session_state.show_boundary)
            st.markdown("---")
        
        with mc:
            fmap, vmin, vmax, st_vals = make_map(st.session_state.param, st.session_state.month, st.session_state.grid_size, st.session_state.opacity, st.session_state.basemap, st.session_state.show_stations, st.session_state.show_cities, st.session_state.show_boundary)
            st_folium(fmap, height=530, use_container_width=True)
        
        with ctrl:
            # Красивая легенда
            colors = get_colors(st.session_state.param)
            grad = ', '.join(reversed(colors))
            hi = t('hot') if st.session_state.param == 'temp' else t('high')
            lo = t('cold') if st.session_state.param == 'temp' else t('low')
            unit = get_unit(st.session_state.param)
            
            st.markdown(f'''
            <div class="legend-box">
                <div class="legend-title">📊 {t("legend")}</div>
                <div style="display:flex; align-items:stretch;">
                    <div class="legend-gradient" style="background:linear-gradient(to bottom, {grad});"></div>
                    <div class="legend-labels">
                        <div class="legend-label">{hi}<br><b>{vmax:.1f}</b>{unit}</div>
                        <div class="legend-label" style="text-align:center;">—</div>
                        <div class="legend-label">{lo}<br><b>{vmin:.1f}</b>{unit}</div>
                    </div>
                </div>
            </div>''', unsafe_allow_html=True)
            
            # Stats
            for v, l in [(max(st_vals), 'max'), (min(st_vals), 'min'), (np.mean(st_vals), 'avg')]:
                st.markdown(f'<div class="stat-card"><div class="stat-value">{v:.1f}</div><div class="stat-label">{t(l)} ({unit})</div></div>', unsafe_allow_html=True)
    
    # COMPARE
    with tabs[1]:
        st.plotly_chart(make_compare(st.session_state.param), use_container_width=True)
    
    # CHART
    with tabs[2]:
        c1, c2 = st.columns([2, 1])
        with c1:
            rks = list(REGIONS.keys())
            idx = st.selectbox(t('region'), range(len(rks)), format_func=lambda i: REGIONS[rks[i]][f'name_{st.session_state.lang}'])
            st.plotly_chart(make_chart(rks[idx]), use_container_width=True)
        with c2:
            d = REGIONS[rks[idx]]
            st.markdown(f"### {d[f'name_{st.session_state.lang}']}")
            st.markdown(f"🏔️ **{t('zone')}:** {t(d['zone'])}")
            m1, m2 = st.columns(2)
            m1.metric("🌡️ Год", f"{d['t_year']}°C")
            m2.metric("💧", f"{d['precip']} мм")
            m1.metric("❄️ Янв", f"{d['t_jan']}°C")
            m2.metric("🔥 Июл", f"{d['t_jul']}°C")
    
    # TIMELINE
    with tabs[3]:
        st.markdown(f'''
        <div style="background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(16,185,129,0.1)); padding: 1.25rem; border-radius: 14px; border: 1px solid rgba(59,130,246,0.2); margin-bottom: 1rem;">
            <h4 style="margin:0; color:#f8fafc;">📅 {t("timeline_title")}</h4>
            <p style="margin:0.5rem 0 0 0; color:#94a3b8;">{t("timeline_desc")}</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Контролы
        tc1, tc2 = st.columns([1, 1])
        with tc1:
            city_options = ['kz_avg'] + list(CLIMATE_HISTORY.keys())
            city_names = [t('kz_avg')] + list(CLIMATE_HISTORY.keys())
            selected_city = st.selectbox(t('select_city'), city_options, format_func=lambda x: t('kz_avg') if x == 'kz_avg' else x)
        with tc2:
            param_options = ['t_year', 't_jan', 't_jul', 'precip']
            param_names_map = {'t_year': t('year_temp'), 't_jan': t('jan_temp'), 't_jul': t('jul_temp'), 'precip': t('year_precip')}
            selected_param = st.selectbox(t('select_param'), param_options, format_func=lambda x: param_names_map[x])
        
        # Графики
        gc1, gc2 = st.columns([2, 1])
        
        with gc1:
            fig, change, change_decade = make_timeline_chart(selected_city, selected_param)
            st.plotly_chart(fig, use_container_width=True)
        
        with gc2:
            # Статистика изменений
            unit = 'мм' if selected_param == 'precip' else '°C'
            trend_text = t('warming') if change > 0 and selected_param != 'precip' else (t('cooling') if change < 0 and selected_param != 'precip' else '')
            
            st.markdown(f'''
            <div class="stat-card" style="margin-top: 20px;">
                <div class="stat-label">{t("change")} {t("since_1975")}</div>
                <div class="stat-value" style="color: {"#ef4444" if change > 0 and selected_param != "precip" else "#3b82f6"};">
                    {"+" if change > 0 else ""}{change:.1f}{unit}
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                    {trend_text}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown(f'''
            <div class="stat-card">
                <div class="stat-label">{t("change")} {t("per_decade")}</div>
                <div class="stat-value" style="color: {"#ef4444" if change_decade > 0 and selected_param != "precip" else "#3b82f6"};">
                    {"+" if change_decade > 0 else ""}{change_decade:.2f}{unit}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Мини-факты
            if selected_param == 't_year':
                st.markdown('''
                <div style="background: rgba(239, 68, 68, 0.1); padding: 1rem; border-radius: 10px; border-left: 3px solid #ef4444; margin-top: 1rem;">
                    <div style="font-size: 0.8rem; color: #f8fafc;">🌡️ <b>Факт</b></div>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                        Казахстан теплеет быстрее среднемирового — на ~0.3°C за десятилетие
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            elif selected_param == 'precip':
                st.markdown('''
                <div style="background: rgba(59, 130, 246, 0.1); padding: 1rem; border-radius: 10px; border-left: 3px solid #3b82f6; margin-top: 1rem;">
                    <div style="font-size: 0.8rem; color: #f8fafc;">💧 <b>Факт</b></div>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                        Осадки сокращаются, особенно в южных и западных регионах
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        
        # Сравнение всех городов
        st.markdown("---")
        st.markdown(f"### 🏙️ Сравнение городов")
        st.plotly_chart(make_multi_city_chart(selected_param), use_container_width=True)
    
    # AI
    with tabs[4]:
        st.markdown(f'<div class="chat-box"><h4 style="margin:0;color:#f8fafc;">🤖 {t("ai_title")}</h4><p style="color:#94a3b8;margin:0.5rem 0 0 0;">{t("ai_hint")}</p></div>', unsafe_allow_html=True)
        st.write("")
        qc = st.columns(2)
        for col, q in [(qc[0], 'q1'), (qc[1], 'q2'), (qc[0], 'q3'), (qc[1], 'q4')]:
            if col.button(t(q), key=q, use_container_width=True):
                st.session_state['ai_q'] = t(q)
        
        question = st.text_area("", value=st.session_state.get('ai_q', ''), placeholder=t('ai_hint'), height=80, label_visibility="collapsed")
        bc = st.columns([1, 1, 3])
        if bc[0].button(f"🔍 {t('ask')}", type="primary", use_container_width=True) and question:
            with st.spinner("⏳"):
                ans = ask_ai(question)
                st.session_state.chat_history.append({'q': question, 'a': ans})
                st.session_state.pop('ai_q', None)
                st.rerun()
        if bc[1].button(f"🗑️ {t('clear')}", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        for item in reversed(st.session_state.chat_history):
            st.markdown(f'<div class="chat-msg chat-user">👤 {item["q"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-msg chat-ai">🤖 {item["a"]}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
