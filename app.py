"""
Климат Казахстана - Интерактивный портал
Казгидромет - 3 языка: Қазақша / Русский / English
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import urllib3
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Климат Казахстана | Казгидромет", page_icon="🌤️", layout="wide", initial_sidebar_state="expanded")

if 'selected_layer' not in st.session_state: st.session_state.selected_layer = 'temperature'
if 'current_page' not in st.session_state: st.session_state.current_page = 0
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'lang' not in st.session_state: st.session_state.lang = 'ru'

API_KEY = "sk-xquciybelqijbpxynvxppleljcwbbizelikzxvorrinirlqt"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab5 100%);
    border-radius: 20px; padding: 2.5rem; margin-bottom: 2rem; text-align: center;
    box-shadow: 0 10px 40px rgba(30, 58, 95, 0.3);
}
.main-header h1 { font-size: 2.8rem; margin-bottom: 0.5rem; color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
.main-header p { color: #b8d4e8; font-size: 1.2rem; }
.metric-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 1px solid #e0e0e0; border-radius: 16px; padding: 1.5rem; text-align: center;
    transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 1rem;
}
.metric-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); border-color: #1976d2; }
.metric-value {
    font-size: 2.2rem; font-weight: 700;
    background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.metric-label { color: #666; font-size: 0.95rem; margin-top: 0.5rem; font-weight: 500; }
.info-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border: 1px solid #e0e0e0; border-radius: 16px; padding: 1.8rem; margin: 1rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}
.info-card p { color: #444; font-size: 1.05rem; line-height: 1.7; margin-bottom: 1rem; }
.climate-zone-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border-left: 5px solid;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: all 0.3s ease;
}
.climate-zone-card:hover { transform: translateX(5px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.city-card {
    background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
    border: 1px solid #d0e3f7; border-radius: 16px; padding: 1.5rem; margin: 1rem 0;
    box-shadow: 0 4px 15px rgba(25, 118, 210, 0.1);
}
.city-card h3 { color: #1565c0; margin-bottom: 1rem; font-size: 1.4rem; }
.bulletin-link {
    display: block; background: linear-gradient(135deg, #f0f7ff 0%, #e3f2fd 100%);
    border: 1px solid #90caf9; border-radius: 12px; padding: 1rem 1.2rem; margin: 0.7rem 0;
    color: #1565c0; text-decoration: none; transition: all 0.3s ease; font-weight: 500;
}
.bulletin-link:hover {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    border-color: #1976d2; transform: translateX(5px); box-shadow: 0 4px 12px rgba(25, 118, 210, 0.2);
}
.ai-chat-box { background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%); border: 1px solid #90caf9; border-radius: 16px; padding: 1.5rem; margin: 1rem 0; }
.user-message { background: #e3f2fd; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #1976d2; }
.ai-message { background: #f5f5f5; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #4caf50; }
</style>
""", unsafe_allow_html=True)

