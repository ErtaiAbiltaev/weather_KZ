import requests
from django.shortcuts import render

API_KEY = '75657c6346ed6b8e0167e9488f10b543'

def weather_view(request):
    city = request.POST.get('city', 'Almaty')

    error = None
    weather = None
    hourly = []
    daily = []

    try:
        # 1. Получаем координаты города
        geo_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
        geo_resp = requests.get(geo_url)
        geo_data = geo_resp.json()

        if geo_data.get('cod') != 200:
            error = geo_data.get('message', 'Ошибка при получении данных')
        else:
            lat = geo_data['coord']['lat']
            lon = geo_data['coord']['lon']
            city_name = geo_data['name']

            # 2. Запрашиваем One Call API (без минувших данных)
            one_call_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,alerts&appid={API_KEY}&units=metric&lang=ru"
            one_call_resp = requests.get(one_call_url)
            data = one_call_resp.json()

            # Текущая погода
            current = data['current']
            weather = {
                'city': city_name,
                'temp': current['temp'],
                'feels_like': current['feels_like'],
                'humidity': current['humidity'],
                'wind': current['wind_speed'],
                'description': current['weather'][0]['description'].title(),
                'icon': f"http://openweathermap.org/img/wn/{current['weather'][0]['icon']}@2x.png",
                'dt': current['dt'],  # Время текущей погоды (UNIX)
                'timezone_offset': data['timezone_offset']
            }

            # Почасовой прогноз (следующие 12 часов)
            hourly_raw = data['hourly'][:12]
            for hour in hourly_raw:
                hourly.append({
                    'time': unix_to_local(hour['dt'], data['timezone_offset']),
                    'temp': hour['temp'],
                    'description': hour['weather'][0]['description'].title(),
                    'icon': f"http://openweathermap.org/img/wn/{hour['weather'][0]['icon']}@2x.png"
                })

            # Прогноз на 5 дней (дневной)
            daily_raw = data['daily'][1:6]  # начиная со следующего дня
            for day in daily_raw:
                daily.append({
                    'date': unix_to_local(day['dt'], data['timezone_offset'], date_only=True),
                    'maxtemp': day['temp']['max'],
                    'mintemp': day['temp']['min'],
                    'description': day['weather'][0]['description'].title(),
                    'icon': f"http://openweathermap.org/img/wn/{day['weather'][0]['icon']}@2x.png"
                })

    except Exception as e:
        error = "Не удалось получить данные о погоде."

    return render(request, 'forecast/weather.html', {
        'weather': weather,
        'hourly': hourly,
        'daily': daily,
        'error': error
    })


from datetime import datetime, timezone, timedelta

def unix_to_local(unix_time, tz_offset, date_only=False):
    # Преобразуем UNIX timestamp + смещение таймзоны в локальное время
    local_time = datetime.utcfromtimestamp(unix_time) + timedelta(seconds=tz_offset)
    if date_only:
        return local_time.strftime('%d %b %Y')
    return local_time.strftime('%H:%M')

