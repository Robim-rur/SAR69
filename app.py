import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import time

st.set_page_config(page_title="Scanner EMA50 + ATR", layout="wide")

st.title("📈 Scanner EMA50 + ATR")
st.write("Scanner simplificado para teste de funcionamento.")

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


def valor_final(valor):
    """
    Corrige problema do yfinance retornando Series.
    """
    if isinstance(valor, pd.Series):
        return float(valor.iloc[-1])

    if isinstance(valor, np.ndarray):
        return float(valor[-1])

    return float(valor)


resultados = []

inicio = time.time()

barra = st.progress(0)

for i, ticker in enumerate(ATIVOS):

    try:

        st.write(f"Baixando {ticker}...")

        df = yf.download(
            ticker,
            period="2y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            continue

        df.dropna(inplace=True)

        if len(df) < 60:
            continue

        close = df["Close"].astype(float)
        high = df["High"].astype(float)
        low = df["Low"].astype(float)

        # EMA 50
        ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()

        # ATR
        atr = ta.volatility.AverageTrueRange(
            high=high,
            low=low,
            close=close,
            window=14
        ).average_true_range()

        preco = valor_final(close)
        ema_atual = valor_final(ema50)
        atr_atual = valor_final(atr)

        # filtro simplificado
        if preco > ema_atual:

            gain = preco + (atr_atual * 2)
            loss = preco - atr_atual

            percentual_gain = ((gain / preco) - 1) * 100
            percentual_loss = ((loss / preco) - 1) * 100

            distancia_ema = ((preco / ema_atual) - 1) * 100

            score = (
                percentual_gain
                - abs(percentual_loss)
                - abs(distancia_ema)
            )

            resultados.append({

                "Ativo": ticker.replace(".SA", ""),
                "Preço": round(preco, 2),
                "EMA50": round(ema_atual, 2),
                "ATR": round(atr_atual, 2),

                "Gain ATR": round(gain, 2),
                "Loss ATR": round(loss, 2),

                "% Gain": round(percentual_gain, 2),
                "% Loss": round(percentual_loss, 2),

                "Dist EMA %": round(distancia_ema, 2),

                "Score": round(score, 2)

            })

    except Exception as e:

        st.write(f"Erro em {ticker}: {e}")

    barra.progress((i + 1) / len(ATIVOS))

fim = time.time()

tempo = round(fim - inicio, 2)

st.success(f"Scan concluído em {tempo} segundos.")

if resultados:

    df_resultado = pd.DataFrame(resultados)

    df_resultado = df_resultado.sort_values(
        by="Score",
        ascending=False
    )

    st.subheader("🏆 Melhores probabilidades")

    st.dataframe(
        df_resultado,
        use_container_width=True
    )

else:

    st.warning("Nenhum ativo encontrado.")

            file_name=(
                "scanner_resultado.csv"
            ),

            mime="text/csv"
        )
