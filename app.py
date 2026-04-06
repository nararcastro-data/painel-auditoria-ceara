import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA E ESTILOS (Cards Alinhados)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Nara Pires - Auditoria de Contratos", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        padding: 10px; border-radius: 10px; border-bottom: 8px solid;
        text-align: center; background-color: #f1f3f6;
        min-height: 150px; /* Garante que todos tenham a mesma altura */
        display: flex; flex-direction: column; justify-content: center;
    }
    .metric-card h3 { font-size: 16px !important; margin-bottom: 5px; }
    .metric-card h2 { font-size: 28px !important; margin: 5px 0; }
    .metric-card p { font-size: 12px !important; margin: 0; }
    
    .card-alto { border-color: #FF4B4B; color: #FF4B4B; }
    .card-medio { border-color: #FFA500; color: #FFA500; }
    .card-baixo { border-color: #28A745; color: #28A745; }
    .card-total { border-color: #007BFF; color: #007BFF; }
    .card-base { border-color: #6c757d; color: #6c757d; }
    </style>
    """, unsafe_allow_html=True)

# ─── 1. CARREGAMENTO DOS DADOS CRUS ───
@st.cache_data(ttl=600) 
def load_data():
    df_raw = pd.read_excel('relatorio_anomalias.xlsx', engine='openpyxl')
    
    # Renomeação conforme pedido
    df_raw = df_raw.rename(columns={
        'isn_sic': 'ID Contrato',
        'fornecedor_nome': 'Fornecedor',
        'orgao_nome': 'Órgão',
        'valor_global': 'Valor Global (R$)',
        'score_anomalia': 'Score',
        'percentil_risco': 'Percentil de Risco',
        'data_assinatura': 'Data Assinatura',
        'prazo_vigencia_dias': 'Vigência (Dias)',
        'detectado_em': 'Analisado em' # Ajuste de nome pedido
    })
    
    # Score com 2 casas decimais
    df_raw['Score'] = df_raw['Score'].round(2)
    
    df_raw['Data Assinatura'] = pd.to_datetime(df_raw['Data Assinatura'], errors='coerce')
    df_raw['Mês/Ano'] = df_raw['Data Assinatura'].dt.strftime('%m/%Y').fillna('N/A')
    
    if 'modalidade' not in df_raw.columns:
        df_raw['modalidade'] = 'N/A'
        
    return df_raw

df_base = load_data()
total_base_estatico = 50050 

# ─── 2. BARRA LATERAL: COMPACTA E FIXA ───
# Logo do Ceará no Topo (Menor)
st.sidebar.image("logo_ceara.png", width=120) 

# Estilo CSS para diminuir os espaços vazios da Sidebar
st.sidebar.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 220px; max-width: 260px; }
    [data-testid="stSidebarNav"] { display: none; }
    .st-emotion-cache-16idsys p { margin-bottom: 0px; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.subheader("Filtros")

# Filtros em linha única para economizar altura
lista_mod = ["Todas"] + sorted(list(df_base['modalidade'].dropna().unique()))
sel_mod = st.sidebar.selectbox("🎯 Modalidade", lista_mod, label_visibility="visible")

lista_meses = ["Todos"] + sorted(list(df_base['Mês/Ano'].unique()))
sel_mes = st.sidebar.selectbox("📅 Mês Assinatura", lista_meses, label_visibility="visible")

# Logo da Digital College no final (Bem pequena e sem legenda longa)
st.sidebar.markdown("---")
st.sidebar.image("logo_digital.png", width=100)
st.sidebar.caption("Digital College © 2024")

# ─── 3. FILTRAGEM (MANTENHA ESTA PARTE IGUAL) ───
df = df_base.copy()
if sel_mod != "Todas": df = df[df['modalidade'] == sel_mod]
if sel_mes != "Todos": df = df[df['Mês/Ano'] == sel_mes]

total_anoms = len(df)

# ─────────────────────────────────────────────────────────────────────────────
# FRONT-END
# ─────────────────────────────────────────────────────────────────────────────
st.title("Monitoramento de Riscos - Ceará Transparente")
st.markdown(f"**Painel de Auditoria Digital** | Atualizado: {datetime.now().strftime('%d/%m/%Y')}")

if total_anoms == 0:
    st.warning("⚠️ Nenhum contrato encontrado para os filtros selecionados.")
    st.stop()

# ─── SEÇÃO 1: CARTÕES KPIs (Títulos simplificados para alinhamento) ───
st.write("---")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="metric-card card-base"><h3>Base Total</h3><h2>{total_base_estatico:,}</h2><p>Contratos Lidos</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card card-total"><h3>Anomalias</h3><h2>{total_anoms}</h2><p>Total Isolado</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card card-alto"><h3>Risco ALTO</h3><h2>{len(df[df["nivel_risco"]=="ALTO"])}</h2><p>Crítico 🔴</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card card-medio"><h3>Risco MÉDIO</h3><h2>{len(df[df["nivel_risco"]=="MÉDIO"])}</h2><p>Atenção 🟡</p></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="metric-card card-baixo"><h3>Risco BAIXO</h3><h2>{len(df[df["nivel_risco"]=="BAIXO"])}</h2><p>Monitorado 🟢</p></div>', unsafe_allow_html=True)

# ─── SEÇÃO 2: LAYOUT DASHBOARD ───
st.write("---")
col_esq, col_dir = st.columns([1.2, 1])

with col_esq:
    st.subheader("Resumo Financeiro")
    resumo = df.groupby('nivel_risco')['Valor Global (R$)'].sum().reset_index()
    resumo.columns = ['Nível de Risco', 'Valor Total']
    ordem_r = {'ALTO': 0, 'MÉDIO': 1, 'BAIXO': 2}
    resumo['ordem'] = resumo['Nível de Risco'].map(ordem_r)
    resumo = resumo.sort_values('ordem').drop(columns=['ordem'])
    total_v = resumo['Valor Total'].sum()
    resumo = pd.concat([resumo, pd.DataFrame([{'Nível de Risco': 'TOTAL', 'Valor Total': total_v}])], ignore_index=True)
    mapa_cores = {'ALTO': '🔴 ALTO', 'MÉDIO': '🟡 MÉDIO', 'BAIXO': '🟢 BAIXO', 'TOTAL': '🔵 TOTAL'}
    resumo['Nível de Risco'] = resumo['Nível de Risco'].map(mapa_cores)
    
    st.dataframe(resumo, column_config={
        "Valor Total": st.column_config.NumberColumn(format="R$ %,.2f")
    }, use_container_width=True, hide_index=True)

    st.write("") 
    st.subheader("🏆 Ranking: Top 5 Críticos")
    top5 = df.head(5).copy()
    top5.insert(0, 'Rank', [f'{i}º' for i in range(1, len(top5)+1)])
    st.dataframe(top5[['Rank', 'ID Contrato', 'Fornecedor', 'Valor Global (R$)']], 
                 column_config={"Valor Global (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
                 use_container_width=True, hide_index=True)

with col_dir:
    st.subheader("Proporção de Risco")
    fig_p = px.pie(df, names='nivel_risco', hole=0.4, color='nivel_risco', 
                   color_discrete_map={'ALTO': '#FF4B4B', 'MÉDIO': '#FFA500', 'BAIXO': '#28A745'})
    fig_p.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_p, use_container_width=True)

# ─── SEÇÃO 3: MODALIDADE E ÓRGÃOS ───
st.write("---")
col_mod_ui, col_org_ui = st.columns([1, 1.2])

with col_mod_ui:
    st.subheader("📊 Valor por Modalidade")
    # Gráfico fixo na base original para manter todas as colunas
    df_mod_fixo = df_base.groupby('modalidade')['Valor Global (R$)'].sum().reset_index()
    fig_bar = px.bar(df_mod_fixo, x='modalidade', y='Valor Global (R$)', text_auto='.2s', color_discrete_sequence=["#1f77b4"])
    st.plotly_chart(fig_bar, use_container_width=True)

with col_org_ui:
    st.subheader("🏛️ Distribuição por Órgão")
    df_orgao = df.groupby('Órgão').agg(**{'Anomalias': ('Órgão', 'count')}, **{'Total (R$)': ('Valor Global (R$)', 'sum')}).reset_index()
    df_orgao = df_orgao.sort_values('Anomalias', ascending=False)
    st.dataframe(df_orgao, column_config={"Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f")}, use_container_width=True, hide_index=True)

# ─── SEÇÃO 4: MATRIZ DETALHADA ───
st.write("---")
st.subheader("📑 Matriz Detalhada: Top 20 Riscos (ALTO)")

# Removendo colunas desnecessárias e formatando
colunas_exibir = ['ID Contrato', 'Fornecedor', 'Órgão', 'Valor Global (R$)', 'Score', 'Data Assinatura', 'Analisado em']
df_detalhe = df[df['nivel_risco'] == 'ALTO'].head(20)[colunas_exibir]

st.dataframe(df_detalhe, column_config={
    "Valor Global (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
    "Data Assinatura": st.column_config.DateColumn(format="DD/MM/YYYY"),
    "Score": st.column_config.NumberColumn(format="%.2f")
}, use_container_width=True, hide_index=True)

st.caption(f"Painel Nara Pires | {datetime.now().strftime('%H:%M:%S')}")