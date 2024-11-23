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
# from matplotlib import font_manager

# # 한글 폰트 설정 (폰트 이름으로 설정)
# def set_korean_font():
#     try:
#         # '맑은 고딕' 또는 '나눔고딕' 중 하나를 선택
#         # matplotlib.rc('font', family='Malgun Gothic')  # Windows 기본 한글 폰트
#         matplotlib.rc('font', family='NanumGothic')  # 나눔고딕 사용 시 주석 해제
#         plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
#     except Exception as e:
#         print(f"폰트 설정 실패: {e}")

# set_korean_font()

# 서비스 제목 입력
st.markdown("<h2 style='font-size: 30px; text-align: center;'>다빈치 BTC AXIS</h2>", unsafe_allow_html=True)

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

# 수평선 추가
st.markdown("---")

######################################
#BTC 가격 트랜드 기능

# 'BTC 가격' 체크박스 (기본 체크 상태)
show_btc_price_chart = st.checkbox("BTC 가격", value=True)

if show_btc_price_chart:
    try:
        # 업비트 모듈 초기화
        upbit = ccxt.upbit()

        # 업비트 서비스 시작일
        upbit_start_date = datetime.date(2017, 10, 24)

        # 조회 시작일이 업비트 서비스 시작일 이전이면 자동으로 변경
        if start_date < upbit_start_date:
            start_date = upbit_start_date
            st.warning("업비트 가격을 가져오므로 조회 시작일을 2017년 10월 24일 서비스 개시일로 자동 변경합니다.")

        # 데이터 조회를 위한 타임스탬프 변환
        since = int(datetime.datetime.combine(start_date, datetime.datetime.min.time()).timestamp() * 1000)
        end_timestamp = int(datetime.datetime.combine(end_date, datetime.datetime.max.time()).timestamp() * 1000)

        # 데이터 조회
        ohlcv = []
        from_time = since
        while True:
            data = upbit.fetch_ohlcv("BTC/KRW", timeframe="1d", since=from_time, limit=200)
            if not data:
                break
            ohlcv.extend(data)
            last_time = data[-1][0]
            if last_time >= end_timestamp or last_time == from_time:
                break
            from_time = last_time + 1

        # 초기화
        start_price = None
        end_price = None

        if not ohlcv:
            st.warning("선택한 기간에 대한 데이터가 없습니다. 다른 기간을 선택해 주세요.")
        else:
            # 데이터프레임 변환
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("Date", inplace=True)

            # 조회 시작일과 종료일에 맞게 필터링
            df = df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]

            if not df.empty:
                start_price = df.iloc[0]["close"]  # 시작 가격
                end_price = df.iloc[-1]["close"]  # 종료 가격
                st.write(f"BTC Price (KRW) on {end_date}: {end_price:,.0f} KRW")
            else:
                st.warning(f"No closing price data available for {end_date}.")

            # 꺾은선 차트 생성
            if not df.empty:
                st.write(f"BTC Price in KRW: {start_date} to {end_date}")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df.index, df["close"], label="BTC Price (KRW)", color="green")
                ax.set_title("Bitcoin Price in KRW (Upbit)", fontsize=16)
                ax.set_xlabel("Date", fontsize=12)
                ax.set_ylabel("Price (KRW)", fontsize=12)
                ax.grid(True)
                ax.legend(fontsize=12)
                plt.xticks(rotation=45)
                st.pyplot(fig)

            # 1천만 원 투자 결과 계산
            if start_price and end_price:
                st.markdown("<h2 style='font-size: 20px;'>1천만 원을 투자했다면,</h2>", unsafe_allow_html=True)

                # 초기 투자금액
                initial_investment = 10000000  # 1천만 원

                # 수익률 계산
                return_percentage = ((end_price - start_price) / start_price) * 100
                profit_amount = (return_percentage / 100) * initial_investment
                total_amount = initial_investment + profit_amount

                # 수익률 색상 결정
                color = 'red' if return_percentage >= 0 else 'blue'

                # 결과 출력
                st.markdown(
                    f"BTC에 1천만 원을 투자했더라면, 현재 {total_amount:,.0f} 원이 되었을 것입니다. "
                    f"(<span style='color: {color};'>수익률: {return_percentage:.2f}%</span>)",
                    unsafe_allow_html=True,
                )

    except Exception as e:
        st.error(f"비트코인 데이터를 가져오는 중 오류가 발생했습니다: {e}")


######################################

# 수평선 추가
st.markdown("---")

#####################################
#시가총액 비율 기능

# 'BTC 시가총액 비율' 체크박스
show_market_cap_chart = st.checkbox("BTC 시가총액 비율")

