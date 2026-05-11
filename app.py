import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Terminal Buy Side PRO",
    layout="wide"
)

# =========================================================
# FUNÇÕES INDICADORES
# =========================================================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def stochastic(df, k_period=14, d_period=3):
    low_min = df["Low"].rolling(window=k_period).min()
    high_max = df["High"].rolling(window=k_period).max()

    k = 100 * ((df["Close"] - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()

    return k, d

def psar(df, af=0.02, af_max=0.2):
    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values

    length = len(df)

    psar = close.copy()
    bull = True

    hp = high[0]
    lp = low[0]

    accel = af

    for i in range(2, length):

        prev_psar = psar[i - 1]

        if bull:
            psar[i] = prev_psar + accel * (hp - prev_psar)
        else:
            psar[i] = prev_psar + accel * (lp - prev_psar)

        reverse = False

        if bull:
            if low[i] < psar[i]:
                bull = False
                reverse = True
                psar[i] = hp
                lp = low[i]
                accel = af
        else:
            if high[i] > psar[i]:
                bull = True
                reverse = True
                psar[i] = lp
                hp = high[i]
                accel = af

        if not reverse:
            if bull:
                if high[i] > hp:
                    hp = high[i]
                    accel = min(accel + af, af_max)

                psar[i] = min(psar[i], low[i - 1], low[i - 2])

            else:
                if low[i] < lp:
                    lp = low[i]
                    accel = min(accel + af, af_max)

                psar[i] = max(psar[i], high[i - 1], high[i - 2])

    return pd.Series(psar, index=df.index)

# =========================================================
# DOWNLOAD DADOS
# =========================================================

@st.cache_data(ttl=3600)
def carregar_dados(ticker):

    try:
        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df.empty or len(df) < 100:
            return None

        return df

    except:
        return None

# =========================================================
# CALCULAR SETUP
# =========================================================

def calcular_setup(df):

    # EMA 69
    df["EMA69"] = ema(df["Close"], 69)

    # PSAR
    df["PSAR"] = psar(df)

    # Tendência PSAR
    df["PSAR_BULL"] = df["PSAR"] < df["Close"]

    # Z-SCORE
    periodo = 20

    media = df["Close"].rolling(periodo).mean()
    desvio = df["Close"].rolling(periodo).std()

    df["ZScore"] = (df["Close"] - media) / desvio

    # STOCH
    k, d = stochastic(df)

    df["STOCH_K"] = k
    df["STOCH_D"] = d

    # Distância EMA
    df["DistEMA"] = ((df["Close"] / df["EMA69"]) - 1) * 100

    return df

# =========================================================
# INTERFACE
# =========================================================

st.title("🚀 Terminal Buy Side PRO")
st.markdown(
    """
Scanner Buy Side:
- Preço acima da EMA 69
- PSAR abaixo do preço
- Ranking probabilístico via Z-Score
- Estocástico para timing
"""
)

# =========================================================
# LISTA COMPLETA DE ATIVOS
# =========================================================

ativos_raw = [

    # Bancos
    "BBAS3.SA","ITUB4.SA","ITSA4.SA","BBDC4.SA","BBDC3.SA","SANB11.SA",
    "BPAC11.SA","BRSR6.SA","BMGB4.SA","PSSA3.SA","IRBR3.SA",

    # Energia / Petróleo
    "PETR4.SA","PETR3.SA","PRIO3.SA","RECV3.SA","RRRP3.SA",
    "EQTL3.SA","TAEE11.SA","CPLE6.SA","CMIG4.SA","TRPL4.SA",
    "EGIE3.SA","CPFE3.SA","ELET3.SA","ELET6.SA","ALUP11.SA",
    "NEOE3.SA","ENGI11.SA","CSMG3.SA","SBSP3.SA","SAPR11.SA",
    "SAPR4.SA",

    # Commodities / Industrial
    "VALE3.SA","GGBR4.SA","CSNA3.SA","USIM5.SA","SUZB3.SA",
    "KLBN11.SA","WEGE3.SA","RAIL3.SA","POMO4.SA","KEPL3.SA",

    # Consumo
    "ABEV3.SA","VIVT3.SA","TIMS3.SA","MULT3.SA","ALOS3.SA",
    "ODPV3.SA","RDOR3.SA","CYRE3.SA","TOTS3.SA","JBSS3.SA",

    # ETFs
    "BOVA11.SA","SMAL11.SA","IVVB11.SA","DIVO11.SA",
    "XFIX11.SA","GOLD11.SA","PIBB11.SA","ECOO11.SA",
    "MATB11.SA","BOVV11.SA","FIND11.SA","SPXI11.SA",
    "NASD11.SA","ACWI11.SA","WRLD11.SA","EURP11.SA",
    "TECK11.SA","HASH11.SA","ETHE11.SA","QBTC11.SA",

    # FIIs
    "HGLG11.SA","XPLG11.SA","VILG11.SA","BRCO11.SA",
    "BTLG11.SA","XPML11.SA","VISC11.SA","HSML11.SA",
    "MALL11.SA","KNRI11.SA","JSRE11.SA","PVBI11.SA",
    "HGRE11.SA","MXRF11.SA","KNCR11.SA","KNIP11.SA",
    "CPTS11.SA","IRDM11.SA","TGAR11.SA","TRXF11.SA",
    "HGRU11.SA","ALZR11.SA","XPCA11.SA","VGIA11.SA",
    "RBRR11.SA","KNSC11.SA","HGCR11.SA","MCCI11.SA",
    "RECR11.SA","VRTA11.SA","BCFF11.SA","HFOF11.SA",
    "XPSF11.SA","RBRP11.SA","RBRF11.SA","RZTR11.SA",
    "RURA11.SA","VGIR11.SA","CVBI11.SA","UTLL11.SA",
    "GGRC11.SA","AUVP11.SA","GARE11.SA",

    # BDRs
    "AAPL34.SA","MSFT34.SA","GOGL34.SA","AMZO34.SA",
    "META34.SA","NVDC34.SA","JPMC34.SA","DISB34.SA",
    "SBUX34.SA","TSLA34.SA","NFLX34.SA","MCDC34.SA",
    "P1DD34.SA","BERK34.SA","PFIZ34.SA","N1KE34.SA",
    "COCA34.SA","WALM34.SA","BOAC34.SA","PEPB34.SA"
]

lista_ativos = sorted(list(set(ativos_raw)))

# =========================================================
# BOTÃO SCAN
# =========================================================

if st.button("🔍 ESCANEAR MERCADO"):

    resultados = []

    barra = st.progress(0)

    total = len(lista_ativos)

    for i, ticker in enumerate(lista_ativos):

        df = carregar_dados(ticker)

        if df is not None:

            try:

                df = calcular_setup(df)

                ultimo = df.iloc[-1]
                anterior = df.iloc[-2]

                preco = float(ultimo["Close"])
                ema69 = float(ultimo["EMA69"])
                psar_val = float(ultimo["PSAR"])

                zscore = float(ultimo["ZScore"])
                stoch_k = float(ultimo["STOCH_K"])
                dist_ema = float(ultimo["DistEMA"])

                # FILTRO BUY SIDE
                if preco > ema69 and psar_val < preco:

                    sinal_novo = (
                        anterior["PSAR"] > anterior["Close"]
                        and ultimo["PSAR"] < ultimo["Close"]
                    )

                    status = (
                        "🔥 SINAL NOVO"
                        if sinal_novo
                        else "Alta Mantida"
                    )

                    resultados.append({
                        "Ticker": ticker,
                        "Preço": round(preco, 2),
                        "Z-Score": round(zscore, 2),
                        "Status": status,
                        "Stoch K": round(stoch_k, 2),
                        "Dist EMA69 %": round(dist_ema, 2)
                    })

            except:
                pass

        barra.progress((i + 1) / total)

    # =====================================================
    # RESULTADOS
    # =====================================================

    if len(resultados) > 0:

        df_resultado = pd.DataFrame(resultados)

        prioridade = {
            "🔥 SINAL NOVO": 0,
            "Alta Mantida": 1
        }

        df_resultado["Prioridade"] = df_resultado["Status"].map(prioridade)

        df_resultado = df_resultado.sort_values(
            by=["Prioridade", "Z-Score"],
            ascending=[True, True]
        )

        df_resultado = df_resultado.drop(columns=["Prioridade"])

        st.success(f"{len(df_resultado)} ativos encontrados.")

        st.dataframe(
            df_resultado,
            use_container_width=True,
            height=700
        )

        # =================================================
        # GRÁFICO
        # =================================================

        fig = px.scatter(
            df_resultado,
            x="Z-Score",
            y="Dist EMA69 %",
            color="Status",
            hover_data=["Ticker"],
            title="Mapa Probabilístico"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.warning(
            "Nenhum ativo encontrado no setup Buy Side."
        )
