import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 (제목, 아이콘, 레이아웃)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="🏠",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱을 적용하여 앱 속도 최적화)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 압축된 CSV 파일 URL (pandas가 zip 압축을 자동으로 해제하여 읽습니다)
    url = "https://raw.githubusercontent.com/first2022-cyber/contents/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url)
    return df

# 데이터 로딩
df_raw = load_data()

# -----------------------------------------------------------------------------
# 3. 데이터 전처리 (최신 연도 필터링 및 나이 라벨 추출)
# -----------------------------------------------------------------------------
# 데이터에 포함된 연도 중 가장 최신 연도 자동 추출
latest_year = int(df_raw['연도'].max())

# 가장 최신 연도의 데이터만 선택
df_latest = df_raw[df_raw['연도'] == latest_year].copy()

# '남_'으로 시작하는 열 이름에서 나이 목록 자동 추출 (예: '남_0세' -> '0세')
# 이 방식을 쓰면 '0세'부터 '100세 이상'까지의 순서가 컬럼 정의 순서대로 유지됩니다.
male_cols = [col for col in df_latest.columns if col.startswith('남_')]
age_labels = [col.replace('남_', '') for col in male_cols]
female_cols = [f"여_{age}" for age in age_labels]

# -----------------------------------------------------------------------------
# 4. 앱 헤더 및 드롭다운 선택 상자 (시도 -> 시군구 -> 동)
# -----------------------------------------------------------------------------
st.title("🏠 우리 동네 인구 피라미드")
st.markdown(
    f"**{latest_year}년 기준** 전국 읍·면·동의 나이별 인구 분포를 따뜻하게 살펴볼 수 있는 공간입니다."
)
st.write("---")

# 화면 상단에 3개의 드롭다운을 가로로 배치
col_sido, col_sigungu, col_dong = st.columns(3)

with col_sido:
    # 시·도 목록 추출 및 드롭다운 생성
    sido_list = sorted(df_latest['시도'].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 선택한 시·도로 1차 필터링
df_sido = df_latest[df_latest['시도'] == selected_sido]

with col_sigungu:
    # 선택된 시·도 안의 시·군·구 목록 추출
    sigungu_list = sorted(df_sido['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 선택한 시·군·구로 2차 필터링
df_sigungu = df_sido[df_sido['시군구'] == selected_sigungu]

with col_dong:
    # 선택된 시·군·구 안의 읍·면·동 목록 추출
    dong_list = sorted(df_sigungu['동'].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 최종 선택된 동네 데이터 필터링
df_selected = df_sigungu[df_sigungu['동'] == selected_dong]

# -----------------------------------------------------------------------------
# 5. 선택 지역 인구 요약 정보 카드
# -----------------------------------------------------------------------------
if not df_selected.empty:
    # 해당 동네의 남성 및 여성 나이별 인구 수 계산
    male_counts = df_selected[male_cols].sum().values
    female_counts = df_selected[female_cols].sum().values
    
    total_male = int(male_counts.sum())
    total_female = int(female_counts.sum())
    total_pop = total_male + total_female

    # 동네 주요 통계 수치 표시
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 인구수", f"{total_pop:,} 명")
    m2.metric("남성 인구", f"{total_male:,} 명")
    m3.metric("여성 인구", f"{total_female:,} 명")
    
    # 성비 계산 (여성 100명당 남성 수)
    sex_ratio = round((total_male / total_female * 100), 1) if total_female > 0 else 0
    m4.metric("성비 (여성 100명당)", f"{sex_ratio} 명")

    st.write("---")

    # -------------------------------------------------------------------------
    # 6. Plotly 인구 피라미드 그래프 생성
    # -------------------------------------------------------------------------
    # 남성 인구는 피라미드 왼쪽에 그리려면 값이 음수여야 합니다.
    male_negative = [-val for val in male_counts]
    female_positive = list(female_counts)

    fig = go.Figure()

    # 남성 막대 (왼쪽 배치 - 따뜻하고 아늑한 스카이블루 톤)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=male_negative,
        name='남성',
        orientation='h',
        marker=dict(color='#4C6EF5'),
        customdata=male_counts,
        hovertemplate='<b>나이: %{y}</b><br>남성 인구: %{customdata:,}명<extra></extra>'
    ))

    # 여성 막대 (오른쪽 배치 - 따뜻하고 포근한 웜코랄 톤)
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_positive,
        name='여성',
        orientation='h',
        marker=dict(color='#FF6B6B'),
        customdata=female_counts,
        hovertemplate='<b>나이: %{y}</b><br>여성 인구: %{customdata:,}명<extra></extra>'
    ))

    # X축의 최대 범위를 동적으로 계산 (양쪽에 균등한 여백 제공)
    max_val = max(max(male_counts), max(female_counts)) * 1.1 if max(female_counts) > 0 or max(male_counts) > 0 else 100

    # X축 눈금 표기를 위한 절대값 설정 (음수 기호 제거)
    step = max(1, int(max_val / 4))
    ticks = list(range(0, int(max_val) + step, step))
    tick_vals = [-t for t in reversed(ticks[1:])] + ticks
    tick_text = [f"{abs(t):,}" for t in tick_vals]

    # Layout 및 세로축(Y축) 순서 지정
    # categoryorder='array'와 categoryarray=age_labels를 사용하면
    # 0번째 요소('0세')가 맨 아래(y=0), 마지막 요소('100세 이상')가 맨 위에 고정됩니다.
    fig.update_layout(
        title=dict(
            text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}] 인구 피라미드</b>",
            font=dict(size=20, color="#2C3E50")
        ),
        barmode='overlay',
        xaxis=dict(
            title="인구 수 (명)",
            range=[-max_val, max_val],
            tickvals=tick_vals,
            ticktext=tick_text,
            showgrid=True,
            gridcolor="#E2E8F0"
        ),
        yaxis=dict(
            title="나이 (세)",
            type='category',
            categoryorder='array',       # 배열 순서대로 배치
            categoryarray=age_labels,   # '0세'가 맨 아래, '100세 이상'이 맨 위에 고정됨
            showgrid=False
        ),
        height=900,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Streamlit 화면에 차트 출력
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("선택하신 지역의 인구 데이터가 존재하지 않습니다.")
