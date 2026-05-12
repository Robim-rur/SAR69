import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# =========================
# LISTA COMPLETA
# =========================

ASSETS = [
    "BBAS3.SA","ITUB4.SA","ITSA4.SA","BBDC4.SA","BBDC3.SA","SANB11.SA",
    "BPAC11.SA","BRSR6.SA","TAEE11.SA","TRPL4.SA","CMIG4.SA","CPLE6.SA",
    "CPFE3.SA","EQTL3.SA","ALUP11.SA","NEOE3.SA","ENGI11.SA","EGIE3.SA",
    "CSMG3.SA","SBSP3.SA","SAPR11.SA","SAPR4.SA","PETR4.SA","PETR3.SA",
    "PRIO3.SA","VALE3.SA","SUZB3.SA","KLBN11.SA","RECV3.SA","WEGE3.SA",
    "TOTS3.SA","VIVT3.SA","TIMS3.SA","ABEV3.SA","PSSA3.SA","MULT3.SA",
    "ALOS3.SA","ODPV3.SA","CYRE3.SA","KEPL3.SA","POMO4.SA","RAIL3.SA",
    "RDOR3.SA","JBSS3.SA",
    "BOVA11.SA","SMAL11.SA","IVVB11.SA","DIVO11.SA","IEEX11.SA",
    "HGLG11.SA","XPLG11.SA","VILG11.SA","BRCO11.SA","BTLG11.SA",
    "XPML11.SA","VISC11.SA","HSML11.SA","MALL11.SA","KNRI11.SA",
    "JSRE11.SA","PVBI11.SA","HGRE11.SA","MXRF11.SA","KNCR11.SA",
    "KNIP11.SA","CPTS11.SA","IRDM11.SA","TGAR11.SA","TRXF11.SA",
    "HGRU11.SA","ALZR11.SA","RBRR11.SA","KNSC11.SA","HGCR11.SA",
    "MCCI11.SA","RECR11.SA","VRTA11.SA","HFOF11.SA","XPSF11.SA",
    "RBRP11.SA","RBRF11.SA","RZTR11.SA","RURA11.SA","VGIR11.SA",
    "GGRC11.SA","AUVP11.SA","GARE11.SA",
    "AAPL34.SA","MSFT34.SA","GOGL34.SA","AMZO34.SA","META34.SA",
    "NVDC34.SA","JPMC34.SA","DISB34.SA","SBUX34.SA"
]

# =========================
# INDICADORES ROBUSTOS
# =========================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def atr(df, period=14):
    high, low, close = df["High"], df["Low"], df["Close"]

    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    return tr.rolling(period).mean()

def stochastic(df, period=14):
    low_min = df["Low"].rolling(period).min()
    high_max = df["High"].rolling(period).max()

    denom = (high_max - low_min)
    denom = denom.replace(0, np.nan)

    return 100 * (df["Close"] - low_min) / denom

def adx(df, period=14):
    high, low, close = df["High"], df["Low"], df["Close"]

    up_move = high.diff()
    down_move = low.diff() * -1

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift())
    ], axis=1).max(axis=1)

    atr_val = tr.rolling(period).mean()

    plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / atr_val
    minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / atr_val

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(period).mean(), plus_di, minus_di

# =========================
# SCORE PROBABILÍSTICO
# =========================

def probability(row):
    trend = 1 if row["Close"] > row["EMA50"] else 0
    adx_score = min((row["ADX"] or 0) / 50, 1)
    stoch_score = 1 if row["Stoch"] < 80 else 0.5
    atr_score = min((row["ATR"] / row["Close"]), 1)

    score = (
        0.40 * trend +
        0.25 * adx_score +
        0.20 * stoch_score +
        0.15 * atr_score
    )

    return 1 / (1 + np.exp(-8 * (score - 0.5)))

# =========================
# SCANNER
# =========================

def scan():
    results = []
    debug = []

    for asset in ASSETS:
        try:
            df = yf.download(asset, period="6mo", interval="1d", progress=False)

            if df is None or len(df) < 60:
                debug.append((asset, "dados insuficientes"))
                continue

            df = df.dropna()

            close = df["Close"].astype(float)

            df["EMA50"] = ema(close, 50)
            df["ATR"] = atr(df, 14)
            df["Stoch"] = stochastic(df)
            df["ADX"], df["DI+"], df["DI-"] = adx(df)

            last = df.iloc[-1]

            if np.isnan(last["EMA50"]) or np.isnan(last["ATR"]):
                debug.append((asset, "NaN indicadores"))
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

        except Exception as e:
            debug.append((asset, str(e)))

    df_res = pd.DataFrame(results)

    if not df_res.empty:
        df_res = df_res.sort_values("Probabilidade", ascending=False)

    return df_res, debug

# =========================
# STREAMLIT UI
# =========================

st.set_page_config(layout="wide")
st.title("Scanner Probabilístico B3 (versão estável)")

if st.button("Rodar Scanner"):
    start = datetime.now()

    df, debug = scan()

    end = datetime.now()

    st.subheader("Resultados")

    if df.empty:
        st.warning("Nenhum ativo válido encontrado.")
    else:
        st.dataframe(df)

    st.subheader("Debug (ativos com problema)")
    st.write(debug)

    st.success(f"Tempo: {(end-start).seconds} segundos")