TR = {
    'ru': {
        'title': '🌤️ Климат Казахстана', 'subtitle': 'Интерактивный портал климатических данных РГП «Казгидромет»',
        'pages': ['🏠 Главная', '🗺️ Интерактивная карта', '📊 Климат городов', '🏔️ Климатические зоны', '🤖 ИИ-анализ', '📋 Бюллетени'],
        'nav': 'Навигация', 'contacts': '📞 Контакты',
        'contact_info': '**РГП «Казгидромет»**\n\nг. Астана\n\n📧 info@kazhydromet.kz\n\n🌐 kazhydromet.kz',
        'area': 'км² площадь', 'lat_pos': 'с.ш. широта', 'zones_count': 'климат. зон', 'stations': 'метеостанций',
        'about': '📖 О климате Казахстана', 'norms': '📈 Климатические нормы',
        'jan_temp': 'Ср. температура января', 'jul_temp': 'Ср. температура июля', 'precip': 'Годовые осадки',
        'quick_access': '🗺️ Быстрый доступ к картам',
        'temp_map': '🌡️ Карта температур', 'precip_map': '💧 Карта осадков', 'sun_map': '☀️ Карта солнечного сияния',
        'map_title': '🗺️ Интерактивная климатическая карта',
        'map_hint': '💡 Панель слоёв справа вверху для переключения между картами',
        'select_param': 'Выберите параметр:', 'legend': '📍 Легенда',
        'avg_temp': 'Среднегодовая температура:', 'annual_precip': 'Годовые осадки:', 'sun_hours_legend': 'Солнечное сияние:',
        'cold': 'Холодный', 'cool': 'Прохладный', 'moderate': 'Умеренный', 'warm': 'Тёплый',
        'arid': 'Засушливый', 'sufficient': 'Достаточный', 'humid': 'Влажный',
        'low_sun': 'Умеренное', 'high_sun': 'Высокое', 'very_high_sun': 'Очень высокое',
        'hints': '💡 Подсказки:', 'click_info': '• Кликните на маркер', 'layer_hint': '• Слои справа вверху',
        'cities_title': '📊 Климат городов Казахстана', 'select_city': 'Выберите город',
        'zone': 'Климатическая зона', 'coords': 'Координаты',
        'year_temp': 'Ср. годовая температура', 'year_precip': 'Годовые осадки', 'sun_hours': 'Солнечное сияние', 'wind': 'Ср. скорость ветра',
        'chart_title': 'Годовой ход температуры в г.', 'month': 'Месяц', 'temp_c': 'Температура (°C)',
        'compare': '📊 Сравнение городов', 'select_compare': 'Выберите города',
        'temp_compare': 'Среднегодовая температура', 'precip_compare': 'Годовые осадки',
        'zones_title': '🏔️ Климатические зоны Казахстана',
        'jan': 'Температура января', 'jul': 'Температура июля', 'zone_precip': 'Годовые осадки',
        'distribution': '📊 Распределение по площади', 'zone_share': 'Доля зон (%)',
        'ai_title': '🤖 ИИ-анализ климата',
        'ai_desc': 'Задайте вопрос о климате Казахстана. ИИ-ассистент поможет проанализировать данные и дать рекомендации.',
        'examples': '💡 Примеры:',
        'q1': '🌡️ Сравни климат Астаны и Алматы', 'q2': '🏔️ Какой город самый холодный?',
        'q3': '☀️ Где больше всего солнца?', 'q4': '🌧️ Анализ осадков по регионам',
        'your_q': 'Ваш вопрос:', 'placeholder': 'Например: Какой климат в Караганде?',
        'analyze': '🔍 Анализировать', 'clear': '🗑️ Очистить', 'thinking': '🤔 Анализ...',
        'history': '💬 История', 'you': 'Вы', 'ai': 'ИИ',
        'bulletins_title': '📋 Бюллетени Казгидромета',
        'bulletins_desc': 'Мониторинг климата осуществляется РГП «Казгидромет» при координации с ВМО.',
        'publications': '📥 Публикации', 'by_regions': '📊 По областям',
        'region': 'Область', 'avg_t': 'Ср. t (°C)', 'precip_mm': 'Осадки (мм)', 'zone_col': 'Зона',
        'months': ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
        'desc1': 'Положение Казахстана в умеренных широтах (40-55°с.ш.) определяет высокие значения притока солнечной радиации.',
        'desc2': 'От Атлантического океана Казахстан удалён на 2000-3000 км, что обуславливает континентальность климата.',
        'desc3': 'Поверхность отличается разнообразием: от низменностей до высокогорий на востоке и юго-востоке.',
        'forest_steppe': 'Лесостепная', 'steppe': 'Степная', 'semi_desert': 'Полупустынная', 'desert': 'Пустынная', 'foothill': 'Предгорная',
        'forest_steppe_desc': 'Север страны. Холодная зима, тёплое лето. Наибольшее увлажнение среди равнин.',
        'steppe_desc': 'Центр и север. Резко-континентальный сухой климат с большими перепадами температур.',
        'semi_desert_desc': 'Переходная зона. Жаркое сухое лето, холодная малоснежная зима.',
        'desert_desc': 'Юг и запад. Жаркое лето, мягкая зима. Минимум осадков.',
        'foothill_desc': 'Юго-восток, предгорья Тянь-Шаня и Алтая. Наибольшее увлажнение, мягкий климат.',
    },
    'kk': {
        'title': '🌤️ Қазақстан климаты', 'subtitle': '«Қазгидромет» ЖМК климаттық деректер порталы',
        'pages': ['🏠 Басты', '🗺️ Карта', '📊 Қалалар', '🏔️ Аймақтар', '🤖 ЖИ-талдау', '📋 Бюллетень'],
        'nav': 'Навигация', 'contacts': '📞 Байланыс',
        'contact_info': '**«Қазгидромет» ЖМК**\n\nАстана қ.\n\n📧 info@kazhydromet.kz\n\n🌐 kazhydromet.kz',
        'area': 'км² аумақ', 'lat_pos': 'с.е. ендік', 'zones_count': 'климат. аймақ', 'stations': 'метеостанция',
        'about': '📖 Қазақстан климаты', 'norms': '📈 Климаттық нормалар',
        'jan_temp': 'Қаңтар температурасы', 'jul_temp': 'Шілде температурасы', 'precip': 'Жылдық жауын-шашын',
        'quick_access': '🗺️ Жылдам қол жеткізу',
        'temp_map': '🌡️ Температура', 'precip_map': '💧 Жауын-шашын', 'sun_map': '☀️ Күн сәулесі',
        'map_title': '🗺️ Интерактивті климаттық карта',
        'map_hint': '💡 Қабаттар панелі жоғарғы оң жақта',
        'select_param': 'Параметрді таңдаңыз:', 'legend': '📍 Шартты белгілер',
        'avg_temp': 'Орташа жылдық температура:', 'annual_precip': 'Жылдық жауын-шашын:', 'sun_hours_legend': 'Күн сәулесі:',
        'cold': 'Суық', 'cool': 'Салқын', 'moderate': 'Қалыпты', 'warm': 'Жылы',
        'arid': 'Құрғақ', 'sufficient': 'Жеткілікті', 'humid': 'Ылғалды',
        'low_sun': 'Орташа', 'high_sun': 'Жоғары', 'very_high_sun': 'Өте жоғары',
        'hints': '💡 Кеңестер:', 'click_info': '• Маркерді басыңыз', 'layer_hint': '• Қабаттар жоғарыда',
        'cities_title': '📊 Қалалар климаты', 'select_city': 'Қаланы таңдаңыз',
        'zone': 'Климаттық аймақ', 'coords': 'Координаттар',
        'year_temp': 'Орт. жылдық t', 'year_precip': 'Жылдық жауын-шашын', 'sun_hours': 'Күн сәулесі', 'wind': 'Орт. жел',
        'chart_title': 'Жылдық температура', 'month': 'Ай', 'temp_c': 'Температура (°C)',
        'compare': '📊 Салыстыру', 'select_compare': 'Қалаларды таңдаңыз',
        'temp_compare': 'Орташа температура', 'precip_compare': 'Жауын-шашын',
        'zones_title': '🏔️ Климаттық аймақтар',
        'jan': 'Қаңтар t', 'jul': 'Шілде t', 'zone_precip': 'Жауын-шашын',
        'distribution': '📊 Аумақ бойынша', 'zone_share': 'Аймақтар үлесі (%)',
        'ai_title': '🤖 ЖИ климат талдауы',
        'ai_desc': 'Қазақстан климаты туралы сұрақ қойыңыз.',
        'examples': '💡 Мысалдар:',
        'q1': '🌡️ Астана мен Алматы', 'q2': '🏔️ Ең суық қала?',
        'q3': '☀️ Күн қайда көп?', 'q4': '🌧️ Жауын-шашын талдауы',
        'your_q': 'Сұрағыңыз:', 'placeholder': 'Мысалы: Қарағандыда қандай климат?',
        'analyze': '🔍 Талдау', 'clear': '🗑️ Тазалау', 'thinking': '🤔 Талдау...',
        'history': '💬 Тарих', 'you': 'Сіз', 'ai': 'ЖИ',
        'bulletins_title': '📋 Қазгидромет бюллетеньдері',
        'bulletins_desc': 'Климат мониторингін ДМҰ-мен бірлесіп «Қазгидромет» ЖМК жүзеге асырады.',
        'publications': '📥 Жарияланымдар', 'by_regions': '📊 Облыстар',
        'region': 'Облыс', 'avg_t': 'Орт. t', 'precip_mm': 'Жауын (мм)', 'zone_col': 'Аймақ',
        'months': ['Қаң', 'Ақп', 'Нау', 'Сәу', 'Мам', 'Мау', 'Шіл', 'Там', 'Қыр', 'Қаз', 'Қар', 'Жел'],
        'desc1': 'Қазақстанның қоңыржай ендіктерде орналасуы күн радиациясының жоғары түсуін анықтайды.',
        'desc2': 'Атлант мұхитынан 2000-3000 км қашықтықта орналасқан.',
        'desc3': 'Жер беті алуан түрлі: жазықтардан биік таулар.',
        'forest_steppe': 'Орманды дала', 'steppe': 'Дала', 'semi_desert': 'Шөлейт', 'desert': 'Шөл', 'foothill': 'Тау бөктері',
        'forest_steppe_desc': 'Солтүстік. Суық қыс, жылы жаз.', 'steppe_desc': 'Орталық. Құрғақ континентальды климат.',
        'semi_desert_desc': 'Өтпелі аймақ. Ыстық жаз, суық қыс.', 'desert_desc': 'Оңтүстік. Ыстық жаз, жұмсақ қыс.',
        'foothill_desc': 'Оңтүстік-шығыс. Ең көп ылғалдылық.',
    },
    'en': {
        'title': '🌤️ Climate of Kazakhstan', 'subtitle': 'RSE «Kazhydromet» Interactive Climate Portal',
        'pages': ['🏠 Home', '🗺️ Map', '📊 Cities', '🏔️ Zones', '🤖 AI Analysis', '📋 Bulletins'],
        'nav': 'Navigation', 'contacts': '📞 Contacts',
        'contact_info': '**RSE «Kazhydromet»**\n\nAstana\n\n📧 info@kazhydromet.kz\n\n🌐 kazhydromet.kz',
        'area': 'km² area', 'lat_pos': 'N latitude', 'zones_count': 'climate zones', 'stations': 'weather stations',
        'about': '📖 About Climate', 'norms': '📈 Climate Norms',
        'jan_temp': 'Avg. January temp', 'jul_temp': 'Avg. July temp', 'precip': 'Annual precipitation',
        'quick_access': '🗺️ Quick Access',
        'temp_map': '🌡️ Temperature', 'precip_map': '💧 Precipitation', 'sun_map': '☀️ Sunshine',
        'map_title': '🗺️ Interactive Climate Map',
        'map_hint': '💡 Layer panel in top right corner',
        'select_param': 'Select parameter:', 'legend': '📍 Legend',
        'avg_temp': 'Avg. annual temperature:', 'annual_precip': 'Annual precipitation:', 'sun_hours_legend': 'Sunshine:',
        'cold': 'Cold', 'cool': 'Cool', 'moderate': 'Moderate', 'warm': 'Warm',
        'arid': 'Arid', 'sufficient': 'Sufficient', 'humid': 'Humid',
        'low_sun': 'Moderate', 'high_sun': 'High', 'very_high_sun': 'Very high',
        'hints': '💡 Hints:', 'click_info': '• Click marker', 'layer_hint': '• Layers top right',
        'cities_title': '📊 City Climate', 'select_city': 'Select city',
        'zone': 'Climate zone', 'coords': 'Coordinates',
        'year_temp': 'Avg. annual temp', 'year_precip': 'Annual precip', 'sun_hours': 'Sunshine', 'wind': 'Avg. wind',
        'chart_title': 'Annual temperature in', 'month': 'Month', 'temp_c': 'Temperature (°C)',
        'compare': '📊 Compare', 'select_compare': 'Select cities',
        'temp_compare': 'Avg. temperature', 'precip_compare': 'Precipitation',
        'zones_title': '🏔️ Climate Zones',
        'jan': 'January temp', 'jul': 'July temp', 'zone_precip': 'Precipitation',
        'distribution': '📊 Distribution by area', 'zone_share': 'Zone share (%)',
        'ai_title': '🤖 AI Climate Analysis',
        'ai_desc': 'Ask about Kazakhstan climate.',
        'examples': '💡 Examples:',
        'q1': '🌡️ Compare Astana & Almaty', 'q2': '🏔️ Coldest city?',
        'q3': '☀️ Most sunshine?', 'q4': '🌧️ Precipitation analysis',
        'your_q': 'Your question:', 'placeholder': 'Example: Climate in Karaganda?',
        'analyze': '🔍 Analyze', 'clear': '🗑️ Clear', 'thinking': '🤔 Analyzing...',
        'history': '💬 History', 'you': 'You', 'ai': 'AI',
        'bulletins_title': '📋 Kazhydromet Bulletins',
        'bulletins_desc': 'Climate monitoring by Kazhydromet in coordination with WMO.',
        'publications': '📥 Publications', 'by_regions': '📊 By Regions',
        'region': 'Region', 'avg_t': 'Avg. t', 'precip_mm': 'Precip (mm)', 'zone_col': 'Zone',
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'desc1': 'Kazakhstan in temperate latitudes (40-55°N) receives high solar radiation.',
        'desc2': 'Located 2000-3000 km from the Atlantic Ocean.',
        'desc3': 'Surface varies from lowlands to mountains in east and southeast.',
        'forest_steppe': 'Forest-steppe', 'steppe': 'Steppe', 'semi_desert': 'Semi-desert', 'desert': 'Desert', 'foothill': 'Foothill',
        'forest_steppe_desc': 'North. Cold winter, warm summer.', 'steppe_desc': 'Central. Dry continental climate.',
        'semi_desert_desc': 'Transition zone. Hot dry summer.', 'desert_desc': 'South. Hot summer, mild winter.',
        'foothill_desc': 'Southeast. Highest moisture.',
    }
}

