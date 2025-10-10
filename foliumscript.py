import folium
import pandas as pd
import numpy as np
from folium.plugins import MarkerCluster
import webbrowser
import os


# 读取数据
def load_data(file_path):
    df = pd.read_csv(file_path, header=None)

    # 提取基本信息
    link_ids = df.iloc[:, 0].tolist()
    short_ids = df.iloc[:, 1].tolist()
    # 注意：第3、4列不是经纬度，而是某种ID或坐标编码
    id_x = df.iloc[:, 2].tolist()
    id_y = df.iloc[:, 3].tolist()
    speed_limits = df.iloc[:, 4].tolist()
    lengths = df.iloc[:, 5].tolist()
    directions = df.iloc[:, 6].tolist()

    # 提取速度数据（从第8列开始）
    speed_data = df.iloc[:, 7:].values

    return link_ids, short_ids, id_x, id_y, speed_limits, lengths, directions, speed_data


# 为江南区道路生成模拟坐标
def generate_gangnam_coordinates(num_roads=304):
    """
    为江南区生成模拟的经纬度坐标
    江南区大致范围：37.47°N ~ 37.53°N, 127.02°E ~ 127.12°E
    """
    # 江南区中心坐标
    gangnam_center = [37.4979, 127.0276]  # 江南站附近

    np.random.seed(42)  # 固定随机种子以获得一致的结果

    coordinates = []
    for i in range(num_roads):
        # 在江南区范围内生成随机坐标
        lat = gangnam_center[0] + np.random.uniform(-0.03, 0.03)  # ±0.03度 ≈ ±3km
        lon = gangnam_center[1] + np.random.uniform(-0.05, 0.05)  # ±0.05度 ≈ ±5km
        coordinates.append((lat, lon))

    return coordinates


# 基于道路ID生成更有组织的坐标
def generate_organized_coordinates(link_ids, id_x, id_y):
    """
    基于道路ID和现有的x,y值生成更有组织的坐标布局
    """
    coordinates = []

    # 使用江南区中心作为基准
    base_lat, base_lon = 37.4979, 127.0276

    for i, (link_id, x, y) in enumerate(zip(link_ids, id_x, id_y)):
        # 使用ID和x,y值来生成相对位置
        # 这样可以保持一定的数据相关性
        lat_offset = (hash(str(link_id)) % 1000) / 20000 - 0.025  # -0.025到+0.025
        lon_offset = (hash(str(x) + str(y)) % 1000) / 15000 - 0.033  # -0.033到+0.033

        lat = base_lat + lat_offset
        lon = base_lon + lon_offset

        coordinates.append((lat, lon))

    return coordinates


# 计算统计信息
def calculate_stats(speed_array):
    if len(speed_array) == 0:
        return 0, 0, 0, 0

    valid_speeds = speed_array[speed_array > 0]  # 过滤掉0值

    if len(valid_speeds) == 0:
        return 0, 0, 0, 0

    avg_speed = np.mean(valid_speeds)
    max_speed = np.max(valid_speeds)
    min_speed = np.min(valid_speeds)
    std_speed = np.std(valid_speeds)

    return avg_speed, max_speed, min_speed, std_speed


# 创建热力图数据
def create_heatmap_data(coordinates, speed_data):
    """创建热力图所需的数据格式"""
    heat_data = []
    for i, (lat, lon) in enumerate(coordinates):
        speed_array = speed_data[i]
        valid_speeds = speed_array[speed_array > 0]
        if len(valid_speeds) > 0:
            avg_speed = np.mean(valid_speeds)
            # 将速度转换为权重（0-1之间）
            weight = min(avg_speed / 80.0, 1.0)  # 假设80km/h为上限
            heat_data.append([lat, lon, weight])
    return heat_data


