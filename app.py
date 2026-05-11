import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(layout="wide")

st.title("TESTE REAL YFINANCE")

ATIVOS = [
    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA",
    "ITUB4.SA",
    "WEGE3.SA"
]

resultados = []

inicio = time.time()

for ativo in ATIVOS:

    st.write(f"Baixando {ativo}...")

    try:

        ticker = yf.Ticker(ativo)

        df = ticker.history(
            period="1y",
            interval="1d",
            auto_adjust=True
        )

        if df.empty:

            resultados.append({
                "Ativo": ativo,
                "Status": "SEM DADOS",
                "Linhas": 0
            })

        else:

            resultados.append({
                "Ativo": ativo,
                "Status": "OK",
                "Linhas": len(df),
                "Último Fechamento": round(df["Close"].iloc[-1], 2)
            })

            st.write(df.tail(3))

    except Exception as e:

        resultados.append({
            "Ativo": ativo,
            "Status": str(e),
            "Linhas": 0
        })

fim = time.time()

tempo = round(fim - inicio, 2)

st.subheader("Resultado")

st.dataframe(
    pd.DataFrame(resultados),
    use_container_width=True
)

st.success(f"Tempo total: {tempo} segundos")
