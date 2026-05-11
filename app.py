# app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Scanner ATR Flex",
    layout="wide"
)

# ======================================
# SENHA
# ======================================

SENHA = "LUCRO6"

senha = st.sidebar.text_input(
    "Senha",
    type="password"
)

if senha != SENHA:
    st.warning("Digite a senha.")
    st.stop()

# ======================================
# LISTA DE ATIVOS
# ======================================

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

# ======================================
# FUNÇÕES
# ======================================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def stochastic(df):

    low_min = df["Low"].rolling(14).min()
    high_max = df["High"].rolling(14).max()

    k = 100 * (
        (df["Close"] - low_min) /
        (high_max - low_min)
    )

    d = k.rolling(3).mean()

    return k, d

def atr(df):

    high_low = df["High"] - df["Low"]
    high_close = abs(df["High"] - df["Close"].shift())
    low_close = abs(df["Low"] - df["Close"].shift())

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    return tr.rolling(14).mean()

def dmi(df):

    plus_dm = df["High"].diff()
    minus_dm = -df["Low"].diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr1 = df["High"] - df["Low"]
    tr2 = abs(df["High"] - df["Close"].shift())
    tr3 = abs(df["Low"] - df["Close"].shift())

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    atr_ = tr.rolling(14).mean()

    plus_di = 100 * (
        plus_dm.rolling(14).mean() / atr_
    )

    minus_di = 100 * (
        minus_dm.rolling(14).mean() / atr_
    )

    dx = (
        abs(plus_di - minus_di) /
        (plus_di + minus_di)
    ) * 100

    adx = dx.rolling(14).mean()

    return plus_di, minus_di, adx

# ======================================
# TÍTULO
# ======================================

st.title("Scanner ATR Flexível")

st.write("""
Scanner alinhado ao seu operacional:
- EMA69
- DI+ > DI−
- Candle comprador
- Ranking probabilístico
- Gain/Stop por ATR
""")

# ======================================
# BOTÃO
# ======================================

if st.button("ESCANEAR"):

    resultados = []

    barra = st.progress(0)

    for i, ativo in enumerate(ATIVOS):

        try:

            df = yf.download(
                ativo,
                period="2y",
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            if len(df) < 100:
                continue

            df["EMA69"] = ema(df["Close"], 69)

            k, d = stochastic(df)

            df["K"] = k
            df["D"] = d

            plus_di, minus_di, adx = dmi(df)

            df["PLUS_DI"] = plus_di
            df["MINUS_DI"] = minus_di
            df["ADX"] = adx

            df["ATR"] = atr(df)

            df.dropna(inplace=True)

            ultimo = df.iloc[-1]

            close = float(ultimo["Close"])
            ema69 = float(ultimo["EMA69"])

            plus = float(ultimo["PLUS_DI"])
            minus = float(ultimo["MINUS_DI"])

            adx_val = float(ultimo["ADX"])

            k_val = float(ultimo["K"])
            d_val = float(ultimo["D"])

            atr_val = float(ultimo["ATR"])

            # ======================================
            # FILTROS OBRIGATÓRIOS
            # ======================================

            if close <= ema69:
                continue

            if plus <= minus:
                continue

            if ultimo["Close"] <= ultimo["Open"]:
                continue

            # ======================================
            # SCORE FLEXÍVEL
            # ======================================

            score = 50

            if adx_val > 20:
                score += 10

            if k_val > d_val:
                score += 10

            distancia_ema = (
                abs(close - ema69) / ema69
            ) * 100

            if distancia_ema < 8:
                score += 10

            if volume := ultimo.get("Volume", 0):
                score += 10

            probabilidade = min(score, 95)

            # ======================================
            # ATR
            # ======================================

            gain = close + (atr_val * 2)
            stop = close - (atr_val * 1)

            gain_pct = (
                (gain / close) - 1
            ) * 100

            stop_pct = (
                (stop / close) - 1
            ) * 100

            resultados.append({

                "Ativo": ativo.replace(".SA", ""),
                "Preço": round(close, 2),
                "Probabilidade": round(probabilidade, 1),
                "Score": round(score, 1),
                "ADX": round(adx_val, 1),
                "ATR": round(atr_val, 2),
                "Gain ATR %": round(gain_pct, 2),
                "Stop ATR %": round(stop_pct, 2),
                "Dist EMA69 %": round(distancia_ema, 2)

            })

        except:
            pass

        barra.progress((i + 1) / len(ATIVOS))

    # ======================================
    # RESULTADOS
    # ======================================

    if len(resultados) == 0:

        st.error("Nenhum ativo encontrado.")

    else:

        resultado_df = pd.DataFrame(resultados)

        resultado_df = resultado_df.sort_values(
            by="Probabilidade",
            ascending=False
        )

        st.success(
            f"{len(resultado_df)} ativos encontrados."
        )

        st.dataframe(
            resultado_df,
            use_container_width=True
        )

        fig = px.bar(
            resultado_df.head(15),
            x="Ativo",
            y="Probabilidade",
            title="Melhores Probabilidades"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        csv = resultado_df.to_csv(index=False)

        st.download_button(
            "Baixar CSV",
            csv,
            file_name="scanner.csv",
            mime="text/csv"
        )
