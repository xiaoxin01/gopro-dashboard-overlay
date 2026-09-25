#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'EOF'
Usage:
  gopro-merge-videos.sh INPUT_DIR OUTPUT_DIR [OUTPUT_FILENAME]

Merge MP4 files directly inside INPUT_DIR in creation-time order.
The default output filename is combine.mp4.
EOF
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
    usage >&2
    exit 2
fi

input_dir=$1
output_dir=$2
output_name=${3:-combine.mp4}

if [[ ! -d "$input_dir" ]]; then
    echo "Input directory does not exist: $input_dir" >&2
    exit 1
fi

if [[ "$output_name" == */* || -z "$output_name" ]]; then
    echo "Output filename must be a filename, not a path: $output_name" >&2
    exit 2
fi

command -v ffmpeg >/dev/null 2>&1 || {
    echo "ffmpeg was not found in PATH" >&2
    exit 1
}

command -v python3 >/dev/null 2>&1 || {
    echo "python3 was not found in PATH" >&2
    exit 1
}

mkdir -p "$output_dir"

list_file=$(mktemp "${TMPDIR:-/tmp}/gopro-merge.XXXXXX")
temporary_output="$output_dir/.${output_name}.part.$$"

cleanup() {
    rm -f "$list_file" "$temporary_output"
}
trap cleanup EXIT INT TERM

python3 - "$input_dir" "$list_file" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1])
list_file = Path(sys.argv[2])

def creation_time(path: Path) -> float:
    stat = path.stat()
    return getattr(stat, "st_birthtime", stat.st_mtime)

files = sorted(
    (
        path
        for path in source.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".mp4"
        and not path.name.startswith("._")
    ),
    key=lambda path: (creation_time(path), path.name.casefold()),
)

if not files:
    raise SystemExit(f"No MP4 files found directly inside: {source}")

with list_file.open("w", encoding="utf-8") as output:
    for path in files:
        escaped = str(path.resolve()).replace("\\", "\\\\").replace("'", "'\\''")
        output.write(f"file '{escaped}'\n")

print(f"Found {len(files)} MP4 file(s)")
for path in files:
    print(f"  {path.name}")
PY

output_file="$output_dir/$output_name"

echo "Writing temporary output: $temporary_output"
ffmpeg \
    -hide_banner \
    -f concat \
    -safe 0 \
    -analyzeduration 100M \
    -probesize 100M \
    -thread_queue_size 128 \
    -i "$list_file" \
    -f mp4 \
    -map '0:v:0' \
    -map '0:a:0?' \
    -dn \
    -c:v hevc_videotoolbox \
    -q:v 57 \
    -c:a copy \
    -movflags +faststart \
    -y "$temporary_output"

mv -f "$temporary_output" "$output_file"
echo "Created: $output_file"