# 创建地图
def create_speed_dashboard(file_path, output_file="seoul_gangnam_speed_dashboard.html"):
    print("正在加载数据...")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在")
        return None

    try:
        link_ids, short_ids, id_x, id_y, speed_limits, lengths, directions, speed_data = load_data(file_path)
    except Exception as e:
        print(f"读取数据文件时出错: {e}")
        return None

    print(f"成功加载 {len(link_ids)} 条道路数据")

    # 为江南区道路生成模拟坐标
    print("正在生成江南区道路模拟坐标...")
    coordinates = generate_organized_coordinates(link_ids, id_x, id_y)

    # 创建底图 - 江南区中心坐标
    gangnam_center = [37.4979, 127.0276]  # 江南站
    m = folium.Map(
        location=gangnam_center,
        zoom_start=14,
        tiles='OpenStreetMap'
    )

    # 添加多种地图图层
    folium.TileLayer(
        'Stamen Terrain',
        name='地形图',
        attr='Stamen'
    ).add_to(m)

    folium.TileLayer(
        'CartoDB positron',
        name='浅色地图',
        attr='CartoDB'
    ).add_to(m)

    # 创建标记聚类
    marker_cluster = MarkerCluster().add_to(m)

    print("正在处理道路数据并创建标记...")

    # 创建热力图数据
    heat_data = create_heatmap_data(coordinates, speed_data)

    # 添加热力图
    from folium.plugins import HeatMap
    if heat_data:
        HeatMap(heat_data,
                name='速度热力图',
                min_opacity=0.3,
                max_opacity=0.8,
                radius=15,
                blur=10,
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'red'}).add_to(m)

    valid_points = 0

    for i, (lat, lon) in enumerate(coordinates):
        if i >= len(link_ids):
            break

        valid_points += 1

        # 计算速度统计
        speed_array = speed_data[i]
        avg_speed, max_speed, min_speed, std_speed = calculate_stats(speed_array)

        # 根据平均速度设置颜色
        if avg_speed == 0:
            color = 'gray'
        elif avg_speed < 20:
            color = 'red'
        elif avg_speed < 40:
            color = 'orange'
        elif avg_speed < 60:
            color = 'yellow'
        else:
            color = 'green'

        # 创建弹出窗口内容
        popup_content = f"""
        <div style="width: 300px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">江南区道路段 #{i + 1}</h4>
            <hr style="margin: 5px 0;">
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>道路ID:</b></td><td>{link_ids[i]}</td></tr>
                <tr><td><b>短ID:</b></td><td>{short_ids[i]}</td></tr>
                <tr><td><b>编码X:</b></td><td>{id_x[i]}</td></tr>
                <tr><td><b>编码Y:</b></td><td>{id_y[i]}</td></tr>
                <tr><td><b>限速:</b></td><td>{speed_limits[i]} km/h</td></tr>
                <tr><td><b>长度:</b></td><td>{lengths[i]:.0f} m</td></tr>
                <tr><td><b>方向:</b></td><td>{'上行' if directions[i] == 0 else '下行'}</td></tr>
            </table>
            <hr style="margin: 8px 0;">
            <h5 style="color: #34495e; margin: 8px 0;">速度统计 (km/h)</h5>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>平均速度:</b></td><td style="color: {color}; font-weight: bold;">{avg_speed:.1f}</td></tr>
                <tr><td><b>最高速度:</b></td><td>{max_speed:.1f}</td></tr>
                <tr><td><b>最低速度:</b></td><td>{min_speed:.1f}</td></tr>
                <tr><td><b>标准差:</b></td><td>{std_speed:.1f}</td></tr>
                <tr><td><b>数据点数:</b></td><td>{len(speed_array[speed_array > 0])}</td></tr>
            </table>
            <hr style="margin: 8px 0;">
            <p style="font-size: 10px; color: #7f8c8d; margin: 0;">
                📍 模拟位置 | 🕒 2018年4月数据<br>
                <em>注：坐标为模拟生成，仅用于可视化展示</em>
            </p>
        </div>
        """

        # 添加标记
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=350),
            tooltip=f"道路 {short_ids[i]}: {avg_speed:.1f} km/h",
            icon=folium.Icon(color=color, icon='road', prefix='fa')
        ).add_to(marker_cluster)

        # 每处理50个点显示进度
        if valid_points % 50 == 0:
            print(f"已处理 {valid_points} 个道路点...")

    print(f"成功创建 {valid_points} 个道路标记")

    # 添加图层控制
    folium.LayerControl().add_to(m)

    # 添加标题
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50%; transform: translateX(-50%);
                background-color: rgba(255, 255, 255, 0.9); padding: 12px; 
                border: 2px solid #3498db; border-radius: 8px; 
                z-index: 9999; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0; font-size: 18px; color: #2c3e50;">
            <b>🚕 首尔江南区出租车速度监测仪表盘</b>
        </h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #7f8c8d;">
            304条道路 | 2018年4月数据 | 点击标记查看详细信息
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # 添加图例
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 10px; width: 200px; 
                background-color: rgba(255, 255, 255, 0.9); 
                border: 2px solid #34495e; border-radius: 5px; 
                z-index: 9999; font-size: 12px; padding: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #2c3e50;">
            🚦 速度图例 (km/h)
        </h4>
        <p style="margin: 3px 0;">
            <i class="fa fa-road" style="color: green"></i> 快速: ≥60
        </p>
        <p style="margin: 3px 0;">
            <i class="fa fa-road" style="color: yellow"></i> 中速: 40-59
        </p>
        <p style="margin: 3px 0;">
            <i class="fa fa-road" style="color: orange"></i> 慢速: 20-39
        </p>
        <p style="margin: 3px 0;">
            <i class="fa fa-road" style="color: red"></i> 拥堵: <20
        </p>
        <p style="margin: 3px 0;">
            <i class="fa fa-road" style="color: gray"></i> 无数据
        </p>
        <hr style="margin: 8px 0;">
        <p style="margin: 0; font-size: 10px; color: #e74c3c;">
            <b>注:</b> 坐标为模拟生成<br>显示江南区大致分布
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # 保存地图
    print(f"正在保存地图到 {output_file}...")
    try:
        m.save(output_file)
        print("地图保存成功！")
    except Exception as e:
        print(f"保存地图时出错: {e}")
        return None

    # 在浏览器中打开
    print("在浏览器中打开仪表盘...")
    try:
        webbrowser.open('file://' + os.path.realpath(output_file))
    except:
        print(f"请手动打开文件: {os.path.abspath(output_file)}")

    return m


