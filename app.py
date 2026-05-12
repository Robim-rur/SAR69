import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# =========================
# CONFIG
# =========================

ASSETS = [
    # Bancos
    "BBAS3.SA","ITUB4.SA","ITSA4.SA","BBDC4.SA","BBDC3.SA","SANB11.SA",
    "BPAC11.SA","BRSR6.SA",

    # Energia
    "TAEE11.SA","TRPL4.SA","CMIG4.SA","CPLE6.SA","CPFE3.SA","EQTL3.SA",
    "ALUP11.SA","NEOE3.SA","ENGI11.SA","EGIE3.SA","CSMG3.SA","SBSP3.SA",
    "SAPR11.SA","SAPR4.SA",

    # Commodities
    "PETR4.SA","PETR3.SA","PRIO3.SA","VALE3.SA","SUZB3.SA","KLBN11.SA",
    "RECV3.SA",

    # Consumo
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
    "MCCI11.SA","RECR11.SA","VRTA11.SA","HFOF11.SA","XPSF11.SA",
    "RBRP11.SA","RBRF11.SA","RZTR11.SA","RURA11.SA","VGIR11.SA",
    "GGRC11.SA","AUVP11.SA","GARE11.SA",

    # BDRs
    "AAPL34.SA","MSFT34.SA","GOGL34.SA","AMZO34.SA","META34.SA",
    "NVDC34.SA","JPMC34.SA","DISB34.SA","SBUX34.SA"
]

# =========================
# INDICADORES (SEM LIBS EXTERNAS)
# =========================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def atr(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    return tr.rolling(period).mean()

def stochastic(df, k_period=14):
    low_min = df["Low"].rolling(k_period).min()
    high_max = df["High"].rolling(k_period).max()
    k = 100 * (df["Close"] - low_min) / (high_max - low_min)
    return k

def adx(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = high.diff()
    minus_dm = low.diff().abs()

    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    atr_val = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr_val)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr_val)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(period).mean(), plus_di, minus_di

# =========================
# PROBABILIDADE
# =========================

def probability(row):
    trend = 1 if row["Close"] > row["EMA50"] else 0
    adx_score = min(row["ADX"] / 50, 1)
    stoch_score = 1 if row["Stoch"] < 80 else 0.5
    atr_score = min(row["ATR"] / row["Close"], 1)

    score = (
        0.35 * trend +
        0.25 * adx_score +
        0.20 * stoch_score +
        0.20 * atr_score
    )

    return 1 / (1 + np.exp(-8 * (score - 0.5)))

# =========================
# SCANNER
# =========================

def scan():
    results = []
    debug = {
        "total": 0,
        "valid": 0,
        "errors": 0
    }

    for asset in ASSETS:
        try:
            debug["total"] += 1

            df = yf.download(asset, period="6mo", interval="1d", progress=False)

            if df is None or len(df) < 50:
                continue

            df = df.dropna()

            close = df["Close"].astype(float)

            df["EMA50"] = ema(close, 50)
            df["ATR"] = atr(df, 14)
            df["Stoch"] = stochastic(df)
            df["ADX"], df["DI+"], df["DI-"] = adx(df)

            last = df.iloc[-1]

            if np.isnan(last["ATR"]) or np.isnan(last["ADX"]):
                continue

            if last["DI+"] < last["DI-"]:
                continue

            prob = probability(last)

            gain = last["Close"] + (last["ATR"] * 2)
            loss = last["Close"] - last["ATR"]

            results.append({
                "Ativo": asset,
                "Preço": last["Close"],
                "EMA50": last["EMA50"],
                "ATR": last["ATR"],
                "ADX": last["ADX"],
                "Stoch": last["Stoch"],
                "Gain": gain,
                "Loss": loss,
                "Probabilidade": prob
            })

            debug["valid"] += 1

        except Exception as e:
            debug["errors"] += 1

    df_res = pd.DataFrame(results)

    if not df_res.empty:
        df_res = df_res.sort_values("Probabilidade", ascending=False)

    return df_res, debug

# =========================
# STREAMLIT UI
# =========================

st.set_page_config(page_title="Scanner Probabilístico B3", layout="wide")

st.title("Scanner Probabilístico B3 (EMA50 + ATR + ADX + Stoch)")

if st.button("Rodar Scanner"):
    start = datetime.now()

    df, debug = scan()

    end = datetime.now()

    st.subheader("Resultados")

    if df.empty:
        st.warning("Nenhum ativo passou nos filtros.")
    else:
        st.dataframe(df)

    st.subheader("Debug")
    st.write(debug)

    st.success(f"Tempo: {(end-start).seconds} segundos")