def t(key): return TR[st.session_state.lang].get(key, key)

CITIES = {
    'Астана': {'lat': 51.17, 'lon': 71.45, 't_jan': -14.2, 't_jul': 20.8, 't_year': 3.5, 'precip': 307, 'zone': 'steppe', 'sun': 2200, 'wind': 4.2,
        'name_kk': 'Астана', 'name_en': 'Astana',
        'desc_ru': 'Столица Казахстана. Резко-континентальный климат с холодной зимой и жарким летом.',
        'desc_kk': 'Қазақстан астанасы. Суық қысы және ыстық жазы бар резко-континентальды климат.',
        'desc_en': 'Capital of Kazakhstan. Sharply continental climate with cold winter and hot summer.'},
    'Алматы': {'lat': 43.22, 'lon': 76.85, 't_jan': -4.7, 't_jul': 23.8, 't_year': 10.2, 'precip': 600, 'zone': 'foothill', 'sun': 2500, 'wind': 1.7,
        'name_kk': 'Алматы', 'name_en': 'Almaty',
        'desc_ru': 'Крупнейший город. Мягкий климат благодаря предгорному расположению.',
        'desc_kk': 'Ең ірі қала. Тау бөктеріндегі орналасуының арқасында жұмсақ климат.',
        'desc_en': 'Largest city. Mild climate due to foothill location.'},
    'Шымкент': {'lat': 42.34, 'lon': 69.60, 't_jan': 0.3, 't_jul': 27.5, 't_year': 14.1, 'precip': 484, 'zone': 'semi_desert', 'sun': 2800, 'wind': 2.1,
        'name_kk': 'Шымкент', 'name_en': 'Shymkent',
        'desc_ru': 'Третий город страны. Жаркое лето и мягкая зима.',
        'desc_kk': 'Елдің үшінші қаласы. Ыстық жаз және жұмсақ қыс.',
        'desc_en': 'Third largest city. Hot summer and mild winter.'},
    'Караганда': {'lat': 49.80, 'lon': 73.11, 't_jan': -14.4, 't_jul': 20.4, 't_year': 2.9, 'precip': 295, 'zone': 'steppe', 'sun': 2400, 'wind': 4.8,
        'name_kk': 'Қарағанды', 'name_en': 'Karaganda',
        'desc_ru': 'Центр угольной промышленности. Суровый континентальный климат.',
        'desc_kk': 'Көмір өнеркәсібі орталығы. Қатал континентальды климат.',
        'desc_en': 'Coal industry center. Harsh continental climate.'},
    'Актобе': {'lat': 50.28, 'lon': 57.17, 't_jan': -14.8, 't_jul': 22.5, 't_year': 4.8, 'precip': 285, 'zone': 'semi_desert', 'sun': 2300, 'wind': 5.1,
        'name_kk': 'Ақтөбе', 'name_en': 'Aktobe',
        'desc_ru': 'Западный Казахстан. Резко-континентальный климат с сильными ветрами.',
        'desc_kk': 'Батыс Қазақстан. Қатты желдері бар резко-континентальды климат.',
        'desc_en': 'Western Kazakhstan. Sharply continental climate with strong winds.'},
    'Атырау': {'lat': 46.80, 'lon': 51.88, 't_jan': -7.8, 't_jul': 26.2, 't_year': 10.5, 'precip': 167, 'zone': 'desert', 'sun': 2600, 'wind': 4.5,
        'name_kk': 'Атырау', 'name_en': 'Atyrau',
        'desc_ru': 'Нефтяная столица на Каспии. Пустынный климат.',
        'desc_kk': 'Каспийдегі мұнай астанасы. Шөл климаты.',
        'desc_en': 'Oil capital on Caspian. Desert climate.'},
    'Актау': {'lat': 43.64, 'lon': 51.16, 't_jan': -0.8, 't_jul': 26.8, 't_year': 12.8, 'precip': 150, 'zone': 'desert', 'sun': 2900, 'wind': 5.8,
        'name_kk': 'Ақтау', 'name_en': 'Aktau',
        'desc_ru': 'Порт на Каспии. Самая мягкая зима, много солнца.',
        'desc_kk': 'Каспийдегі порт. Ең жұмсақ қыс, көп күн.',
        'desc_en': 'Caspian port. Mildest winter, lots of sun.'},
    'Кызылорда': {'lat': 44.85, 'lon': 65.51, 't_jan': -5.4, 't_jul': 28.1, 't_year': 11.7, 'precip': 129, 'zone': 'desert', 'sun': 2800, 'wind': 3.2,
        'name_kk': 'Қызылорда', 'name_en': 'Kyzylorda',
        'desc_ru': 'Долина Сырдарьи. Минимум осадков, очень жаркое лето.',
        'desc_kk': 'Сырдария аңғары. Ең аз жауын-шашын, өте ыстық жаз.',
        'desc_en': 'Syrdarya valley. Minimum precipitation, very hot summer.'},
    'Костанай': {'lat': 53.22, 'lon': 63.64, 't_jan': -16.2, 't_jul': 20.6, 't_year': 2.4, 'precip': 310, 'zone': 'forest_steppe', 'sun': 2100, 'wind': 4.4,
        'name_kk': 'Қостанай', 'name_en': 'Kostanay',
        'desc_ru': 'Север страны, житница. Суровый климат лесостепи.',
        'desc_kk': 'Елдің солтүстігі. Орманды дала климаты.',
        'desc_en': 'Northern granary. Forest-steppe climate.'},
    'Петропавловск': {'lat': 54.88, 'lon': 69.14, 't_jan': -17.1, 't_jul': 19.8, 't_year': 1.5, 'precip': 355, 'zone': 'forest_steppe', 'sun': 2000, 'wind': 3.9,
        'name_kk': 'Петропавл', 'name_en': 'Petropavlovsk',
        'desc_ru': 'Самый северный центр. Самый суровый климат.',
        'desc_kk': 'Ең солтүстік орталық. Ең қатал климат.',
        'desc_en': 'Northernmost center. Harshest climate.'},
    'Кокшетау': {'lat': 53.29, 'lon': 69.39, 't_jan': -15.8, 't_jul': 19.6, 't_year': 2.1, 'precip': 330, 'zone': 'forest_steppe', 'sun': 2100, 'wind': 3.8,
        'name_kk': 'Көкшетау', 'name_en': 'Kokshetau',
        'desc_ru': 'Край озёр и лесов. Умеренный климат.',
        'desc_kk': 'Көлдер мен ормандар өлкесі. Қалыпты климат.',
        'desc_en': 'Land of lakes and forests. Moderate climate.'},
    'Уральск': {'lat': 51.23, 'lon': 51.39, 't_jan': -11.4, 't_jul': 23.1, 't_year': 6.1, 'precip': 298, 'zone': 'steppe', 'sun': 2200, 'wind': 4.7,
        'name_kk': 'Орал', 'name_en': 'Uralsk',
        'desc_ru': 'Старейший город запада. Степной климат.',
        'desc_kk': 'Батыстың ең ежелгі қаласы. Дала климаты.',
        'desc_en': 'Oldest western city. Steppe climate.'},
    'Усть-Каменогорск': {'lat': 49.97, 'lon': 82.61, 't_jan': -15.6, 't_jul': 21.2, 't_year': 3.1, 'precip': 425, 'zone': 'foothill', 'sun': 2300, 'wind': 2.4,
        'name_kk': 'Өскемен', 'name_en': 'Ust-Kamenogorsk',
        'desc_ru': 'У Алтайских гор. Предгорный климат с обильными осадками.',
        'desc_kk': 'Алтай тауларының жанында. Мол жауын-шашынды тау бөктері климаты.',
        'desc_en': 'Near Altai mountains. Foothill climate with abundant precipitation.'},
    'Тараз': {'lat': 42.90, 'lon': 71.37, 't_jan': -3.2, 't_jul': 25.4, 't_year': 11.8, 'precip': 380, 'zone': 'foothill', 'sun': 2600, 'wind': 2.3,
        'name_kk': 'Тараз', 'name_en': 'Taraz',
        'desc_ru': 'Древний город на Шёлковом пути. Мягкий климат.',
        'desc_kk': 'Жібек жолындағы ежелгі қала. Жұмсақ климат.',
        'desc_en': 'Ancient Silk Road city. Mild climate.'},
}

