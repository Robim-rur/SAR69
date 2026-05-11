import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# Configuração da página
st.set_page_config(page_title="Terminal Buy Side Pro", layout="wide")

def carregar_dados(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 70:
            return None
        return df
    except:
        return None

def calcular_setup(df):
    # 1. EMA 69 - Filtro de Tendência Mestre
    df['EMA_69'] = ta.ema(df['Close'], length=69)
    
    # 2. SAR Parabólico (Aceleração 0.02, Máximo 0.2)
    sar = ta.psar(df['High'], df['Low'], df['Close'], af=0.02, max_af=0.2)
    # O pandas-ta retorna várias colunas para o PSAR. Vamos pegar a coluna de Long (compra)
    # PSARl_0.02_0.2 (pontos abaixo do preço) e PSARs_0.02_0.2 (pontos acima)
    df['SAR_Long'] = sar['PSARl_0.02_0.2']
    df['SAR_Short'] = sar['PSARs_0.02_0.2']
    
    # 3. Matemática Probabilística: Z-Score (Média 20)
    periodo_z = 20
    df['mean'] = df['Close'].rolling(window=periodo_z).mean()
    df['std'] = df['Close'].rolling(window=periodo_z).std()
    df['z_score'] = (df['Close'] - df['mean']) / df['std']
    
    # 4. Estocástico (14, 3, 3)
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
    df = pd.concat([df, stoch], axis=1)
    
    return df

def main():
    st.title("🚀 Terminal Buy Side + SAR Parabólico")
    st.write("Filtro: Preço > EMA 69 & SAR abaixo do preço | Ranking: Z-Score")

    # Lista consolidada e higienizada
    ativos_raw = [
        "ITUB4.SA","BBDC4.SA","BBAS3.SA","BPAC11.SA","ITSA4.SA","B3SA3.SA",
        "EGIE3.SA","CPLE6.SA","CPFE3.SA","TAEE11.SA","TRPL4.SA","CMIG4.SA",
        "SAPR11.SA","SAPR4.SA","VIVT3.SA","TIMS3.SA","ABEV3.SA","PSSA3.SA",
        "MULT3.SA","ALOS3.SA","ODPV3.SA","CYRE3.SA","KEPL3.SA","POMO4.SA",
        "TOTS3.SA","PETR4.SA","PRIO3.SA","VALE3.SA","WEGE3.SA","RDOR3.SA",
        "SBSP3.SA","BBSE3.SA","GARE11.SA","HGLG11.SA","XPLG11.SA","VILG11.SA",
        "BRCO11.SA","BTLG11.SA","XPML11.SA","VISC11.SA","HSML11.SA","MALL11.SA",
        "KNRI11.SA","JSRE11.SA","PVBI11.SA","HGRE11.SA","MXRF11.SA","KNCR11.SA",
        "KNIP11.SA","CPTS11.SA","IRDM11.SA","TGAR11.SA","TRXF11.SA","HGRU11.SA",
        "ALZR11.SA","XPCA11.SA","VGIA11.SA","RBRR11.SA","KNSC11.SA","HGCR11.SA",
        "MCCI11.SA","RECR11.SA","VRTA11.SA","BCFF11.SA","HFOF11.SA","XPSF11.SA",
        "RBRP11.SA","RBRF11.SA","RZTR11.SA","RURA11.SA","VGIR11.SA","CVBI11.SA",
        "UTLL11.SA","GGRC11.SA","AUVP11.SA","IEEX11.SA","EQTL3.SA","ELET3.SA",
        "ELET6.SA","ALUP11.SA","NEOE3.SA","ENGI11.SA","CSMG3.SA","BBDC3.SA",
        "SANB11.SA","BRSR6.SA","PETR3.SA","SUZB3.SA","KLBN11.SA","JBSS3.SA",
        "RECV3.SA","RAIL3.SA","AAPL34.SA","MSFT34.SA","GOGL34.SA","AMZO34.SA",
        "META34.SA","NVDC34.SA","JPMC34.SA","DISB34.SA","SBUX34.SA","BOVA11.SA",
        "SMAL11.SA","IVVB11.SA","DIVO11.SA","GARE11.SA
    ]
    
    lista_ativos = sorted(list(set(ativos_raw)))

    if st.sidebar.button("🔍 Escanear com SAR"):
        resultados = []
        progresso = st.progress(0)
        
        for idx, ticker in enumerate(lista_ativos):
            df = carregar_dados(ticker)
            if df is not None:
                df = calcular_setup(df)
                
                ultimo = df.iloc[-1]
                anterior = df.iloc[-2]
                
                preco = ultimo['Close']
                ema69 = ultimo['EMA_69']
                z_score = ultimo['z_score']
                sar_long = ultimo['SAR_Long']
                stoch_k = ultimo['STOCHk_14_3_3']

                # FILTROS BUY SIDE:
                # 1. Preço acima da EMA 69 (Tendência)
                # 2. SAR abaixo do Preço (Momento de Compra)
                if preco > ema69 and not pd.isna(sar_long):
                    
                    # Checar se o sinal do SAR é NOVO (Inversão)
                    sinal_novo = "SINAL NOVO" if not pd.isna(ultimo['SAR_Long']) and not pd.isna(anterior['SAR_Short']) else "Mantendo Alta"
                    
                    resultados.append({
                        "Ticker": ticker,
                        "Preço": round(preco, 2),
                        "Z-Score (Prob)": round(z_score, 2),
                        "Status SAR": sinal_novo,
                        "Stoch K": round(stoch_k, 2),
                        "Dist. EMA 69 %": round(((preco/ema69)-1)*100, 2)
                    })
            
            progresso.progress((idx + 1) / len(lista_ativos))

        if resultados:
            df_final = pd.DataFrame(resultados)
            # Ranking: Primeiro ativos com SINAL NOVO, depois pelo menor Z-Score
            df_final = df_final.sort_values(by=["Status SAR", "Z-Score (Prob)"], ascending=[False, True])

            st.subheader(f"📊 Ranking: {len(df_final)} Ativos Confirmados no Buy Side")
            st.dataframe(
                df_final.style.applymap(lambda x: 'background-color: #004d00' if x == 'SINAL NOVO' else '', subset=['Status SAR'])
                .background_gradient(subset=['Z-Score (Prob)'], cmap='RdYlGn_r')
            )
        else:
            st.warning("Nenhum ativo com setup completo (Preço > EMA 69 + SAR Autoral).")

if __name__ == "__main__":
    main()
