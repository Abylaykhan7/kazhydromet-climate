from netCDF4 import Dataset
import numpy as np
from datetime import datetime, timedelta
import os

# Путь к исходному и новому файлу NetCDF
input_file_path = r'C:\Users\galymov_a\Desktop\WRF\wrfout_d01.nc'
output_file_path = r'C:\Temp\mike21_data_144_dynamic_time.nc'  # Название файла изменено на динамическое

# Проверяем и создаем директорию, если нужно
if not os.path.exists(os.path.dirname(output_file_path)):
    os.makedirs(os.path.dirname(output_file_path))

# Открываем исходный файл NetCDF
dataset = Dataset(input_file_path, mode='r')

# Извлекаем переменные
longitude = dataset.variables['XLONG'][0, :, :]  # Размерность (lat, lon)
latitude = dataset.variables['XLAT'][0, :, :]  # Размерность (lat, lon)
u10 = dataset.variables['U10']
v10 = dataset.variables['V10']
sp = dataset.variables['PSFC']

# Проверяем размеры переменных
time_dim_available = u10.shape[0]
print(f"Доступно временных шагов в исходном файле: {time_dim_available}")

# Извлекаем начальную дату и время из исходного файла
time_var = dataset.variables['Times']  # Предполагается, что переменная времени называется 'Times'
start_time_str = ''.join(time_var[0].astype(str))  # Преобразуем массив байтов в строку
start_time = datetime.strptime(start_time_str, '%Y-%m-%d_%H:%M:%S')  # Парсим строку в datetime формат
print(f"Начальная дата и время из WRF файла: {start_time}")

# Выбор данных над Каспийским морем
lat_min, lat_max = 36.0, 47.0
lon_min, lon_max = 47.0, 54.0

# Находим индексы для выбранного диапазона широты и долготы
lat_inds = np.where((latitude[:, 0] >= lat_min) & (latitude[:, 0] <= lat_max))[0]
lon_inds = np.where((longitude[0, :] >= lon_min) & (longitude[0, :] <= lon_max))[0]

# Создаем новый файл NetCDF
new_dataset = Dataset(output_file_path, 'w', format='NETCDF4')

# Создаем размеры для нового файла (144 временных шага, 6 суток по 24 часа)
time_dim = 144
new_dataset.createDimension('time', time_dim)
new_dataset.createDimension('latitude', len(lat_inds))
new_dataset.createDimension('longitude', len(lon_inds))

# Создаем переменные
times = new_dataset.createVariable('time', np.float64, ('time',))
latitudes = new_dataset.createVariable('latitude', np.float32, ('latitude',))
longitudes = new_dataset.createVariable('longitude', np.float32, ('longitude',))
u10_var = new_dataset.createVariable('u10', np.float32, ('time', 'latitude', 'longitude'))
v10_var = new_dataset.createVariable('v10', np.float32, ('time', 'latitude', 'longitude'))
sp_var = new_dataset.createVariable('sp', np.float32, ('time', 'latitude', 'longitude'))

# Заполняем широту и долготу
latitudes[:] = latitude[lat_inds, 0]
longitudes[:] = longitude[0, lon_inds]

# Определяем временные шаги
time_steps = np.arange(0, time_dim)  # Часы с начала (с 0 до 143)

# Заполняем временные шаги в новом файле
times[:] = time_steps
times.units = f'hours since {start_time.strftime("%Y-%m-%d %H:%M:%S")}'  # Используем начальную дату из WRF файла
times.calendar = 'gregorian'

# Итеративно обрабатываем данные по времени
for t in range(time_dim):
    # Определяем индекс для повторения данных
    repeat_index = t % time_dim_available  # Повторяем данные каждые 4 шага

    print(f"Processing time step {t + 1}/{time_dim} (using data from step {repeat_index + 1})")

    # Извлечение данных для текущего временного шага
    u10_caspian = u10[repeat_index, lat_inds, :][:, lon_inds]
    v10_caspian = v10[repeat_index, lat_inds, :][:, lon_inds]
    sp_caspian = sp[repeat_index, lat_inds, :][:, lon_inds]

    # Преобразование давления из Паскалей в гектопаскали
    sp_caspian_hPa = sp_caspian / 100.0

    # Добавляем данные в новый файл
    u10_var[t, :, :] = u10_caspian
    v10_var[t, :, :] = v10_caspian
    sp_var[t, :, :] = sp_caspian_hPa

# Добавляем глобальные атрибуты
current_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
new_dataset.Conventions = 'CF-1.6'
new_dataset.history = f'Created on {current_datetime}\nOriginal history: {start_time_str}'

# Закрываем новый файл
new_dataset.close()

# Закрываем исходный файл
dataset.close()

print(f"Данные успешно сохранены в новый файл на 144 часа: {output_file_path}")
