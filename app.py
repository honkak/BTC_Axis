##############################################
# 비트코인 기준 자산비교 서비스 개발_2024.11.23 #
##############################################

import streamlit as st
import FinanceDataReader as fdr
import datetime
import pandas as pd
import yfinance as yf
import streamlit_analytics
from pycoingecko import CoinGeckoAPI
import matplotlib.pyplot as plt
import requests
import ccxt

# 한글 폰트 설정
def set_korean_font():
    try:
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # 예시: Nanum Gothic
        font_prop = font_manager.FontProperties(fname=font_path)
        matplotlib.rc('font', family=font_prop.get_name())
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
    except Exception as e:
        print(f"폰트 설정 실패: {e}")

set_korean_font()

# 서비스 제목 입력
st.markdown("<h2 style='font-size: 24px; text-align: center;'>다빈치 BTC Axis</h2>", unsafe_allow_html=True)

# 날짜 입력 (조회 시작일과 종료일을 같은 행에 배치)
col_start_date, col_end_date = st.columns(2)

with col_start_date:
    start_date = st.date_input(
        "조회 시작일을 선택해 주세요",
        datetime.datetime(2024, 1, 1)
    )

with col_end_date:
    end_date = st.date_input(
        "조회 종료일을 선택해 주세요",
        datetime.datetime.now()
    )

# 시작 날짜와 종료 날짜 비교
if start_date > end_date:
    st.warning("시작일이 종료일보다 더 늦습니다. 날짜를 자동으로 맞바꿔 반영합니다.")
    start_date, end_date = end_date, start_date  # 날짜를 바꿈

# 종목 코드 입력 필드
col_code1, col_code2, col_code3 = st.columns(3)

with col_code1:
    code1 = st.text_input('종목코드 1', value='', placeholder='종목코드를 입력하세요 - (예시)QQQ')

with col_code2:
    code2 = st.text_input('종목코드 2', value='', placeholder='종목코드를 입력하세요 - (예시)005930')

with col_code3:
    code3 = st.text_input('종목코드 3', value='', placeholder='종목코드를 입력하세요 - (예시)AAPL')

# '기준시점 수익률 비교' 체크박스
fixed_ratio = st.checkbox("기준시점 수익률 비교(Baseline return)")

# 수평선 추가
st.markdown("---")

##########################################################

# 'BTC 시가총액 비율' 체크박스
show_market_cap_chart = st.checkbox("BTC 시가총액 비율")

# 'BTC 시가총액 비율'이 체크된 경우에만 원형 차트 표시
if show_market_cap_chart:
    cg = CoinGeckoAPI()

    try:
        # 글로벌 시가총액 가져오기 (재시도 로직 포함)
        global_data = None
        for attempt in range(3):  # 최대 3번 재시도
            try:
                global_data = cg.get_global()
                if global_data:
                    break
            except Exception:
                time.sleep(2)  # 2초 대기 후 재시도
        if not global_data:
            raise ValueError("글로벌 암호화폐 시가총액 데이터를 가져오는 데 실패했습니다.")

        global_market_cap = global_data.get('data', {}).get('total_market_cap', {}).get('usd', 0)

        # 상위 암호화폐 시가총액 가져오기
        top_coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=5, page=1)
        if not top_coins:
            raise ValueError("상위 암호화폐 시가총액 데이터를 가져오는 데 실패했습니다.")

        # 데이터 정리
        labels = [coin['name'] for coin in top_coins] + ['Others']
        sizes = [coin['market_cap'] for coin in top_coins]

        # 시가총액 합계와 'Others' 계산
        total_top_market_cap = sum(sizes)
        others_market_cap = max(global_market_cap - total_top_market_cap, 0)  # 음수 방지
        sizes.append(others_market_cap)

        # 데이터 검증
        if any(size < 0 for size in sizes) or not sizes:
            raise ValueError("시가총액 데이터가 올바르지 않습니다.")

        # 파이 차트 생성
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.set_title('비트코인 도미넌스_전체 암호화폐 시장에서 BTC가 차지하는 비율(%)')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"암호화폐 시가총액 데이터를 불러오는 데 실패했습니다: {e}")

##########################################################

# # '김치프리미엄' 체크박스 추가
# show_kimchi_premium = st.checkbox("김치프리미엄 보기")

# # '김치프리미엄' 체크박스 선택 시 실행
# if show_kimchi_premium:
#     try:
#         # 환율 가져오기 함수
#         def get_exchange_rate():
#             url = "https://open.er-api.com/v6/latest/USD"
#             response = requests.get(url)
#             response.raise_for_status()
#             data = response.json()
#             return data['rates']['KRW']

#         # 업비트와 Binance의 데이터 가져오기
#         def fetch_historical_data():
#             upbit = ccxt.upbit()
#             binance = ccxt.binance()

#             since = upbit.parse8601(start_date.isoformat())
#             upbit_data = upbit.fetch_ohlcv("BTC/KRW", timeframe="1d", since=since)
#             upbit_df = pd.DataFrame(upbit_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
#             upbit_df["Date"] = pd.to_datetime(upbit_df["timestamp"], unit="ms")
#             upbit_df.set_index("Date", inplace=True)

#             binance_data = binance.fetch_ohlcv("BTC/USDT", timeframe="1d", since=since)
#             binance_df = pd.DataFrame(binance_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
#             binance_df["Date"] = pd.to_datetime(binance_df["timestamp"], unit="ms")
#             binance_df.set_index("Date", inplace=True)

#             exchange_rate = get_exchange_rate()
#             binance_df["Close (KRW)"] = binance_df["close"] * exchange_rate

#             df = pd.DataFrame({
#                 "Upbit (KRW)": upbit_df["close"],
#                 "Binance (KRW)": binance_df["Close (KRW)"]
#             })
#             df["Kimchi Premium (%)"] = (df["Upbit (KRW)"] - df["Binance (KRW)"]) / df["Binance (KRW)"] * 100
#             return df

#         # 데이터 가져오기
#         df = fetch_historical_data()

#         # 차트 그리기
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.plot(df.index, df["Kimchi Premium (%)"], label="Kimchi Premium (%)", color="blue")
#         ax.axhline(0, color="red", linestyle="--", label="Parity Line (0%)")
#         ax.set_title("Kimchi Premium Over Selected Period")
#         ax.set_xlabel("Date")
#         ax.set_ylabel("Kimchi Premium (%)")
#         ax.legend()
#         ax.grid()

#         st.pyplot(fig)
#     except Exception as e:
#         st.error(f"김치프리미엄 데이터를 가져오거나 시각화하는 데 실패했습니다: {e}")
