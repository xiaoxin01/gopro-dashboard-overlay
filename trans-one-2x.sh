#!/bin/bash

# 获取原路径和目的路径
file=$1
dest=$2
fit=$3


# 打印文件名
echo "Processing file: $file"

# 获取文件名，不包含路径
filename=$(basename "$file")

# 目标文件路径
destfile="$dest/$filename"

# 执行另一个脚本
# ./another_script.sh "$file"
bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac-2x --layout-xml gopro_overlay/layouts/power-1920x1080-2.xml --use-gpx-only --gpx "$fit" --video-time-end file-modified "$file" "$destfile"
