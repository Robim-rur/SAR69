import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ta.trend import EMAIndicator
from datetime import datetime

st.set_page_config(layout="wide")

st.title("Scanner TESTE - Apenas EMA50")

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

resultados = []
debug = []

progress = st.progress(0)

inicio = datetime.now()

for i, ativo in enumerate(ATIVOS):

    try:

        st.write(f"Lendo {ativo}...")

        df = yf.download(
            ativo,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if df.empty:
            debug.append([ativo, "SEM DADOS"])
            continue

        if len(df) < 60:
            debug.append([ativo, f"POUCOS DADOS ({len(df)})"])
            continue

        df.dropna(inplace=True)

        ema = EMAIndicator(
            close=df["Close"],
            window=50
        )

        df["EMA50"] = ema.ema_indicator()

        df.dropna(inplace=True)

        if len(df) == 0:
            debug.append([ativo, "SEM EMA"])
            continue

        ultimo = df.iloc[-1]

        close = float(ultimo["Close"])
        ema50 = float(ultimo["EMA50"])

        # TESTE MAIS SIMPLES POSSÍVEL
        if close > ema50:

            distancia = ((close / ema50) - 1) * 100

            resultados.append({
                "Ativo": ativo,
                "Preço": round(close, 2),
                "EMA50": round(ema50, 2),
                "% Distância EMA": round(distancia, 2)
            })

            debug.append([ativo, "PASSOU"])

        else:

            debug.append([ativo, "ABAIXO EMA50"])

    except Exception as e:

        debug.append([ativo, str(e)])

    progress.progress((i + 1) / len(ATIVOS))

fim = datetime.now()

tempo_total = (fim - inicio).seconds

st.subheader("Resultado")

if len(resultados) > 0:

    df_result = pd.DataFrame(resultados)

    df_result.sort_values(
        by="% Distância EMA",
        ascending=False,
        inplace=True
    )

    st.success(f"{len(df_result)} ativos encontrados.")

    st.dataframe(
        df_result,
        use_container_width=True
    )

else:

    st.error("Nenhum ativo passou nem no teste simples.")

st.subheader("Debug")

df_debug = pd.DataFrame(
    debug,
    columns=["Ativo", "Status"]
)

st.dataframe(
    df_debug,
    use_container_width=True
)

st.info(f"Tempo total: {tempo_total} segundos")

st.success("Scanner concluído.")
)

st.dataframe(
    df_debug,
    use_container_width=True
)

st.success("Scanner concluído.")
