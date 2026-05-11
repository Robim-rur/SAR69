# app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Scanner Probabilístico ATR",
    layout="wide"
)

# =========================
# SENHA
# =========================

SENHA = "LUCRO6"

senha = st.sidebar.text_input("Senha", type="password")

if senha != SENHA:
    st.warning("Digite a senha correta.")
    st.stop()

# =========================
# LISTA DE ATIVOS
# =========================

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

# =========================
# FUNÇÕES
# =========================

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def stochastic(df, k_period=14, d_period=3):

    low_min = df['Low'].rolling(k_period).min()
    high_max = df['High'].rolling(k_period).max()

    k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    d = k.rolling(d_period).mean()

    return k, d

def atr(df, period=14):

    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)

    true_range = ranges.max(axis=1)

    return true_range.rolling(period).mean()

def dmi(df, period=14):

    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff() * -1

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift())
    tr3 = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr_ = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr_)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr_)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()

    return plus_di, minus_di, adx

# =========================
# TÍTULO
# =========================

st.title("Scanner Probabilístico ATR")
st.write("Ranking probabilístico baseado no seu setup operacional.")

# =========================
# BOTÃO
# =========================

if st.button("ESCANEAR MERCADO"):

    resultados = []

    progresso = st.progress(0)

    for i, ativo in enumerate(ATIVOS):

        try:

            df = yf.download(
                ativo,
                period="3y",
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            if len(df) < 200:
                continue

            df.dropna(inplace=True)

            # =====================
            # INDICADORES
            # =====================

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

            if len(df) < 50:
                continue

            ultimo = df.iloc[-1]

            close = float(ultimo["Close"])
            ema69 = float(ultimo["EMA69"])
            k_val = float(ultimo["K"])
            d_val = float(ultimo["D"])
            plus = float(ultimo["PLUS_DI"])
            minus = float(ultimo["MINUS_DI"])
            adx_val = float(ultimo["ADX"])
            atr_val = float(ultimo["ATR"])

            # =====================
            # FILTROS
            # =====================

            tendencia = close > ema69

            estocastico_ok = (
                k_val > d_val
                and k_val < 80
            )

            dmi_ok = plus > minus

            adx_ok = adx_val >= 14

            distancia_ema = abs((close - ema69) / ema69) * 100

            distancia_ok = distancia_ema <= 15

            candle_forca = (
                ultimo["Close"] > ultimo["Open"]
            )

            if not tendencia:
                continue

            if not estocastico_ok:
                continue

            if not dmi_ok:
                continue

            if not adx_ok:
                continue

            if not distancia_ok:
                continue

            if not candle_forca:
                continue

            # =====================
            # ATR
            # =====================

            gain = close + (atr_val * 2)
            stop = close - (atr_val * 1)

            gain_pct = ((gain / close) - 1) * 100
            stop_pct = ((stop / close) - 1) * 100

            # =====================
            # SCORE
            # =====================

            score = 0

            if close > ema69:
                score += 20

            if plus > minus:
                score += 20

            if adx_val > 20:
                score += 15

            if k_val > d_val:
                score += 15

            if distancia_ema < 8:
                score += 10

            if candle_forca:
                score += 10

            if gain_pct > abs(stop_pct):
                score += 10

            # =====================
            # PROBABILIDADE
            # =====================

            prob_gain = min(95, max(45, score))

            # =====================
            # FILTRO FINAL
            # =====================

            if score < 55:
                continue

            resultados.append({

                "Ativo": ativo.replace(".SA", ""),
                "Preço": round(close, 2),
                "Probabilidade Gain (%)": round(prob_gain, 1),
                "Score": round(score, 1),
                "ADX": round(adx_val, 1),
                "ATR": round(atr_val, 2),
                "Gain ATR (%)": round(gain_pct, 2),
                "Stop ATR (%)": round(stop_pct, 2),
                "Dist EMA69 (%)": round(distancia_ema, 2)

            })

        except:
            pass

        progresso.progress((i + 1) / len(ATIVOS))

    # =========================
    # RESULTADOS
    # =========================

    if len(resultados) == 0:

        st.error("Nenhum ativo encontrado.")

    else:

        resultado_df = pd.DataFrame(resultados)

        resultado_df = resultado_df.sort_values(
            by="Probabilidade Gain (%)",
            ascending=False
        )

        st.success(f"{len(resultado_df)} ativos encontrados.")

        st.dataframe(
            resultado_df,
            use_container_width=True
        )

        fig = px.bar(
            resultado_df.head(15),
            x="Ativo",
            y="Probabilidade Gain (%)",
            title="Top Probabilidades"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        csv = resultado_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Baixar CSV",
            csv,
            file_name=f"scanner_{datetime.now().date()}.csv",
            mime="text/csv"
        )
