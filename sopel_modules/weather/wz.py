from . import darksky
from . import here
from . import utils
from . import irc
from . import shorturl

from functools import reduce
from datetime import datetime, date

class WZ:
    UV=[irc.PLAIN] + [irc.GREEN] * 2 + [irc.YELLOW] * 3 + [irc.ORANGE] * 2 + [irc.RED] * 3 + [irc.PURPLE]

    def __init__(
            self,
            here_url,
            here_api_key,
            darksky_url,
            darksky_key
    ):

        self.here = here.Here(here_url, here_api_key)
        self.darksky = darksky.DarkSky(darksky_url, darksky_key)

    def __short(self, url):
        short_url = shorturl.ShortenUrl(url)
        if short_url is not None:
            return short_url
        return url


    def __uv_color(self, index):
        try:
            return WZ.UV[int(index)]
        except:
            return irc.PURPLE

    def __uv_rating(self, index):
        return f"{irc.COLOR}{self.__uv_color(index)}{index}{irc.RESET}"

    def __high(self):
        return f"{irc.COLOR}{irc.RED}↑{irc.RESET}"

    def __low(self):
        return f"{irc.COLOR}{irc.ROYAL_BLUE}↓{irc.RESET}"

    def __both(self, temp):
      temp_f = float(temp)
      temp_c = (5.0 / 9.0) * (temp_f - 32.0)
      return f"{int(temp_f):d}F/{temp_c:.2f}C"

    def _get(self, text):
        location, lat, lng = self.here.location(text)

        weather = self.darksky.weather(lat, lng)
        weather = weather.json()

        return(location, weather)

    def get(self, text, kind="current", **kwargs):
        location, weather = self._get(text)
        return getattr(self, f"get_{kind}")(location, weather, **kwargs)
        

    def get_forecast(self, location, weather, days):
        tz = weather['timezone']
        current = weather["currently"]
        forecast_data = weather["daily"]["data"]

        result = f"{location} Conditions: {current['summary']} | {weather['daily']['summary']} | "
        def f(i):
            fd = forecast_data[i]
            day = utils.unix_to_localtime(fd['time'], tz=tz, fmt='%a')
            high = self.__both(fd['temperatureHigh'])
            apparent_high = self.__both(fd['apparentTemperatureHigh'])
            low = self.__both(fd['temperatureLow'])
            apparent_low = self.__both(fd['apparentTemperatureLow'])
            return (
               f"{irc.BOLD}{day}{irc.RESET} "
               f"{self.__high()}{apparent_high} {self.__low()}{apparent_low} "
               f"{fd['summary']}"
            )
        result += ' | '.join([f(x) for x in range(0, days)])
        return result

    def get_current(self, location, weather):
        tz = weather['timezone']
        current = weather["currently"]
        forecast_data = weather["daily"]["data"]

        sunrise = utils.unix_to_localtime(forecast_data[0]['sunriseTime'], tz=tz)
        sunset = utils.unix_to_localtime(forecast_data[0]['sunsetTime'], tz=tz)
        temp = self.__both(current['temperature'])
        feel = self.__both(current['apparentTemperature'])
        high = self.__both(forecast_data[0]['temperatureHigh'])
        low = self.__both(forecast_data[0]['temperatureLow'])
        result = (
            f"{location} Conditions: {current['summary']} | "
            f"Temp: {temp}, Feels-Like: {feel} | "
            f"UV Index: {self.__uv_rating(current['uvIndex'])} | "
            f"{self.__high()}High: {high}, {self.__low()}Low: {low} | "
            f"Humidity: {current['humidity']*100:.2f}% | "
            f"Sunrise: {sunrise}, "
            f"Sunset: {sunset} | "
            f"Today's Forecast: {forecast_data[0]['summary']}"
        )
        if 'alerts' in weather:
            result += " | Alerts: "
            seen = set()
            alerts = [x for x in weather['alerts'] if x['uri'] not in seen and not seen.add(x['uri'])]
            result += ', '.join([x['title'] + ' ' + self.__short(x['uri']) for x in alerts])
        return result

    def get_hourly(self, location, weather, hours):
        hourly = weather['hourly']['data']
        result = f"{location} | {weather['hourly']['summary']} | "
        tz = weather['timezone']

        def h(x):
            hour = int(utils.unix_to_localtime(x['time'], tz=tz, fmt='%H'))
            day = utils.unix_to_localtime(x['time'], tz=tz, fmt='%a')
            temp = self.__both(x['apparentTemperature'])
            return (
              f"{hour} {x['summary']} "
              f"{temp}/"
              f"{int(100 * x['humidity'])}%/"
              f"{int(100 * x['precipProbability'])}%"
            )
        result += ' | '.join([h(hourly[x]) for x in range(0, hours)])
        return result

    def get_rain(self, loation, weather):
        result = f"{location} | {weather['hourly']['summary']} | "
        hourly = weather['hourly']['data']
        groups = [0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 101]
        def get_group(percip):
            for i in range(1, len(groups)):
                if groups[i] > percip:
                    return i - 1

        def group(data, x):
            percip = int(100 * x['precipProbability'])
            g = get_group(percip)
            ptype = x.get('precipType', 'none')
            if data[-1]['group'] == g and (data[-1]['type'] == ptype or ptype == 'none'):
                pass
            else:
                data[-1]['end'] = x['time']
                data.append({'group': g, 'start': x['time'], 'type': ptype})
            return data
        h0 = hourly[0]
        data = reduce(group, hourly[1:], [{'group': get_group((100 * h0['precipProbability'])), 'start': h0['time'], 'type': h0.get('precipType', 'none')}])
        last_day = None
        last_type = None
        results = []
        for g in data:
            percent = groups[g['group']]
            time = datetime.fromtimestamp(g['start'])
            hour = time.strftime("%-I%p")
            day = time.day
            if last_day != day:
                results.append(f'{irc.BOLD}{time.strftime("%b %-d")}{irc.RESET}')
                last_day = day
            r = f"{hour} {percent}%"
            if g['type'] != last_type and g['type'] != 'none':
                last_type = g['type']
                r = f"{irc.BOLD}{last_type}{irc.RESET} {r}"
            results.append(r)
        return(result + ' | '.join(results))
