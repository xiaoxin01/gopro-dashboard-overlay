#!/usr/bin/env python3
"""
gopro-export-json.py — 把运动数据导出为「播放器外挂数据」JSON，供 player/index.html 使用。

设计目标（方案 C：播放器端外挂）：
  视频原片完全不动；本脚本只把 FIT / GPX / GoPro 元数据导出为列式 JSON（时间戳 + 各字段数值），
  播放器按视频时间实时查询、绘制仪表盘。改仪表盘样式/开关 = 改播放器页面，无需重新渲染视频。

用法：
  # 1) GoPro 视频自带元数据（数据自动与视频时间对齐）
  python3 bin/gopro-export-json.py --input GX040274.MP4 out.json

  # 2) 纯 GPX / FIT（无视频，时间轴从数据起点开始）
  python3 bin/gopro-export-json.py --gpx ride.gpx out.json
  python3 bin/gopro-export-json.py --fit ride.fit out.json

  # 3) 外部 GPX / FIT 对齐到某段视频（数据被限制在视频时间段内，t = 相对视频开头秒）
  python3 bin/gopro-export-json.py --input video.mp4 --gpx ride.gpx out.json
  #    --video-time-start created|modified|accessed 控制“视频 0 秒”取文件哪个时间

输出 JSON 结构（列式，便于浏览器解析与插值）：
  {
    "version": 1,
    "meta": {
      "source": "ride.gpx", "start_iso": "...", "end_iso": "...",
      "video_duration_s": 123.4 | null, "fields": ["t", "speed", ...]
    },
    "series": {
      "t":      [0.0, 0.4, ...],          # 相对视频/数据起点秒
      "speed":  [5.3, 5.8, ...] | null,   # m/s
      "hr":     [...],                    # bpm（FIT 才有）
      "cad":    [...],                    # rpm
      "power":  [...],                    # W
      "grad":   [...],                    # %
      "alt":    [...],                    # m
      "odo":    [...],                    # m
      "dist":   [...],                    # m（GPS 点间距）
      "lat":    [...], "lon": [...],      # 度
      "dop":    [...], "atemp": [...],    # degC（FIT 才有）
    }
  }
"""

import argparse
import datetime
import json
import pathlib
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gopro_overlay import gpmd_filters, timeseries_process  # noqa: E402
from gopro_overlay.assertion import assert_file_exists  # noqa: E402
from gopro_overlay.ffmpeg import FFMPEG  # noqa: E402
from gopro_overlay.ffmpeg_gopro import FFMPEGGoPro  # noqa: E402
from gopro_overlay.framemeta import FrameMeta, LoadFlag  # noqa: E402
from gopro_overlay.framemeta_gpx import timeseries_to_framemeta  # noqa: E402
from gopro_overlay.gpmd import GPSFix, GPS_FIXED_VALUES  # noqa: E402
from gopro_overlay.loading import GoproLoader, load_external  # noqa: E402
from gopro_overlay.log import log  # noqa: E402
from gopro_overlay.timeunits import timeunits  # noqa: E402
from gopro_overlay.units import units  # noqa: E402

# ---- 处理管线 ---------------------------------------------------------------

PACKETS_PER_SECOND = 18
LOCKED_2D = lambda e: e.gpsfix in GPS_FIXED_VALUES  # noqa: E731
LOCKED_3D = lambda e: e.gpsfix == GPSFix.LOCK_3D.value  # noqa: E731


def process_framemeta(ts: FrameMeta) -> None:
    """GoPro GPMD FrameMeta：18Hz 原始点，按原项目管线处理。"""
    ts.process_deltas(timeseries_process.calculate_speeds(), skip=PACKETS_PER_SECOND * 3, filter_fn=LOCKED_2D)
    ts.process(timeseries_process.calculate_odo(), filter_fn=LOCKED_2D)
    ts.process_deltas(timeseries_process.calculate_gradient(), skip=PACKETS_PER_SECOND * 3, filter_fn=LOCKED_3D)
    ts.process(timeseries_process.filter_locked())


