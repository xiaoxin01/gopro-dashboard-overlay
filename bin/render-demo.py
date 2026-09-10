#!/usr/bin/env python3
"""
render-demo.py — 从 gopro-export-json.py 输出的 JSON 生成一段带仪表盘的演示 MP4。

用法：
  python3 bin/render-demo.py player/example-data/wanzheyiquan.json demo.mp4
  python3 bin/render-demo.py data.json demo.mp4 --start 14540 --duration 30 --fps 10

设计：深色渐变背景 + 仪表盘（速度/功率/心率/踏频/海拔/坡度/距离 + 速度曲线 + 海拔剖面），
逐帧用 PIL 绘制，通过 rawvideo 管道喂给 ffmpeg 编码。用于方案 C 播放器外挂效果的离线演示。
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1280, 720
FONT_PATH = Path(__file__).resolve().parent.parent / "gopro_overlay" / "fonts" / "Verdana.ttf"

# 配色（与播放器一致）
C_BG_TOP = (10, 14, 18)
C_BG_BOT = (20, 28, 38)
C_PANEL = (12, 16, 20, 180)
C_LINE = (255, 255, 255, 36)
C_TEXT = (244, 247, 249)
C_DIM = (154, 167, 176)
C_ACCENT = (61, 224, 201)
C_POWER = (255, 182, 92)
C_HR = (255, 107, 107)
C_CAD = (61, 224, 201)
C_ALT = (127, 184, 255)
C_GRAD = (184, 224, 107)
C_DIST = (244, 247, 249)


def load_font(size):
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except Exception:
        return ImageFont.load_default()


def lerp(a, b, t):
    if a is None or b is None:
        return a if a is not None else b
    return a + (b - a) * t


def sample(series, fields, t):
    """按时间 t 在列式 series 中二分查找并线性插值。"""
    ts = series["t"]
    if t < ts[0] or t > ts[-1]:
        return None
    lo, hi = 0, len(ts) - 1
    while lo < hi:
        mid = (lo + hi + 1) >> 1
        if ts[mid] <= t:
            lo = mid
        else:
            hi = mid - 1
    i = lo
    i1 = min(i + 1, len(ts) - 1)
    span = ts[i1] - ts[i]
    frac = (t - ts[i]) / span if span > 0 else 0
    out = {"t": t}
    for f in fields:
        arr = series.get(f)
        if arr is None:
            out[f] = None
            continue
        a, b = arr[i], arr[i1]
        out[f] = lerp(a, b, frac)
    return out


def draw_gradient_bg(img):
    """竖向渐变背景。"""
    draw = ImageDraw.Draw(img)
    for y in range(H):
        frac = y / H
        r = int(C_BG_TOP[0] + (C_BG_BOT[0] - C_BG_TOP[0]) * frac)
        g = int(C_BG_TOP[1] + (C_BG_BOT[1] - C_BG_TOP[1]) * frac)
        b = int(C_BG_TOP[2] + (C_BG_BOT[2] - C_BG_TOP[2]) * frac)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def rounded_panel(draw, x, y, w, h, r=12):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=C_PANEL, outline=C_LINE, width=1)


def draw_text(draw, x, y, text, font, fill, anchor="la"):
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


def draw_frame(series, fields, t, history, profile, profile_t0, profile_t1, alt_min, alt_max, track_pts, track_bounds, frame_idx):
    img = Image.new("RGB", (W, H))
    draw_gradient_bg(img)
    draw = ImageDraw.Draw(img, "RGBA")

    p = sample(series, fields, t)
    if p is None:
        p = {f: None for f in fields}
        p["t"] = t

    f_big = load_font(52)
    f_med = load_font(30)
    f_small = load_font(16)
    f_label = load_font(13)
    f_tiny = load_font(11)

    # ---- 左上：速度 ----
    rounded_panel(draw, 36, 30, 250, 104, 14)
    draw_text(draw, 56, 50, "SPEED", f_label, C_DIM)
    spd = p.get("speed")
    spd_kmh = spd * 3.6 if spd is not None else None
    draw_text(draw, 56, 82, f"{spd_kmh:.1f}" if spd_kmh is not None else "--", f_big, C_TEXT)
    draw_text(draw, 185, 86, "km/h", f_small, C_DIM)
    if p.get("lat") is not None:
        draw_text(draw, 56, 116, f"{p['lat']:.5f}, {p['lon']:.5f}", f_tiny, (255, 255, 255, 80))

    # ---- 左中：功率 / 心率 / 踏频 ----
    tile_y, tile_w, tile_h, gap = 146, 116, 78, 10
    tiles = [
        ("POWER", p.get("power"), "W", C_POWER, 0),
        ("HR", p.get("hr"), "bpm", C_HR, 1),
        ("CAD", p.get("cad"), "rpm", C_CAD, 2),
    ]
    for label, val, unit, color, idx in tiles:
        x = 36 + idx * (tile_w + gap)
        rounded_panel(draw, x, tile_y, tile_w, tile_h, 12)
        draw_text(draw, x + 14, tile_y + 18, label, f_label, C_DIM)
        txt = f"{val:.0f}" if val is not None else "--"
        draw_text(draw, x + 14, tile_y + 46, txt, f_med, color)
        if val is not None:
            draw_text(draw, x + 14 + len(txt) * 17 + 6, tile_y + 50, unit, f_tiny, C_DIM)

    # ---- 右上：海拔 / 坡度 / 距离 ----
    rx = W - 36 - 250
    ry = 30
    items = [
        ("ALT", p.get("alt"), "m", C_ALT, 72),
        ("GRAD", p.get("grad"), "%", C_GRAD, 54),
        ("DIST", p.get("odo") / 1000 if p.get("odo") is not None else None, "km", C_DIST, 54),
    ]
    cy = ry
    for label, val, unit, color, hh in items:
        rounded_panel(draw, rx, cy, 250, hh, 12)
        draw_text(draw, rx + 16, cy + 16, label, f_label, C_DIM)
        txt = f"{val:.0f}" if val is not None and label != "DIST" else (f"{val:.2f}" if val is not None else "--")
        draw_text(draw, rx + 16, cy + 36 if hh == 72 else cy + 28, txt, f_med if hh == 72 else load_font(26), color)
        if val is not None:
            draw_text(draw, rx + 16 + len(txt) * 15 + 8, cy + 40 if hh == 72 else cy + 32, unit, f_tiny, C_DIM)
        cy += hh + 12

    # ---- 右中：海拔剖面 ----
    py = 314
    rounded_panel(draw, rx, py, 250, 78, 12)
    draw_text(draw, rx + 16, py + 16, "ELEVATION", f_label, C_DIM)
    if profile and alt_max > alt_min:
        pts = []
        for i, (tt, aa) in enumerate(profile):
            if aa is None:
                continue
            px = rx + 16 + (tt - profile_t0) / (profile_t1 - profile_t0) * 218
            py2 = py + 54 - (aa - alt_min) / (alt_max - alt_min) * 40
            pts.append((px, py2))
        if len(pts) > 1:
            draw.line(pts, fill=C_ALT, width=2)
        # 当前位置游标
        if t is not None:
            cx = rx + 16 + (t - profile_t0) / (profile_t1 - profile_t0) * 218
            cx = max(rx + 16, min(rx + 234, cx))
            draw.line([(cx, py + 24), (cx, py + 64)], fill=(255, 255, 255, 160), width=1)
            draw.ellipse([cx - 3, py + 50 - 3, cx + 3, py + 50 + 3], fill=(255, 255, 255))

    # ---- 右中下：轨迹地图 ----
    my = 404
    rounded_panel(draw, rx, my, 250, 180, 12)
    draw_text(draw, rx + 16, my + 16, "TRACK", f_label, C_DIM)
    if track_pts and track_bounds:
        minLat, maxLat, minLon, maxLon, latScale, lonScale = track_bounds
        pad, plotW, plotH = 16, 218, 140
        dLat = maxLat - minLat or 1
        dLon = maxLon - minLon or 1
        scale = min(plotW / (dLon * lonScale), plotH / (dLat * latScale))
        cLat = (minLat + maxLat) / 2
        cLon = (minLon + maxLon) / 2
        def mpx(lon): return rx + pad + plotW / 2 + (lon - cLon) * lonScale * scale
        def mpy(lat): return my + 24 + plotH / 2 - (lat - cLat) * latScale * scale
        pts = [(mpx(lon), mpy(lat)) for lat, lon in track_pts]
        if len(pts) > 1:
            draw.line(pts, fill=(61, 224, 201, 115), width=2)
        if p.get("lat") is not None and p.get("lon") is not None:
            cx, cy = mpx(p["lon"]), mpy(p["lat"])
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=C_ACCENT, width=2)
            draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 255))

    # ---- 底部：速度曲线 ----
    curve_x, curve_y, curve_w, curve_h = 36, 600, W - 72, 90
    rounded_panel(draw, curve_x, curve_y, curve_w, curve_h, 12)
    draw_text(draw, curve_x + 16, curve_y + 16, f"SPEED · last {len(history) * 0.1:.0f}s", f_label, C_DIM)
    if len(history) > 1:
        vmax = max(h[1] for h in history) * 3.6
        vmax = max(vmax, 10)
        plot_top, plot_bot = curve_y + 28, curve_y + curve_h - 14
        pts = []
        for i, (tt, vv) in enumerate(history):
            if vv is None:
                continue
            px = curve_x + 18 + i / (len(history) - 1) * (curve_w - 36)
            py2 = plot_bot - (vv * 3.6) / vmax * (plot_bot - plot_top)
            pts.append((px, py2))
        if len(pts) > 1:
            draw.line(pts, fill=C_ACCENT, width=2)
            # 填充
            fill_pts = pts + [(pts[-1][0], plot_bot), (pts[0][0], plot_bot)]
            draw.polygon(fill_pts, fill=(61, 224, 201, 40))
        # 当前点
        if pts:
            draw.ellipse([pts[-1][0] - 4, pts[-1][1] - 4, pts[-1][0] + 4, pts[-1][1] + 4], fill=(255, 255, 255))
        # 刻度
        draw_text(draw, curve_x + 10, plot_bot + 4, "0", f_tiny, (255, 255, 255, 90))
        draw_text(draw, curve_x + 10, plot_top, f"{vmax:.0f} km/h", f_tiny, (255, 255, 255, 90))

    # ---- 时间码 ----
    hh = int(t // 3600)
    mm = int((t % 3600) // 60)
    ss = int(t % 60)
    time_str = f"{hh:02d}:{mm:02d}:{ss:02d}" if hh > 0 else f"{mm:02d}:{ss:02d}"
    draw_text(draw, W // 2, 20, time_str, load_font(20), (255, 255, 255, 120), anchor="ma")

    return img


def main():
    parser = argparse.ArgumentParser(description="Render a demo MP4 with dashboard overlay from export JSON")
    parser.add_argument("json", type=Path, help="Input JSON from gopro-export-json.py")
    parser.add_argument("output", type=Path, help="Output MP4")
    parser.add_argument("--start", type=float, default=None, help="Start time in seconds (default: auto-pick)")
    parser.add_argument("--duration", type=float, default=30, help="Duration in seconds")
    parser.add_argument("--fps", type=int, default=10, help="Frame rate")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg binary")
    args = parser.parse_args()

    data = json.load(open(args.json))
    # 行式（v2）→ 列式（运行时列式便于采样）
    if "rows" in data and "fields" in data:
        series = {f: [row[i] for row in data["rows"]] for i, f in enumerate(data["fields"])}
        meta_fields = data["fields"]
    else:
        series = data["series"]
        meta_fields = data["meta"]["fields"]
    fields = [f for f in meta_fields if f != "t" and series.get(f) is not None]
    t_total = series["t"][-1]

    # 自动选片段：速度变化最大的窗口
    if args.start is None:
        best = None
        step = max(1, int(args.fps * 5))
        win = int(args.duration * args.fps)
        for s in range(0, len(series["t"]) - win, step):
            seg = [series["speed"][i] for i in range(s, s + win) if series["speed"][i] is not None]
            if len(seg) < 10:
                continue
            score = max(seg) - min(seg)
            if best is None or score > best[0]:
                best = (score, series["t"][s])
        args.start = best[1] if best else 0

    print(f"Rendering {args.duration}s @ {args.fps}fps from t={args.start:.0f}s (total {t_total:.0f}s)")

    # 预计算海拔剖面（全程，每 10s 一点）
    profile = []
    alt_vals = []
    for i in range(0, len(series["t"]), max(1, int(10 * args.fps))):
        tt = series["t"][i]
        aa = series["alt"][i] if series.get("alt") else None
        profile.append((tt, aa))
        if aa is not None:
            alt_vals.append(aa)
    alt_min = min(alt_vals) if alt_vals else 0
    alt_max = max(alt_vals) if alt_vals else 1
    if alt_max - alt_min < 2:
        alt_min -= 1
        alt_max += 1
    profile_t0 = profile[0][0]
    profile_t1 = profile[-1][0]

    # 预计算轨迹（降采样到最多 2000 点）
    track_pts = []
    track_bounds = None
    if series.get("lat") and series.get("lon"):
        raw = [(series["lat"][i], series["lon"][i]) for i in range(len(series["t"]))
               if series["lat"][i] is not None and series["lon"][i] is not None]
        if len(raw) >= 2:
            lats = [p[0] for p in raw]
            lons = [p[1] for p in raw]
            minLat, maxLat = min(lats), max(lats)
            minLon, maxLon = min(lons), max(lons)
            step = max(1, len(raw) // 2000)
            track_pts = raw[::step]
            if track_pts[-1] != raw[-1]:
                track_pts.append(raw[-1])
            centerLat = (minLat + maxLat) / 2
            track_bounds = (minLat, maxLat, minLon, maxLon, 111320, 111320 * math.cos(centerLat * math.pi / 180))

    # ffmpeg 管道
    cmd = [
        args.ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-framerate", str(args.fps),
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        str(args.output),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    history = []
    n_frames = int(args.duration * args.fps)
    for fi in range(n_frames):
        t = args.start + fi / args.fps
        p = sample(series, fields, t)
        if p and p.get("speed") is not None:
            history.append((t, p["speed"]))
            if len(history) > 1200:  # 最多保留 120s @10fps
                history.pop(0)
        img = draw_frame(series, fields, t, history, profile, profile_t0, profile_t1, alt_min, alt_max, track_pts, track_bounds, fi)
        proc.stdin.write(img.tobytes())
        if fi % 50 == 0:
            print(f"  frame {fi}/{n_frames}  t={t:.1f}s")

    proc.stdin.close()
    proc.wait()
    print(f"Done -> {args.output}")


if __name__ == "__main__":
    main()
