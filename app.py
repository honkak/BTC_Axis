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
import time
import numpy as np # numpy import 추가

# 서비스 제목 입력
st.markdown("<h2 style='font-size: 30px; text-align: center;'>다빈치 BITCOIN 분석 서비스</h2>", unsafe_allow_html=True)

# 날짜 입력 (조회 시작일과 종료일을 같은 행에 배치)
col_start_date, col_end_date = st.columns(2)

with col_start_date:
    start_date = st.date_input(
        "조회 시작일을 선택해 주세요",
        datetime.datetime(2025, 1, 1)
    )

with col_end_date:
    end_date = st.date_input(
        "조회 종료일을 선택해 주세요",
        datetime.datetime.now()
    )

# 시작 날짜와 종료 날짜 비교
if start_date > end_date:
    st.warning("시작일이 종료일보다 더 늦습니다. 날짜를 자동으로 맞바꿔 반영합니다.")
    start_date, end_date = end_date, start_date # 날짜를 바꿈

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
            start_date = upbit_start_date
            st.warning("업비트 가격을 가져오므로 조회 시작일을 2017년 10월 24일 서비스 개시일로 자동 변경합니다.")

        # 현재 날짜 가져오기
        today = datetime.date.today()

        # 조회 종료일이 미래인 경우 현재 날짜로 변경
        if end_date > today:
            st.warning("조회 종료일이 미래 날짜이므로 종료일을 오늘로 설정합니다.")
            end_date = today

        # 데이터 조회를 위한 타임스탬프 변환
        since = int(datetime.datetime.combine(start_date, datetime.datetime.min.time()).timestamp() * 1000)
        end_timestamp = int(datetime.datetime.combine(end_date, datetime.datetime.max.time()).timestamp() * 1000)

        # 데이터 조회
        ohlcv = []
        from_time = since
        while True:
            # API 호출 간격 확보 (선택적)
            # time.sleep(0.1)
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
                # 종료일 문구 출력 (오늘로 고정되었음을 알림)
                st.write(f"BTC Price (KRW) on {end_date}: {end_price:,.0f} KRW")
            else:
                st.warning(f"No closing price data available for {end_date}.")

            # 꺾은선 차트 생성
            if not df.empty:
                st.write(f"BTC Price in KRW: {start_date} to {end_date}")
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
    # until은 datetime 객체이므로 timestamp()로 변환 필요
    until_ts_ms = until.timestamp() * 1000
    
    # since는 int(시작 타임스탬프)
    current_since = since
    
    while current_since < until_ts_ms:
        try:
            # API 호출 전에 지연 시간 추가
            time.sleep(0.1) 
            
            # API 호출
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, current_since, limit=200)  # 최대 200개
            
            if not ohlcv:
                break
            
            # 조회 기간을 초과하는 데이터는 제거
            ohlcv = [data for data in ohlcv if data[0] <= until_ts_ms]
            if not ohlcv:
                break

            all_data.extend(ohlcv)
            current_since = ohlcv[-1][0] + 1  # 마지막 데이터의 타임스탬프를 기준으로 다음 데이터 요청
        except Exception as e:
            # 오류 발생 시 경고 출력 및 루프 중단
            st.warning(f"Error fetching {symbol}: {e}. Stopping data fetch for this symbol.")
            break
            
    return all_data

