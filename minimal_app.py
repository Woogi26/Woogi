import streamlit as st
import pandas as pd
import os

# 페이지 설정
st.set_page_config(
    page_title="재고 관리 시스템 (간소화 버전)",
    page_icon="📦",
    layout="wide"
)

# 앱 제목 및 설명
st.title("📦 재고 관리 시스템 (간소화 버전)")
st.markdown("""
이 대시보드는 재고 수준 모니터링 및 기본적인 데이터 뷰 기능을 제공합니다.  
CSV 파일을 업로드하여 재고 데이터를 분석해보세요.
""")

# 샘플 데이터 생성
def create_sample_data():
    data = {
        'item_id': ['KP001', 'KP002', 'KP003', 'KP004', 'KP005'],
        'item_name': ['컴퓨터 키보드', '무선 마우스', '27인치 모니터', '노트북 파우치', 'USB 메모리'],
        'category': ['전자제품', '전자제품', '전자제품', '액세서리', '전자제품'],
        'quantity': [45, 30, 12, 22, 60],
        'price': [55000, 35000, 250000, 25000, 20000],
        'min_stock': [15, 10, 5, 8, 20],
        'location': ['A-1-1', 'A-1-2', 'A-2-1', 'B-1-1', 'A-3-1']
    }
    return pd.DataFrame(data)

# 데이터 업로드 섹션
uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])

# 샘플 데이터 사용 옵션
use_sample_data = st.checkbox("샘플 데이터 사용", value=True if uploaded_file is None else False)

# 데이터 로드
df = None

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("데이터 로드 완료!")
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {str(e)}")
elif use_sample_data:
    # 샘플 데이터 로드 시도
    try:
        # 경로 목록
        sample_data_paths = [
            'sample_data.csv',  # 현재 폴더
            os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd(), 'sample_data.csv'),
            os.path.join(os.getcwd(), 'sample_data.csv'),
            os.path.join(os.getcwd(), 'single_folder_app', 'sample_data.csv')
        ]
        
        # 파일 존재 확인
        found_file = False
        for path in [p for p in sample_data_paths if p]:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    st.info(f"샘플 데이터 로드 완료! (경로: {path})")
                    found_file = True
                    break
                except Exception as e:
                    continue
        
        # 파일을 찾지 못했거나 로드 실패 시 내장 샘플 데이터 사용
        if not found_file or df is None:
            df = create_sample_data()
            st.info("내장된 샘플 데이터를 사용합니다.")
    except Exception as e:
        # 모든 로드 실패 시 내장 샘플 데이터 사용
        df = create_sample_data()
        st.info("내장된 샘플 데이터를 사용합니다.")

# 데이터가 로드된 경우 표시
if df is not None:
    # 타입 변환
    try:
        if 'item_id' in df.columns:
            df['item_id'] = df['item_id'].astype(str)
        
        for col in ['quantity', 'price', 'min_stock']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    except Exception as e:
        st.warning(f"데이터 변환 중 경고: {str(e)}")
    
    # 기본 정보 표시
    st.header("기본 재고 정보")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("총 품목 수", f"{len(df)}개")
    
    with col2:
        if 'quantity' in df.columns and 'price' in df.columns:
            total_value = (df['quantity'] * df['price']).sum()
            st.metric("총 재고 가치", f"₩{total_value:,.0f}")
        else:
            st.metric("총 재고 가치", "데이터 없음")
    
    # 데이터 뷰
    st.header("데이터 뷰")
    
    # 검색 필터
    search_term = st.text_input("품목 검색 (ID 또는 이름)")
    
    # 필터 적용
    filtered_df = df.copy()
    
    if search_term:
        try:
            if 'item_id' in df.columns and 'item_name' in df.columns:
                filtered_df = filtered_df[
                    (filtered_df['item_id'].astype(str).str.contains(search_term, case=False, na=False)) | 
                    (filtered_df['item_name'].astype(str).str.contains(search_term, case=False, na=False))
                ]
            elif 'item_id' in df.columns:
                filtered_df = filtered_df[filtered_df['item_id'].astype(str).str.contains(search_term, case=False, na=False)]
            elif 'item_name' in df.columns:
                filtered_df = filtered_df[filtered_df['item_name'].astype(str).str.contains(search_term, case=False, na=False)]
        except Exception as e:
            st.warning(f"검색 필터링 중 오류: {str(e)}")
    
    # 필터링된 데이터 표시
    st.dataframe(filtered_df, use_container_width=True)
    st.write(f"표시된 품목: {len(filtered_df)} / 전체 품목: {len(df)}")
    
    # 부족 재고 표시
    if 'quantity' in df.columns and 'min_stock' in df.columns:
        try:
            low_stock = df[df['quantity'] < df['min_stock']]
            if len(low_stock) > 0:
                st.header("⚠️ 부족 재고 품목")
                columns_to_show = [col for col in ['item_id', 'item_name', 'quantity', 'min_stock', 'location'] if col in low_stock.columns]
                st.dataframe(low_stock[columns_to_show], use_container_width=True)
        except Exception as e:
            st.warning(f"부족 재고 분석 중 오류: {str(e)}")

# 푸터
st.markdown("---")
st.markdown("© 2023 재고 관리 시스템 | 간소화 버전 1.0") 