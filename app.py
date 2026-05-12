import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import time

st.set_page_config(
    page_title="Scanner Probabilístico ATR",
    layout="wide"
)

st.title("📈 Scanner Probabilístico ATR + EMA50 + SAR")

st.write(
    """
    Scanner probabilístico para swing trade.
    Classifica os ativos pela maior probabilidade matemática
    de atingir o gain antes do loss.
    """
)

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

def limpar_serie(coluna):

    if isinstance(coluna, pd.DataFrame):
        coluna = coluna.squeeze()

    if isinstance(coluna, np.ndarray):
        coluna = pd.Series(coluna.flatten())

    return pd.Series(coluna).astype(float)

def calcular_probabilidade(
    distancia_gain,
    distancia_loss,
    adx,
    distancia_ema,
    sar_score
):
    """
    Modelo probabilístico simplificado.
    """

    rr = distancia_gain / abs(distancia_loss)

    base = 50

    # Reward/Risk
    base += rr * 8

    # ADX
    if adx > 25:
        base += 10

    if adx > 35:
        base += 5

    # EMA
    if distancia_ema > 0:
        base += 10

    # SAR
    base += sar_score

    # penalização excesso esticado
    if distancia_ema > 12:
        base -= 15

    return max(1, min(base, 99))

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
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            continue

        if len(df) < 100:
            continue

        close = limpar_serie(df["Close"])
        high = limpar_serie(df["High"])
        low = limpar_serie(df["Low"])

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

        adx = ta.trend.ADXIndicator(
            high=high,
            low=low,
            close=close,
            window=14
        ).adx()

        sar = ta.trend.PSARIndicator(
            high=high,
            low=low,
            close=close
        ).psar()

        preco = float(close.iloc[-1])
        ema = float(ema50.iloc[-1])
        atr_final = float(atr.iloc[-1])
        adx_final = float(adx.iloc[-1])
        sar_final = float(sar.iloc[-1])

        # filtro leve
        if preco < ema:
            continue

        gain = preco + (atr_final * 2)
        loss = preco - atr_final

        percentual_gain = ((gain / preco) - 1) * 100
        percentual_loss = ((loss / preco) - 1) * 100

        distancia_ema = ((preco / ema) - 1) * 100

        sar_score = 0

        if preco > sar_final:
            sar_score += 10

        probabilidade = calcular_probabilidade(
            percentual_gain,
            percentual_loss,
            adx_final,
            distancia_ema,
            sar_score
        )

        resultados.append({

            "Ativo": ticker.replace(".SA", ""),
            "Preço": round(preco, 2),

            "EMA50": round(ema, 2),
            "SAR": round(sar_final, 2),
            "ADX": round(adx_final, 2),

            "ATR": round(atr_final, 2),

            "Gain ATR": round(gain, 2),
            "Loss ATR": round(loss, 2),

            "% Gain": round(percentual_gain, 2),
            "% Loss": round(percentual_loss, 2),

            "Dist EMA %": round(distancia_ema, 2),

            "Probabilidade Gain Antes Loss %":
                round(probabilidade, 2)

        })

    except Exception as e:

        st.write(f"Erro em {ticker}: {e}")

    barra.progress((i + 1) / len(ATIVOS))

fim = time.time()

tempo = round(fim - inicio, 2)

st.success(f"✅ Scan concluído em {tempo} segundos.")

if resultados:

    df_resultado = pd.DataFrame(resultados)

    df_resultado = df_resultado.sort_values(
        by="Probabilidade Gain Antes Loss %",
        ascending=False
    )

    st.subheader(
        "🏆 Ranking de Probabilidade de Atingir o Gain Antes do Loss"
    )

    st.dataframe(
        df_resultado,
        use_container_width=True
    )

else:

    st.warning("Nenhum ativo encontrado.")
