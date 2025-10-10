import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os


# 读取所有年份的数据
def load_all_years_data():
    years = ['2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']
    all_data = []

    for year in years:
        file_path = f"{year}.xls"
        try:
            df = pd.read_excel(file_path, sheet_name='차량통행속도')
            df['年份'] = int(year)
            df['年份_str'] = str(year)  # 添加字符串类型的年份列
            df['日期'] = pd.to_datetime(df['일자'], format='%Y%m%d')
            df['月日'] = df['日期'].dt.strftime('%m-%d')
            df['日'] = df['日期'].dt.day

            # 重命名列
            df = df.rename(columns={
                '평균속도': '平均车速(km/h)',
                '날씨': '天气',
                '최고온도(℃)': '最高温度',
                '최저온도(℃)': '最低温度',
                '일자': '日期代码'
            })

            all_data.append(df)
            print(f"成功加载 {year} 年数据: {len(df)} 条记录")

        except Exception as e:
            print(f"加载 {year} 年数据时出错: {e}")

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df


# 创建动画图表 - 修复年份小数问题
def create_speed_animation(df):
    # 颜色映射
    year_colors = {
        '2017': '#1f77b4', '2018': '#ff7f0e', '2019': '#2ca02c',
        '2020': '#d62728', '2021': '#9467bd', '2022': '#8c564b',
        '2023': '#e377c2', '2024': '#7f7f7f', '2025': '#bcbd22'
    }

    # 创建动画散点图 - 使用字符串年份
    fig = px.scatter(
        df,
        x='日',
        y='平均车速(km/h)',
        animation_frame='年份_str',  # 使用字符串年份
        color='年份_str',  # 使用字符串年份
        color_discrete_map=year_colors,
        size='平均车速(km/h)',
        hover_name='天气',
        hover_data={
            '最高温度': True,
            '最低温度': True,
            '日': False,
            '年份_str': False
        },
        title='首尔市区4月份每日平均车速变化 (2017-2025)',
        labels={
            '日': '日期 (日)',
            '平均车速(km/h)': '平均车速 (km/h)',
            '年份_str': '年份'
        },
        size_max=15
    )

    # 更新布局
    fig.update_layout(
        width=1000,
        height=600,
        font=dict(size=12),
        plot_bgcolor='white',
        xaxis=dict(
            title='日期 (4月份每日)',
            tickmode='linear',
            dtick=1,
            range=[0.5, 30.5]
        ),
        yaxis=dict(
            title='平均车速 (km/h)',
            range=[18, 27]
        ),
        showlegend=True
    )

    # 更新动画设置
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 500

    # 修复动画帧标签显示
    for frame in fig.frames:
        frame.name = str(frame.name)  # 确保帧名称为字符串

    return fig


