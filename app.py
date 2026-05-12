import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import time

st.set_page_config(page_title="Scanner EMA50", layout="wide")

st.title("Scanner EMA50")

ATIVOS = [
    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA",
    "ITUB4.SA",
    "WEGE3.SA"
]

def valor_final(v):
    if isinstance(v, pd.Series):
        return float(v.iloc[-1])

    if isinstance(v, np.ndarray):
        return float(v[-1])

    return float(v)

resultados = []

inicio = time.time()

barra = st.progress(0)

for i, ticker in enumerate(ATIVOS):

    try:

        st.write(f"Baixando {ticker}...")

        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            continue

        close = df["Close"].astype(float)
        high = df["High"].astype(float)
        low = df["Low"].astype(float)

        ema50 = ta.trend.EMAIndicator(
            close=close,
            window=50
        ).ema_indicator()

        atr = ta.volatility.AverageTrueRange(
            high=high,
            low=low,
            close=close,
            window=14
        ).average_true_range()

        preco = valor_final(close)
        ema = valor_final(ema50)
        atr_final = valor_final(atr)

        if preco > ema:

            gain = preco + (atr_final * 2)
            loss = preco - atr_final

            resultados.append({

                "Ativo": ticker,
                "Preço": round(preco, 2),
                "EMA50": round(ema, 2),
                "ATR": round(atr_final, 2),
                "Gain": round(gain, 2),
                "Loss": round(loss, 2)

            })

    except Exception as e:

        st.write(f"Erro em {ticker}: {e}")

    barra.progress((i + 1) / len(ATIVOS))

fim = time.time()

st.success(f"Tempo total: {round(fim - inicio, 2)} segundos")

if resultados:

    df_resultado = pd.DataFrame(resultados)

    st.dataframe(
        df_resultado,
        use_container_width=True
    )

else:

    st.warning("Nenhum ativo encontrado.")