def city_name(k):
    if st.session_state.lang == 'kk': return CITIES[k].get('name_kk', k)
    if st.session_state.lang == 'en': return CITIES[k].get('name_en', k)
    return k

def city_desc(k):
    if st.session_state.lang == 'kk': return CITIES[k].get('desc_kk', '')
    if st.session_state.lang == 'en': return CITIES[k].get('desc_en', '')
    return CITIES[k].get('desc_ru', '')

REGIONS = {
    'Акмолинская': {'t': 2.8, 'p': 320, 'z': 'steppe', 'kk': 'Ақмола', 'en': 'Akmola'},
    'Актюбинская': {'t': 5.2, 'p': 270, 'z': 'semi_desert', 'kk': 'Ақтөбе', 'en': 'Aktobe'},
    'Алматинская': {'t': 8.5, 'p': 450, 'z': 'foothill', 'kk': 'Алматы', 'en': 'Almaty'},
    'Атырауская': {'t': 10.1, 'p': 165, 'z': 'desert', 'kk': 'Атырау', 'en': 'Atyrau'},
    'ВКО': {'t': 3.5, 'p': 400, 'z': 'foothill', 'kk': 'ШҚО', 'en': 'East Kaz.'},
    'Жамбылская': {'t': 10.8, 'p': 340, 'z': 'semi_desert', 'kk': 'Жамбыл', 'en': 'Zhambyl'},
    'ЗКО': {'t': 5.8, 'p': 290, 'z': 'steppe', 'kk': 'БҚО', 'en': 'West Kaz.'},
    'Карагандинская': {'t': 3.2, 'p': 280, 'z': 'steppe', 'kk': 'Қарағанды', 'en': 'Karaganda'},
    'Костанайская': {'t': 2.5, 'p': 315, 'z': 'forest_steppe', 'kk': 'Қостанай', 'en': 'Kostanay'},
    'Кызылординская': {'t': 11.2, 'p': 130, 'z': 'desert', 'kk': 'Қызылорда', 'en': 'Kyzylorda'},
    'Мангистауская': {'t': 12.5, 'p': 145, 'z': 'desert', 'kk': 'Маңғыстау', 'en': 'Mangystau'},
    'Павлодарская': {'t': 2.9, 'p': 260, 'z': 'steppe', 'kk': 'Павлодар', 'en': 'Pavlodar'},
    'СКО': {'t': 1.8, 'p': 345, 'z': 'forest_steppe', 'kk': 'СҚО', 'en': 'North Kaz.'},
    'Туркестанская': {'t': 13.5, 'p': 420, 'z': 'semi_desert', 'kk': 'Түркістан', 'en': 'Turkestan'},
}

