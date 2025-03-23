import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt

def plot_inventory_status(df):
    """재고 상태 시각화 - 현재 수량 vs 최소 재고 수준"""
    # 현재 재고와 최소 재고 비교 차트
    fig = go.Figure()
    
    # 데이터 정렬 (현재 수량 기준)
    sorted_df = df.sort_values(by='quantity')
    
    # 현재 재고 수량
    fig.add_trace(go.Bar(
        x=sorted_df['item_name'],
        y=sorted_df['quantity'],
        name='현재 재고',
        marker_color='royalblue'
    ))
    
    # 최소 재고 수준
    fig.add_trace(go.Bar(
        x=sorted_df['item_name'],
        y=sorted_df['min_stock'],
        name='최소 재고 수준',
        marker_color='red'
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title='품목별 현재 재고 vs 최소 재고 수준',
        xaxis_title='품목',
        yaxis_title='수량',
        barmode='group',
        height=600,
        xaxis={'categoryorder':'total descending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_inventory_value(df):
    """품목별 재고 가치 시각화"""
    # 총 가치 계산
    df_value = df.copy()
    df_value['total_value'] = df_value['quantity'] * df_value['price']
    df_value = df_value.sort_values(by='total_value', ascending=False)
    
    # 파이 차트로 표시
    fig = px.pie(
        df_value, 
        values='total_value', 
        names='item_name',
        title='품목별 재고 가치 분포',
        hover_data=['quantity', 'price'],
        labels={'total_value': '총 가치'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=600)
    
    st.plotly_chart(fig, use_container_width=True)

def plot_abc_analysis(df_abc):
    """ABC 분석 결과 시각화"""
    # ABC 클래스별 색상 매핑
    color_map = {'A': 'red', 'B': 'gold', 'C': 'green'}
    
    # 누적 백분율 곡선
    fig = go.Figure()
    
    # 각 품목의 가치(막대 그래프)
    fig.add_trace(go.Bar(
        x=df_abc['item_name'],
        y=df_abc['total_value'],
        name='품목별 가치',
        marker_color=[color_map[cls] for cls in df_abc['abc_class']]
    ))
    
    # 누적 백분율(선 그래프)
    fig.add_trace(go.Scatter(
        x=df_abc['item_name'],
        y=df_abc['cumulative_percentage'],
        name='누적 백분율',
        yaxis='y2',
        line=dict(color='royalblue', width=3)
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title='ABC 분석 (파레토 차트)',
        xaxis_title='품목',
        yaxis_title='총 가치',
        barmode='relative',
        height=600,
        yaxis2=dict(
            title='누적 백분율 (%)',
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ABC 클래스별 요약
    st.subheader('ABC 분석 요약')
    class_summary = df_abc.groupby('abc_class').agg(
        품목수=('item_name', 'count'),
        총가치=('total_value', 'sum')
    ).reset_index()
    
    # 총 가치 대비 비율 계산
    total_value = class_summary['총가치'].sum()
    class_summary['가치비율'] = (class_summary['총가치'] / total_value * 100).round(2)
    class_summary['가치비율'] = class_summary['가치비율'].astype(str) + '%'
    
    st.table(class_summary)

def plot_location_distribution(df):
    """위치별 재고 분포 시각화"""
    location_count = df.groupby('location').size().reset_index(name='count')
    location_count = location_count.sort_values(by='count', ascending=False)
    
    fig = px.bar(
        location_count, 
        x='location', 
        y='count',
        title='위치별 품목 분포',
        labels={'location': '위치', 'count': '품목 수'},
        color='count',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

def plot_stock_status_gauge(df):
    """재고 상태 게이지 차트"""
    # 재고 상태 계산
    total_items = len(df)
    low_stock = len(df[df['quantity'] < df['min_stock']])
    excess_stock = len(df[df['quantity'] > df['min_stock'] * 2])
    healthy_stock = total_items - low_stock - excess_stock
    
    # 백분율 계산
    low_percent = round(low_stock / total_items * 100, 1)
    healthy_percent = round(healthy_stock / total_items * 100, 1)
    excess_percent = round(excess_stock / total_items * 100, 1)
    
    # 게이지 차트 생성
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig1 = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = low_percent,
            title = {'text': "부족 재고 비율"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "red"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "gold"},
                    {'range': [70, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 30
                }
            }
        ))
        fig1.update_layout(height=250)
        st.plotly_chart(fig1, use_container_width=True)
        st.write(f"부족 재고 품목: {low_stock}개")
    
    with col2:
        fig2 = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = healthy_percent,
            title = {'text': "정상 재고 비율"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 30], 'color': "lightcoral"},
                    {'range': [30, 70], 'color': "gold"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "green", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        fig2.update_layout(height=250)
        st.plotly_chart(fig2, use_container_width=True)
        st.write(f"정상 재고 품목: {healthy_stock}개")
    
    with col3:
        fig3 = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = excess_percent,
            title = {'text': "과잉 재고 비율"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "gold"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "gold"},
                    {'range': [70, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "orange", 'width': 4},
                    'thickness': 0.75,
                    'value': 30
                }
            }
        ))
        fig3.update_layout(height=250)
        st.plotly_chart(fig3, use_container_width=True)
        st.write(f"과잉 재고 품목: {excess_stock}개") 