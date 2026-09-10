#!/usr/bin/env python3
"""
init-offset.py — 根据原视频的修改时间和时长，自动计算数据与合并视频的时间偏移。

GoPro 视频文件的 mtime 是录制结束时间，开始时间 = mtime - duration。
多个章节（GX01/GX02/GX03 同编号）视为连续录制，按时间顺序拼接。
合并视频（combine.mp4）的第 0 秒对应第一个视频的开始时间。

offset_s 定义：数据时间 = 视频时间 + offset_s
  播放器里 sampleAt(video.currentTime + offset_s)

用法：
  python3 bin/init-offset.py \\
    --data player/example-data/wanzheyiquan.json \\
    --video-dir "/Volumes/ssd/cycling/20260725-皖浙天路" \\
    --combined "/Volumes/ssd/cycling-out/20260725-皖浙天路/combine.mp4" \\
    player/example-data/wanzheyiquan.offset.json
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def video_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def parse_gopro_name(filename: str):
    """GX010437.MP4 -> (chapter=1, session=0437); GX020440 -> (2, 0440)"""
    m = re.match(r"GX(\d{2})(\d{4})\.MP4", filename, re.IGNORECASE)
    if m:
        return int(m.group(1)), m.group(2)
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Auto-compute data-to-video offset from GoPro source files")
    parser.add_argument("--data", type=Path, required=True, help="Exported JSON (from gopro-export-json.py)")
    parser.add_argument("--video-dir", type=Path, required=True, help="Directory containing original GoPro MP4 files")
    parser.add_argument("--combined", type=Path, help="Path to the combined MP4 (for reference only)")
    parser.add_argument("output", type=Path, help="Output offset JSON file")
    args = parser.parse_args()

    # 读取数据开始时间（UTC）
    data = json.load(open(args.data))
    data_start_iso = data["meta"]["start_iso"]
    data_start_utc = datetime.datetime.fromisoformat(data_start_iso.replace("Z", "+00:00"))

    # 扫描视频文件
    videos = []
    for f in sorted(args.video_dir.glob("*.MP4")) + sorted(args.video_dir.glob("*.mp4")):
        if f.name.startswith("._"):
            continue
        chapter, session = parse_gopro_name(f.name)
        if session is None:
            continue
        mtime = f.stat().st_mtime
        dur = video_duration(f)
        start_local = datetime.datetime.fromtimestamp(mtime - dur)
        start_utc = start_local.astimezone(datetime.timezone.utc)
        videos.append({
            "file": f.name,
            "session": session,
            "chapter": chapter,
            "duration_s": round(dur, 3),
            "mtime_local": start_local.strftime("%Y-%m-%d %H:%M:%S"),
            "start_utc": start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "_start_utc_dt": start_utc,
        })

    if not videos:
        print("No GoPro MP4 files found", file=sys.stderr)
        sys.exit(1)

    # 按开始时间排序（同 session 的 chapter 按章节号排）
    videos.sort(key=lambda v: (v["_start_utc_dt"], v["chapter"]))

    # 计算合并视频时间轴
    segments = []
    running = 0.0
    for v in videos:
        segments.append({
            "video": v["file"],
            "session": v["session"],
            "video_start_s": round(running, 3),
            "duration_s": v["duration_s"],
            "start_utc": v["start_utc"],
        })
        running += v["duration_s"]

    # 第一个视频的开始时间 = 合并视频第 0 秒
    first_video_start_utc = videos[0]["_start_utc_dt"]
    offset_s = (first_video_start_utc - data_start_utc).total_seconds()

    # 合并视频时长（如果提供了）
    combined_duration = None
    if args.combined and args.combined.exists():
        combined_duration = video_duration(args.combined)

    result = {
        "version": 1,
        "offset_s": round(offset_s, 3),
        "data_start_utc": data_start_iso,
        "first_video_start_utc": first_video_start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "first_video": videos[0]["file"],
        "combined_duration_s": round(combined_duration, 3) if combined_duration else None,
        "total_source_duration_s": round(running, 3),
        "segments": segments,
        "note": "offset_s = 数据时间 - 视频时间；播放器 sampleAt(video.currentTime + offset_s)。手动微调只需改 offset_s。",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Data start (UTC):   {data_start_iso}")
    print(f"First video start:  {first_video_start_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}  ({videos[0]['file']})")
    print(f"Offset:             {offset_s:.1f}s  (data time = video time + {offset_s:.1f}s)")
    print(f"Source videos:      {len(videos)} files, {running/60:.1f} min total")
    if combined_duration:
        print(f"Combined duration:  {combined_duration/60:.1f} min")
    print(f"Wrote -> {args.output}")


if __name__ == "__main__":
    main()