def process_timeseries(ts) -> None:
    """外部 GPX/FIT Timeseries：直接在原始数据点上处理，不插值到 10Hz 网格。
    GPX 无 gpsfix 概念，不跑 filter_locked；skip=1 逐点计算速度/坡度。"""
    ts.process_deltas(timeseries_process.calculate_speeds(), skip=1)
    ts.process(timeseries_process.calculate_odo())
    ts.process_deltas(timeseries_process.calculate_gradient(), skip=1)


def number(v) -> Optional[float]:
    if v is None:
        return None
    return v.magnitude


def round_or_none(v: Optional[float], ndigits: int):
    return None if v is None else round(v, ndigits)


# 行式导出：每行 = [t, speed, hr, cad, power, grad, alt, odo, dist, lat, lon, dop, atemp]
ROW_FIELDS = ["t", "speed", "hr", "cad", "power", "grad", "alt", "odo", "dist", "lat", "lon", "dop", "atemp"]


def export_rows(entries, meta: dict, t0: datetime.datetime, every: float = 0) -> dict:
    """从 Entry 迭代器导出行式 JSON。时间与各字段在同一行，全空列自动剔除。"""
    rows = []
    last_t = -1e18
    cum_dist = 0.0
    last_cum_dist = 0.0

    for entry in entries:
        d = number(entry.dist)
        if d is not None:
            cum_dist += d

        t = (entry.dt - t0).total_seconds()
        if every > 0 and t < last_t + every:
            continue
        last_t = t

        odo = number(entry.codo)
        if odo is None:
            odo = cum_dist

        row = [
            round(t, 2),
            round_or_none(number(entry.speed if entry.speed is not None else entry.cspeed), 3),
            round_or_none(number(entry.hr), 0),
            round_or_none(number(entry.cad), 0),
            round_or_none(number(entry.power), 0),
            round_or_none(number(entry.grad if entry.grad is not None else entry.cgrad), 2),
            round_or_none(number(entry.alt), 1),
            round(odo, 1),
            round(cum_dist - last_cum_dist, 1),
            round_or_none(entry.point.lat, 6) if entry.point else None,
            round_or_none(entry.point.lon, 6) if entry.point else None,
            round_or_none(number(entry.dop), 1),
            round_or_none(number(entry.atemp), 1),
        ]
        last_cum_dist = cum_dist
        rows.append(row)

    # 剔除全空列（t 列和 odo 列始终保留）
    present_idx = [0, 7]  # t, odo
    for ci in range(1, len(ROW_FIELDS)):
        if ci == 7:
            continue
        if any(row[ci] is not None for row in rows):
            present_idx.append(ci)
    present_idx.sort()
    fields = [ROW_FIELDS[i] for i in present_idx]
    rows = [[row[i] for i in present_idx] for row in rows]

    meta["fields"] = fields
    return {"version": 2, "meta": meta, "fields": fields, "rows": rows}


