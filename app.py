import streamlit as st
import pandas as pd
import os
import time
import importlib
import sys

# 필요한 패키지 확인 및 설치
def check_install_packages():
    required_packages = {
        'numpy': 'numpy',
        'plotly.express': 'plotly',
        'altair': 'altair',
        'openpyxl': 'openpyxl',
        'xlsxwriter': 'xlsxwriter',
        'PIL': 'pillow'
    }
    
    missing_packages = []
    
    for module_name, package_name in required_packages.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        st.warning(f"일부 필요한 패키지가 설치되어 있지 않습니다: {', '.join(missing_packages)}")
        st.info("pip install " + " ".join(missing_packages) + " 명령으로 설치할 수 있습니다.")
        return False
    return True

# 패키지 확인
packages_ok = check_install_packages()

# 커스텀 모듈 임포트 - 경로 수정
try:
    from helpers import load_data, calculate_inventory_metrics, generate_abc_analysis, export_to_excel
    from visualization import (
        plot_inventory_status, 
        plot_inventory_value, 
        plot_abc_analysis, 
        plot_location_distribution, 
        plot_stock_status_gauge
    )
except ImportError as e:
    st.error(f"모듈 임포트 오류: {str(e)}")
    st.info("필요한 모듈 파일(helpers.py, visualization.py)이 현재 폴더에 있는지 확인하세요.")
    st.stop()

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

# 패키지가 설치되어 있지 않으면 대시보드 표시하지 않음
if not packages_ok:
    st.warning("필요한 패키지가 모두 설치될 때까지 대시보드가 제대로 표시되지 않을 수 있습니다.")

# 데이터 로드
if uploaded_file is not None:
    with st.spinner('데이터 로드 중...'):
        try:
            df = load_data(uploaded_file)
            if df is not None:
                st.session_state.data = df
                st.session_state.metrics = calculate_inventory_metrics(df)
                st.session_state.abc_analysis = generate_abc_analysis(df)
                st.sidebar.success("데이터 로드 완료!")
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {str(e)}")
elif use_sample_data:
    # 샘플 데이터 로드 - 경로 수정
    with st.spinner('샘플 데이터 로드 중...'):
        # 여러 가능한 샘플 데이터 경로 시도
        sample_data_paths = [
            'sample_data.csv',  # 현재 폴더
            os.path.join(os.path.dirname(__file__), 'sample_data.csv'),  # 스크립트 위치 기준
            os.path.join(os.getcwd(), 'sample_data.csv'),  # 현재 작업 디렉토리 기준
            os.path.join(os.getcwd(), 'single_folder_app', 'sample_data.csv')  # 상위 구조 고려
        ]
        
        sample_loaded = False
        for path in sample_data_paths:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    st.session_state.data = df
                    st.session_state.metrics = calculate_inventory_metrics(df)
                    st.session_state.abc_analysis = generate_abc_analysis(df)
                    st.sidebar.info(f"샘플 데이터 로드 완료! (경로: {path})")
                    sample_loaded = True
                    break
                except Exception as e:
                    st.warning(f"샘플 데이터 로드 시도 중 오류 발생 ({path}): {str(e)}")
        
        if not sample_loaded:
            st.error("샘플 데이터 파일을 찾을 수 없습니다. 다음 경로에서 시도했습니다: " + ", ".join(sample_data_paths))

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
                    try:
                        # Excel 보고서 링크 생성
                        with pd.ExcelWriter('temp_report.xlsx', engine='xlsxwriter') as writer:
                            for sheet_name, data in report_dfs:
                                data.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        with open('temp_report.xlsx', 'rb') as f:
                            excel_data = f.read()
                        
                        # 임시 파일 삭제
                        try:
                            os.remove('temp_report.xlsx')
                        except:
                            pass
                        
                        # 다운로드 링크 제공
                        st.download_button(
                            label="Excel 보고서 다운로드",
                            data=excel_data,
                            file_name=f"inventory_report_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        st.success("보고서가 생성되었습니다. 다운로드 버튼을 클릭하여 저장하세요.")
                    except Exception as e:
                        st.error(f"보고서 생성 중 오류 발생: {str(e)}")
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

# 디버그 정보
if st.sidebar.checkbox("디버그 정보 표시", False):
    st.sidebar.subheader("환경 정보")
    st.sidebar.text(f"Python 버전: {sys.version}")
    st.sidebar.text(f"Streamlit 버전: {st.__version__}")
    st.sidebar.text(f"Pandas 버전: {pd.__version__}")
    
    st.sidebar.subheader("파일 경로")
    st.sidebar.text(f"현재 작업 디렉토리: {os.getcwd()}")
    st.sidebar.text(f"스크립트 위치: {os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '알 수 없음'}")
    
    if 'sample_data_path' in locals():
        st.sidebar.text(f"샘플 데이터 경로: {sample_data_path}")

# 앱 실행 방법:
# streamlit run app.py 