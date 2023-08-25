from .widgets.text import CachingText, Text
from .widgets.map import MovingMap, JourneyMap
from .widgets.widgets import Widget


def journey_map(at, entry, **kwargs) -> Widget:
    return JourneyMap(
        at=at,
        location=lambda: entry().point,
        **kwargs
    )


def moving_map(at, entry, **kwargs) -> Widget:
    return MovingMap(
        at=at,
        location=lambda: entry().point,
        azimuth=lambda: entry().azi,
        **kwargs
    )


def metric_value(entry, accessor, converter, formatter, default="-"):
    def value():
        v = accessor(entry())
        if v is not None:
            v = converter(v)
            if isinstance(formatter, str) and formatter.endswith("kg"):
                number = int(formatter[:-2])
                print("NUMBER", number)    
                return lambda q: str(round(q.m / number, 1)) + "w/kg"
            else:
                return formatter(v)
        return default

    return value


def text(cache=True, **kwargs) -> Widget:
    if cache:
        return CachingText(**kwargs)
    else:
        return Text(**kwargs)


def metric(entry, accessor, formatter, converter=lambda x: x, cache=True, **kwargs):
    return text(cache, value=metric_value(entry, accessor, converter, formatter), **kwargs)