if fixed_ratio:
    # 코인/종목 코드 입력 필드 (디폴트 값 ETH, SOL 반영)
    col_code1, col_code2, col_code3 = st.columns(3)
    with col_code1:
        code1 = st.text_input('자산코드 1', value='ETH', placeholder='코드입력 - (예시)ETH')
    with col_code2:
        code2 = st.text_input('자산코드 2', value='SOL', placeholder='코드입력 - (예시)SOL')
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
    
    # ccxt API 호출을 위한 타임스탬프
    start_timestamp_ms = int(start_datetime.timestamp() * 1000)
    
    # 체크박스
    col_cb1, col_cb2, col_cb3 = st.columns(3)
    with col_cb1:
        add_usd = st.checkbox("USD/BTC(달러)")
    with col_cb2:
        add_krw = st.checkbox("KRW/BTC(원화)")
    with col_cb3:
        # (예정) 텍스트 제거 및 기능 구현 완료
        add_apartment = st.checkbox("SPY/BTC(S&P500)")

    # 기준시점 수익률 비교 차트 생성
    ohlcv_data = {}
    
    # 1. 코인/BTC 데이터 조회
    if codes:
        for code in codes:
            try:
                pair = f"{code}/BTC"
                # 전체 데이터 가져오기
                ohlcv = fetch_full_ohlcv(upbit, pair, "1d", start_timestamp_ms, end_datetime)
                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["Date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.normalize()
                df.set_index("Date", inplace=True)

                # 기간 필터링
                df = df.loc[start_datetime:end_datetime].dropna()
                ohlcv_data[f"{code}/BTC"] = df["close"]
            except Exception as e:
                st.warning(f"[{code}/BTC] 데이터를 가져오는 중 문제가 발생했습니다: {e}")

    # 2. BTC/USDT 데이터 미리 가져오기 (USD/BTC 및 SPY/BTC에서 재사용)
    btc_usdt_data = None
    if add_usd or add_apartment:
        try:
            btc_usdt_ohlcv = fetch_full_ohlcv(upbit, "BTC/USDT", "1d", start_timestamp_ms, end_datetime)
            df_btc_usdt = pd.DataFrame(btc_usdt_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df_btc_usdt["Date"] = pd.to_datetime(df_btc_usdt["timestamp"], unit="ms").dt.normalize()
            df_btc_usdt.set_index("Date", inplace=True)
            btc_usdt_data = df_btc_usdt.loc[start_datetime:end_datetime].dropna()
        except Exception as e:
            st.warning(f"BTC/USDT (USD 기준) 데이터를 가져오는 중 문제가 발생했습니다: {e}")
            
    # 3. USD/BTC 추가
    if add_usd and btc_usdt_data is not None:
        try:
            # USD/BTC = 1 / BTC/USDT (Close)
            ohlcv_data["USD/BTC"] = 1 / btc_usdt_data["close"]
        except Exception as e:
            st.warning(f"USD/BTC 비율을 계산하는 중 문제가 발생했습니다: {e}")

    # 4. KRW/BTC 추가
    if add_krw:
        try:
            btc_krw_ohlcv = fetch_full_ohlcv(upbit, "BTC/KRW", "1d", start_timestamp_ms, end_datetime)
            df_btc_krw = pd.DataFrame(btc_krw_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df_btc_krw["Date"] = pd.to_datetime(df_btc_krw["timestamp"], unit="ms").dt.normalize()
            df_btc_krw.set_index("Date", inplace=True)
            df_btc_krw = df_btc_krw.loc[start_datetime:end_datetime].dropna()
            
            # KRW/BTC = 1 / BTC/KRW (Close)
            ohlcv_data["KRW/BTC"] = 1 / df_btc_krw["close"]
        except Exception as e:
            st.warning(f"KRW/BTC 데이터를 가져오는 중 문제가 발생했습니다: {e}")

    # 5. SPY/BTC 추가 (S&P 500 대비 BTC) - 구현된 기능
    if add_apartment:
        if btc_usdt_data is not None:
            try:
                # 5-1. SPY (S&P 500 ETF) 가격 데이터 (USD)
                spy_df = fdr.DataReader('SPY', start=start_date, end=end_date)
                spy_close = spy_df['Close'].rename('SPY_Close').asfreq('D') # 일별 빈도로 변경

                # 5-2. BTC/USDT (USD) 가격
                btc_usdt_close = btc_usdt_data["close"].rename('BTC_USDT_Close').asfreq('D')

                # 5-3. 날짜 기준 병합 및 SPY/BTC 비율 계산
                ratio_df = pd.concat([spy_close, btc_usdt_close], axis=1).dropna()
                # SPY 가격을 BTC 가격으로 나눔 (SPY 1주를 사는데 필요한 BTC 수량의 역수 개념)
                ratio_df['SPY/BTC'] = ratio_df['SPY_Close'] / ratio_df['BTC_USDT_Close']

                # 5-4. 최종 데이터 추가
                ohlcv_data["SPY/BTC"] = ratio_df['SPY/BTC']
            except Exception as e:
                st.warning(f"SPY/BTC (S&P500) 데이터를 가져오거나 계산하는 중 문제가 발생했습니다: {e}")
        else:
            st.warning("SPY/BTC 데이터를 계산하려면 BTC/USDT 데이터가 필요합니다. 데이터를 불러올 수 없습니다.")


    # 최종 차트 생성
    if ohlcv_data:
        df_combined = pd.DataFrame(ohlcv_data).dropna() # NaN 값 제거
        
        if not df_combined.empty:
            # 기준 시점(첫 번째 유효한 값)으로 정규화
            first_valid_row = df_combined.iloc[0]
            # 0으로 나누는 오류 방지: 0인 경우 해당 컬럼의 변화율 계산에서 제외하거나 경고
            safe_first_valid_row = first_valid_row.replace(0, np.nan) 
            df_normalized = df_combined.div(safe_first_valid_row) * 100 - 100
            
            # 모든 값이 NaN인 컬럼 제거
            df_normalized = df_normalized.dropna(axis=1, how='all')


            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_ylabel("Percentage Change (%)", fontsize=12)

            # 0%에 붉은 점선 추가
            ax.axhline(y=0, color="red", linestyle="--", linewidth=1, label="0% Baseline")

            for column in df_normalized.columns:
                ax.plot(df_normalized.index, df_normalized[column], label=column)

            ax.set_title(f"Asset Performance Relative to BTC ({start_date} to {end_date})", fontsize=16)
            ax.set_xlabel("Date", fontsize=12)
            ax.legend()
            ax.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning("선택한 기간에 유효한 데이터가 없어 차트를 생성할 수 없습니다.")
    else:
        st.warning("조회결과가 없습니다. 코드를 입력하거나 자산을 선택해주세요.")

    #######################

# 주어진 코인 이름과 코인 코드 (생략 없이 유지)
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


######################################

# 수평선 추가
st.markdown("---")

#####################################
#시가총액 비율 기능

# 'BTC 시가총액 비율' 체크박스
show_market_cap_chart = st.checkbox("Bitcoin 시가총액 비율")

if show_market_cap_chart:
    cg = CoinGeckoAPI()

    try:
        # 강제로 현재 시점 기준으로 365일 전부터 데이터 설정
        end_date_cap = datetime.datetime.now()
        start_date_cap = end_date_cap - datetime.timedelta(days=365)

        # 1. 상위 암호화폐 시가총액 가져오기 (최신 데이터) - API 호출 1
        time.sleep(1) # API 지연 추가
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
        
        # 금(Gold) 시가총액 정의 및 가져오기 (사용자 요청에 따라 고정값으로 하드코딩)
        # 1. 고정값 설정 (실제 금 시가총액 추정치: 약 $15.8T USD)
        global_gold_market_cap = 15800000000000
        gold_asset_name = "Global Physical Gold Market Cap (Fixed Estimate)"
        
        # BTC 시가총액 vs. 금 시가총액 비율 계산
        btc_vs_gold_ratio = (btc_market_cap / global_gold_market_cap) * 100

        # 데이터 검증 및 출력
        st.write(f"Global Crypto Market Cap (USD): {int(global_market_cap):,} (USD)")
        st.write(f"Bitcoin Market Cap (USD): {int(btc_market_cap):,} (USD)")
        
        # Bitcoin Dominance: 붉은색으로 출력 요청 반영 (1차 차트 위의 도미넌스)
        st.markdown(
            f"<p style='font-size: 16px;'><span style='color: red;'>Bitcoin Dominance(vs other Coin): <b>{btc_dominance:.2f}%</b></span></p>",
            unsafe_allow_html=True
        )

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

        # 2. 365일 전부터 현재까지 BTC 도미넌스 데이터 가져오기 - API 호출 2
        start_timestamp = int(start_date_cap.timestamp())
        end_timestamp = int(end_date_cap.timestamp())
        
        time.sleep(1) # API 지연 추가
        # Coingecko API는 도미넌스 데이터를 직접 제공하지 않고 BTC 마켓캡과 Total 마켓캡을 제공
        # 여기서는 BTC 마켓캡 데이터를 가져와서 (global_market_cap이 고정되지 않았다는 가정 하에) 추세만 확인
        # 현재 코드의 로직을 유지하며, global_market_cap이 과거 데이터에 따라 변동될 수 있음을 유의
        btc_dominance_data = cg.get_coin_market_chart_range_by_id(
            id='bitcoin',
            vs_currency='usd',
            from_timestamp=start_timestamp,
            to_timestamp=end_timestamp
        )

        # 도미넌스 데이터 처리 
        # CoinGecko는 BTC 도미넌스 자체를 주지 않으므로, 이 데이터는 실제 BTC 마켓캡 추이입니다.
        # 그러나 기존 코드에서 'market_caps'를 사용했으므로 이를 BTC 마켓캡 트렌드로 사용
        dominance_dates = [datetime.datetime.fromtimestamp(price[0] / 1000) for price in btc_dominance_data['market_caps']]
        
        # 실제 CoinGecko API로 과거의 전체 마켓캡을 가져오지 못하므로, 
        # 기존 로직 대신, BTC 마켓캡이 어떻게 변했는지 보여주는 방식으로 수정합니다.
        # 즉, 이는 도미넌스가 아니라 BTC 마켓캡의 변화율입니다.
        df_market_cap = pd.DataFrame(btc_dominance_data['market_caps'], columns=['timestamp', 'market_cap'])
        df_market_cap['Date'] = pd.to_datetime(df_market_cap['timestamp'], unit='ms').dt.normalize()
        df_market_cap.set_index('Date', inplace=True)
        
        # 첫날을 기준으로 변화율 (%) 계산
        initial_cap = df_market_cap.iloc[0]['market_cap']
        df_market_cap['Market Cap Change (%)'] = (df_market_cap['market_cap'] / initial_cap) * 100 - 100

        # 강제 기간: 365일 전부터 현재 날짜까지
        start_date_str = start_date_cap.strftime("%Y-%m-%d")
        end_date_str = end_date_cap.strftime("%Y-%m-%d")

        
        # 꺾은선 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df_market_cap.index, df_market_cap["Market Cap Change (%)"], label="BTC Market Cap Change (%)", color="green")
        ax.axhline(0, color='red', linestyle='--', linewidth=0.8) # 0% 기준선 추가
        ax.set_title(f"BTC Market Cap Change Over Time ({start_date_str} to {end_date_str})", fontsize=title_font_size)
        ax.set_xlabel("Date", fontsize=axis_font_size)
        ax.set_ylabel("BTC Market Cap Change (%)", fontsize=axis_font_size)
        ax.grid(True)
        ax.legend(fontsize=font_size)
        plt.xticks(rotation=45, fontsize=axis_font_size)  # X축 날짜를 대각선으로 표시
        st.pyplot(fig) # <<-- 꺾은선 그래프 출력 (두 번째 차트)

        
        # [수정된 위치]: 꺾은선 그래프 (두 번째 차트) 바로 아래로 이동
        # [추가] 글로벌 Gold 시가총액 출력 (고정값의 이름 사용)
        st.write(f"{gold_asset_name} (USD): {int(global_gold_market_cap):,} (USD)")
        
        # [수정] BTC vs Gold 시가총액 비율을 'Bitcoin Dominance (vs Gold): X%' 형식으로 붉은색 출력
        st.markdown(
            f"<p style='font-size: 16px; color: red;'>Bitcoin Dominance (vs Gold): <b>{btc_vs_gold_ratio:.2f}%</b></p>",
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"암호화폐 데이터를 불러오는 데 실패했습니다: {e}")

######################################

# 수평선 추가
st.markdown("---")

#####################################
# '김치프리미엄' 체크박스 추가
show_kimchi_premium = st.checkbox("김치프리미엄 보기")


# 환율 가져오기 함수 (현재 환율)
@st.cache_data(ttl=3600)
def get_exchange_rate():
    url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data['rates']['KRW']


if show_kimchi_premium:
    st.write("100일 동안의 Bitcoin 김치프리미엄 변화추이") # 체크박스 클릭 시 텍스트 표시
    try:
        
        # 업비트와 코인게코 데이터를 사용한 김치프리미엄 계산
        def fetch_historical_data():
            upbit = ccxt.upbit()
            cg = CoinGeckoAPI()

            # 최근 100일 기준으로 설정
            end_date_hist = datetime.datetime.now()
            start_date_hist = end_date_hist - datetime.timedelta(days=100)

            # 업비트 데이터 가져오기 (ccxt는 자체적으로 호출 지연 처리가 있을 수 있으나, 안전을 위해 time.sleep 추가는 생략)
            since = int(start_date_hist.timestamp() * 1000)
            upbit_data = upbit.fetch_ohlcv("BTC/KRW", timeframe="1d", since=since)
            upbit_df = pd.DataFrame(upbit_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            upbit_df["Date"] = pd.to_datetime(upbit_df["timestamp"], unit="ms").dt.normalize()
            upbit_df.set_index("Date", inplace=True)

            # 코인게코 데이터를 가져오기 (API 호출 전에 지연 추가)
            time.sleep(1)
            btc_market_data = cg.get_coin_market_chart_range_by_id(
                id="bitcoin",
                vs_currency="usd",
                from_timestamp=int(start_date_hist.timestamp()),
                to_timestamp=int(end_date_hist.timestamp())
            )
            
            # CoinGecko 데이터는 날짜별 [timestamp, price] 형태로 되어 있음
            cg_df = pd.DataFrame(btc_market_data["prices"], columns=["timestamp", "price_usd"])
            cg_df["Date"] = pd.to_datetime(cg_df["timestamp"], unit="ms").dt.normalize()
            cg_df.set_index("Date", inplace=True)

            # 환율 적용 (현재 환율 사용)
            exchange_rate = get_exchange_rate()
            # 코인게코 USD 가격을 현재 환율로 KRW로 변환
            cg_df["Close (KRW)"] = cg_df["price_usd"] * exchange_rate

            # 김치프리미엄 계산
            df = pd.DataFrame({
                "Upbit (KRW)": upbit_df["close"],
                "CoinGecko (KRW)": cg_df["Close (KRW)"]
            })
            # 날짜를 기준으로 병합(join) 수행
            df = df.dropna()
            
            # 김프 계산
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
        
        st.pyplot(fig)
        
        # 현재 김치프리미엄 값 출력 (수정된 부분: 라벨과 값 모두 붉은색 적용)
        if current_premium is not None:
            st.markdown(
                f"<p style='font-size: 16px;'><span style='color: red;'>현재 Bitcoin 김치 프리미엄: <b>{current_premium:.2f}%</b></span></p>",
                unsafe_allow_html=True
            )
    except Exception as e:
        st.error(f"김치프리미엄 데이터를 가져오거나 시각화하는 데 실패했습니다: {e}")


#############################

# 수평선 추가
st.markdown("---")

#####################################
# 'USDT 가격변화' 기능 구현
        
# CoinGecko에서 USDT/USD 데이터를 가져오는 함수 (100일)
@st.cache_data(ttl=3600)  # 데이터를 1시간 동안 캐싱
def fetch_usdt_prices_cg():
    # CoinGecko API 호출 전에 지연 시간 추가
    time.sleep(1) 
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
    df_fx = fdr.DataReader('USD/KRW', start=start_date_fx, end=end_date_fx)
    
    # 인덱스 이름 'date'로 정규화 및 날짜만 남기기
    df_fx.index = df_fx.index.normalize()
    df_fx.index.name = 'date'
    
    # 'Close' 컬럼만 사용 (종가)
    return df_fx['Close'].rename('FX_KRW_Price')


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
        # CoinGecko에서 USDT/USD 데이터 가져오기 (데이터는 여전히 필요)
        prices_usdt_usd = fetch_usdt_prices_cg()
        df_usdt_usd = pd.DataFrame(prices_usdt_usd, columns=["timestamp", "price"])
        df_usdt_usd["date"] = pd.to_datetime(df_usdt_usd["timestamp"], unit="ms").dt.normalize()
        df_usdt_usd = df_usdt_usd[["date", "price"]].set_index("date").rename(columns={"price": "USDT_CG_USD_Price"})

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
        
        # KRW 기준 차트 생성
        st.write("100일 동안의 USDT 및 USD 가격 변화 (KRW 기준)")
        fig_krw, ax_krw = plt.subplots(figsize=(10, 6))
        
        # 1. 업비트 USDT/KRW 가격 (파란색)
        ax_krw.plot(df_combined.index, df_combined["price_krw"], label="USDT/KRW Price (Upbit)", color="blue")
        
        # 2. USD/KRW 역사적 환율 (빨간색)  
        ax_krw.plot(df_combined.index, df_combined["FX_KRW_Price"], label="USD/KRW Historical Exchange Rate (FX Market)", color="red")
        
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


#####################################