def region_name(k):
    if st.session_state.lang == 'kk': return REGIONS[k].get('kk', k)
    if st.session_state.lang == 'en': return REGIONS[k].get('en', k)
    return k

ZONES = {
    'forest_steppe': {'color': '#2ecc71', 'jan': '-17°C', 'jul': '+20°C', 'precip': '320-360 мм', 'area': 5},
    'steppe': {'color': '#f39c12', 'jan': '-15..-19°C', 'jul': '+19..+23°C', 'precip': '230-340 мм', 'area': 26},
    'semi_desert': {'color': '#e67e22', 'jan': '-10..-20°C', 'jul': '+21..+25°C', 'precip': '134-330 мм', 'area': 14},
    'desert': {'color': '#e74c3c', 'jan': '-5..-15°C', 'jul': '+25..+30°C', 'precip': '100-200 мм', 'area': 44},
    'foothill': {'color': '#3498db', 'jan': '-3..-5°C', 'jul': '+22..+26°C', 'precip': '400-600 мм', 'area': 11},
}

BULLETINS = [
    ("Климат Казахстана", "https://www.kazhydromet.kz/ru/klimat/klimat-kazahstana-1"),
    ("Климат городов", "https://www.kazhydromet.kz/ru/klimat/klimat-gorodov-kazahstana"),
    ("По областям", "https://www.kazhydromet.kz/ru/klimat/klimat-kazahstana-po-oblastyam"),
    ("Изменение климата", "https://www.kazhydromet.kz/ru/klimat/ezhegodnyy-byulleten-monitoringa-sostoyaniya-i-izmeneniya-klimata-kazahstana"),
    ("Снежный покров", "https://www.kazhydromet.kz/ru/klimat/ezhegodnyy-byulleten-monitoringa-snezhnogo-pokrova-na-territorii-respubliki-kazahstan"),
    ("Ветер", "https://www.kazhydromet.kz/ru/klimat/ezhegodnyy-byulleten-monitoringa-prizemnogo-vetra-na-territorii-respubliki-kazahstan"),
    ("Солнечное сияние", "https://www.kazhydromet.kz/ru/klimat/ezhegodnyy-byulleten-prodolzhitelnosti-solnechnogo-siyaniya-na-territorii-respubliki-kazahstan"),
]

