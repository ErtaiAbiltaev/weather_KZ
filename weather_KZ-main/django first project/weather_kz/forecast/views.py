from datetime import datetime
import requests
from django.shortcuts import render

API_KEY = '88344296624c4734a40103525251510'

def format_time(date_str):
    # date_str: '2023-10-15 14:00'
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    # Вернем в формате '15 окт, 14:00'
    return dt.strftime('%d %b, %H:%M')

def weather_view(request):
    city = request.POST.get('city', 'Almaty')
    error = None
    weather = None
    hourly = []
    daily = []

    try:
        url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days=5&lang=ru"
        resp = requests.get(url)
        data = resp.json()

        if 'error' in data:
            error = data['error']['message']
        else:
            location = data['location']
            current = data['current']
            forecast_days = data['forecast']['forecastday']

            weather = {
                'city': location['name'],
                'temp': current['temp_c'],
                'feels_like': current['feelslike_c'],
                'humidity': current['humidity'],
                'wind': current['wind_kph'],
                'description': current['condition']['text'],
                'icon': 'https:' + current['condition']['icon'],
                'last_updated': format_time(current['last_updated']),
            }

            # Почасовой прогноз: берем 12 часов начиная с текущего времени
            # Для этого берем часы из сегодня и завтра, чтобы покрыть 12 часов вперед
            hours_all = forecast_days[0]['hour'] + forecast_days[1]['hour']

            # Нужно отфильтровать часы, чтобы начать с текущего часа
            now = datetime.strptime(current['last_updated'], '%Y-%m-%d %H:%M')
            filtered_hours = [h for h in hours_all if datetime.strptime(h['time'], '%Y-%m-%d %H:%M') >= now]

            for hour in filtered_hours[:12]:
                hourly.append({
                    'time': datetime.strptime(hour['time'], '%Y-%m-%d %H:%M').strftime('%H:%M'),
                    'temp': hour['temp_c'],
                    'description': hour['condition']['text'],
                    'icon': 'https:' + hour['condition']['icon'],
                })

            # Прогноз на 5 дней
            for day in forecast_days[:5]:
                daily.append({
                    'date': datetime.strptime(day['date'], '%Y-%m-%d').strftime('%d %b'),
                    'maxtemp': day['day']['maxtemp_c'],
                    'mintemp': day['day']['mintemp_c'],
                    'description': day['day']['condition']['text'],
                    'icon': 'https:' + day['day']['condition']['icon'],
                })

    except Exception:
        error = "Не удалось получить данные о погоде."

    return render(request, 'forecast/weather.html', {
        'weather': weather,
        'hourly': hourly,
        'daily': daily,
        'error': error,
    })