import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 设置页面宽度为宽屏模式，以充分利用页面空间
st.set_page_config(layout="wide", page_title="晶圆数据分析")

wafer_options = ['TOX', 'HfO2', 'Al2O3']
sheet_options = ['I0', 'If', 'Iave']


# 使用缓存装饰器缓存读取文件的结果
@st.cache_data
def load_and_process_data(uploaded_file, sheet_name):
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)

    # 生成列名
    columns = ['Date', 'Time'] + [f'{wafer_options[i // 6]}_{["L", "B", "C", "T", "R", "Ave"][i % 6]}' for i in
                                  range(18)]
    df.columns = columns
    df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), format='%d-%m-%Y %H:%M:%S')

    # 计算统计数据并转置
    stats_df = pd.DataFrame()
    for col in columns[2:]:
        mean = df[col].mean()
        sigma = df[col].std()
        one_sigma = sigma / mean if mean != 0 else np.nan
        range_val = (df[col].max() - df[col].min()) / mean if mean != 0 else np.nan
        stats_df.loc['1sigma', col] = one_sigma
        stats_df.loc['Peak to Peak', col] = range_val

    return df, stats_df


# Streamlit应用标题
st.title('晶圆数据分析')

# 文件上传器
uploaded_file = st.file_uploader("选择一个Excel文件", type="xlsx")

if uploaded_file is not None:
    # 创建侧边栏下拉菜单用于选择要读取的Sheet
    selected_sheet = st.sidebar.selectbox('选择要读取的Sheet:', sheet_options)

    # 加载和处理数据，并缓存结果
    df, transposed_stats_df = load_and_process_data(uploaded_file, selected_sheet)

    # 创建侧边栏下拉菜单用于选择每个晶圆的具体点位
    point_options = ['L', 'B', 'C', 'T', 'R', 'Ave']

    selected_points = {}
    for wafer in wafer_options:
        selected_point = st.sidebar.selectbox(f'选择{wafer}的点位:', point_options,
                                              key=f'select_{wafer}_{selected_sheet}')
        selected_points[wafer] = selected_point

    # 显示统计数据（转置）
    st.subheader('统计数据')
    st.dataframe(transposed_stats_df.style.format("{:.4f}"),width=2000, height=100)


    # 定义绘图函数
    def update_plots(df, selected_points):
        # 使用容器来控制布局
        container = st.container()
        with container:
            cols = st.columns([1, 1, 1])  # 确保三列均匀分布
            for idx, wafer in enumerate(wafer_options):
                with cols[idx]:
                    selected_column = f'{wafer}_{selected_points[wafer]}'

                    # 检查所选列是否存在
                    if selected_column in df.columns:
                        fig, ax = plt.subplots(figsize=(12, 6))  # 增大图表尺寸
                        ax.plot(df['DateTime'], df[selected_column], marker='o', color='g', label=selected_column)

                        first_five_avg = df[selected_column][:5].mean()
                        if pd.notna(first_five_avg) and first_five_avg != 0:
                            upper_limit_1 = first_five_avg * 1.0075
                            lower_limit_1 = first_five_avg * 0.9925
                            upper_limit_2 = first_five_avg * 1.015
                            lower_limit_2 = first_five_avg * 0.985

                            # 添加标线但不添加标签
                            ax.axhline(y=upper_limit_1, color='r', linestyle='--')
                            ax.axhline(y=lower_limit_1, color='r', linestyle='--')
                            ax.axhline(y=upper_limit_2, color='r', linestyle='--')
                            ax.axhline(y=lower_limit_2, color='r', linestyle='--')

                        ax.legend()
                        ax.set_title(f'{wafer} {selected_points[wafer]}_{selected_sheet}')
                        ax.set_ylabel('Signal:cts/s')
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
                    else:
                        st.write(f"警告: 列 '{selected_column}' 不存在于数据中.")


    # 每次选择改变时自动更新图表
    update_plots(df, selected_points)