# 显示数据统计信息
def show_data_statistics(file_path):
    print("\n正在分析数据...")
    try:
        link_ids, short_ids, id_x, id_y, speed_limits, lengths, directions, speed_data = load_data(file_path)

        print(f"=== 江南区道路数据统计 ===")
        print(f"道路段总数: {len(link_ids)}")
        print(f"数据时间点数: {speed_data.shape[1]} (2018年4月每5分钟)")

        # 计算总体速度统计
        all_speeds = speed_data[speed_data > 0]
        if len(all_speeds) > 0:
            print(f"\n总体速度统计:")
            print(f"  - 平均速度: {np.mean(all_speeds):.2f} km/h")
            print(f"  - 速度范围: {np.min(all_speeds):.2f} - {np.max(all_speeds):.2f} km/h")
            print(f"  - 标准差: {np.std(all_speeds):.2f} km/h")

        # 显示道路特征
        print(f"\n道路特征:")
        print(f"  - 平均限速: {np.mean(speed_limits):.1f} km/h")
        print(f"  - 平均长度: {np.mean(lengths):.1f} 米")
        print(f"  - 上行道路: {sum(1 for d in directions if d == 0)} 条")
        print(f"  - 下行道路: {sum(1 for d in directions if d == 1)} 条")

    except Exception as e:
        print(f"分析数据时出错: {e}")


# 主程序
if __name__ == "__main__":
    # 使用您的数据文件
    file_path = "urban-core.csv"

    print("首尔江南区出租车速度仪表盘生成器")
    print("=" * 50)

    # 首先显示数据统计
    show_data_statistics(file_path)

    print("\n" + "=" * 50)
    print("开始创建仪表盘...")

    # 创建仪表盘
    dashboard = create_speed_dashboard(file_path)

    if dashboard:
        print("\n🎉 江南区道路速度仪表盘创建成功！")
        print("\n📊 功能特色:")
        print("  - 🚦 颜色编码速度等级")
        print("  - 🔥 速度热力图叠加")
        print("  - 📍 304条江南区道路模拟分布")
        print("  - 📈 详细的速度统计分析")
        print("  - 🗺️  多种地图样式可选")
        print("\n💡 使用说明:")
        print("  - 点击道路标记查看详细信息")
        print("  - 使用右上角图层控制切换地图和热力图")
        print("  - 标记会自动聚类显示")
        print("  - 坐标基于江南区地理范围模拟生成")
    else:
        print("\n❌ 创建仪表盘失败")