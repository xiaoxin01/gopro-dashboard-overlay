#!/bin/bash

# 获取原路径和目的路径
fit=$1
src=$2

# 遍历原路径下的所有 gpx 文件
for file in "$src"/*.gpx
do
  # # 打印文件名
  # echo "Processing file: $file"

  # 获取文件名，不包含路径
  filename=$(basename "$file")

  # 目标文件路径
  destfile="$dest/$filename".gpx

  # 执行另一个脚本
  # ./another_script.sh "$file"
  python bin/find-time.py "$fit" "$file"
  
done