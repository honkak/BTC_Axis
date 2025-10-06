##############################################
# 비트코인 기준 자산비교 서비스 개발_2025.10.06 #
##############################################

import streamlit as st
import FinanceDataReader as fdr
import datetime
import pandas as pd
from pycoingecko import CoinGeckoAPI
import matplotlib.pyplot as plt
import requests
import ccxt
import matplotlib.ticker as ticker
import numpy as np # numpy 추가

# 서비스 제목 입력
st.markdown("<h2 style='font-size: 30px; text-align: center;'>다빈치 BITCOIN 분석 서비스</h2>", unsafe_allow_html=True)

# 날짜 입력 (조회 시작일과 종료일을 같은 행에 배치)
col_start_date, col_end_date = st.columns(2)

with col_start_date:
    # 2025.01.01 대신 더 합리적인 시작 날짜 (예: 100일 전) 또는 유지
    default_start_date = datetime.datetime.now() - datetime.timedelta(days=100)
    start_date = st.date_input(
        "조회 시작일을 선택해 주세요",
        default_start_date # 기본값을 100일 전으로 설정 (CoinGecko 제한 고려)
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
show_btc_price_chart = st.checkbox("Bitcoin 가격", value=False)

if show_btc_price_chart:
    try:
        # 업비트 모듈 초기화
        upbit = ccxt.upbit()

        # 업비트 서비스 시작일
        upbit_start_date = datetime.date(2017, 10, 24)

        # 조회 시작일이 업비트 서비스 시작일 이전이면 자동으로 변경
        if start_date < upbit_start_date:
            st.warning("업비트 가격을 가져오므로 조회 시작일을 2017년 10월 24일 서비스 개시일로 자동 변경합니다.")
            effective_start_date = upbit_start_date
        else:
            effective_start_date = start_date

        # 현재 날짜 가져오기
        today = datetime.date.today()

        # 조회 종료일이 미래인 경우 현재 날짜로 변경
        if end_date > today:
            st.warning("조회 종료일이 미래 날짜이므로 종료일을 오늘로 설정합니다.")
            effective_end_date = today
        else:
            effective_end_date = end_date

        # 데이터 조회를 위한 타임스탬프 변환
        since = int(datetime.datetime.combine(effective_start_date, datetime.datetime.min.time()).timestamp() * 1000)
        end_timestamp = int(datetime.datetime.combine(effective_end_date, datetime.datetime.max.time()).timestamp() * 1000)

        # 데이터 조회
        ohlcv = []
        from_time = since
        while True:
            data = upbit.fetch_ohlcv("BTC/KRW", timeframe="1d", since=from_time, limit=200)
            if not data:
                break
            # 데이터가 종료일 타임스탬프를 초과하는지 확인하고 필터링
            filtered_data = [d for d in data if d[0] <= end_timestamp]
            ohlcv.extend(filtered_data)
            
            if not data:
                 break
            
            last_time = data[-1][0]
            if last_time >= end_timestamp: # 마지막 데이터가 종료일 이후이면 종료
                 break
            from_time = last_time + 1
            
            # 마지막 데이터가 조회 기간 내의 데이터가 아니면 (즉, 마지막 날짜에 도달하면) 반복 중단
            if not filtered_data and ohlcv:
                 break


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
            df = df[(df.index >= pd.to_datetime(effective_start_date)) & (df.index <= pd.to_datetime(effective_end_date) + datetime.timedelta(days=1) - datetime.timedelta(seconds=1))]

            if not df.empty:
                start_price = df.iloc[0]["close"]  # 시작 가격
                end_price = df.iloc[-1]["close"]  # 종료 가격
                # 종료일 문구 출력
                st.write(f"BTC Price (KRW) on {effective_end_date}: {end_price:,.0f} KRW")
            else:
                st.warning(f"No closing price data available for {effective_end_date}.")

            # 꺾은선 차트 생성
            if not df.empty:
                st.write(f"BTC Price in KRW: {effective_start_date} to {effective_end_date}")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df.index, df["close"], label="BTC Price (KRW)", color="green")
                
                # 세로축을 100M 단위로 변환
                def format_krw(value, tick_number):
                    return f"{value / 1e8:.1f} 100M"  # 100M 단위로 변환
                
                ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_krw))
                
                ax.set_title("Bitcoin Price in KRW (Upbit)", fontsize=16)
                ax.set_xlabel("Date", fontsize=12)
                ax.set_ylabel("Price (100M KRW)", fontsize=12)  # 세로축 단위 표시 변경
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
# '비트코인 기준 자산흐름' 체크박스
fixed_ratio = st.checkbox("BTC 기준 자산흐름(Bitcoin Axis)")

