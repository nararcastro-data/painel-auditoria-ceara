import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA E ESTILOS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Nara Pires - Auditoria de Contratos", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        padding: 15px; border-radius: 10px; border-bottom: 8px solid;
        text-align: center; background-color: #f1f3f6;
        min-height: 160px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .card-alto { border-color: #FF4B4B; color: #FF4B4B; }
    .card-medio { border-color: #FFA500; color: #FFA500; }
    .card-baixo { border-color: #28A745; color: #28A745; }
    .card-total { border-color: #007BFF; color: #007BFF; }
    .card-base { border-color: #6c757d; color: #6c757d; }
    </style>
    """, unsafe_allow_html=True)

# ─── 1. CARREGAMENTO DOS DADOS CRUS (CACHE) ───
@st.cache_data(ttl=600) 
def load_data():
    # Lê o Excel
    df_raw = pd.read_excel('relatorio_anomalias.xlsx', engine='openpyxl')
    
    # Renomeia
    df_raw = df_raw.rename(columns={
        'isn_sic': 'Contrato',
        'fornecedor_nome': 'Fornecedor',
        'orgao_nome': 'Órgão',
        'valor_global': 'Valor Global (R$)',
        'score_anomalia': 'Score',
        'percentil_risco': 'Percentil de Risco',
        'data_assinatura': 'Data de Assinatura',
        'prazo_vigencia_dias': 'Vigência (Dias)'
    })
    
    df_raw['Score'] = df_raw['Score'].round(4)
    
    # Tratamento de Datas para o Filtro
    df_raw['Data de Assinatura'] = pd.to_datetime(df_raw['Data de Assinatura'], errors='coerce')
    df_raw['Mês/Ano'] = df_raw['Data de Assinatura'].dt.strftime('%m/%Y').fillna('Não Informado')
    
    # Proteção caso a DAG falhe em trazer a modalidade
    if 'modalidade' not in df_raw.columns:
        df_raw['modalidade'] = 'N/A'
        
    return df_raw

df_base = load_data()
total_base_estatico = 50050 # Base completa de contratos

# ─── 2. BARRA LATERAL: FILTROS DINÂMICOS ───
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135695.png", width=80)
st.sidebar.title("Filtros de Auditoria")
st.sidebar.write("Refine a busca no painel:")

# Filtro: Modalidade
lista_mod = ["Todas"] + sorted(list(df_base['modalidade'].dropna().unique()))
sel_mod = st.sidebar.selectbox("📍 Modalidade", lista_mod)

# Filtro: Data de Assinatura (Mês/Ano)
lista_meses = ["Todos"] + sorted(list(df_base['Mês/Ano'].unique()))
sel_mes = st.sidebar.selectbox("📅 Mês de Assinatura", lista_meses)

# ─── 3. APLICAÇÃO DOS FILTROS NO DATAFRAME ───
df = df_base.copy()

if sel_mod != "Todas":
    df = df[df['modalidade'] == sel_mod]

if sel_mes != "Todos":
    df = df[df['Mês/Ano'] == sel_mes]

# ─── 4. RECALCULANDO TABELAS COM OS DADOS FILTRADOS ───
total_anoms = len(df)

if total_anoms > 0:
    # Recalcula Órgãos
    df_orgao = df.groupby('Órgão').agg(
        **{'Qtd Anomalias': ('Órgão', 'count')},
        **{'Valor Total (R$)': ('Valor Global (R$)', 'sum')}
    ).reset_index()
    df_orgao['% do Total'] = (df_orgao['Qtd Anomalias'] / total_anoms) * 100
    df_orgao = df_orgao.sort_values('Qtd Anomalias', ascending=False)
    
    # Recalcula Modalidades
    df_mod = df.groupby('modalidade')['Valor Global (R$)'].sum().reset_index()
    df_mod.columns = ['modalidade', 'valor']
    df_mod = df_mod.sort_values('valor', ascending=False)
else:
    # Se o filtro ficar vazio, cria tabelas em branco para não dar erro na tela
    df_orgao = pd.DataFrame(columns=['Órgão', 'Qtd Anomalias', 'Valor Total (R$)', '% do Total'])
    df_mod = pd.DataFrame(columns=['modalidade', 'valor'])

# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO DO DASHBOARD (FRONT-END)
# ─────────────────────────────────────────────────────────────────────────────
st.title("🔎 Monitoramento de Riscos - Ceará Transparente")
st.markdown(f"**Painel de Auditoria Digital** | Data: {datetime.now().strftime('%d/%m/%Y')}")

if total_anoms == 0:
    st.warning("⚠️ Nenhum contrato atípico encontrado para os filtros selecionados.")
    st.stop() # Para de desenhar a tela se não houver dados

# ─── SEÇÃO 1: CARTÕES KPIs ───
st.write("---")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="metric-card card-base"><h3>Contratos</h3><h2>{total_base_estatico:,}</h2><p>Base Completa</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card card-total"><h3>Total Analisado</h3><h2>{total_anoms}</h2><p>Anomalias Detectadas 🔍</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card card-alto"><h3>Risco ALTO 🔴</h3><h2>{len(df[df["nivel_risco"]=="ALTO"])}</h2><p>Crítico ▲</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card card-medio"><h3>Risco MÉDIO 🟡</h3><h2>{len(df[df["nivel_risco"]=="MÉDIO"])}</h2><p>Atenção ▬</p></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="metric-card card-baixo"><h3>Risco BAIXO 🟢</h3><h2>{len(df[df["nivel_risco"]=="BAIXO"])}</h2><p>Monitorado ▼</p></div>', unsafe_allow_html=True)

# ─── SEÇÃO 2: FAIXA DE COMANDO DE RISCO (LAYOUT AJUSTADO) ───
st.write("---")
col_esq, col_dir = st.columns([1.2, 1])

with col_esq:
    st.subheader("💰 Resumo Financeiro")
    resumo = df.groupby('nivel_risco')['Valor Global (R$)'].sum().reset_index()
    resumo.columns = ['Nível de Risco', 'Valor Total em Risco']
    
    ordem_r = {'ALTO': 0, 'MÉDIO': 1, 'BAIXO': 2}
    resumo['ordem'] = resumo['Nível de Risco'].map(ordem_r)
    resumo = resumo.sort_values('ordem').drop(columns=['ordem'])
    
    total_v = resumo['Valor Total em Risco'].sum()
    linha_t = pd.DataFrame([{'Nível de Risco': 'TOTAL GERAL', 'Valor Total em Risco': total_v}])
    resumo = pd.concat([resumo, linha_t], ignore_index=True)
    
    mapa_cores = {'ALTO': '🔴 ALTO', 'MÉDIO': '🟡 MÉDIO', 'BAIXO': '🟢 BAIXO', 'TOTAL GERAL': '🔵 TOTAL'}
    resumo['Nível de Risco'] = resumo['Nível de Risco'].map(mapa_cores)
    
    st.dataframe(resumo, column_config={
        "Nível de Risco": st.column_config.TextColumn("Nível de Risco"),
        "Valor Total em Risco": st.column_config.NumberColumn("Valor Total em Risco", format="R$ %,.2f")
    }, use_container_width=True, hide_index=True)

    st.write("") 

    st.subheader("🏆 Ranking: Top 5 Críticos")
    top5 = df.head(5).copy()
    top5.insert(0, 'Rank', [f'{i}º' for i in range(1, len(top5)+1)])
    st.dataframe(top5[['Rank', 'Contrato', 'Fornecedor', 'Valor Global (R$)']], 
                 column_config={"Valor Global (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
                 use_container_width=True, hide_index=True)

with col_dir:
    st.subheader("🍕 Proporção de Risco")
    fig_p = px.pie(df, names='nivel_risco', hole=0.4, color='nivel_risco', 
                   color_discrete_map={'ALTO': '#FF4B4B', 'MÉDIO': '#FFA500', 'BAIXO': '#28A745'})
    fig_p.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
    fig_p.update_layout(margin=dict(t=20, b=20, l=20, r=20),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    st.plotly_chart(fig_p, use_container_width=True)

# ─── SEÇÃO 3: MODALIDADE E ÓRGÃOS ───
st.write("---")
col_mod_ui, col_org_ui = st.columns([1, 1.2])

with col_mod_ui:
    st.subheader("📊 Valor Anômalo por Modalidade")
    fig_bar = px.bar(df_mod, x='modalidade', y='valor', text_auto='.2s', 
                     labels={'valor':'Valor (R$)', 'modalidade':'Modalidade'},
                     color_discrete_sequence=["#1f77b4"])
    st.plotly_chart(fig_bar, use_container_width=True)

with col_org_ui:
    st.subheader("🏛️ Matriz de Distribuição por Órgão")
    st.dataframe(df_orgao, column_config={
        "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
        "% do Total": st.column_config.NumberColumn(format="%.2f%%")
    }, use_container_width=True, hide_index=True)

# ─── SEÇÃO 4: MATRIZ DETALHADA TOP 20 ───
st.write("---")
st.subheader("📑 Matriz Detalhada: Contratos com Maior Risco (ALTO)")
df_alto_20 = df[df['nivel_risco'] == 'ALTO'].head(20).drop(columns=['nivel_risco'])
st.dataframe(df_alto_20, column_config={
    "Valor Global (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
    "Data de Assinatura": st.column_config.DateColumn(format="DD/MM/YYYY")
}, use_container_width=True, hide_index=True)

st.caption(f"Atualizado em: {datetime.now().strftime('%H:%M:%S')}")