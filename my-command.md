# batch

bash trans-one.sh /Volumes/gopro/DCIM/20250420-银屏山/GX010303.MP4 /Volumes/udisk/cycling/20250420-银屏山 ~/Downloads/银屏山巴黎鲁贝-14.gpx

bash trans-one.sh /Volumes/gopro/DCIM/20250420-银屏山/GX010303-cat.MP4 /Volumes/udisk/cycling/20250420-银屏山 ~/Downloads/银屏山巴黎鲁贝-14.gpx

bash trans.sh /Volumes/gopro/DCIM/20250322-万佛湖万佛山 /Volumes/udisk/cycling/20250322-万佛湖万佛山 ~/Downloads/万佛湖万佛山.fit

# 修改 gpx 文件时间偏移（秒）

python bin/gpx_time_offset.py example.txt output.gpx -14

# 合并视频和音频

ffmpeg -i GX010175.MP4 -i 1.MP3 -map 0:v -map 1:a -c copy GX010175-merged.MP4


# 提取 gopro 视频文件中的 gps 信息

## 单一一个

bin/gopro-to-gpx.py /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010181.MP4 GX010181.gpx --only-locked

## 批量提取

bash scripts/extract-gps.sh /Volumes/gopro/DCIM/20250420-银屏山 /Volumes/gopro/DCIM/20250420-银屏山

# 获得两个 gpx 之间的秒差

python bin/find-time.py tmp/_4_.gpx /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010182.MP4.gpx

## 批量获取两个 gpx 之间的秒差

bash scripts/compare-gps-time.sh ~/Downloads/银屏山巴黎鲁贝.gpx /Volumes/gopro/DCIM/20250420-银屏山

# cat

bin/gopro-cut.py /Volumes/gopro/DCIM/20250420-银屏山/GX010303.MP4 --start 00:02:11.000000 --end 00:02:21.000000 /Volumes/gopro/DCIM/20250420-银屏山/GX010303-cat.MP4

# test

bin/gopro-dashboard.py --font "Andale Mono" --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --gpx ~/Downloads/_4_.gpx ./GX010181-1m.MP4 GX010181-1m-d.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac-t --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11870394097_ACTIVITY.fit ./GX010149-10s.MP4 GX010126-dashboard.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-2.xml --fit ~/Downloads/20230806-庐南川藏线.fit ./tmp/GX010126-10s.MP4 ./tmp/GX010126-dashboard.MP4


bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11926376810_ACTIVITY.fit /Volumes/Untitled/DCIM/100GOPRO/GX010125.MP4 /Volumes/2T-udisk/GX010125.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/20230806-庐南川藏线.fit /Volumes/Untitled/DCIM/100GOPRO/GX020130.MP4 /Volumes/2T-udisk/GX020130.MP4

bin/gopro-cut.py /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010181.MP4 --start 00:01:26.000000 --end 00:02:26.000000 GX010181-1m.MP4

bin/gopro-extract.py GX020123-10s.MP4 GX020123.json