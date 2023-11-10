# batch

bash trans-one.sh /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010180.MP4 /Volumes/2T-udisk/20231104-庐南五连爬 /Users/chenjinxin/Downloads/_4_-5.gpx

bash trans.sh /Volumes/Untitled/DCIM/20231104-庐南五连爬 /Volumes/2T-udisk/20231015-紫蓬山刘铭传 /Users/chenjinxin/Downloads/12589526273_ACTIVITY.fit

# 合并视频和音频

ffmpeg -i GX010175.MP4 -i 1.MP3 -map 0:v -map 1:a -c copy GX010175-merged.MP4


# 提取 gopro 视频文件中的 gps 信息

## 单一一个

bin/gopro-to-gpx.py /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010181.MP4 GX010181.gpx --only-locked

## 批量提取

bash scripts/extract-gps.sh /Volumes/Untitled/DCIM/20231104-庐南五连爬 /Volumes/Untitled/DCIM/20231104-庐南五连爬

# 获得两个 gpx 之间的秒差

python bin/find-time.py tmp/_4_.gpx /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010182.MP4.gpx

## 批量获取两个 gpx 之间的秒差

bash scripts/compare-gps-time.sh tmp/_4_.gpx /Volumes/Untitled/DCIM/20231104-庐南五连爬

# cat

bin/gopro-cut.py /Volumes/2T-udisk/20231104-庐南五连爬/GX010177.MP4 --start 00:06:50.000000 --end 01:06:50.000000 /Volumes/2T-udisk/20231104-庐南五连爬/GX010177-cat.MP4

# test

bin/gopro-dashboard.py --font "Andale Mono" --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --gpx ~/Downloads/_4_.gpx ./GX010181-1m.MP4 GX010181-1m-d.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac-t --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11870394097_ACTIVITY.fit ./GX010149-10s.MP4 GX010126-dashboard.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-2.xml --fit ~/Downloads/20230806-庐南川藏线.fit ./tmp/GX010126-10s.MP4 ./tmp/GX010126-dashboard.MP4


bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11926376810_ACTIVITY.fit /Volumes/Untitled/DCIM/100GOPRO/GX010125.MP4 /Volumes/2T-udisk/GX010125.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/20230806-庐南川藏线.fit /Volumes/Untitled/DCIM/100GOPRO/GX020130.MP4 /Volumes/2T-udisk/GX020130.MP4

bin/gopro-cut.py /Volumes/Untitled/DCIM/20231104-庐南五连爬/GX010181.MP4 --start 00:01:26.000000 --end 00:02:26.000000 GX010181-1m.MP4

bin/gopro-extract.py GX020123-10s.MP4 GX020123.json