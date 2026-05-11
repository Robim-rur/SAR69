# app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Scanner EMA50 + SAR + Probabilidade",
    layout="wide"
)

# =========================================================
# LISTA DE ATIVOS
# =========================================================

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

# =========================================================
# FUNÇÕES
# =========================================================

def calcular_ema(df, periodo=50):
    return df["Close"].ewm(span=periodo).mean()

def calcular_atr(df, periodo=14):

    high_low = df["High"] - df["Low"]

    high_close = abs(
        df["High"] - df["Close"].shift()
    )

    low_close = abs(
        df["Low"] - df["Close"].shift()
    )

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    atr = tr.rolling(periodo).mean()

    return atr

def calcular_estocastico(df, periodo=14):

    low_min = df["Low"].rolling(periodo).min()

    high_max = df["High"].rolling(periodo).max()

    k = 100 * (
        (df["Close"] - low_min)
        / (high_max - low_min)
    )

    return k

def calcular_adx(df, periodo=14):

    plus_dm = df["High"].diff()

    minus_dm = df["Low"].diff() * -1

    plus_dm[plus_dm < 0] = 0

    minus_dm[minus_dm < 0] = 0

    tr1 = df["High"] - df["Low"]

    tr2 = abs(df["High"] - df["Close"].shift())

    tr3 = abs(df["Low"] - df["Close"].shift())

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    atr = tr.rolling(periodo).mean()

    plus_di = 100 * (
        plus_dm.rolling(periodo).mean() / atr
    )

    minus_di = 100 * (
        minus_dm.rolling(periodo).mean() / atr
    )

    dx = (
        abs(plus_di - minus_di)
        / abs(plus_di + minus_di)
    ) * 100

    adx = dx.rolling(periodo).mean()

    return adx, plus_di, minus_di

def calcular_sar(df, af=0.02, af_max=0.2):

    high = df["High"].values
    low = df["Low"].values

    sar = np.zeros(len(df))

    trend = 1

    ep = low[0]

    acceleration = af

    sar[0] = low[0]

    for i in range(1, len(df)):

        sar[i] = (
            sar[i-1]
            + acceleration * (ep - sar[i-1])
        )

        if trend == 1:

            if low[i] < sar[i]:

                trend = -1
                sar[i] = ep
                ep = low[i]
                acceleration = af

            else:

                if high[i] > ep:

                    ep = high[i]

                    acceleration = min(
                        acceleration + af,
                        af_max
                    )

        else:

            if high[i] > sar[i]:

                trend = 1
                sar[i] = ep
                ep = high[i]
                acceleration = af

            else:

                if low[i] < ep:

                    ep = low[i]

                    acceleration = min(
                        acceleration + af,
                        af_max
                    )

    return sar

# =========================================================
# TÍTULO
# =========================================================

st.title("📈 Scanner EMA50 + SAR + Probabilidade")

st.markdown("""
Scanner probabilístico flexível para swing trade diário.

### Regras obrigatórias:
- SOMENTE preço acima da EMA50

### Score:
- SAR
- DMI
- ADX
- Estocástico
- Candle
- Volume

### ATR:
- Gain = 2 ATR
- Stop = 1 ATR
""")

# =========================================================
# BOTÃO
# =========================================================

if st.button("ESCANEAR MERCADO"):

    resultados = []

    progresso = st.progress(0)

    for idx, ativo in enumerate(ATIVOS):

        try:

            df = yf.download(
                ativo,
                period="1y",
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            if len(df) < 100:
                continue

            df.dropna(inplace=True)

            # =================================================
            # INDICADORES
            # =================================================

            df["EMA50"] = calcular_ema(df)

            df["ATR"] = calcular_atr(df)

            df["SAR"] = calcular_sar(df)

            df["ADX"], df["DI+"], df["DI-"] = calcular_adx(df)

            df["K"] = calcular_estocastico(df)

            df["VOL20"] = df["Volume"].rolling(20).mean()

            ultimo = df.iloc[-1]

            # =================================================
            # DADOS
            # =================================================

            close = float(ultimo["Close"])

            ema50 = float(ultimo["EMA50"])

            sar = float(ultimo["SAR"])

            adx = float(ultimo["ADX"])

            di_plus = float(ultimo["DI+"])

            di_minus = float(ultimo["DI-"])

            k = float(ultimo["K"])

            atr = float(ultimo["ATR"])

            candle_verde = (
                ultimo["Close"] > ultimo["Open"]
            )

            volume_ok = (
                ultimo["Volume"] > ultimo["VOL20"]
            )

            # =================================================
            # ÚNICO FILTRO OBRIGATÓRIO
            # =================================================

            if close > ema50:

                # =============================================
                # ATR
                # =============================================

                atr_gain = close + (atr * 2)

                atr_stop = close - (atr * 1)

                gain_pct = (
                    (atr_gain / close) - 1
                ) * 100

                loss_pct = (
                    (close / atr_stop) - 1
                ) * 100

                # =============================================
                # SCORE
                # =============================================

                score = 50

                # SAR
                if sar < close:
                    score += 10

                # DMI
                if di_plus > di_minus:
                    score += 10

                # ADX
                score += min(adx / 2, 10)

                # Estocástico
                if k > 40:
                    score += 10

                # Candle verde
                if candle_verde:
                    score += 5

                # Volume
                if volume_ok:
                    score += 5

                probabilidade = min(
                    round(score, 1),
                    99
                )

                resultados.append({

                    "Ativo": ativo.replace(".SA", ""),

                    "Preço": round(close, 2),

                    "Probabilidade": probabilidade,

                    "ADX": round(adx, 1),

                    "DI+": round(di_plus, 1),

                    "DI-": round(di_minus, 1),

                    "Estocástico": round(k, 1),

                    "ATR Gain": round(atr_gain, 2),

                    "ATR Stop": round(atr_stop, 2),

                    "Gain %": round(gain_pct, 2),

                    "Loss %": round(loss_pct, 2)
                })

        except:
            pass

        progresso.progress(
            (idx + 1) / len(ATIVOS)
        )

    # =========================================================
    # RESULTADOS
    # =========================================================

    if len(resultados) == 0:

        st.warning("Nenhum ativo encontrado.")

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
            use_container_width=True,
            hide_index=True
        )

        fig = px.bar(
            resultado_df.head(15),
            x="Ativo",
            y="Probabilidade",
            title="Top Probabilidades"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        csv = resultado_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Baixar CSV",
            csv,
            "scanner_probabilidade.csv",
            "text/csv"
        )

# =========================================================
# RODAPÉ
# =========================================================

st.markdown("---")

st.caption(
    f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
)
