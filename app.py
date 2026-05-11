# =========================================================
# SAR69 PROBABILÍSTICO PROFISSIONAL
# Compatível com Streamlit Cloud Python 3.14
# SEM pandas-ta
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="SAR69 PRO",
    layout="wide"
)

SENHA = "LUCRO6"

# =========================================================
# LOGIN
# =========================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🔒 SAR69 PRO")

    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        if senha == SENHA:
            st.session_state.logado = True
            st.rerun()

        else:
            st.error("Senha incorreta")

    st.stop()

# =========================================================
# LISTA OFICIAL DE ATIVOS
# =========================================================

ATIVOS = [

    # Bancos
    "BBAS3.SA","ITUB4.SA","ITSA4.SA","BBDC4.SA","BBDC3.SA","SANB11.SA",
    "BPAC11.SA","BRSR6.SA",

    # Energia / Elétricas
    "TAEE11.SA","TRPL4.SA","CMIG4.SA","CPLE6.SA","CPFE3.SA","EQTL3.SA",
    "ALUP11.SA","NEOE3.SA","ENGI11.SA","EGIE3.SA","CSMG3.SA","SBSP3.SA",
    "SAPR11.SA","SAPR4.SA",

    # Commodities
    "PETR4.SA","PETR3.SA","PRIO3.SA","VALE3.SA","SUZB3.SA","KLBN11.SA",
    "RECV3.SA",

    # Consumo / Serviços
    "WEGE3.SA","TOTS3.SA","VIVT3.SA","TIMS3.SA","ABEV3.SA","PSSA3.SA",
    "MULT3.SA","ALOS3.SA","ODPV3.SA","CYRE3.SA","KEPL3.SA","POMO4.SA",
    "RAIL3.SA","RDOR3.SA","JBSS3.SA",

    # ETFs
    "BOVA11.SA","SMAL11.SA","IVVB11.SA","DIVO11.SA","IEEX11.SA",

    # FIIs
    "HGLG11.SA","XPLG11.SA","VILG11.SA","BRCO11.SA","BTLG11.SA",
    "XPML11.SA","VISC11.SA","HSML11.SA","MALL11.SA","KNRI11.SA",
    "JSRE11.SA","PVBI11.SA","HGRE11.SA","MXRF11.SA","KNCR11.SA",
    "KNIP11.SA","CPTS11.SA","IRDM11.SA","TGAR11.SA","TRXF11.SA",
    "HGRU11.SA","ALZR11.SA","RBRR11.SA","KNSC11.SA","HGCR11.SA",
    "MCCI11.SA","RECR11.SA","VRTA11.SA","BCFF11.SA","HFOF11.SA",
    "XPSF11.SA","RBRP11.SA","RBRF11.SA","RZTR11.SA","RURA11.SA",
    "VGIR11.SA","CVBI11.SA","GGRC11.SA","AUVP11.SA","GARE11.SA",

    # BDRs
    "AAPL34.SA","MSFT34.SA","GOGL34.SA","AMZO34.SA","META34.SA",
    "NVDC34.SA","JPMC34.SA","DISB34.SA","SBUX34.SA"

]

# =========================================================
# INDICADORES
# =========================================================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def stochastic(df, k_period=14, d_period=3):

    low_min = df["Low"].rolling(k_period).min()
    high_max = df["High"].rolling(k_period).max()

    k = 100 * ((df["Close"] - low_min) / (high_max - low_min))
    d = k.rolling(d_period).mean()

    return k, d

