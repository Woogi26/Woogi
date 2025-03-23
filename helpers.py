import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import base64
import io
from datetime import datetime

def load_data(file):
    """파일에서 데이터 로드하고 기본 전처리 수행"""
    try:
        # 파일 확장자 확인
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            st.error('지원되지 않는 파일 형식입니다. CSV 또는 Excel 파일을 업로드해주세요.')
            return None
        
        # 필수 열 확인
        required_columns = ['item_id', 'item_name', 'quantity', 'location', 'price', 'min_stock']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f'다음 필수 열이 누락되었습니다: {", ".join(missing_columns)}')
            return None
        
        # 데이터 타입 변환
        df['item_id'] = df['item_id'].astype(str)
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['min_stock'] = pd.to_numeric(df['min_stock'], errors='coerce')
        
        # 결측치 처리
        if df.isna().any().any():
            st.warning('데이터에 결측치가 있습니다. 일부 분석이 부정확할 수 있습니다.')
        
        return df
    
    except Exception as e:
        st.error(f'데이터 로드 중 오류가 발생했습니다: {str(e)}')
        return None

def calculate_inventory_metrics(df):
    """재고 관련 주요 지표 계산"""
    metrics = {}
    
    # 총 재고 품목 수
    metrics['total_items'] = len(df)
    
    # 총 재고 가치
    metrics['total_value'] = (df['quantity'] * df['price']).sum()
    
    # 부족 재고 품목 (현재 수량이 최소 재고 수준보다 적은 품목)
    low_stock = df[df['quantity'] < df['min_stock']]
    metrics['low_stock_count'] = len(low_stock)
    metrics['low_stock_items'] = low_stock
    
    # 과잉 재고 품목 (현재 수량이 최소 재고 수준의 2배 이상인 품목)
    excess_stock = df[df['quantity'] > df['min_stock'] * 2]
    metrics['excess_stock_count'] = len(excess_stock)
    metrics['excess_stock_items'] = excess_stock
    
    # 재고 상태가 양호한 품목
    healthy_stock = df[(df['quantity'] >= df['min_stock']) & (df['quantity'] <= df['min_stock'] * 2)]
    metrics['healthy_stock_count'] = len(healthy_stock)
    
    return metrics

def generate_abc_analysis(df):
    """ABC 분석 (파레토 분석) 수행"""
    # 각 품목의 총 가치 계산
    df_abc = df.copy()
    df_abc['total_value'] = df_abc['quantity'] * df_abc['price']
    
    # 총 가치 기준으로 정렬
    df_abc = df_abc.sort_values(by='total_value', ascending=False)
    
    # 누적 가치 및 누적 백분율 계산
    df_abc['cumulative_value'] = df_abc['total_value'].cumsum()
    df_abc['cumulative_percentage'] = 100 * df_abc['cumulative_value'] / df_abc['total_value'].sum()
    
    # ABC 등급 할당
    df_abc['abc_class'] = np.where(df_abc['cumulative_percentage'] <= 80, 'A',
                          np.where(df_abc['cumulative_percentage'] <= 95, 'B', 'C'))
    
    return df_abc

def get_download_link(df, filename, text):
    """데이터프레임을 다운로드 링크로 변환"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def export_to_excel(df):
    """데이터프레임을 Excel 파일로 변환하여 다운로드 링크 생성"""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='재고 데이터', index=False)
    writer.close()
    
    output.seek(0)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inventory_report_{current_time}.xlsx"
    
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Excel 파일 다운로드</a>'
    
    return href 