def main():
    parser = argparse.ArgumentParser(
        description="Export FIT/GPX/GoPro metadata to the player-overlay JSON consumed by player/index.html",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--ffmpeg-dir", type=pathlib.Path, help="Directory where ffmpeg/ffprobe located, default=Look in PATH")
    parser.add_argument("--input", type=pathlib.Path, help="GoPro MP4 video file (metadata source or alignment anchor)")
    parser.add_argument("--gpx", type=pathlib.Path, help="External GPX file")
    parser.add_argument("--fit", type=pathlib.Path, help="External FIT file")
    parser.add_argument("--video-time-start", default="created", choices=["created", "modified", "accessed"],
                        help="Which file timestamp counts as video second 0 when aligning external data")
    parser.add_argument("--gps-dop-max", type=float, default=10, help="Max DOP - points above are 'Not Locked'")
    parser.add_argument("--gps-speed-max", type=float, default=60, help="Max GPS Speed (kph) - points above are 'Not Locked'")
    parser.add_argument("--every", type=float, default=0,
                        help="Output a point every N seconds (default 0 = all original data points; 1 = ~1Hz downsample)")
    parser.add_argument("output", type=pathlib.Path, help="Output JSON file")

    args = parser.parse_args()

    if not args.input and not args.gpx and not args.fit:
        parser.error("Need at least one of --input / --gpx / --fit")

    ffmpeg_gopro = FFMPEGGoPro(FFMPEG(args.ffmpeg_dir))

    # ---- 决定数据来源与时间基准 --------------------------------------------

    if args.gpx and args.fit:
        parser.error("Only one of --gpx / --fit may be given")

    external = args.gpx or args.fit

    if args.input and external:
        # 模式 C：外部 GPX/FIT 对齐到视频时间轴（用原始数据点，不插值）
        video = assert_file_exists(args.input)
        recording = ffmpeg_gopro.find_recording(video)
        duration = recording.video.duration

        fns = {
            "file-created": lambda f: f.ctime,
            "file-modified": lambda f: f.mtime,
            "file-accessed": lambda f: f.atime,
        }
        start_date = datetime.datetime.fromtimestamp(fns[args.video_time_start](recording.file))
        end_date = start_date + duration.timedelta()

        ext_ts = load_external(assert_file_exists(external), units)
        log(f"External file:   {ext_ts.min} -> {ext_ts.max}")
        log(f"Video window:    {start_date} -> {end_date}")

        process_timeseries(ext_ts)
        t0 = start_date

        def entries_in_window():
            for e in ext_ts.items():
                if start_date <= e.dt <= end_date:
                    yield e

        entries = entries_in_window()
        meta = {
            "source": str(external),
            "start_iso": ext_ts.min.isoformat(),
            "end_iso": ext_ts.max.isoformat(),
            "video_start_iso": start_date.isoformat(),
            "video_duration_s": round(duration.millis() / 1000.0, 2),
            "alignment": "external-to-video",
        }
    elif external:
        # 模式 B：纯 GPX/FIT，用原始数据点，时间轴从数据起点开始
        ext_ts = load_external(assert_file_exists(external), units)
        process_timeseries(ext_ts)
        t0 = ext_ts.min
        entries = ext_ts.items()
        meta = {
            "source": str(external),
            "start_iso": ext_ts.min.isoformat(),
            "end_iso": ext_ts.max.isoformat(),
            "video_start_iso": None,
            "video_duration_s": None,
            "alignment": "data-only",
        }
    else:
        # 模式 A：GoPro 视频自带 GPMD 元数据（FrameMeta 本身就是原始 18Hz 点）
        video = assert_file_exists(args.input)
        loader = GoproLoader(
            ffmpeg_gopro=ffmpeg_gopro,
            units=units,
            flags={LoadFlag.ACCL, LoadFlag.CORI, LoadFlag.GRAV},
            gps_lock_filter=gpmd_filters.standard(
                dop_max=args.gps_dop_max,
                speed_max=units.Quantity(args.gps_speed_max, units.kph),
            ),
        )
        gopro = loader.load(video)
        frame_meta = gopro.framemeta
        if len(frame_meta) == 0:
            log("No GPS information found in the video - was GPS recording enabled?")
            sys.exit(1)

        process_framemeta(frame_meta)
        t0 = frame_meta.date_at(frame_meta.min)
        entries = frame_meta.items()
        meta = {
            "source": str(video),
            "start_iso": frame_meta.date_at(frame_meta.min).isoformat(),
            "end_iso": frame_meta.date_at(frame_meta.max).isoformat(),
            "video_start_iso": frame_meta.date_at(frame_meta.min).isoformat(),
            "video_duration_s": round(gopro.recording.video.duration.millis() / 1000.0, 2),
            "alignment": "gopro-metadata",
        }

    payload = export_rows(entries, meta, t0, args.every)

    if len(payload["rows"]) < 1:
        log("No data points exported")
        sys.exit(1)

    meta["duration_s"] = round(payload["rows"][-1][0] - payload["rows"][0][0], 2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    n = len(payload["rows"])
    log(f"Exported {n} points -> {args.output}")
    log(f"Time span: {payload['meta']['start_iso']} -> {payload['meta']['end_iso']} ({payload['meta']['duration_s']}s)")
    log(f"Fields: {', '.join(payload['fields'])}")


if __name__ == "__main__":
    main()
