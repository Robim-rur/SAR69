# =========================
# APP SCANNER ROBUSTO B3
# EMA50 + DMI + STOCH + ATR PROBABILÍSTICO
# ADX COMO PESO (NÃO FILTRO)
# =========================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# TA-LIB FREE
import ta

# =========================
# LISTA COMPLETA
# =========================
TICKERS = [
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
"MCCI11.SA","RECR11.SA","VRTA11.SA","BCFF11.SA","HFOF11.SA",
"XPSF11.SA","RBRP11.SA","RBRF11.SA","RZTR11.SA","RURA11.SA",
"VGIR11.SA","CVBI11.SA","GGRC11.SA","AUVP11.SA","GARE11.SA",
"AAPL34.SA","MSFT34.SA","GOGL34.SA","AMZO34.SA","META34.SA",
"NVDC34.SA","JPMC34.SA","DISB34.SA","SBUX34.SA"
]

# =========================
# FUNÇÃO SEGURA DE DOWNLOAD
# =========================
def get_data(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False)

    if df is None or df.empty:
        return None

    df = df.dropna()

    # força Series 1D
    for col in ["Open","High","Low","Close","Volume"]:
        if col in df.columns:
            df[col] = pd.Series(df[col].values).astype(float)

    return df

# =========================
# INDICADORES
# =========================
def indicators(df):

    close = df["Close"].astype(float).squeeze()

    ema50 = ta.trend.ema_indicator(close, window=50).squeeze()

    adx = ta.trend.adx(df["High"], df["Low"], df["Close"], window=14).squeeze()
    dmp = ta.trend.adx_pos(df["High"], df["Low"], df["Close"], window=14).squeeze()
    dmn = ta.trend.adx_neg(df["High"], df["Low"], df["Close"], window=14).squeeze()

    stoch_k = ta.momentum.stoch(df["High"], df["Low"], df["Close"], window=14).squeeze()
    stoch_d = ta.momentum.stoch_signal(df["High"], df["Low"], df["Close"], window=3).squeeze()

    atr = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14).squeeze()

    return ema50, adx, dmp, dmn, stoch_k, stoch_d, atr

# =========================
# PROBABILIDADE SIMPLIFICADA
# =========================
def probability_model(df, ema50, adx, dmp, dmn, stoch_k, stoch_d, atr):

    last = -1

    price = df["Close"].iloc[last]

    trend = 1 if price > ema50.iloc[last] else 0
    strength = min(adx.iloc[last] / 40, 1)

    momentum = 1 if dmp.iloc[last] > dmn.iloc[last] else 0

    stoch_ok = 1 if stoch_k.iloc[last] > stoch_d.iloc[last] else 0

    score = (trend * 0.4 + momentum * 0.3 + stoch_ok * 0.2 + strength * 0.1)

    # ATR based RR 2:1
    atr_val = float(atr.iloc[last])
    gain = price + (2 * atr_val)
    loss = price - atr_val

    # probabilidade heurística calibrada
    prob_gain_first = score * 100

    return prob_gain_first, gain, loss, score

# =========================
# APP
# =========================
st.title("Scanner Robusto B3 - Probabilidade Gain vs Loss")

results = []
errors = []

start = time.time()

for t in TICKERS:
    try:
        st.write(f"Baixando {t}...")

        df = get_data(t)

        if df is None:
            errors.append((t,"sem dados"))
            continue

        ema50, adx, dmp, dmn, k, d, atr = indicators(df)

        if len(df) < 60:
            errors.append((t,"dados insuficientes"))
            continue

        prob, gain, loss, score = probability_model(df, ema50, adx, dmp, dmn, k, d, atr)

        results.append({
            "Ticker": t,
            "Score": round(score,3),
            "Prob Gain (%)": round(prob,2),
            "Gain ATR": round(gain,2),
            "Loss ATR": round(loss,2)
        })

    except Exception as e:
        errors.append((t,str(e)))

df_res = pd.DataFrame(results)

if not df_res.empty:
    df_res = df_res.sort_values("Prob Gain (%)", ascending=False)

    st.success("Scan concluído")
    st.dataframe(df_res)

else:
    st.warning("Nenhum ativo válido encontrado")

st.write("Debug erros:", errors)

st.write("Tempo:", round(time.time()-start,2),"s")
