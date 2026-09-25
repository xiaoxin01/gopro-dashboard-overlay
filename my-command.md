# 外挂数据显示方案

## 导出 player 支持的 json 文件

使用 FIT 文件生成 player 支持的 JSON 数据文件：

```shell
.venv/bin/python bin/gopro-export-json.py \
  --fit "player/example-data/庐南川藏线_三公山.fit" \
  "player/example-data/庐南川藏线_三公山.json"
```

将 `--fit` 后的路径替换为输入 FIT 文件，将最后一个路径替换为输出 JSON 文件路径。

## 生成 player 使用的 offset 文件

根据原始 GoPro 视频文件的录制时间、合并视频时长和导出的数据 JSON，生成 offset 文件：

```shell
.venv/bin/python bin/init-offset.py \
  --data "player/example-data/庐南川藏线_三公山.json" \
  --video-dir "/Volumes/ssd/cycling/20260920-庐南加三公山" \
  --combined "/Volumes/ssd/cycling-out/20260920-庐南加三公山/combine.mp4" \
  "player/example-data/庐南川藏线_三公山.offset.json"
```

其中 `--video-dir` 是合并前的原始 GoPro 视频目录，`--combined` 是合并后的视频文件。

## Merging all MP4 files in a directory

On macOS, you can use `bin/merge-videos.sh` to merge the MP4 files directly
inside an input directory. Files are ordered by creation time, and the result is
HEVC-transcoded with `hevc_videotoolbox`. The default output filename is
`combine.mp4`.

```shell
bin/merge-videos.sh \
  "/Volumes/ssd/cycling/20260920-庐南加三公山" \
  "/Volumes/ssd/cycling-out/20260920-庐南加三公山"
```

To choose a different output filename, provide it as the third argument:

```shell
bin/merge-videos.sh \
  "/Volumes/ssd/cycling/20260726-浙西天路" \
  "/Volumes/ssd/cycling-out/20260726-浙西天路" \
  merged.mp4
```

The command requires `ffmpeg` and `python3`. It ignores macOS `._` metadata files,
copies the first audio stream, and writes to a temporary file before replacing the
final output so an interrupted conversion does not leave a seemingly complete
but unplayable MP4.

## 播放

    http://127.0.0.1:8000/player/index.html?data=example-data/庐南川藏线_三公山.json&video=video2/combine.mp4

# batch

bash trans-one-2x.sh /Volumes/ssd/cycling/20260725-皖浙天路/GX010438.MP4 /Volumes/ssd/cycling-out/20260725-皖浙天路 ~/Downloads/皖浙天路顺时针一圈.gpx

bash trans-one.sh /Volumes/gopro/DCIM/20250525-银屏山土路越野/GX010360.MP4 /Volumes/ssd/cycling/20250525-银屏山土路越野 ~/Downloads/霍山到龙井峡.gpx

bash trans.sh /Volumes/gopro/DCIM/20260509-龙井峡 /Volumes/ssd/cycling/20260509-龙井峡 ~/Downloads/霍山到龙井峡.gpx

# 修改 gpx 文件时间偏移（秒）

python bin/gpx_time_offset.py example.txt output.gpx -14

# 合并视频和音频

ffmpeg -i GX010175.MP4 -i 1.MP3 -map 0:v -map 1:a -c copy GX010175-merged.MP4


# 提取 gopro 视频文件中的 gps 信息

## 单一一个

bin/gopro-to-gpx.py /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010181.MP4 GX010181.gpx --only-locked

## 批量提取

bash scripts/extract-gps.sh /Volumes/gopro/DCIM/20260509-龙井峡 /Volumes/gopro/DCIM/20260509-龙井峡

# 获得两个 gpx 之间的秒差

python bin/find-time.py tmp/_4_.gpx /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010182.MP4.gpx

## 批量获取两个 gpx 之间的秒差

bash scripts/compare-gps-time.sh ~/Downloads/霍山到龙井峡.gpx /Volumes/gopro/DCIM/20260509-龙井峡

# cat

bin/gopro-cut.py /Volumes/ssd/cycling/20250420-银屏山/GX010302.MP4 --start 00:00:26.000000 --end 00:22:21.000000 /Volumes/ssd/cycling/20250420-银屏山/GX010302.MP4-cat.MP4

# test

bin/gopro-dashboard.py --font "Andale Mono" --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --gpx ~/Downloads/_4_.gpx ./GX010181-1m.MP4 GX010181-1m-d.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac-t --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11870394097_ACTIVITY.fit ./GX010149-10s.MP4 GX010126-dashboard.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-2.xml --fit ~/Downloads/20230806-庐南川藏线.fit ./tmp/GX010126-10s.MP4 ./tmp/GX010126-dashboard.MP4


bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11926376810_ACTIVITY.fit /Volumes/Untitled/DCIM/100GOPRO/GX010125.MP4 /Volumes/2T-udisk/GX010125.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/20230806-庐南川藏线.fit /Volumes/Untitled/DCIM/100GOPRO/GX020130.MP4 /Volumes/2T-udisk/GX020130.MP4

bin/gopro-cut.py /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010181.MP4 --start 00:01:26.000000 --end 00:02:26.000000 GX010181-1m.MP4

bin/gopro-extract.py GX020123-10s.MP4 GX020123.json
