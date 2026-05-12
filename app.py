import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime

st.set_page_config(
    page_title="Scanner SAR + EMA50",
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

def calcular_ema(df, periodo=50):
    return df["Close"].ewm(span=periodo).mean()

def calcular_atr(df, periodo=14):

    high_low = df["High"] - df["Low"]

    high_close = np.abs(df["High"] - df["Close"].shift())

    low_close = np.abs(df["Low"] - df["Close"].shift())

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    atr = tr.rolling(periodo).mean()

    return atr

def calcular_sar(df, step=0.02, max_step=0.2):

    high = df["High"].values
    low = df["Low"].values

    sar = np.zeros(len(df))

    trend = 1

    af = step

    ep = low[0]

    sar[0] = low[0]

    for i in range(1, len(df)):

        prev_sar = sar[i - 1]

        if trend == 1:

            sar[i] = prev_sar + af * (ep - prev_sar)

            if low[i] < sar[i]:

                trend = -1

                sar[i] = ep

                ep = low[i]

                af = step

            else:

                if high[i] > ep:

                    ep = high[i]

                    af = min(af + step, max_step)

        else:

            sar[i] = prev_sar + af * (ep - prev_sar)

            if high[i] > sar[i]:

                trend = 1

                sar[i] = ep

                ep = high[i]

                af = step

            else:

                if low[i] < ep:

                    ep = low[i]

                    af = min(af + step, max_step)

    return sar

def calcular_score(df):

    score = 0

    close = df["Close"].iloc[-1]

    ema50 = df["EMA50"].iloc[-1]

    sar = df["SAR"].iloc[-1]

    volume = df["Volume"].iloc[-1]

    vol_media = df["Volume"].rolling(20).mean().iloc[-1]

    if close > ema50:
        score += 40

    if close > sar:
        score += 40

    if volume > vol_media:
        score += 20

    return score

# =========================
# INTERFACE
# =========================

st.title("📈 Scanner SAR + EMA50 + ATR")

st.write("""
Scanner probabilístico focado em:

- Tendência por EMA50
- Gatilho por SAR
- Gain/Loss pelo ATR
- Ranking por probabilidade
""")

if st.button("ESCANEAR MERCADO"):

    inicio = time.time()

    resultados = []

    progresso = st.progress(0)

    status = st.empty()

    total = len(ATIVOS)

    for i, ativo in enumerate(ATIVOS):

        try:

            status.write(f"Baixando {ativo}...")

            df = yf.download(
                ativo,
                period="1y",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            if df.empty:
                continue

            if len(df) < 60:
                continue

            df["EMA50"] = calcular_ema(df)

            df["ATR"] = calcular_atr(df)

            df["SAR"] = calcular_sar(df)

            close = float(df["Close"].iloc[-1])

            ema50 = float(df["EMA50"].iloc[-1])

            sar = float(df["SAR"].iloc[-1])

            atr = float(df["ATR"].iloc[-1])

            volume = float(df["Volume"].iloc[-1])

            vol_media = float(
                df["Volume"].rolling(20).mean().iloc[-1]
            )

            # FILTRO PRINCIPAL
            if close > ema50 and close > sar:

                gain = close + (atr * 2)

                loss = close - (atr * 1)

                potencial_gain = (
                    (gain - close) / close
                ) * 100

                potencial_loss = (
                    (close - loss) / close
                ) * 100

                score = calcular_score(df)

                resultados.append({

                    "Ativo": ativo,

                    "Preço": round(close, 2),

                    "EMA50": round(ema50, 2),

                    "SAR": round(sar, 2),

                    "ATR": round(atr, 2),

                    "Gain ATR": round(gain, 2),

                    "Loss ATR": round(loss, 2),

                    "% Gain": round(potencial_gain, 2),

                    "% Loss": round(potencial_loss, 2),

                    "Volume x Média":
                        round(volume / vol_media, 2),

                    "Score": score
                })

        except Exception as e:

            st.write(f"Erro em {ativo}: {e}")

        progresso.progress((i + 1) / total)

    tempo_total = round(time.time() - inicio, 2)

    st.success(f"Scan concluído em {tempo_total} segundos.")

    if len(resultados) == 0:

        st.error("Nenhum ativo encontrado.")

    else:

        resultado_df = pd.DataFrame(resultados)

        resultado_df = resultado_df.sort_values(
            by="Score",
            ascending=False
        )

        st.subheader("📊 Ranking Probabilístico")

        st.dataframe(
            resultado_df,
            use_container_width=True
        )

        csv = resultado_df.to_csv(index=False)

        st.download_button(
            "📥 Baixar CSV",
            csv,
            file_name="scanner_resultado.csv",
            mime="text/csv"
        )