if show_market_cap_chart:
    cg = CoinGeckoAPI()

    try:
        # 강제로 현재 시점 기준으로 365일 전부터 데이터 설정
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=365)

        # 상위 암호화폐 시가총액 가져오기 (최신 데이터)
        top_coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=100, page=1)
        if not top_coins:
            raise ValueError("상위 암호화폐 데이터를 가져오는 데 실패했습니다.")

        # 상위 5개 코인과 Others 처리
        top_5_coins = top_coins[:5]  # 상위 5개 코인
        top_5_market_cap = sum(coin['market_cap'] for coin in top_5_coins)
        others_market_cap = sum(coin['market_cap'] for coin in top_coins[5:])  # 나머지 코인

        # 데이터 준비
        labels = [coin['name'] for coin in top_5_coins] + ['Others']
        sizes = [coin['market_cap'] for coin in top_5_coins] + [others_market_cap]

        # Bitcoin 색상 및 다른 조각 색상 설정
        pie_colors = ['#1f77b4'] + ['#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6']

        # 모든 조각을 5%씩 분리
        explode = [0.05 for _ in labels]

        # 폰트 및 스타일 설정
        font_size = 10  # 차트 폰트 크기
        title_font_size = 14  # 차트 제목 폰트 크기
        axis_font_size = 8  # 축 폰트 크기

        # BTC 시가총액 및 도미넌스 계산
        btc_market_cap = sizes[0]
        global_market_cap = top_5_market_cap + others_market_cap
        btc_dominance = (btc_market_cap / global_market_cap) * 100

        # 데이터 검증 및 출력
        st.write(f"Global Market Cap (USD): {int(global_market_cap):,} USD")
        st.write(f"BTC Market Cap (USD): {int(btc_market_cap):,} USD")
        st.write(f"BTC Dominance: {btc_dominance:.2f}%")

        # 파이 차트 생성
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(
            sizes,
            labels=labels,
            autopct=lambda p: f'{p:.1f}%' if p > 0 else '',
            startangle=140,
            colors=pie_colors,
            explode=explode
        )
        ax.set_title('Market Cap Distribution(Now)', fontsize=title_font_size)
        st.pyplot(fig)

        # 365일 전부터 현재까지 BTC 도미넌스 데이터 가져오기
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        btc_dominance_data = cg.get_coin_market_chart_range_by_id(
            id='bitcoin',
            vs_currency='usd',
            from_timestamp=start_timestamp,
            to_timestamp=end_timestamp
        )

        # 도미넌스 데이터 처리
        dominance_dates = [datetime.datetime.fromtimestamp(price[0] / 1000) for price in btc_dominance_data['market_caps']]
        dominance_values = [
            (price[1] / global_market_cap) * 100 if global_market_cap > 0 else 0
            for price in btc_dominance_data['market_caps']
        ]

        # 강제 기간: 365일 전부터 현재 날짜까지
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=365)
        
        # 날짜를 문자열로 포맷
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        
        # 꺾은선 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dominance_dates, dominance_values, label="BTC Dominance (%)", color="green")  # 녹색 꺾은선 그래프
        ax.set_title(f"BTC Dominance Over Time ({start_date_str} to {end_date_str})", fontsize=title_font_size)
        ax.set_xlabel("Date", fontsize=axis_font_size)
        ax.set_ylabel("BTC Dominance (%)", fontsize=axis_font_size)
        ax.set_ylim(0, 100)  # Y축 범위 0% ~ 100%
        ax.grid(True)
        ax.legend(fontsize=font_size)
        plt.xticks(rotation=45, fontsize=axis_font_size)  # X축 날짜를 대각선으로 표시
        st.pyplot(fig)

    except Exception as e:
        st.error(f"암호화폐 데이터를 불러오는 데 실패했습니다: {e}")

######################################

# 수평선 추가
st.markdown("---")

#####################################


# '김치프리미엄' 체크박스 추가
show_kimchi_premium = st.checkbox("김치프리미엄 보기")

if show_kimchi_premium:
    try:
        # 환율 가져오기 함수
        def get_exchange_rate():
            url = "https://open.er-api.com/v6/latest/USD"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data['rates']['KRW']

        # 업비트와 코인게코 데이터를 사용한 김치프리미엄 계산
        def fetch_historical_data():
            upbit = ccxt.upbit()
            cg = CoinGeckoAPI()

            # 최근 100일 기준으로 설정
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=100)

            # 업비트 데이터 가져오기
            since = int(start_date.timestamp() * 1000)
            upbit_data = upbit.fetch_ohlcv("BTC/KRW", timeframe="1d", since=since)
            upbit_df = pd.DataFrame(upbit_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            upbit_df["Date"] = pd.to_datetime(upbit_df["timestamp"], unit="ms")
            upbit_df.set_index("Date", inplace=True)

            # 코인게코 데이터를 가져오기
            btc_market_data = cg.get_coin_market_chart_range_by_id(
                id="bitcoin",
                vs_currency="usd",
                from_timestamp=int(start_date.timestamp()),
                to_timestamp=int(end_date.timestamp())
            )
            cg_df = pd.DataFrame(btc_market_data["prices"], columns=["timestamp", "price_usd"])
            cg_df["Date"] = pd.to_datetime(cg_df["timestamp"], unit="ms")
            cg_df.set_index("Date", inplace=True)

            # 환율 적용
            exchange_rate = get_exchange_rate()
            cg_df["Close (KRW)"] = cg_df["price_usd"] * exchange_rate

            # 김치프리미엄 계산
            df = pd.DataFrame({
                "Upbit (KRW)": upbit_df["close"],
                "CoinGecko (KRW)": cg_df["Close (KRW)"]
            })
            df["Kimchi Premium (%)"] = (df["Upbit (KRW)"] - df["CoinGecko (KRW)"]) / df["CoinGecko (KRW)"] * 100
            return df

        # 데이터 가져오기
        df = fetch_historical_data()

        # 현재 김치프리미엄 계산
        current_premium = df["Kimchi Premium (%)"].iloc[-1] if not df.empty else None

        # 차트 그리기
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df.index, df["Kimchi Premium (%)"], label="Kimchi Premium (%)", color="blue")
        ax.axhline(0, color="red", linestyle="--", label="Parity Line (0%)")
        ax.set_title("Kimchi Premium Over Last 100 Days (Upbit vs CoinGecko)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Kimchi Premium (%)")
        ax.legend()
        ax.grid()

        # 현재 김치프리미엄 값 출력
        if current_premium is not None:
            st.markdown(f"<h3>현재 김치프리미엄: {current_premium:.2f}%</h3>", unsafe_allow_html=True)

        st.pyplot(fig)
    except Exception as e:
        st.error(f"김치프리미엄 데이터를 가져오거나 시각화하는 데 실패했습니다: {e}")




#############################


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

