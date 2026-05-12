import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import StochasticOscillator
from ta.volatility import AverageTrueRange
import time

st.set_page_config(page_title="Scanner Probabilístico B3", layout="wide")

# =========================
# LISTA DE ATIVOS
# =========================
TICKERS = [
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
    "MCCI11.SA","RECR11.SA","VRTA11.SA","BCFF11.SA","HFOF11.SA",
    "XPSF11.SA","RBRP11.SA","RBRF11.SA","RZTR11.SA","RURA11.SA",
    "VGIR11.SA","GGRC11.SA","AUVP11.SA","GARE11.SA",

    # BDRs
    "AAPL34.SA","MSFT34.SA","GOGL34.SA","AMZO34.SA","META34.SA",
    "NVDC34.SA","JPMC34.SA","DISB34.SA","SBUX34.SA"
]

# =========================
# FUNÇÃO SEGURA DE DOWNLOAD
# =========================
def get_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df.dropna()

        # FORÇAR 1D (CORREÇÃO CRÍTICA)
        df["Close"] = df["Close"].astype(float).squeeze()
        df["High"] = df["High"].astype(float).squeeze()
        df["Low"] = df["Low"].astype(float).squeeze()

        return df

    except:
        return None


# =========================
# SCORE PROBABILÍSTICO
# =========================
def compute_score(df):

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # EMA 50
    ema = EMAIndicator(close=close, window=50).ema_indicator()

    # ADX (peso)
    adx = ADXIndicator(high=high, low=low, close=close, window=14)
    adx_val = adx.adx().iloc[-1]

    # Estocástico
    stoch = StochasticOscillator(high=high, low=low, close=close)
    k = stoch.stoch().iloc[-1]
    d = stoch.stoch_signal().iloc[-1]

    # ATR (gain/loss model)
    atr = AverageTrueRange(high=high, low=low, close=close, window=14)
    atr_val = atr.average_true_range().iloc[-1]

    price = close.iloc[-1]
    ema_val = ema.iloc[-1]

    # =========================
    # FEATURES NORMALIZADAS
    # =========================

    trend = 1 if price > ema_val else 0

    momentum = 1 if k > d else 0

    adx_weight = min(adx_val / 50, 1)

    volatility_factor = atr_val / price

    # =========================
    # PROBABILIDADE GAIN VS LOSS (2:1 ATR)
    # =========================
    expected_gain = 2 * atr_val
    expected_loss = atr_val

    prob_gain = (trend * 0.4 +
                 momentum * 0.3 +
                 adx_weight * 0.3)

    prob_gain = max(0, min(prob_gain, 1))

    return {
        "price": price,
        "trend": trend,
        "momentum": momentum,
        "adx": adx_val,
        "atr": atr_val,
        "prob_gain": prob_gain
    }


# =========================
# SCANNER
# =========================
st.title("📊 Scanner Probabilístico - B3 (EMA50 + ATR 2:1)")

if st.button("Rodar Scanner"):

    start = time.time()

    results = []
    errors = 0

    for t in TICKERS:

        df = get_data(t)

        if df is None:
            continue

        try:
            score = compute_score(df)

            results.append({
                "Ticker": t,
                "Preço": round(score["price"], 2),
                "Tendência(EMA50)": score["trend"],
                "Momentum": score["momentum"],
                "ADX": round(score["adx"], 2),
                "ATR": round(score["atr"], 4),
                "Prob Gain": round(score["prob_gain"], 3)
            })

        except:
            errors += 1

    if len(results) == 0:
        st.error("Nenhum ativo válido encontrado.")
    else:

        df = pd.DataFrame(results)

        df = df.sort_values("Prob Gain", ascending=False)

        st.success(f"Scan concluído em {round(time.time()-start,2)}s")

        st.dataframe(df)

        st.markdown("### 🏆 Top oportunidades")
        st.dataframe(df.head(10))
