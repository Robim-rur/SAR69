import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(layout="wide")

st.title("TESTE DEFINITIVO YFINANCE")

ATIVOS = [
    "PETR4.SA",
    "VALE3.SA",
    "BBAS3.SA",
    "ITUB4.SA",
    "WEGE3.SA"
]

resultados = []

inicio = datetime.now()

for ativo in ATIVOS:

    st.write(f"Baixando {ativo}...")

    try:

        df = yf.download(
            ativo,
            period="1y",
            interval="1d",
            progress=False,
            auto_adjust=True,
            threads=False
        )

        if df.empty:

            resultados.append({
                "Ativo": ativo,
                "Status": "DATAFRAME VAZIO",
                "Linhas": 0
            })

        else:

            resultados.append({
                "Ativo": ativo,
                "Status": "OK",
                "Linhas": len(df)
            })

            st.write(df.tail())

    except Exception as e:

        resultados.append({
            "Ativo": ativo,
            "Status": str(e),
            "Linhas": 0
        })

fim = datetime.now()

tempo = (fim - inicio).seconds

st.subheader("Resultado")

st.dataframe(pd.DataFrame(resultados), use_container_width=True)

st.success(f"Tempo total: {tempo} segundos")