# 替代方案：使用go.Scatter手动创建动画
def create_speed_animation_manual(df):
    """手动创建动画，更好地控制年份显示"""

    years = sorted(df['年份'].unique())

    # 创建基础图形
    fig = go.Figure()

    # 为每一年添加轨迹（初始隐藏）
    for year in years:
        year_data = df[df['年份'] == year]
        fig.add_trace(
            go.Scatter(
                x=year_data['日'],
                y=year_data['平均车速(km/h)'],
                mode='markers',
                marker=dict(
                    size=year_data['平均车速(km/h)'] * 0.6,  # 大小与速度相关
                    sizemode='diameter',
                    sizeref=2. * max(df['平均车速(km/h)']) / (40. ** 2),
                    sizemin=4,
                    color=px.colors.qualitative.Set1[years.index(year) % len(px.colors.qualitative.Set1)]
                ),
                name=str(year),
                visible=(year == years[0])  # 只有第一年可见
            )
        )

    # 创建动画帧
    frames = []
    for year in years:
        year_data = df[df['年份'] == year]
        frame = go.Frame(
            data=[go.Scatter(
                x=year_data['日'],
                y=year_data['平均车速(km/h)'],
                mode='markers',
                marker=dict(
                    size=year_data['平均车速(km/h)'] * 0.6,
                    sizemode='diameter',
                    sizeref=2. * max(df['平均车速(km/h)']) / (40. ** 2),
                    sizemin=4,
                    color=px.colors.qualitative.Set1[years.index(year) % len(px.colors.qualitative.Set1)]
                ),
                name=str(year)
            )],
            name=str(year)
        )
        frames.append(frame)

    fig.frames = frames

    # 创建动画按钮
    fig.update_layout(
        updatemenus=[{
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 1000, "redraw": True},
                                    "fromcurrent": True, "transition": {"duration": 500}}],
                    "label": "播放",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": True},
                                      "mode": "immediate", "transition": {"duration": 0}}],
                    "label": "暂停",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }],
        sliders=[{
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {
                "font": {"size": 16},
                "prefix": "年份: ",
                "visible": True,
                "xanchor": "right"
            },
            "transition": {"duration": 500},
            "pad": {"b": 10, "t": 50},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": [{
                "args": [
                    [str(year)],
                    {"frame": {"duration": 500, "redraw": True},
                     "mode": "immediate", "transition": {"duration": 500}}
                ],
                "label": str(year),
                "method": "animate"
            } for year in years]
        }]
    )

    # 更新布局
    fig.update_layout(
        width=1000,
        height=600,
        title='首尔市区4月份每日平均车速变化 (2017-2025)',
        xaxis_title='日期 (4月份每日)',
        yaxis_title='平均车速 (km/h)',
        showlegend=True,
        xaxis=dict(range=[0.5, 30.5], dtick=5),
        yaxis=dict(range=[18, 27])
    )

    return fig


# 创建优化版本的时间滑块动画
def create_optimized_speed_animation(df):
    """优化版本，解决年份小数问题"""

    # 确保年份为字符串
    df['年份_str'] = df['年份'].astype(str)

    # 颜色映射
    colors = px.colors.qualitative.Set1

    fig = px.scatter(
        df,
        x='日',
        y='平均车速(km/h)',
        animation_frame='年份_str',
        color='年份_str',
        size='平均车速(km/h)',
        hover_data=['天气', '最高温度', '最低温度'],
        title='首尔市区4月份每日平均车速变化 (2017-2025)',
        labels={
            '日': '日期 (日)',
            '平均车速(km/h)': '平均车速 (km/h)',
            '年份_str': '年份'
        },
        size_max=15
    )

    # 修复动画设置
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 500

    # 修复滑块显示
    years = sorted(df['年份_str'].unique())
    fig.layout.sliders[0].currentvalue.prefix = '年份: '
    fig.layout.sliders[0].steps = [
        dict(
            args=[
                [str(year)],
                {"frame": {"duration": 500, "redraw": True},
                 "mode": "immediate", "transition": {"duration": 500}}
            ],
            label=str(year),
            method="animate"
        ) for year in years
    ]

    # 更新布局
    fig.update_layout(
        width=1000,
        height=600,
        xaxis=dict(range=[0.5, 30.5], dtick=5),
        yaxis=dict(range=[18, 27])
    )

    return fig


