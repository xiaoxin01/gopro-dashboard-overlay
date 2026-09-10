#!/usr/bin/env python3
"""
serve.py — 支持 HTTP Range 请求的本地静态文件服务器。

Python 内置的 http.server 不支持 Range，导致大视频无法拖动进度条/seek。
这个脚本子类化 SimpleHTTPRequestHandler，实现 bytes Range 支持。

用法：
  python3 bin/serve.py [port] [directory]
  python3 bin/serve.py 8765            # 当前目录，端口 8765
  python3 bin/serve.py 8765 /path/to/dir
"""

import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class RangeHTTPRequestHandler(SimpleHTTPRequestHandler):
    """支持 Range: bytes=start-end 的静态文件处理器。"""

    def send_head(self):
        """重写 send_head，处理 Range 请求。"""
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.stat(path)
        file_size = fs.st_size

        # 解析 Range 头
        range_header = self.headers.get('Range')
        if range_header:
            m = re.match(r'bytes=(\d*)-(\d*)', range_header)
            if m:
                start = int(m.group(1)) if m.group(1) else None
                end = int(m.group(2)) if m.group(2) else None

                if start is None and end is not None:
                    # 后缀范围：最后 N 字节
                    start = max(0, file_size - end)
                    end = file_size - 1
                elif start is not None and end is None:
                    end = file_size - 1
                elif start is not None and end is not None:
                    end = min(end, file_size - 1)

                if start is not None and start <= end and start < file_size:
                    length = end - start + 1
                    f.seek(start)
                    self.send_response(206)
                    self.send_header('Content-Type', ctype)
                    self.send_header('Content-Length', str(length))
                    self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
                    self.end_headers()
                    return f

        # 无 Range：完整文件
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(file_size))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def end_headers(self):
        # CORS 头，方便本地开发
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        # 精简日志：只打印请求行和状态码
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    directory = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    os.chdir(directory)
    server = ThreadingHTTPServer(('127.0.0.1', port), RangeHTTPRequestHandler)
    print(f"Serving {directory} at http://127.0.0.1:{port}  (Range-enabled)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == '__main__':
    main()
