import bisect
from datetime import timedelta

from geographiclib.geodesic import Geodesic

from .gpmd import GPS_FIXED_VALUES
from .point import PintPoint3, Point
from .smoothing import Kalman, SimpleExponential
from .units import units


# this is almost certainly wrong? - we are treating this as 3x1D samples, but it's not.
def process_kalman_pp3(new, key):
    kx = Kalman()
    ky = Kalman()
    kz = Kalman()

    def process(item):
        xyz = key(item)
        return {new: PintPoint3(
            x=kx.update(xyz.x),
            y=ky.update(xyz.y),
            z=kz.update(xyz.z)
        )}

    return process


def process_kalman(new, key):
    k = Kalman()

    def process(item):
        v = key(item)
        return {new: k.update(v)}

    return process


def process_ses(new, key, alpha=0.4):
    ses = SimpleExponential(alpha=alpha)

    def process(item):
        return {new: ses.update(key(item))}

    return process


def distance_azi_between(a: Point, b: Point):
    inverse = Geodesic.WGS84.Inverse(a.lat, a.lon, b.lat, b.lon)
    dist = units.Quantity(inverse['s12'], units.m)
    raw_azi = inverse['azi1']
    return dist, raw_azi


def calculate_speeds():
    def accept(a, b, c):
        dist, raw_azi = distance_azi_between(a.point, b.point)

        time = units.Quantity((b.dt - a.dt).total_seconds(), units.seconds)
        azi = units.Quantity(raw_azi, units.degree)

        raw_cog = 0 + raw_azi if raw_azi >= 0 else 360 + raw_azi
        cog = units.Quantity(raw_cog, units.degree)

        speed = dist / time if time.magnitude > 0 else units.Quantity(0, units.mps)

        return {
            "cspeed": speed,
            "dist": dist / c,  # suspect this isn't right!
            "time": time,
            "azi": azi,
            "cog": cog
        }

    return accept


def calculate_odo():
    total = [units.Quantity(0.0, units.m)]

    def accept(e):
        if e.dist is not None:
            total[0] += e.dist
        return {"codo": total[0]}

    return accept


def filter_locked():
    fields = ["speed", "cspeed", "azi", "cog", "time", "dist", "grad", "cgrad", "alt"]

    def accept(e):
        if e.gpsfix not in GPS_FIXED_VALUES:
            return {f: None for f in fields}

    return accept


def calculate_gradient():
    # have to move a bit to calculate decent gradient
    # this is called for frames ~2 sec apart.
    def accept(a, b, c):
        if a.alt and b.alt:
            gain = b.alt - a.alt

            dist, _ = distance_azi_between(a.point, b.point)

            if dist and dist.magnitude > 1.0:
                grad = (gain / dist) * 100.0
                if abs(grad.magnitude) < 45:
                    field = "cgrad"
                else:
                    field = "bad_grad"

                return {
                    field: grad,
                    "grad_gain": gain,
                    "grad_dist": dist,
                    "grad_other_packet": b.packet,
                    "grad_other_packet_index": b.packet_index,
                }

    return accept


def process_gradient_window(
    ts, window_seconds=5, time_shift_seconds=0, filter_fn=lambda e: True
):
    """Calculate each point's gradient from the surrounding time window.

    The elevation difference is measured between points near t-window and
    t+window, so the effective baseline is about 10 seconds instead of one
    adjacent GPS interval. A positive time shift calculates the slope around
    a later time and assigns it to the current entry, advancing the displayed
    slope without changing the global data/video offset.
    """
    entries = list(ts.items())
    if len(entries) < 3:
        return

    dates = [entry.dt for entry in entries]
    delta = timedelta(seconds=window_seconds)
    shift = timedelta(seconds=time_shift_seconds)
    calculate = calculate_gradient()

    for index, center in enumerate(entries):
        sample_dt = center.dt + shift
        before_target = sample_dt - delta
        after_target = sample_dt + delta
        before_index = bisect.bisect_right(dates, before_target) - 1
        after_index = bisect.bisect_left(dates, after_target)
        if before_index < 0 or after_index >= len(entries):
            continue

        before = entries[before_index]
        after = entries[after_index]
        if not (filter_fn(before) and filter_fn(center) and filter_fn(after)):
            continue

        updates = calculate(before, after, after_index - before_index)
        if updates and "cgrad" in updates:
            center.update(**updates)
