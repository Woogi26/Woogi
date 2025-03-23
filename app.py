import streamlit as st
import pandas as pd
import os
import time

# 커스텀 모듈 임포트 - 경로 수정
from helpers import load_data, calculate_inventory_metrics, generate_abc_analysis, export_to_excel
from visualization import (
    plot_inventory_status, 
    plot_inventory_value, 
    plot_abc_analysis, 
    plot_location_distribution, 
    plot_stock_status_gauge
)

# 페이지 설정
st.set_page_config(
    page_title="재고 관리 시스템",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 앱 제목 및 설명
st.title("📦 재고 관리 시스템")
st.markdown("""
이 대시보드는 재고 수준 모니터링, 시각화 및 기본적인 재고 분석 기능을 제공합니다.  
CSV 또는 Excel 파일을 업로드하여 재고 데이터를 분석해보세요.
""")

# 세션 상태 초기화
if 'data' not in st.session_state:
    st.session_state.data = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'abc_analysis' not in st.session_state:
    st.session_state.abc_analysis = None

# 사이드바 설정
st.sidebar.header("📊 재고 관리 대시보드")

# 데이터 업로드 섹션
st.sidebar.subheader("데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 파일 업로드", type=['csv', 'xlsx', 'xls'])

# 샘플 데이터 사용 옵션
use_sample_data = st.sidebar.checkbox("샘플 데이터 사용", value=True if uploaded_file is None else False)

# 테마 설정
theme = st.sidebar.selectbox("테마 설정", ["라이트", "다크"], index=0)
if theme == "다크":
    st.markdown("""
    <style>
    .reportview-container {
        background-color: #0e1117;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #0e1117;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 메인 탭 설정
tabs = st.tabs(["📊 대시보드", "📈 재고 분석", "📋 데이터 뷰", "📥 보고서"])

# 데이터 로드
if uploaded_file is not None:
    with st.spinner('데이터 로드 중...'):
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.data = df
            st.session_state.metrics = calculate_inventory_metrics(df)
            st.session_state.abc_analysis = generate_abc_analysis(df)
            st.sidebar.success("데이터 로드 완료!")
elif use_sample_data:
    # 샘플 데이터 로드 - 경로 수정
    with st.spinner('샘플 데이터 로드 중...'):
        sample_data_path = 'sample_data.csv'  # 현재 폴더에 있는 샘플 데이터 파일
        if os.path.exists(sample_data_path):
            df = pd.read_csv(sample_data_path)
            st.session_state.data = df
            st.session_state.metrics = calculate_inventory_metrics(df)
            st.session_state.abc_analysis = generate_abc_analysis(df)
            st.sidebar.info("샘플 데이터 로드 완료!")
        else:
            st.error("샘플 데이터 파일을 찾을 수 없습니다.")

# 데이터가 로드된 경우 대시보드 표시
if st.session_state.data is not None and st.session_state.metrics is not None:
    df = st.session_state.data
    metrics = st.session_state.metrics
    
    # 탭 1: 대시보드
    with tabs[0]:
        st.header("재고 대시보드")
        
        # KPI 지표 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 품목 수", f"{metrics['total_items']}개")
        with col2:
            st.metric("총 재고 가치", f"₩{metrics['total_value']:,.0f}")
        with col3:
            st.metric("부족 재고 품목", f"{metrics['low_stock_count']}개")
        with col4:
            st.metric("과잉 재고 품목", f"{metrics['excess_stock_count']}개")
        
        # 재고 상태 게이지 차트
        st.subheader("재고 상태 요약")
        plot_stock_status_gauge(df)
        
        # 재고 상태 시각화
        st.subheader("재고 수준 현황")
        plot_inventory_status(df)
        
        # 위치별 분포
        st.subheader("위치별 재고 분포")
        plot_location_distribution(df)
        
        # 부족 재고 항목 표시
        if metrics['low_stock_count'] > 0:
            st.subheader("⚠️ 부족 재고 품목")
            st.dataframe(
                metrics['low_stock_items'][['item_id', 'item_name', 'quantity', 'min_stock', 'location']],
                use_container_width=True
            )
    
    # 탭 2: 재고 분석
    with tabs[1]:
        st.header("재고 분석")
        
        # 재고 가치 분석
        st.subheader("재고 가치 분석")
        plot_inventory_value(df)
        
        # ABC 분석 (파레토 분석)
        st.subheader("ABC 분석 (파레토 분석)")
        if st.session_state.abc_analysis is not None:
            plot_abc_analysis(st.session_state.abc_analysis)
        else:
            st.warning("ABC 분석 데이터를 생성할 수 없습니다.")
    
    # 탭 3: 데이터 뷰
    with tabs[2]:
        st.header("데이터 뷰")
        
        # 데이터 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'location' in df.columns:
                location_filter = st.multiselect(
                    "위치별 필터링",
                    options=df['location'].unique(),
                    default=[]
                )
        with col2:
            if 'category' in df.columns:
                category_filter = st.multiselect(
                    "카테고리별 필터링",
                    options=df['category'].unique(),
                    default=[]
                )
        with col3:
            stock_status = st.multiselect(
                "재고 상태별 필터링",
                options=["부족 재고", "정상 재고", "과잉 재고"],
                default=[]
            )
        
        # 검색 필터
        search_term = st.text_input("품목 검색 (ID 또는 이름)")
        
        # 필터 적용
        filtered_df = df.copy()
        
        if location_filter:
            filtered_df = filtered_df[filtered_df['location'].isin(location_filter)]
        
        if 'category' in df.columns and category_filter:
            filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]
        
        if stock_status:
            if "부족 재고" in stock_status:
                status_df1 = filtered_df[filtered_df['quantity'] < filtered_df['min_stock']]
            else:
                status_df1 = pd.DataFrame()
                
            if "정상 재고" in stock_status:
                status_df2 = filtered_df[(filtered_df['quantity'] >= filtered_df['min_stock']) & 
                                       (filtered_df['quantity'] <= filtered_df['min_stock'] * 2)]
            else:
                status_df2 = pd.DataFrame()
                
            if "과잉 재고" in stock_status:
                status_df3 = filtered_df[filtered_df['quantity'] > filtered_df['min_stock'] * 2]
            else:
                status_df3 = pd.DataFrame()
                
            filtered_df = pd.concat([status_df1, status_df2, status_df3])
        
        if search_term:
            filtered_df = filtered_df[
                (filtered_df['item_id'].astype(str).str.contains(search_term, case=False)) | 
                (filtered_df['item_name'].str.contains(search_term, case=False))
            ]
        
        # 필터링된 데이터 표시
        st.dataframe(filtered_df, use_container_width=True)
        st.write(f"표시된 품목: {len(filtered_df)} / 전체 품목: {len(df)}")
    
    # 탭 4: 보고서
    with tabs[3]:
        st.header("보고서 생성")
        
        # 보고서 옵션
        report_options = st.multiselect(
            "보고서에 포함할 내용 선택",
            options=["기본 재고 정보", "부족 재고 항목", "과잉 재고 항목", "ABC 분석 결과"],
            default=["기본 재고 정보", "부족 재고 항목"]
        )
        
        if st.button("보고서 생성"):
            with st.spinner("보고서 생성 중..."):
                # 보고서용 데이터프레임 생성
                report_dfs = []
                
                if "기본 재고 정보" in report_options:
                    report_dfs.append(("기본 재고 정보", df))
                
                if "부족 재고 항목" in report_options and metrics['low_stock_count'] > 0:
                    report_dfs.append(("부족 재고 항목", metrics['low_stock_items']))
                
                if "과잉 재고 항목" in report_options and metrics['excess_stock_count'] > 0:
                    report_dfs.append(("과잉 재고 항목", metrics['excess_stock_items']))
                
                if "ABC 분석 결과" in report_options and st.session_state.abc_analysis is not None:
                    report_dfs.append(("ABC 분석 결과", st.session_state.abc_analysis))
                
                # 보고서 생성
                if report_dfs:
                    # Excel 보고서 링크 생성
                    with pd.ExcelWriter('temp_report.xlsx', engine='xlsxwriter') as writer:
                        for sheet_name, data in report_dfs:
                            data.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    with open('temp_report.xlsx', 'rb') as f:
                        excel_data = f.read()
                    
                    # 임시 파일 삭제
                    os.remove('temp_report.xlsx')
                    
                    # 다운로드 링크 제공
                    st.download_button(
                        label="Excel 보고서 다운로드",
                        data=excel_data,
                        file_name=f"inventory_report_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.success("보고서가 생성되었습니다. 다운로드 버튼을 클릭하여 저장하세요.")
                else:
                    st.warning("보고서에 포함할 내용을 선택하세요.")
else:
    # 데이터가 로드되지 않은 경우 안내 메시지 표시
    for tab in tabs:
        with tab:
            st.info("데이터를 업로드하거나 샘플 데이터를 사용하여 대시보드를 표시합니다.")

# 푸터
st.sidebar.markdown("---")
st.sidebar.markdown("© 2023 재고 관리 시스템 | 버전 1.0")

# 앱 실행 방법:
# streamlit run app.py 