def dmi(df, period=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = low.diff() * -1

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2], axis=1).max(axis=1)
    tr = pd.concat([tr, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()

    return plus_di, minus_di, adx, atr

# =========================================================
# SCORE
# =========================================================

def calcular_score(df):

    score = 0

    close = df["Close"].iloc[-1]
    ema69 = df["EMA69"].iloc[-1]

    # tendência principal
    if close > ema69:
        score += 30

    # força compradora
    if df["DI+"].iloc[-1] > df["DI-"].iloc[-1]:
        score += 25

    # tendência forte
    if df["ADX"].iloc[-1] > 20:
        score += 15

    # momentum
    if df["%K"].iloc[-1] > df["%D"].iloc[-1]:
        score += 10

    # volume
    vol_media = df["Volume"].rolling(20).mean().iloc[-1]

    if df["Volume"].iloc[-1] > vol_media:
        score += 10

    # candle positivo
    if df["Close"].iloc[-1] > df["Open"].iloc[-1]:
        score += 10

    return score

# =========================================================
# CLASSIFICAÇÃO
# =========================================================

def classificar(score):

    if score >= 90:
        return "EXTREMA"

    elif score >= 80:
        return "MUITO ALTA"

    elif score >= 70:
        return "ALTA"

    elif score >= 60:
        return "MÉDIA"

    return "BAIXA"

def probabilidade(score):

    if score >= 90:
        return 90

    elif score >= 80:
        return 82

    elif score >= 70:
        return 74

    elif score >= 60:
        return 66

    return 55

# =========================================================
# ATR POR CLASSE
# =========================================================

def atr_parametros(ativo):

    if "11.SA" in ativo:
        return 1.2, 1.0

    elif "34.SA" in ativo:
        return 2.5, 1.0

    else:
        return 2.0, 1.0

# =========================================================
# APP
# =========================================================

st.title("📈 SAR69 PROBABILÍSTICO")

st.markdown("Scanner diário com ranking probabilístico")

periodo = st.selectbox(
    "Histórico",
    ["1y", "2y", "5y", "10y"],
    index=2
)

resultados = []

barra = st.progress(0)

for i, ativo in enumerate(ATIVOS):

    try:

        df = yf.download(
            ativo,
            period=periodo,
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if len(df) < 120:
            continue

        df["EMA69"] = ema(df["Close"], 69)

        k, d = stochastic(df)

        df["%K"] = k
        df["%D"] = d

        plus_di, minus_di, adx, atr = dmi(df)

        df["DI+"] = plus_di
        df["DI-"] = minus_di
        df["ADX"] = adx
        df["ATR"] = atr

        ultimo = df.iloc[-1]

        # filtros obrigatórios

        tendencia = ultimo["Close"] > ultimo["EMA69"]
        dmi_ok = ultimo["DI+"] > ultimo["DI-"]

        if tendencia and dmi_ok:

            gain_mult, stop_mult = atr_parametros(ativo)

            entrada = ultimo["Close"]
            atr_valor = ultimo["ATR"]

            stop = entrada - (atr_valor * stop_mult)
            gain = entrada + (atr_valor * gain_mult)

            risco_pct = ((entrada - stop) / entrada) * 100
            gain_pct = ((gain - entrada) / entrada) * 100

            score = calcular_score(df)

            classe = classificar(score)

            prob = probabilidade(score)

            resultados.append({

                "Ativo": ativo.replace(".SA", ""),
                "Preço": round(entrada, 2),
                "ATR": round(atr_valor, 2),
                "Stop": round(stop, 2),
                "Gain": round(gain, 2),
                "Risco %": round(risco_pct, 2),
                "Gain %": round(gain_pct, 2),
                "ADX": round(ultimo["ADX"], 2),
                "Score": score,
                "Classificação": classe,
                "Probabilidade Gain %": prob

            })

    except:
        pass

    progresso = int((i + 1) / len(ATIVOS) * 100)

    barra.progress(progresso)

# =========================================================
# RESULTADOS
# =========================================================

if resultados:

    resultado_df = pd.DataFrame(resultados)

    resultado_df = resultado_df.sort_values(
        by="Probabilidade Gain %",
        ascending=False
    )

    st.success(f"{len(resultado_df)} ativos encontrados")

    st.dataframe(
        resultado_df,
        use_container_width=True,
        height=700
    )

    fig = px.bar(
        resultado_df.head(15),
        x="Ativo",
        y="Probabilidade Gain %"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.warning("Nenhum ativo encontrado")
