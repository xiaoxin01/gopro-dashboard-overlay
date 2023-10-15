# batch

bash trans.sh /Volumes/Untitled/DCIM/20231015-紫蓬山刘铭传 /Volumes/2T-udisk/20231015-紫蓬山刘铭传 /Users/chenjinxin/Downloads/10040340022.fit

# test

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac-t --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11870394097_ACTIVITY.fit ./GX010149-10s.MP4 GX010126-dashboard.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac-t --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/20230806-庐南川藏线.fit ./GX010126-10s.MP4 GX010126-dashboard.MP4


bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/11926376810_ACTIVITY.fit /Volumes/Untitled/DCIM/100GOPRO/GX010125.MP4 /Volumes/2T-udisk/GX010125.MP4

bin/gopro-dashboard.py --font "Andale Mono" --profile overlay-mac --layout-xml gopro_overlay/layouts/power-1920x1080-my.xml --fit ~/Downloads/20230806-庐南川藏线.fit /Volumes/Untitled/DCIM/100GOPRO/GX020130.MP4 /Volumes/2T-udisk/GX020130.MP4

bin/gopro-cut.py /Volumes/Untitled/DCIM/20230825-大运河东向f/GX010149.MP4 --start 00:03:41.000000 --end 00:03:51.000000 GX010149-10s.MP4

bin/gopro-extract.py GX020123-10s.MP4 GX020123.json