def fetch_full_ohlcv(exchange, symbol, timeframe, since, until):
    """업비트 API를 통해 전체 데이터를 가져오는 함수"""
    all_data = []
    # until은 datetime 객체, timestamp()는 초 단위, ccxt는 밀리초 단위를 사용
    until_ts_ms = int(until.timestamp() * 1000)
    
    while since < until_ts_ms:
        try:
            # limit=200이므로 최대 200개
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=200)  
            if not ohlcv:
                break
            
            # 종료 시점 이전에 있는 데이터만 추가
            filtered_ohlcv = [data for data in ohlcv if data[0] <= until_ts_ms]
            all_data.extend(filtered_ohlcv)
            
            if not filtered_ohlcv: # 필터링된 데이터가 없으면 중단
                break
                
            last_time = ohlcv[-1][0]
            if last_time >= until_ts_ms: # 원본 데이터의 마지막이 종료 시점 이후이면 중단
                 break
                 
            since = last_time + 1  # 마지막 데이터의 다음 타임스탬프를 기준으로 다음 데이터 요청
            
        except Exception as e:
            st.warning(f"{symbol} 데이터를 가져오는 중 문제가 발생했습니다: {e}")
            break
            
    return all_data

if fixed_ratio:
    # 코인/종목 코드 입력 필드
    col_code1, col_code2, col_code3 = st.columns(3)
    with col_code1:
        code1 = st.text_input('자산코드 1', value='', placeholder='코드입력 - (예시)ETH')
    with col_code2:
        code2 = st.text_input('자산코드 2', value='', placeholder='코드입력 - (예시)SOL')
    with col_code3:
        code3 = st.text_input('자산코드 3', value='', placeholder='코드입력 - (예시)XRP')

    # 업비트 모듈 초기화
    upbit = ccxt.upbit()

    # 입력된 종목 코드 리스트
    codes = [code1.strip().upper(), code2.strip().upper(), code3.strip().upper()]
    codes = [code for code in codes if code]  # 빈 코드 제거

    # 날짜 변환 (datetime.date → datetime.datetime)
    try:
        start_datetime = datetime.datetime.combine(start_date, datetime.datetime.min.time())
        end_datetime = datetime.datetime.combine(end_date, datetime.datetime.max.time())
    except NameError:
        st.error("start_date와 end_date가 상위 코드에서 정의되지 않았습니다.")
        st.stop()

    col_cb1, col_cb2, col_cb3 = st.columns(3)
    with col_cb1:
        add_usd = st.checkbox("USD/BTC(달러)")
    with col_cb2:
        add_krw = st.checkbox("KRW/BTC(원화)")
    with col_cb3:
        add_apartment = st.checkbox("SPY/BTC(S&P500)(예정)")

    # 기준시점 수익률 비교 차트 생성
    ohlcv_data = {}
    if codes:
        for code in codes:
            try:
                pair = f"{code}/BTC"
                # 전체 데이터 가져오기
                ohlcv = fetch_full_ohlcv(upbit, pair, "1d", int(start_datetime.timestamp() * 1000), end_datetime)
                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["Date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.normalize()
                df.set_index("Date", inplace=True)

                # 기간 필터링 (최종 점검)
                df = df.loc[start_datetime.date():end_datetime.date()]
                ohlcv_data[f"{code}/BTC"] = df["close"]
            except Exception as e:
                st.warning(f"{code} 데이터를 가져오는 중 문제가 발생했습니다: {e}")

    # USD/BTC와 KRW/BTC 추가
    if add_usd:
        try:
            # CoinGecko 대신 Upbit BTC/USDT 사용
            ohlcv = fetch_full_ohlcv(upbit, "BTC/USDT", "1d", int(start_datetime.timestamp() * 1000), end_datetime)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["Date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.normalize()
            df.set_index("Date", inplace=True)
            df = df.loc[start_datetime.date():end_datetime.date()]
            # BTC/USDT의 역수: 1 BTC를 얻는 데 필요한 USD (USD/BTC)가 아니라
            # 1 USD를 얻는 데 필요한 BTC (USD/BTC, BTC 단위)가 됨.
            # BTC 기준으로 자산 흐름을 보려면 1 / Price (즉, 1 USD를 얻는 데 필요한 BTC)를 써야 함.
            ohlcv_data["USD/BTC"] = 1 / df["close"] 
        except Exception as e:
            st.warning(f"USD/BTC 데이터를 가져오는 중 문제가 발생했습니다: {e}")

    if add_krw:
        try:
            ohlcv = fetch_full_ohlcv(upbit, "BTC/KRW", "1d", int(start_datetime.timestamp() * 1000), end_datetime)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["Date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.normalize()
            df.set_index("Date", inplace=True)
            df = df.loc[start_datetime.date():end_datetime.date()]
            # KRW/BTC: 1 KRW를 얻는 데 필요한 BTC
            ohlcv_data["KRW/BTC"] = 1 / df["close"]
        except Exception as e:
            st.warning(f"KRW/BTC 데이터를 가져오는 중 문제가 발생했습니다: {e}")

    # 최종 차트 생성
    if ohlcv_data:
        df_combined = pd.DataFrame(ohlcv_data).dropna()
        
        # 시작 시점의 가격을 100으로 기준하여 % 변화율 계산: (현재 가격 / 시작 가격) * 100 - 100
        if not df_combined.empty:
            df_combined = df_combined / df_combined.iloc[0] * 100 - 100 
        else:
            st.warning("데이터가 너무 적어 BTC 기준 자산흐름 차트를 그릴 수 없습니다.")
            st.stop()


        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_ylabel("Percentage Change (%)", fontsize=12)

        # 0%에 붉은 점선 추가
        ax.axhline(y=0, color="red", linestyle="--", linewidth=1, label="0% Baseline (BTC Performance)")

        for column in df_combined.columns:
            ax.plot(df_combined.index, df_combined[column], label=column)

        ax.set_title(f"Asset Performance Relative to BTC ({start_date} to {end_date})", fontsize=16)
        ax.set_xlabel("Date", fontsize=12)
        ax.legend()
        ax.grid(True)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("조회결과가 없습니다. 코드를 입력해주세요.")

---

# 코인 리스트 표시 기능 (변경 없음)
# ... (코인 리스트 관련 코드) ...
coins = [
    ("이더리움", "ETH"), ("리플", "XRP"), ("에이다", "ADA"),
    ("솔라나", "SOL"), ("폴카닷", "DOT"), ("도지코인", "DOGE"), ("체인링크", "LINK"),
    ("라이트코인", "LTC"), ("비트코인캐시", "BCH"), ("스텔라루멘", "XLM"), ("트론", "TRX"),
    ("이오스", "EOS"), ("비체인", "VET"), ("테조스", "XTZ"), ("코스모스", "ATOM"),
    ("파일코인", "FIL"), ("이더리움클래식", "ETC"), ("네오", "NEO"), ("퀀텀", "QTUM"),
    ("아이콘", "ICX"), ("온톨로지", "ONT"), ("질리카", "ZIL"), ("스테이터스네트워크토큰", "SNT"),
    ("메인프레임", "MFT"), ("시빅", "CVC"), ("스톰엑스", "STMX"), ("펀디엑스", "PUNDIX"),
    ("오미세고", "OMG"), ("왁스", "WAXP"), ("엔진코인", "ENJ"), ("디센트럴랜드", "MANA"),
    ("샌드박스", "SAND"), ("엑시인피니티", "AXS"), ("칠리즈", "CHZ"), ("보라", "BORA"),
    ("플레이댑", "PLA"), ("알파쿼크", "AQT"), ("밀크", "MLK"), ("썸씽", "SSX"),
    ("무비블록", "MBL"), ("메디블록", "MED"), ("아하토큰", "AHT"), ("디카르고", "DKA"),
    ("센티넬프로토콜", "UPP"), ("피르마체인", "FCT2"), ("아르고", "AERGO"), ("오브스", "ORBS"),
    ("카바", "KAVA"), ("스트라이크", "STRK"), ("스택스", "STX"), ("폴리곤", "MATIC"),
    ("스와이프", "SXP"), ("앵커", "ANKR"), ("세럼", "SRM"), ("솔라", "SXP"),
    ("이캐시", "XEC"), ("비트토렌트", "BTT"), ("트러스트월렛토큰", "TWT"), ("오션프로토콜", "OCEAN"),
    ("오리진프로토콜", "OGN"), ("온버프", "ONIT"), ("오키드", "OXT"), ("프롬", "PROM"),
    ("파리생제르맹", "PSG"), ("퀴즈톡", "QTCON"), ("래드웍스", "RAD"), ("레이디움", "RAY"),
    ("레이", "REI"), ("아이젝", "RLC"), ("랠리", "RLY"), ("랜더토큰", "RNDR"),
    ("리저브라이트", "RSR"), ("레이븐코인", "RVN"), ("신세틱스", "SNX"), ("스타게이트파이낸스", "STG"),
    ("썬", "SUN"), ("쓰레쉬홀드", "T"), ("트루USD", "TUSD"), ("팍스달러", "USDP"),
    ("밸리디티", "VAL"), ("일드길드게임즈", "YGG"), ("토트넘훗스퍼", "SPURS")
]

# 코인 리스트 데이터프레임 구성
columns = ["코인명1", "코인코드1", "코인명2", "코인코드2", "코인명3", "코인코드3"]
data = []

for i in range(0, len(coins), 3):
    row = []
    for j in range(3):
        if i + j < len(coins):
            row.extend(coins[i + j])
        else:
            row.extend(["", ""])  # 빈칸 채우기
    data.append(row)

df_coins = pd.DataFrame(data, columns=columns)

# 스타일링 함수 정의
def highlight_columns(x):
    # 기본 스타일: 텍스트 색상을 지정하지 않아 Streamlit 테마에 따르게 함 (다크모드=흰색, 라이트모드=검은색)
    style = pd.DataFrame("", index=x.index, columns=x.columns)
    
    # 1, 3, 5열 (이름 열)에 회색 배경과 검은색 텍스트 적용 (다크모드 가시성 확보)
    style.iloc[:, [0, 2, 4]] = "background-color: lightgrey; color: black;"
    
    return style

# 상태 초기화
if "show_coins" not in st.session_state:
    st.session_state.show_coins = False

# 버튼 배치
col_button1 = st.columns([1])[0] # 버튼을 가운데 정렬하기 위해 1열 컬럼만 사용
with col_button1:
    if st.button("코인 리스트"):
        st.session_state.show_coins = not st.session_state.show_coins

# 데이터프레임 표시
if st.session_state.show_coins:
    # st.markdown("### 코인 리스트")
    st.dataframe(df_coins.style.apply(highlight_columns, axis=None), use_container_width=True)


---

#####################################
#시가총액 비율 기능 (변경 없음)

# 'BTC 시가총액 비율' 체크박스
show_market_cap_chart = st.checkbox("Bitcoin 시가총액 비율")

if show_market_cap_chart:
    cg = CoinGeckoAPI()

    try:
        # 강제로 현재 시점 기준으로 365일 전부터 데이터 설정
        end_date_cap = datetime.datetime.now()
        start_date_cap = end_date_cap - datetime.timedelta(days=365)

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
        pie_colors = ['#5ba6e1'] + ['#e57373', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6']

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
        st.write(f"Global Market Cap (USD): {int(global_market_cap):,} (USD)")
        st.write(f"Bitcoin Market Cap (USD): {int(btc_market_cap):,} (USD)")
        st.write(f"Bitcoin Dominance: {btc_dominance:.2f}(%)")

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
        start_timestamp = int(start_date_cap.timestamp())
        end_timestamp = int(end_date_cap.timestamp())
        btc_dominance_data = cg.get_coin_market_chart_range_by_id(
            id='bitcoin',
            vs_currency='usd',
            from_timestamp=start_timestamp,
            to_timestamp=end_timestamp
        )

        # 도미넌스 데이터 처리
        # CoinGecko API는 직접적인 Dominance 데이터를 제공하지 않음. 
        # Market Cap 데이터를 가져와서 (BTC Market Cap / Global Market Cap) * 100으로 계산해야 함.
        # 현재 코드에서는 btc_market_data['market_caps']를 사용하고 있는데, 
        # 이는 사실상 BTC의 시가총액 변화 데이터임.
        # 정확한 도미넌스 변화를 그리려면 Global Market Cap 데이터가 필요함.
        # CoinGecko의 'market_caps' 필드 자체가 BTC 시가총액을 나타냄. 
        # Global Market Cap의 역사적 데이터는 API가 다소 복잡하므로, 일단 현재 로직 유지 (단, 정확한 도미넌스는 아닐 수 있음)
        dominance_dates = [datetime.datetime.fromtimestamp(price[0] / 1000) for price in btc_dominance_data['market_caps']]
        
        # 임시로 가장 최신 Global Market Cap으로 나누어 Dominance 변화를 추정 (정확하지 않음)
        # 실제로는 각 날짜의 Global Market Cap을 가져와야 함.
        dominance_values = [
            (price[1] / global_market_cap) * 100 if global_market_cap > 0 else 0
            for price in btc_dominance_data['market_caps']
        ]


        # 강제 기간: 365일 전부터 현재 날짜까지
        start_date_str = start_date_cap.strftime("%Y-%m-%d")
        end_date_str = end_date_cap.strftime("%Y-%m-%d")

        
        # 꺾은선 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dominance_dates, dominance_values, label="BTC Dominance (%) (Approximation)", color="green")  # 녹색 꺾은선 그래프
        ax.set_title(f"BTC Dominance Over Time ({start_date_str} to {end_date_str})", fontsize=title_font_size)
        ax.set_xlabel("Date", fontsize=axis_font_size)
        ax.set_ylabel("BTC Dominance (%)", fontsize=axis_font_size)
        ax.set_ylim(min(dominance_values) * 0.9 if dominance_values else 0, max(dominance_values) * 1.1 if dominance_values else 100) # Y축 범위 동적 조절
        ax.grid(True)
        ax.legend(fontsize=font_size)
        plt.xticks(rotation=45, fontsize=axis_font_size)  # X축 날짜를 대각선으로 표시
        st.pyplot(fig)

    except Exception as e:
        st.error(f"암호화폐 데이터를 불러오는 데 실패했습니다: {e}")

---

#####################################
# '김치프리미엄' 체크박스 추가
show_kimchi_premium = st.checkbox("김치프리미엄 보기")

# CoinGecko에서 USDT/USD 데이터를 가져오는 함수 (변경 없음)
@st.cache_data(ttl=3600)  # 데이터를 1시간 동안 캐싱
def fetch_usdt_prices_cg():
    url = "https://api.coingecko.com/api/v3/coins/tether/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "100",
        "interval": "daily"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # 오류 시 예외 발생
    data = response.json()
    return data["prices"]


if show_kimchi_premium:
    try:
        # 환율 가져오기 함수 (현재 환율) (변경 없음)
        @st.cache_data(ttl=3600)
        def get_exchange_rate():
            url = "https://open.er-api.com/v6/latest/USD"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data['rates']['KRW']

        # 업비트와 코인게코 데이터를 사용한 김치프리미엄 계산 (날짜 반영)
        def fetch_historical_data_kimchi(start_date_kr, end_date_kr):
            upbit = ccxt.upbit()
            cg = CoinGeckoAPI()
            
            # 조회 기간 설정
            start_datetime_hist = datetime.datetime.combine(start_date_kr, datetime.datetime.min.time())
            end_datetime_hist = datetime.datetime.combine(end_date_kr, datetime.datetime.max.time())
            
            # 조회 기간의 일수 계산 (CoinGecko days 파라미터 대신 range 사용)
            # CoinGecko는 timestamp로 조회 가능하므로, 이를 사용
            start_timestamp = int(start_datetime_hist.timestamp())
            end_timestamp = int(end_datetime_hist.timestamp())

            # 1. 업비트 BTC/KRW 데이터 가져오기 (종료 시점 포함)
            upbit_data = fetch_full_ohlcv(
                upbit, 
                "BTC/KRW", 
                "1d", 
                int(start_datetime_hist.timestamp() * 1000), 
                end_datetime_hist
            )
            
            upbit_df = pd.DataFrame(upbit_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            upbit_df["Date"] = pd.to_datetime(upbit_df["timestamp"], unit="ms").dt.normalize()
            upbit_df.set_index("Date", inplace=True)
            # 날짜 필터링
            upbit_df = upbit_df.loc[start_datetime_hist.date():end_datetime_hist.date()]
            
            # 2. 코인게코 BTC/USD 데이터 가져오기
            # CoinGecko의 get_coin_market_chart_range_by_id는 UTC 기준 일일 데이터를 제공.
            btc_market_data = cg.get_coin_market_chart_range_by_id(
                id="bitcoin",
                vs_currency="usd",
                from_timestamp=start_timestamp,
                to_timestamp=end_timestamp
            )
            
            # CoinGecko 데이터는 UTC 자정 기준으로 넘어오므로, 인덱스 맞추기 위해 정규화
            cg_df = pd.DataFrame(btc_market_data["prices"], columns=["timestamp", "price_usd"])
            cg_df["Date"] = pd.to_datetime(cg_df["timestamp"], unit="ms").dt.normalize()
            cg_df.set_index("Date", inplace=True)
            
            # 3. USD/KRW 역사적 환율 데이터 가져오기
            # CoinGecko BTC/USD를 원화로 변환하기 위해 해당 기간의 USD/KRW 종가 필요
            start_date_str = start_date_kr.strftime("%Y-%m-%d")
            end_date_str = end_date_kr.strftime("%Y-%m-%d")
            
            try:
                # FinanceDataReader로 환율 가져오기
                df_fx = fdr.DataReader('USD/KRW', start=start_date_str, end=end_date_str)
                df_fx.index = df_fx.index.normalize()
                df_fx = df_fx['Close'].rename('FX_KRW_Price')
            except Exception as fe:
                st.warning(f"환율 데이터를 가져오는 데 실패했습니다 (FinanceDataReader): {fe}. 현재 환율로 대체합니다.")
                current_rate = get_exchange_rate()
                # 모든 날짜에 대해 현재 환율을 적용하는 DataFrame 생성 (정확도는 떨어지나 차트 생성을 위함)
                date_range = pd.date_range(start=start_date_kr, end=end_date_kr, freq='D')
                df_fx = pd.Series(current_rate, index=date_range).rename('FX_KRW_Price')


            # 4. 데이터 병합
            df = pd.DataFrame({
                "Upbit (KRW)": upbit_df["close"],
            })
            
            # CoinGecko 데이터 병합
            df = df.join(cg_df["price_usd"].rename("CoinGecko (USD)"), how='inner')
            
            # 환율 데이터 병합 (날짜 기준 병합)
            df = df.join(df_fx, how='inner')
            
            # 코인게코 USD 가격을 역사적 FX 환율로 KRW로 변환
            df["CoinGecko (KRW)"] = df["CoinGecko (USD)"] * df["FX_KRW_Price"]
            
            df = df.dropna()
            
            # 김프 계산
            df["Kimchi Premium (%)"] = (df["Upbit (KRW)"] - df["CoinGecko (KRW)"]) / df["CoinGecko (KRW)"] * 100
            
            return df

        # 데이터 가져오기 (선택된 날짜 반영)
        df = fetch_historical_data_kimchi(start_date, end_date)

        # 현재 김치프리미엄 계산
        current_premium = df["Kimchi Premium (%)"].iloc[-1] if not df.empty else None

        # 차트 그리기
        if not df.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df.index, df["Kimchi Premium (%)"], label="Kimchi Premium (%)", color="blue")
            ax.axhline(0, color="red", linestyle="--", label="Parity Line (0%)")
            ax.set_title(f"Kimchi Premium Over Time ({start_date} to {end_date})")
            ax.set_xlabel("Date")
            ax.set_ylabel("Kimchi Premium (%)")
            ax.legend()
            ax.grid()

            # 현재 김치프리미엄 값 출력
            if current_premium is not None:
                st.markdown(
                    f"<p style='font-size: 16px;'>현재 Bitcoin 김치 프리미엄: <b>{current_premium:.2f}%</b></p>",
                    unsafe_allow_html=True
                )
            
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
             st.warning("선택한 기간에 대한 김치프리미엄 데이터를 계산할 수 없습니다. 날짜 범위를 확인해 주세요.")
             
    except Exception as e:
        st.error(f"김치프리미엄 데이터를 가져오거나 시각화하는 데 실패했습니다: {e}")


---

#####################################
# 'USDT 가격변화' 기능 구현 (변경 없음)
# ... (USDT 가격변화 관련 코드) ...

# CoinGecko에서 USDT/USD 데이터를 가져오는 함수 (100일)
@st.cache_data(ttl=3600)  # 데이터를 1시간 동안 캐싱
def fetch_usdt_prices_cg():
    url = "https://api.coingecko.com/api/v3/coins/tether/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "100",  # 데이터를 100일로 제한
        "interval": "daily"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["prices"]


# USD/KRW 역사적 환율 데이터를 가져오는 함수 (FinanceDataReader 사용)
@st.cache_data(ttl=3600)
def fetch_historical_usd_krw_rate():
    end_date_fx = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date_fx = (datetime.datetime.now() - datetime.timedelta(days=100)).strftime("%Y-%m-%d")
    
    # USD/KRW 환율 데이터 가져오기
    # FinanceDataReader를 사용하여 'USD/KRW' 심볼을 조회
    df_fx = fdr.DataReader('USD/KRW', start=start_date_fx, end=end_date_fx)
    
    # 인덱스 이름 'date'로 정규화 및 날짜만 남기기
    df_fx.index = df_fx.index.normalize()
    df_fx.index.name = 'date'
    
    # 'Close' 컬럼만 사용 (종가)
    return df_fx['Close'].rename('FX_KRW_Price')


# 환율 데이터를 가져오는 함수 (USD -> KRW, 현재 환율)
@st.cache_data(ttl=3600)  # 데이터를 1시간 동안 캐싱
def fetch_usd_to_krw_rate():
    # open.er-api.com으로 변경 (기존 api.exchangerate-api.com/v4/latest/USD는 일일 제한 우려)
    url = "https://open.er-api.com/v6/latest/USD" 
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data["rates"]["KRW"]

# 업비트에서 USDT/KRW 데이터를 가져오는 함수
@st.cache_data(ttl=3600)  # 데이터를 1시간 동안 캐싱
def fetch_usdt_krw_upbit():
    url = "https://api.upbit.com/v1/candles/days"
    params = {"market": "KRW-USDT", "count": 100}  # 100일 데이터만 요청
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    # 최신 데이터가 맨 뒤로 오도록 순서를 뒤집음
    data.reverse()
    return [{"date": item["candle_date_time_utc"], "price": item["trade_price"]} for item in data]

# 'USDT 가격변화' 체크박스
show_usdt_chart = st.checkbox("USDT 가격변화")

if show_usdt_chart:
    try:
        # CoinGecko에서 USDT/USD 데이터 가져오기
        prices_usdt_usd = fetch_usdt_prices_cg()
        df_usdt_usd = pd.DataFrame(prices_usdt_usd, columns=["timestamp", "price"])
        df_usdt_usd["date"] = pd.to_datetime(df_usdt_usd["timestamp"], unit="ms").dt.normalize()
        df_usdt_usd = df_usdt_usd[["date", "price"]].set_index("date").rename(columns={"price": "USDT_CG_USD_Price"})

        # USD to KRW 환율 (현재 환율, 수평선용)
        usd_to_krw_latest = fetch_usd_to_krw_rate()

        # 업비트에서 USDT/KRW 데이터 가져오기
        usdt_krw_data = fetch_usdt_krw_upbit()
        df_usdt_krw = pd.DataFrame(usdt_krw_data)
        df_usdt_krw["date"] = pd.to_datetime(df_usdt_krw["date"]).dt.normalize()
        df_usdt_krw.rename(columns={"price": "price_krw"}, inplace=True)
        df_usdt_krw = df_usdt_krw.set_index("date")
        
        # USD/KRW 역사적 환율 데이터 가져오기
        df_fx_krw = fetch_historical_usd_krw_rate()

        # 데이터 병합 (날짜를 기준으로)
        df_combined = df_usdt_usd.merge(df_usdt_krw, left_index=True, right_index=True, how='inner')
        df_combined = df_combined.merge(df_fx_krw, left_index=True, right_index=True, how='inner')
        
        # CoinGecko USDT 가격을 역사적 FX 환율로 변환 (참고용)
        df_combined["USDT_CG_KRW_Converted"] = df_combined["USDT_CG_USD_Price"] * df_combined["FX_KRW_Price"]

        
        # KRW 기준 차트 생성
        st.write("100일 동안의 USDT 및 USD 가격 변화 (KRW 기준)")
        fig_krw, ax_krw = plt.subplots(figsize=(10, 6))
        
        # 1. 업비트 USDT/KRW 가격 (파란색)
        ax_krw.plot(df_combined.index, df_combined["price_krw"], label="USDT/KRW Price (Upbit)", color="blue")
        
        # 2. USD/KRW 역사적 환율 (빨간색) <--- 사용자 요청 추가 차트
        ax_krw.plot(df_combined.index, df_combined["FX_KRW_Price"], label="USD/KRW Historical Exchange Rate (FX Market)", color="red")
        
        # 3. CoinGecko USDT 환율 변환 (주황색 점선, 보조선)
        ax_krw.plot(df_combined.index, df_combined["USDT_CG_KRW_Converted"], label="USDT/USD (CG) x FX Rate (Reference)", color="orange", linestyle='--')
        
        # 4. 현재 외환 시장 환율 수평선
        ax_krw.axhline(y=usd_to_krw_latest, color="green", linestyle=":", label=f"Latest FX Rate ({usd_to_krw_latest:,.0f} KRW)")
        
        ax_krw.set_title("USDT/KRW vs USD/KRW Price Over 100 Days")
        ax_krw.set_xlabel("Date")
        ax_krw.set_ylabel("Price (KRW)")
        ax_krw.legend()
        ax_krw.grid()
        plt.xticks(rotation=45)
        st.pyplot(fig_krw)

        # 현재 가격 차이 출력 (USDT/KRW vs. 실제 USD/KRW 환율)
        latest_upbit_krw = df_combined["price_krw"].iloc[-1]
        latest_usd_fx = df_combined["FX_KRW_Price"].iloc[-1]
        
        premium_krw = latest_upbit_krw - latest_usd_fx
        premium_percent = (premium_krw / latest_usd_fx) * 100
        
        st.markdown(
            f"""
            <p style='font-size: 16px;'>
                <strong>[최신 데이터]</strong><br>
                업비트 USDT/KRW 가격: {latest_upbit_krw:,.2f} KRW<br>
                실제 USD/KRW 외환시장 환율: {latest_usd_fx:,.2f} KRW<br>
                <span style='color: {'red' if premium_percent >= 0 else 'blue'};'>USDT (업비트) 프리미엄/디스카운트: {premium_percent:.2f}%</span>
            </p>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"USDT/USD 데이터를 가져오는 중 오류가 발생했습니다: {e}")
