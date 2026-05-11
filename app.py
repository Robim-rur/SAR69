# app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import plotly.express as px
from datetime import datetime

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Terminal Buy Side PRO",
    layout="wide"
)

# =========================================================
# TÍTULO
# =========================================================

st.title("🚀 Terminal Buy Side PRO")
st.caption(
    "EMA 69 + SAR + DMI/ADX + Estocástico + Ranking Probabilístico"
)

# =========================================================
# LISTA DE ATIVOS
# =========================================================

ATIVOS = sorted(list(set([

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

])))

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("⚙️ Configurações")

periodo = st.sidebar.selectbox(
    "Período histórico",
    ["1y", "2y", "5y"],
    index=1
)

adx_minimo = st.sidebar.slider(
    "ADX mínimo",
    10,
    40,
    20
)

zscore_max = st.sidebar.slider(
    "Z-Score máximo",
    -3.0,
    3.0,
    1.0,
    step=0.1
)

mostrar_grafico = st.sidebar.checkbox(
    "Mostrar gráfico do ativo selecionado",
    value=True
)

# =========================================================
# CACHE
# =========================================================

@st.cache_data(ttl=3600)
def baixar_dados(ticker, periodo):
    try:
        df = yf.download(
            ticker,
            period=periodo,
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            return None

        if len(df) < 120:
            return None

        df.dropna(inplace=True)

        return df

    except:
        return None

# =========================================================
# INDICADORES
# =========================================================

def calcular_indicadores(df):

    # EMA 69
    df["EMA69"] = ta.ema(df["Close"], length=69)

    # SAR
    sar = ta.psar(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        af=0.02,
        max_af=0.2
    )

    psar_long_col = [c for c in sar.columns if "PSARl" in c]
    psar_short_col = [c for c in sar.columns if "PSARs" in c]

    if len(psar_long_col) > 0:
        df["SAR_LONG"] = sar[psar_long_col[0]]

    if len(psar_short_col) > 0:
        df["SAR_SHORT"] = sar[psar_short_col[0]]

    # DMI / ADX
    adx = ta.adx(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        length=14
    )

    df["ADX"] = adx["ADX_14"]
    df["DMP"] = adx["DMP_14"]
    df["DMN"] = adx["DMN_14"]

    # Estocástico
    stoch = ta.stoch(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        k=14,
        d=3,
        smooth_k=3
    )

    df["STOCH_K"] = stoch["STOCHk_14_3_3"]
    df["STOCH_D"] = stoch["STOCHd_14_3_3"]

    # ATR
    df["ATR"] = ta.atr(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        length=14
    )

    # Z-SCORE
    media = df["Close"].rolling(20).mean()
    desvio = df["Close"].rolling(20).std()

    df["Z_SCORE"] = (
        (df["Close"] - media) / desvio
    )

    # Distância EMA
    df["DIST_EMA"] = (
        ((df["Close"] / df["EMA69"]) - 1) * 100
    )

    # Força tendência
    df["FORCA"] = (
        (df["DMP"] - df["DMN"]) + df["ADX"]
    )

    # Volatilidade
    df["VOLAT"] = (
        (df["ATR"] / df["Close"]) * 100
    )

    df.dropna(inplace=True)

    return df

# =========================================================
# PROBABILIDADE
# =========================================================

def calcular_score(ultimo):

    score = 0

    # Tendência
    if ultimo["Close"] > ultimo["EMA69"]:
        score += 25

    # DMI
    if ultimo["DMP"] > ultimo["DMN"]:
        score += 20

    # ADX
    if ultimo["ADX"] > 20:
        score += 15

    # Estocástico
    if ultimo["STOCH_K"] > ultimo["STOCH_D"]:
        score += 10

    # SAR
    if not pd.isna(ultimo["SAR_LONG"]):
        score += 15

    # Z-Score
    if ultimo["Z_SCORE"] < 0:
        score += 10

    # Distância EMA
    if ultimo["DIST_EMA"] < 8:
        score += 5

    return min(score, 100)

# =========================================================
# ESCANEAMENTO
# =========================================================

if st.sidebar.button("🔍 ESCANEAR MERCADO"):

    resultados = []

    progresso = st.progress(0)

    total = len(ATIVOS)

    inicio = datetime.now()

    for idx, ticker in enumerate(ATIVOS):

        df = baixar_dados(ticker, periodo)

        if df is not None:

            try:

                df = calcular_indicadores(df)

                ultimo = df.iloc[-1]
                anterior = df.iloc[-2]

                # =====================================================
                # FILTROS PRINCIPAIS
                # =====================================================

                tendencia_ok = (
                    ultimo["Close"] > ultimo["EMA69"]
                )

                dmi_ok = (
                    ultimo["DMP"] > ultimo["DMN"]
                )

                adx_ok = (
                    ultimo["ADX"] >= adx_minimo
                )

                stoch_ok = (
                    ultimo["STOCH_K"] > ultimo["STOCH_D"]
                )

                sar_ok = (
                    not pd.isna(ultimo["SAR_LONG"])
                )

                zscore_ok = (
                    ultimo["Z_SCORE"] <= zscore_max
                )

                # =====================================================
                # DETECÇÃO NOVO SINAL SAR
                # =====================================================

                sinal_novo = False

                if (
                    pd.isna(anterior["SAR_LONG"])
                    and
                    not pd.isna(ultimo["SAR_LONG"])
                ):
                    sinal_novo = True

                # =====================================================
                # SETUP FINAL
                # =====================================================

                if (
                    tendencia_ok
                    and dmi_ok
                    and adx_ok
                    and stoch_ok
                    and sar_ok
                    and zscore_ok
                ):

                    probabilidade = calcular_score(ultimo)

                    resultados.append({

                        "Ticker": ticker,

                        "Probabilidade %": probabilidade,

                        "Preço": round(float(ultimo["Close"]), 2),

                        "ADX": round(float(ultimo["ADX"]), 2),

                        "D+": round(float(ultimo["DMP"]), 2),

                        "D-": round(float(ultimo["DMN"]), 2),

                        "Z-Score": round(float(ultimo["Z_SCORE"]), 2),

                        "Stoch K": round(float(ultimo["STOCH_K"]), 2),

                        "Dist EMA69 %": round(float(ultimo["DIST_EMA"]), 2),

                        "Volatilidade %": round(float(ultimo["VOLAT"]), 2),

                        "SAR": (
                            "SINAL NOVO"
                            if sinal_novo
                            else "EM TENDÊNCIA"
                        )

                    })

            except:
                pass

        progresso.progress((idx + 1) / total)

    fim = datetime.now()

    tempo = fim - inicio

    # =========================================================
    # RESULTADOS
    # =========================================================

    if len(resultados) > 0:

        resultado_df = pd.DataFrame(resultados)

        resultado_df = resultado_df.sort_values(
            by=[
                "Probabilidade %",
                "Z-Score"
            ],
            ascending=[
                False,
                True
            ]
        )

        st.success(
            f"✅ {len(resultado_df)} ativos encontrados | Tempo: {tempo}"
        )

        st.dataframe(
            resultado_df,
            use_container_width=True,
            height=700
        )

        # =====================================================
        # GRÁFICO
        # =====================================================

        if mostrar_grafico:

            ativo_escolhido = st.selectbox(
                "Selecione um ativo",
                resultado_df["Ticker"].tolist()
            )

            df_graf = baixar_dados(
                ativo_escolhido,
                periodo
            )

            if df_graf is not None:

                df_graf = calcular_indicadores(df_graf)

                graf = px.line(
                    df_graf,
                    y=[
                        "Close",
                        "EMA69"
                    ],
                    title=ativo_escolhido
                )

                st.plotly_chart(
                    graf,
                    use_container_width=True
                )

    else:

        st.warning(
            "Nenhum ativo encontrado nos critérios atuais."
        )

# =========================================================
# RODAPÉ
# =========================================================

st.markdown("---")

st.caption(
    "Terminal Buy Side PRO | EMA69 + DMI + ADX + SAR + Estocástico + Z-Score"
)
