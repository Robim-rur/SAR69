import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Teste Yahoo", layout="wide")

st.title("Teste Simples Yahoo Finance")

ATIVOS = [
    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA"
]

resultado = []

inicio = time.time()

for ativo in ATIVOS:

    st.write(f"Testando {ativo}")

    try:

        ticker = yf.Ticker(ativo)

        hist = ticker.history(period="3mo")

        if hist.empty:

            resultado.append({
                "Ativo": ativo,
                "Status": "Sem dados",
                "Linhas": 0
            })

        else:

            ultimo = float(hist["Close"].iloc[-1])

            resultado.append({
                "Ativo": ativo,
                "Status": "OK",
                "Linhas": len(hist),
                "Último Fechamento": round(ultimo, 2)
            })

            st.write(hist.tail())

    except Exception as e:

        resultado.append({
            "Ativo": ativo,
            "Status": str(e),
            "Linhas": 0
        })

fim = time.time()

tempo = round(fim - inicio, 2)

st.subheader("Resultado Final")

st.dataframe(
    pd.DataFrame(resultado),
    use_container_width=True
)

st.success(f"Tempo total: {tempo} segundos")