def create_map(layer="temperature"):
    m = folium.Map(location=[48.0, 66.9], zoom_start=5, tiles=None)
    folium.TileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attr='OSM', name='🗺️ OpenStreetMap').add_to(m)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='🛰️ Satellite').add_to(m)
    folium.TileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr='OpenTopoMap', name='🏔️ Topography').add_to(m)
    folium.TileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', attr='CartoDB', name='📋 Light').add_to(m)
    
    def get_color(val, lyr):
        if lyr == "temperature":
            if val < 0: return '#2196F3'
            elif val < 5: return '#4CAF50'
            elif val < 10: return '#FF9800'
            else: return '#F44336'
        elif lyr == "precipitation":
            if val < 200: return '#F44336'
            elif val < 300: return '#FF9800'
            elif val < 400: return '#4CAF50'
            else: return '#2196F3'
        else:
            if val < 2200: return '#2196F3'
            elif val < 2500: return '#FF9800'
            else: return '#F44336'
    
    for key, d in CITIES.items():
        name = city_name(key)
        if layer == "temperature": val, txt = d['t_year'], f"{d['t_year']}°C"
        elif layer == "precipitation": val, txt = d['precip'], f"{d['precip']} mm"
        else: val, txt = d['sun'], f"{d['sun']} h"
        
        popup = f"""<div style="font-family:Inter,Arial;min-width:220px;padding:8px;">
            <h4 style="color:#1565c0;margin:0 0 8px;border-bottom:2px solid #1976d2;padding-bottom:5px;">{name}</h4>
            <p style="margin:4px 0;background:#e3f2fd;padding:6px;border-radius:4px;"><b>{t(d['zone'])}</b></p>
            <table style="width:100%;font-size:0.9em;">
                <tr><td>❄️ {t('jan')}:</td><td><b>{d['t_jan']}°C</b></td></tr>
                <tr><td>☀️ {t('jul')}:</td><td><b>{d['t_jul']}°C</b></td></tr>
                <tr><td>💧 {t('precip')}:</td><td><b>{d['precip']} mm</b></td></tr>
                <tr><td>💨 {t('wind')}:</td><td><b>{d['wind']} m/s</b></td></tr>
                <tr><td>🌞 {t('sun_hours')}:</td><td><b>{d['sun']} h</b></td></tr>
            </table>
            <p style="font-size:0.85em;color:#555;margin:8px 0 0;">{city_desc(key)}</p>
        </div>"""
        
        folium.CircleMarker([d['lat'], d['lon']], radius=14, popup=folium.Popup(popup, max_width=300),
            tooltip=f"{name}: {txt}", color='white', fill=True, fillColor=get_color(val, layer), fillOpacity=0.85, weight=2).add_to(m)
        folium.Marker([d['lat'], d['lon']], icon=folium.DivIcon(
            html=f'<div style="font-size:11px;font-weight:bold;color:#1a237e;text-shadow:1px 1px white,-1px -1px white;">{name}</div>',
            icon_size=(100,20), icon_anchor=(50,-8))).add_to(m)
    
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    return m