# 其他函数保持不变...
def create_comparison_dashboard(df):
    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '年度平均车速趋势',
            '月度每日平均车速热力图',
            '天气对车速的影响',
            '温度与车速关系'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "heatmap"}],
            [{"type": "box"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )

    # 1. 年度平均车速趋势
    yearly_avg = df.groupby('年份')['平均车速(km/h)'].mean().reset_index()
    fig.add_trace(
        go.Scatter(
            x=yearly_avg['年份'],
            y=yearly_avg['平均车速(km/h)'],
            mode='lines+markers',
            name='年度平均',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ),
        row=1, col=1
    )

    # 2. 热力图 - 每日车速变化
    heatmap_data = df.pivot_table(
        values='平均车速(km/h)',
        index='年份',
        columns='日',
        aggfunc='mean'
    )

    fig.add_trace(
        go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="车速 km/h")
        ),
        row=1, col=2
    )

    # 3. 天气对车速的影响
    weather_data = df[df['天气'].notna()]
    weather_order = ['맑음', '구름조금', '구름많음', '흐림', '비', '눈']
    weather_mapping = {
        '맑음': '晴天',
        '구름조금': '少云',
        '구름많음': '多云',
        '흐림': '阴天',
        '비': '雨天',
        '눈': '雪天'
    }

    weather_data = weather_data.copy()
    weather_data['天气中文'] = weather_data['天气'].map(weather_mapping)

    for weather_kor in weather_order:
        weather_chi = weather_mapping[weather_kor]
        weather_speeds = weather_data[weather_data['天气'] == weather_kor]['平均车速(km/h)']
        if len(weather_speeds) > 0:
            fig.add_trace(
                go.Box(
                    y=weather_speeds,
                    name=weather_chi,
                    boxpoints='outliers',
                    marker_color='#ff7f0e'
                ),
                row=2, col=1
            )

    # 4. 温度与车速关系
    temp_data = df[df['最高温度'].notna()]
    fig.add_trace(
        go.Scatter(
            x=temp_data['最高温度'],
            y=temp_data['平均车速(km/h)'],
            mode='markers',
            marker=dict(
                size=8,
                color=temp_data['年份'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="年份")
            ),
            text=temp_data['年份'],
            hovertemplate=(
                "最高温度: %{x}°C<br>"
                "平均车速: %{y} km/h<br>"
                "年份: %{text}<extra></extra>"
            ),
            name='温度-车速关系'
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=800,
        title_text="首尔市区4月份交通速度综合分析仪表板 (2017-2025)",
        showlegend=False,
        font=dict(size=10)
    )

    fig.update_xaxes(title_text="年份", row=1, col=1)
    fig.update_yaxes(title_text="平均车速 (km/h)", row=1, col=1)
    fig.update_xaxes(title_text="日期 (日)", row=1, col=2)
    fig.update_yaxes(title_text="年份", row=1, col=2)
    fig.update_xaxes(title_text="天气状况", row=2, col=1)
    fig.update_yaxes(title_text="车速 (km/h)", row=2, col=1)
    fig.update_xaxes(title_text="最高温度 (°C)", row=2, col=2)
    fig.update_yaxes(title_text="平均车速 (km/h)", row=2, col=2)

    return fig


# 主程序
def main():
    print("正在加载首尔市区交通速度数据...")
    print("=" * 60)

    # 加载数据
    df = load_all_years_data()

    if df.empty:
        print("没有成功加载任何数据，请检查文件路径")
        return

    print(f"\n总共加载 {len(df)} 条记录")
    print(f"数据时间范围: {df['年份'].min()}年 - {df['年份'].max()}年")

    # 创建优化版本的时间滑块动画
    print("\n正在创建优化版本的时间滑块动画...")
    optimized_fig = create_optimized_speed_animation(df)
    optimized_fig.write_html("seoul_traffic_speed_animation_optimized.html")
    print("✅ 优化版本时间滑块动画已保存: seoul_traffic_speed_animation_optimized.html")

    # 创建手动版本动画
    print("正在创建手动版本动画...")
    manual_fig = create_speed_animation_manual(df)
    manual_fig.write_html("seoul_traffic_speed_animation_manual.html")
    print("✅ 手动版本动画已保存: seoul_traffic_speed_animation_manual.html")

    # 创建综合分析仪表板
    print("正在创建综合分析仪表板...")
    dashboard_fig = create_comparison_dashboard(df)
    dashboard_fig.write_html("seoul_traffic_analysis_dashboard.html")
    print("✅ 综合分析仪表板已保存: seoul_traffic_analysis_dashboard.html")

    print("\n🎯 分析完成！")
    print("生成的文件:")
    print("  - seoul_traffic_speed_animation_optimized.html (优化版本)")
    print("  - seoul_traffic_speed_animation_manual.html (手动版本)")
    print("  - seoul_traffic_analysis_dashboard.html (综合分析仪表板)")
    print("\n💡 推荐使用优化版本，解决了年份小数显示问题")


if __name__ == "__main__":
    main()