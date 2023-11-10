import gpxpy
from scipy.spatial import cKDTree
import sys

def calculate_distance(lat1, lon1, lat2, lon2):
    # 使用合适的方法来计算两点之间的距离，例如 Haversine 公式
    # 这里给出一个简单的示例（单位为米）
    return ((lat2 - lat1)**2 + (lon2 - lon1)**2)**0.5

def adjust_start_time(gpx_file_1, gpx_file_2):
    # 读取 GPX 文件
    with open(gpx_file_1, 'r') as f:
        gpx_1 = gpxpy.parse(f)

    with open(gpx_file_2, 'r') as f:
        gpx_2 = gpxpy.parse(f)

    # 获取所有轨迹点
    points_1 = [point for track in gpx_1.tracks for segment in track.segments for point in segment.points]
    points_2 = [point for track in gpx_2.tracks for segment in track.segments for point in segment.points]

    # 如果 points_2 的长度为 0 ，则返回 None
    if len(points_2) == 0:
        return None

    # 构建 kd 树
    tree_2 = cKDTree([(point.latitude, point.longitude) for point in points_2])

    best_match = None
    smallest_distance = float('inf')

    for point_1 in points_1:
        # 在kd树中找到最近的点
        nearest_point_idx = tree_2.query([point_1.latitude, point_1.longitude])[1]
        nearest_point = points_2[nearest_point_idx]

        distance = calculate_distance(point_1.latitude, point_1.longitude, nearest_point.latitude, nearest_point.longitude)

        if distance < smallest_distance:
            smallest_distance = distance
            best_match = (point_1.time, nearest_point.time)

    if best_match is not None:
        start_time_1, start_time_2 = best_match
        time_difference = (start_time_2 - start_time_1).total_seconds()
        return start_time_2, time_difference
    else:
        return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("请提供两个GPX文件的路径作为参数")
    else:
        gpx_file_1 = sys.argv[1]
        gpx_file_2 = sys.argv[2]

        result = adjust_start_time(gpx_file_1, gpx_file_2)

        gpx_file_2 = gpx_file_2.split('/')[-1]
        if result is not None:
            correct_start_time, time_difference = result
            # 获取文件名：gpx_file_2
            print(f'{gpx_file_2}, {time_difference}, {correct_start_time}')
        else:
            print(f'{gpx_file_2}, 0, 0')
