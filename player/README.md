# 播放器外挂显示（方案 C）

视频原片**完全不动**，运动数据单独导出为 JSON，由本地播放器页面在播放时实时叠加仪表盘。
改仪表样式、开关、布局 = 改播放器页面刷新即可，**零视频渲染**。

```
player/
├── index.html            # 播放器（单文件，含全部样式与逻辑）
├── example-data/out.json # 示例数据（由仓库内 out.gpx 导出）
└── README.md
```

## 三步使用

### 1. 导出数据 JSON

```bash
# GoPro 视频自带元数据（数据自动对齐视频时间轴）
.venv/bin/python bin/gopro-export-json.py --input GX040274.MP4 out.json

# 纯 GPX / FIT（时间轴从数据起点开始）
.venv/bin/python bin/gopro-export-json.py --gpx ride.gpx out.json
.venv/bin/python bin/gopro-export-json.py --fit ride.fit out.json

# 外部 GPX / FIT 对齐到某段视频（--video-time-start 选视频文件时间作为 0 秒）
.venv/bin/python bin/gopro-export-json.py --input video.mp4 --gpx ride.gpx out.json
```

可选参数：`--every N` 每隔 N 秒降采样（默认 0 = 输出 FIT/GPX 全部原始数据点，不插值；`--every 1` 强制 1Hz）。

导出 JSON 为行式格式（时间与数据在同一行）：
```json
{"version":2, "meta":{...}, "fields":["t","speed","hr",...], "rows":[[0.0,5.97,141,...],[1.0,5.82,140,...]]}
```
全空字段（如 GPX 无 dop）自动从 fields 中剔除。播放器同时兼容旧版列式格式。

### 2. 打开播放器

直接双击 `player/index.html`，或配合本地服务（**推荐用支持 Range 的 serve.py**，否则大视频无法拖动进度条）：

```bash
# 推荐：支持 HTTP Range，大视频可正常 seek/拖动
python3 bin/serve.py 8765

# 不推荐：Python 内置 http.server 不支持 Range，大视频进度条无法拖动
# python3 -m http.server 8765

# 浏览器打开 http://localhost:8765/player/index.html
```

### 3. 加载数据和视频

两种方式任选：

**方式 A：URL 参数**（配合本地服务，适合固定搭配）
```
http://localhost:8765/player/index.html?data=example-data/wanzheyiquan.json&video=video-src/combine.mp4
```
支持参数：`data=`（数据 JSON）、`video=`（视频文件，相对路径）、`offset=`（全局偏移秒数）、`offsetFile=`（指定 offset 文件）。

**方式 B：拖拽 / 按钮**（灵活，适合临时查看）
把 **JSON 数据**和**视频**拖进窗口，或点顶栏「打开数据 JSON」「打开视频」按钮选择文件。先拖数据可无视频预览仪表盘动画，再拖视频即叠加。

> 视频通过按钮/拖拽加载时用本地文件句柄（blob URL），天然支持 seek；通过 URL 参数加载时走 HTTP，需服务器支持 Range（serve.py 已支持）。

## 播放器功能

- 仪表盘：速度 / 功率 / 心率 / 踏频 / 海拔 / 坡度 / 距离 / 温度，速度曲线（近 120s）、海拔剖面（全程 + 游标）、轨迹地图（全程路线 + 当前位置）
- 数据字段缺失（如 GPX 无心率）时对应仪表自动隐藏
- 快捷键：空格 播放/暂停，←/→ 快退快进 5s
- 倍速 0.5×–4×；进度条拖动
- 「仪表盘」按钮可逐个开关仪表（状态记忆在浏览器 localStorage）
- 纯数据模式（无视频）可用虚拟时钟预览动画
- **时间偏移（offset）**：数据与视频时间轴不对齐时可微调，支持 ±0.1/±1/±10s 按钮、直接输入、重置；按数据文件名记忆在 localStorage；顶栏显示当前 offset 标签（分段映射时显示当前段总偏移）

## 时间偏移（offset）

当数据起点与视频起点不一致，或多段视频合并后中间有暂停/间隔时，用 offset 对齐。

offset 文件包含每段视频的独立映射（`segments`），播放器根据当前视频时间自动找到对应片段，用该段的 offset 跳转到数据点——视频间的暂停不会导致数据错位。

```
数据时间 = 视频时间 + 该段 offset + 用户微调
```

**自动初始化**（根据原视频修改时间和时长计算每段 offset）：

```bash
.venv/bin/python bin/init-offset.py \
  --data player/example-data/wanzheyiquan.json \
  --video-dir "/Volumes/ssd/cycling/20260725-皖浙天路" \
  --combined "/Volumes/ssd/cycling-out/20260725-皖浙天路/combine.mp4" \
  player/example-data/wanzheyiquan.offset.json
```

输出含 `offset_s`（首段偏移）和 `segments`（每段视频的 `video_start_s` / `duration_s` / `start_utc`）。

**自动加载**：数据 JSON 同目录下如有同名 `.offset.json`，播放器自动应用，无需额外参数。

**手动微调**：播放器「仪表盘」面板顶部「时间偏移」区，显示当前段的基础 offset + 微调值，±0.1/±1/±10s 按钮为全局微调（在分段映射基础上统一偏移），调整自动保存。

**URL 参数**（可选）：
```
?offset=49              # 单一全局偏移（无 offset 文件时）
?offsetFile=xxx.offset.json  # 指定 offset 文件
```

## 自定义

页面顶部 `CONFIG` 对象集中配置：

```js
const CONFIG = {
  speedUnit: 'kph',     // 'kph' | 'mph'
  distanceUnit: 'km',   // 'km' | 'mi'
  historyWindow: 120,   // 速度曲线时间窗（秒）
  profileStep: 1.0,     // 海拔剖面采样步长（秒）
  palette: { ... },     // 仪表配色
};
```

仪表列表（`WIDGETS` 数组）可增删，改完刷新即生效。

## 局限

- 播放器是本地播放工具，产出不是「合成好的 MP4」；要上传平台或分发成片，需定稿后按原项目方式烧录一次
- 轨迹地图为纯 Canvas 绘制（无街道底图，仅显示路线轮廓和当前位置）
- 本地双击打开时请用拖拽加载数据；`?data=&video=` URL 参数方式需配合支持 Range 的本地服务（`python3 bin/serve.py`），否则大视频无法拖动进度条