def call_ai(prompt):
    try:
        lang_map = {'ru': 'русском', 'kk': 'казахском (қазақша)', 'en': 'English'}
        lang_inst = f"Отвечай на {lang_map[st.session_state.lang]} языке." if st.session_state.lang != 'en' else "Respond in English."
        data = "\n".join([f"{city_name(k)}: t={d['t_year']}°C, jan={d['t_jan']}°C, jul={d['t_jul']}°C, precip={d['precip']}mm, sun={d['sun']}h" for k,d in CITIES.items()])
        resp = requests.post(API_URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [
                {"role": "system", "content": f"Ты климатолог Казгидромета. {lang_inst}\nДанные:\n{data}"},
                {"role": "user", "content": prompt}], "max_tokens": 1200, "temperature": 0.7}, timeout=60, verify=False)
        if resp.status_code == 200: return resp.json()['choices'][0]['message']['content']
        return f"Error: {resp.status_code}"
    except Exception as e: return f"Error: {str(e)}"

def main():
    with st.sidebar:
        st.image("https://www.kazhydromet.kz/img/kgm.ab98eab3.png", width=180)
        st.markdown("### 🌤️ Казгидромет")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        if c1.button("🇰🇿 QAZ", use_container_width=True, type="primary" if st.session_state.lang == 'kk' else "secondary"):
            st.session_state.lang = 'kk'; st.rerun()
        if c2.button("🇷🇺 RUS", use_container_width=True, type="primary" if st.session_state.lang == 'ru' else "secondary"):
            st.session_state.lang = 'ru'; st.rerun()
        if c3.button("🇬🇧 ENG", use_container_width=True, type="primary" if st.session_state.lang == 'en' else "secondary"):
            st.session_state.lang = 'en'; st.rerun()
        st.markdown("---")
        pages = t('pages')
        page_idx = st.radio(t('nav'), range(len(pages)), format_func=lambda i: pages[i], index=st.session_state.current_page)
        st.session_state.current_page = page_idx
        st.markdown("---")
        st.markdown(f"### {t('contacts')}")
        st.markdown(t('contact_info'))
    
    if page_idx == 0:  # Главная
        st.markdown(f'<div class="main-header"><h1>{t("title")}</h1><p>{t("subtitle")}</p></div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">2 724 900</div><div class="metric-label">{t("area")}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">40-55°</div><div class="metric-label">{t("lat_pos")}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value">5</div><div class="metric-label">{t("zones_count")}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value">207</div><div class="metric-label">{t("stations")}</div></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"## {t('about')}")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f'<div class="info-card"><p>{t("desc1")}</p><p>{t("desc2")}</p><p>{t("desc3")}</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f"### {t('norms')}")
            st.metric(t('jan_temp'), "-17°C .. 0°C")
            st.metric(t('jul_temp'), "+19°C .. +28°C")
            st.metric(t('precip'), "100-600 mm")
        st.markdown("---")
        st.markdown(f"## {t('quick_access')}")
        c1, c2, c3 = st.columns(3)
        if c1.button(t('temp_map'), use_container_width=True, type="primary"):
            st.session_state.selected_layer = 'temperature'; st.session_state.current_page = 1; st.rerun()
        if c2.button(t('precip_map'), use_container_width=True, type="primary"):
            st.session_state.selected_layer = 'precipitation'; st.session_state.current_page = 1; st.rerun()
        if c3.button(t('sun_map'), use_container_width=True, type="primary"):
            st.session_state.selected_layer = 'sunshine'; st.session_state.current_page = 1; st.rerun()
    
    elif page_idx == 1:  # Карта
        st.markdown(f"## {t('map_title')}")
        st.info(t('map_hint'))
        st.markdown(f"### {t('select_param')}")
        c1, c2, c3 = st.columns(3)
        if c1.button(t('temp_map'), use_container_width=True, type="primary" if st.session_state.selected_layer == "temperature" else "secondary"):
            st.session_state.selected_layer = "temperature"; st.rerun()
        if c2.button(t('precip_map'), use_container_width=True, type="primary" if st.session_state.selected_layer == "precipitation" else "secondary"):
            st.session_state.selected_layer = "precipitation"; st.rerun()
        if c3.button(t('sun_map'), use_container_width=True, type="primary" if st.session_state.selected_layer == "sunshine" else "secondary"):
            st.session_state.selected_layer = "sunshine"; st.rerun()
        st.markdown("---")
        cm, cl = st.columns([4, 1])
        with cl:
            st.markdown(f"### {t('legend')}")
            if st.session_state.selected_layer == "temperature":
                st.markdown(f"**{t('avg_temp')}**\n\n🔵 < 0°C — {t('cold')}\n\n🟢 0-5°C — {t('cool')}\n\n🟠 5-10°C — {t('moderate')}\n\n🔴 > 10°C — {t('warm')}")
            elif st.session_state.selected_layer == "precipitation":
                st.markdown(f"**{t('annual_precip')}**\n\n🔴 < 200mm — {t('arid')}\n\n🟠 200-300mm — {t('moderate')}\n\n🟢 300-400mm — {t('sufficient')}\n\n🔵 > 400mm — {t('humid')}")
            else:
                st.markdown(f"**{t('sun_hours_legend')}**\n\n🔵 < 2200h — {t('low_sun')}\n\n🟠 2200-2500h — {t('high_sun')}\n\n🔴 > 2500h — {t('very_high_sun')}")
            st.markdown("---")
            st.markdown(f"**{t('hints')}**\n\n{t('click_info')}\n\n{t('layer_hint')}")
        with cm:
            st_folium(create_map(st.session_state.selected_layer), width=900, height=550)
    
    elif page_idx == 2:  # Города
        st.markdown(f"## {t('cities_title')}")
        keys = list(CITIES.keys())
        names = [city_name(k) for k in keys]
        idx = st.selectbox(t('select_city'), range(len(keys)), format_func=lambda i: names[i])
        d = CITIES[keys[idx]]
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f'<div class="city-card"><h3>{city_name(keys[idx])}</h3><p><b>{t("zone")}:</b> {t(d["zone"])}</p><p><b>{t("coords")}:</b> {d["lat"]:.2f}°N, {d["lon"]:.2f}°E</p><p style="color:#555;">{city_desc(keys[idx])}</p></div>', unsafe_allow_html=True)
            st.metric(t('year_temp'), f"{d['t_year']}°C")
            st.metric(t('year_precip'), f"{d['precip']} mm")
            st.metric(t('sun_hours'), f"{d['sun']} h")
            st.metric(t('wind'), f"{d['wind']} m/s")
        with c2:
            months = t('months')
            amp = (d['t_jul'] - d['t_jan']) / 2
            mean = (d['t_jul'] + d['t_jan']) / 2
            temps = [mean + amp * math.sin((i - 3) * math.pi / 6) for i in range(12)]
            fig = go.Figure(go.Scatter(x=months, y=temps, fill='tozeroy', fillcolor='rgba(33,150,243,0.2)', line=dict(color='#1976D2', width=3), mode='lines+markers', marker=dict(size=10)))
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(title=f"{t('chart_title')} {city_name(keys[idx])}", xaxis_title=t('month'), yaxis_title=t('temp_c'), template="plotly_white", height=380)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        st.markdown(f"### {t('compare')}")
        cmp = st.multiselect(t('select_compare'), range(len(keys)), format_func=lambda i: names[i], default=[0, 1, 6])
        if cmp:
            df = pd.DataFrame({'City': [city_name(keys[i]) for i in cmp], 'Temp': [CITIES[keys[i]]['t_year'] for i in cmp], 'Precip': [CITIES[keys[i]]['precip'] for i in cmp]})
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.bar(df, x='City', y='Temp', color='Temp', color_continuous_scale='RdYlBu_r', title=t('temp_compare')).update_layout(template="plotly_white"), use_container_width=True)
            c2.plotly_chart(px.bar(df, x='City', y='Precip', color='Precip', color_continuous_scale='Blues', title=t('precip_compare')).update_layout(template="plotly_white"), use_container_width=True)
    
    elif page_idx == 3:  # Зоны
        st.markdown(f"## {t('zones_title')}")
        for zk, zd in ZONES.items():
            st.markdown(f'<div class="climate-zone-card" style="border-left-color:{zd["color"]};"><h3 style="color:{zd["color"]};margin-top:0;">{t(zk)}</h3><p><b>{t("jan")}:</b> {zd["jan"]}</p><p><b>{t("jul")}:</b> {zd["jul"]}</p><p><b>{t("zone_precip")}:</b> {zd["precip"]}</p><p style="color:#555;">{t(zk+"_desc")}</p></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"### {t('distribution')}")
        fig = px.pie(values=[ZONES[k]['area'] for k in ZONES], names=[t(k) for k in ZONES], color_discrete_sequence=[ZONES[k]['color'] for k in ZONES], title=t('zone_share'))
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    elif page_idx == 4:  # ИИ
        st.markdown(f"## {t('ai_title')}")
        st.markdown(f'<div class="ai-chat-box"><p>{t("ai_desc")}</p></div>', unsafe_allow_html=True)
        st.markdown(f"### {t('examples')}")
        c1, c2 = st.columns(2)
        if c1.button(t('q1'), use_container_width=True): st.session_state.ai_q = t('q1').replace('🌡️ ', '')
        if c1.button(t('q2'), use_container_width=True): st.session_state.ai_q = t('q2').replace('🏔️ ', '')
        if c2.button(t('q3'), use_container_width=True): st.session_state.ai_q = t('q3').replace('☀️ ', '')
        if c2.button(t('q4'), use_container_width=True): st.session_state.ai_q = t('q4').replace('🌧️ ', '')
        st.markdown("---")
        q = st.text_area(t('your_q'), value=st.session_state.get('ai_q', ''), height=100, placeholder=t('placeholder'))
        c1, c2 = st.columns([1, 3])
        if c1.button(t('analyze'), type="primary", use_container_width=True) and q:
            with st.spinner(t('thinking')):
                ans = call_ai(q)
                st.session_state.chat_history.append({'q': q, 'a': ans})
                if 'ai_q' in st.session_state: del st.session_state.ai_q
                st.rerun()
        if c2.button(t('clear'), use_container_width=True):
            st.session_state.chat_history = []
            if 'ai_q' in st.session_state: del st.session_state.ai_q
            st.rerun()
        if st.session_state.chat_history:
            st.markdown(f"### {t('history')}")
            for item in reversed(st.session_state.chat_history):
                st.markdown(f'<div class="user-message"><b>🧑 {t("you")}:</b> {item["q"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-message"><b>🤖 {t("ai")}:</b><br>{item["a"]}</div>', unsafe_allow_html=True)
                st.markdown("---")
    
    elif page_idx == 5:  # Бюллетени
        st.markdown(f"## {t('bulletins_title')}")
        st.markdown(f'<div class="info-card"><p>{t("bulletins_desc")}</p></div>', unsafe_allow_html=True)
        st.markdown(f"### {t('publications')}")
        for title, url in BULLETINS:
            st.markdown(f'<a href="{url}" target="_blank" class="bulletin-link">📄 {title}</a>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"### {t('by_regions')}")
        data = [{t('region'): region_name(k), t('avg_t'): v['t'], t('precip_mm'): v['p'], t('zone_col'): t(v['z'])} for k, v in REGIONS.items()]
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
