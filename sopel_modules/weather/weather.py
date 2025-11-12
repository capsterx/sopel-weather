from sopel.config.types import StaticSection, ChoiceAttribute, ValidatedAttribute
from sopel.module import commands, example
from .wz import WZ
from .utils import geoip_lookup

import sopel.module
import socket

class WeatherSection(StaticSection):
    here_url = ValidatedAttribute('here_url', default="https://geocoder.api.here.com/6.2/geocode.json")
    here_api_key = ValidatedAttribute('here_api_key', default=None)
    darksky_url = ValidatedAttribute("darksky_url", default="https://api.darksky.net/forecast")
    darksky_key = ValidatedAttribute("darksky_key", default=None)

def configure(config):
    config.define_section('weather', WeatherSection, validate=False)
    config.weather.configure_setting('here_url', 'here.com api url')
    config.weather.configure_setting('here_api_key', 'here.com api key')
    config.weather.configure_setting('darksky_url', 'darksky.com api url')
    config.weather.configure_setting('darksky_key', 'darksky.com id')

def setup(bot):
    bot.config.define_section('weather', WeatherSection)

def check(bot, trigger):
    msg = None
    if not bot.config.weather.here_url:
        msg = 'Weather API here.com url not configured.'
    elif not bot.config.weather.here_api_key:
        msg = 'Weather API here.com app code not configured.'
    elif not bot.config.weather.darksky_url:
        msg = 'Weather API darksky.com url not configured.'
    elif not bot.config.weather.darksky_key:
        msg = 'Weather API darksky.com key not configured.'
    return msg

def weather(bot, trigger, **kwargs):
    msg = check(bot, trigger)
    if not msg:
        wz = WZ(
            bot.config.weather.here_url,
            bot.config.weather.here_api_key,
            bot.config.weather.darksky_url,
            bot.config.weather.darksky_key
        )
        search = trigger.group(2)
        if not search:
            search = bot.db.get_nick_value(trigger.nick, "weather.default")

        if not search:
            addr = socket.gethostbyname(trigger.host.strip())
            geozip = geoip_lookup(addr)
            if geozip.postal.code:
                msg = wz.get(geozip.postal.code, **kwargs)
            else:
                msg = f"Sorry {trigger.nick}, I can't figure out where you are"
        else:
            msg = wz.get(search, **kwargs)
    bot.say(msg)


@sopel.module.commands('wz', 'wx')
@sopel.module.example('.wz 90210')
@sopel.module.example('.wz Los Vegas, NV')
def weatherbot_current(bot, trigger):
    weather(bot, trigger, kind="current")

@sopel.module.commands('wzf', 'wxf')
@sopel.module.example('.wzf 90210')
@sopel.module.example('.wzf Los Vegas, NV')
def weatherbot_forecast(bot, trigger):
    weather(bot, trigger, kind="forecast", days=5)

@sopel.module.commands('wzh', 'wxh')
@sopel.module.example('.wzh 90210')
@sopel.module.example('.wzh Los Vegas, NV')
def weatherbot_hourly(bot, trigger):
    weather(bot, trigger, kind="hourly", hours=12)

@sopel.module.commands('wzr', 'wxr')
@sopel.module.example('.wzr 90210')
@sopel.module.example('.wzr Los Vegas, NV')
def weatherbot_hourly(bot, trigger):
    weather(bot, trigger, kind="rain")

@sopel.module.commands('wzd', 'wxd')
@sopel.module.example('.wzd 90210')
@sopel.module.example('.wzd Los Vegas, NV')
def weatherbot_set_default(bot, trigger):
    msg = check(bot, trigger)
    if not msg:
      if not trigger.group(2):
        msg = f"Usage .wzd <default>"
      else:
        bot.db.set_nick_value(trigger.nick, "weather.default", trigger.group(2))
        msg = f"{trigger.nick} default set to {trigger.group(2)}"
    bot.say(msg)
