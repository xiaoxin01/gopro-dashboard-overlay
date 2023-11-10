#!/bin/bash

# 获取原路径和目的路径
src=$1
dest=$2
fit=$3

# 遍历原路径下的所有 mp4 文件
for file in "$src"/*.MP4
do
  # 打印文件名
  echo "Processing file: $file"

  # 获取文件名，不包含路径
  filename=$(basename "$file")

  # 目标文件路径
  destfile="$dest/$filename".gpx

  # 执行另一个脚本
  # ./another_script.sh "$file"
  bin/gopro-to-gpx.py "$file" "$destfile" --only-locked
  
done