import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import argparse

def adjust_gpx_time(input_file, output_file, offset_seconds):
    # 解析 XML 文件
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # 定义命名空间
    namespaces = {
        '': 'http://www.topografix.com/GPX/1/1',
        'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1',
        'gpxx': 'http://www.garmin.com/xmlschemas/GpxExtensions/v3'
    }
    
    # 注册命名空间
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    
    # 修改 metadata 中的时间
    metadata = root.find('metadata', namespaces)
    if metadata is not None:
        time_elem = metadata.find('time', namespaces)
        if time_elem is not None:
            original_time = datetime.strptime(time_elem.text, '%Y-%m-%dT%H:%M:%SZ')
            adjusted_time = original_time + timedelta(seconds=offset_seconds)
            time_elem.text = adjusted_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 修改所有轨迹点的时间
    for trkpt in root.findall('.//trkpt', namespaces):
        time_elem = trkpt.find('time', namespaces)
        if time_elem is not None:
            original_time = datetime.strptime(time_elem.text, '%Y-%m-%dT%H:%M:%SZ')
            adjusted_time = original_time + timedelta(seconds=offset_seconds)
            time_elem.text = adjusted_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 保存修改后的文件
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

def main():
    parser = argparse.ArgumentParser(description='调整 GPX 文件中的时间偏移')
    parser.add_argument('input_file', help='输入的 GPX 文件路径')
    parser.add_argument('output_file', help='输出的 GPX 文件路径')
    parser.add_argument('offset_seconds', type=int, help='时间偏移量（秒），负数表示减少时间')
    
    args = parser.parse_args()
    
    adjust_gpx_time(args.input_file, args.output_file, args.offset_seconds)
    print(f'已完成时间偏移调整，输出文件：{args.output_file}')

if __name__ == '__main__':
    main() 