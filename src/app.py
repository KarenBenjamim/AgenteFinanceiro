"""
Agente Financeiro Inteligente
======================================
Interface gráfica Premium Dark Cyber Mode usando Streamlit.

Para executar:
    streamlit run app.py
"""

import streamlit as st
import sys
import os
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(Path(os.path.dirname(os.path.abspath(__file__))) / ".env")

# ============================================================
# SISTEMA DE LOGGING
# ============================================================

LOG_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / "logs" / "admin_logs.json"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def inicializar_logs():
    """Inicializa o arquivo de logs se não existir."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def registrar_log(tipo: str, mensagem: str, detalhes: dict = None):
    """Registra um log no sistema."""
    try:
        inicializar_logs()
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": tipo,
            "mensagem": mensagem,
            "detalhes": detalhes or {}
        }
        logs.append(log_entry)
        if len(logs) > 1000:
            logs = logs[-1000:]
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except (IOError, json.JSONDecodeError, OSError) as e:
        print(f"Erro ao registrar log: {type(e).__name__}: {e}")

def obter_logs():
    """Obtém todos os logs."""
    try:
        inicializar_logs()
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError, OSError):
        return []

def limpar_logs():
    """Limpa todos os logs."""
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return True
    except (IOError, OSError):
        return False

# ============================================================
# IMPORTS DOS AGENTES
# ============================================================

from agente_orquestrador import classificar_mensagem
from agente_extracao import extrair_dados
from agente_conselheiro import analise_mensagem, obter_dados_planilha, analisar_historico
from data_manager import (
    registrar_despesa, registrar_renda, 
    registrar_despesa_sem_duplicar, registrar_renda_sem_duplicar,
    CATEGORIAS_DESPESAS, CATEGORIAS_RENDAS
)
from google_sheets_connector import GoogleSheetsConnector

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="FinAI - Agente Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS PREMIUM DARK CYBER MODE
# ============================================================

st.markdown("""
<style>
    /* ========== RESET E BASE ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ========== BACKGROUND PRINCIPAL ========== */
    .stApp {
        background-color: #0F172A;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #0F172A;
    }
    
    [data-testid="stHeader"] {
        background-color: #0F172A;
    }
    
    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background-color: #090D16;
        border-right: 1px solid #1E293B;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background-color: #090D16;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #94A3B8;
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: #94A3B8 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #94A3B8;
    }
    
    /* Sidebar - Item ativo */
    [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #1E293B;
        border-radius: 8px;
        padding: 8px 12px;
    }
    
    /* ========== TIPOGRAFIA ========== */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    
    .main-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
    }
    
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #94A3B8;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    p, span, label, .stMarkdown {
        color: #94A3B8;
    }
    
    /* ========== CARDS / CONTAINERS ========== */
    .cyber-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    /* Card de Métrica - Base */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: left;
        height: 100%;
    }
    
    /* Card Verde (Saldo/Receitas) */
    .metric-card-success {
        background: linear-gradient(135deg, #064E3B 0%, #022C22 100%);
        border: 1px solid #059669;
    }
    
    /* Card Vermelho (Despesas) */
    .metric-card-danger {
        background: linear-gradient(135deg, #7F1D1D 0%, #450A0A 100%);
        border: 1px solid #DC2626;
    }
    
    /* Card Azul (Regras/IA) */
    .metric-card-info {
        background: linear-gradient(135deg, #1E3A8A 0%, #172554 100%);
        border: 1px solid #3B82F6;
    }
    
    .metric-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.25rem;
    }
    
    .metric-trend {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    
    .trend-up {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
    }
    
    .trend-down {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
    }
    
    /* ========== TABELAS ========== */
    .cyber-table {
        background-color: #1E293B;
        border-radius: 12px;
        overflow: hidden;
    }
    
    [data-testid="stDataFrame"] {
        background-color: #1E293B;
        border-radius: 12px;
    }
    
    [data-testid="stDataFrame"] table {
        color: #E2E8F0;
    }
    
    [data-testid="stDataFrame"] th {
        background-color: #0F172A !important;
        color: #94A3B8 !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stDataFrame"] td {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
        border-bottom: 1px solid #334155 !important;
    }
    
    /* Valor positivo (verde) */
    .valor-positivo {
        color: #10B981 !important;
        font-weight: 600;
    }
    
    /* Valor negativo (vermelho) */
    .valor-negativo {
        color: #EF4444 !important;
        font-weight: 600;
    }
    
    /* ========== BOTÕES ========== */
    .stButton > button,
    .stFormSubmitButton > button,
    button[data-testid^="baseButton"] {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        padding: 0.625rem 1.25rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button *,
    .stFormSubmitButton > button *,
    button[data-testid^="baseButton"] * {
        color: #FFFFFF !important;
    }
    
    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    button[data-testid^="baseButton"]:hover {
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        color: #FFFFFF !important;
    }
    
    .stButton > button[kind="secondary"],
    .stFormSubmitButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background: #1E293B;
        color: #FFFFFF !important;
        border: 1px solid #334155;
    }
    
    .stButton > button[kind="secondary"]:hover,
    .stFormSubmitButton > button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background: #334155;
        color: #FFFFFF !important;
    }
    
    /* Botão de tipo selecionado */
    .tipo-btn-ativo {
        border-bottom: 3px solid;
        padding-bottom: 8px;
    }
    
    .tipo-receita { border-color: #10B981; }
    .tipo-despesa { border-color: #EF4444; }
    .tipo-transferencia { border-color: #3B82F6; }
    
    /* ========== INPUTS ========== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
        padding: 0.75rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    .stSelectbox > div > div {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox > div > div > div {
        color: #E2E8F0 !important;
    }
    
    .stDateInput > div > div > input {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        color: #E2E8F0 !important;
    }
    
    /* ========== FILE UPLOADER ========== */
    [data-testid="stFileUploader"] {
        background-color: #1E293B;
        border: 2px dashed #334155;
        border-radius: 12px;
        padding: 1rem;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #3B82F6;
    }
    
    /* ========== CHAT ========== */
    [data-testid="stChatMessage"] {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #2563EB;
    }
    
    .stChatInputContainer {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    
    /* Pílulas de sugestão */
    .suggestion-pill {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        color: #94A3B8;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .suggestion-pill:hover {
        background-color: #334155;
        color: #FFFFFF;
    }
    
    /* ========== BADGES DE STATUS ========== */
    .status-badge {
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .badge-green {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
    }
    
    .badge-yellow {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
    }
    
    .badge-red {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
    }
    
    /* ========== EXPANDERS ========== */
    .streamlit-expanderHeader {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderContent {
        background-color: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 0 0 8px 8px !important;
    }
    
    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0F172A;
        gap: 0;
        border-bottom: 1px solid #334155;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8;
        background-color: transparent;
        border-radius: 0;
        padding: 1rem 1.5rem;
        border-bottom: 2px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF;
    }
    
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: transparent !important;
        border-bottom: 2px solid #3B82F6 !important;
    }
    
    /* ========== ALERTAS ========== */
    .stAlert {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }
    
    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0F172A;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
    
    /* ========== DIVIDERS ========== */
    hr {
        border-color: #334155;
        margin: 1.5rem 0;
    }
    
    /* ========== HIDE STREAMLIT DEFAULTS ========== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ========== CONFIG ITEMS ADMIN ========== */
    .config-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid #334155;
    }
    
    .config-icon {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        font-size: 1rem;
    }
    
    .config-label {
        flex: 1;
        color: #E2E8F0;
        font-weight: 500;
    }
    
    .config-value {
        color: #94A3B8;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INICIALIZAÇÃO DO ESTADO
# ============================================================

if 'historico_chat' not in st.session_state:
    st.session_state.historico_chat = []

if 'transacoes_pendentes' not in st.session_state:
    st.session_state.transacoes_pendentes = []

if 'tipo_transacao' not in st.session_state:
    st.session_state.tipo_transacao = "despesa"

if 'admin_autenticado' not in st.session_state:
    st.session_state.admin_autenticado = False

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def processar_valor(valor_str: str) -> float:
    """Converte string de valor para float."""
    if not valor_str:
        return 0.0
    try:
        valor = str(valor_str).replace("R$", "").replace(" ", "")
        valor = valor.replace(".", "").replace(",", ".")
        return float(valor)
    except:
        return 0.0

def formatar_moeda(valor: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_dados_planilha():
    """Carrega dados da planilha com cache."""
    try:
        dados = obter_dados_planilha()
        if "erro" not in dados:
            return dados
        return {"despesas": [], "rendas": []}
    except (ConnectionError, TimeoutError, Exception) as e:
        print(f"Erro ao carregar planilha: {type(e).__name__}: {e}")
        return {"despesas": [], "rendas": []}

# ============================================================
# SIDEBAR - NAVEGAÇÃO
# ============================================================

with st.sidebar:
    # Logo/Título
    st.markdown("""
    <div style="padding: 1rem 0; text-align: center; border-bottom: 1px solid #1E293B; margin-bottom: 1rem;">
        <span style="font-size: 1.5rem; font-weight: 700; color: #FFFFFF;">📊 Agente Financeiro</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu de navegação
    pagina = st.radio(
        "Menu",
        ["Início", "Chat AI", "Nova Transação", "Histórico", "Admin (Logs)"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Info na sidebar
    st.markdown("""
    <div style="padding: 1rem; background-color: #1E293B; border-radius: 8px; margin-top: 1rem;">
        <p style="color: #94A3B8; font-size: 0.8rem; margin: 0;">
            Assistente financeiro inteligente com IA
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PÁGINA: INÍCIO
# ============================================================

if pagina == "Início":
    st.markdown('<h1 class="main-title">Seu Início Financeiro.</h1>', unsafe_allow_html=True)
    
    dados = carregar_dados_planilha()
    analise = analisar_historico(dados) if (dados.get("despesas") or dados.get("rendas")) else None
    
    if analise:
        total_despesas = analise['total_despesas']
        total_rendas = analise['total_rendas']
        saldo = total_rendas - total_despesas
        num_regras = 5  # Placeholder
    else:
        total_despesas = 0
        total_rendas = 0
        saldo = 0
        num_regras = 0
    
    # ===== CARDS DE MÉTRICAS =====
    col1, col2, col3 = st.columns(3)
    
    with col1:
        trend_class = "trend-up" if saldo >= 0 else "trend-down"
        trend_text = "Trendin ↗" if saldo >= 0 else "Trendin ↘"
        st.markdown(f'''
        <div class="metric-card metric-card-success">
            <div class="metric-label">Saldo Atual</div>
            <div class="metric-value">{formatar_moeda(saldo)}</div>
            <span class="metric-trend {trend_class}">{trend_text}</span>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card metric-card-danger">
            <div class="metric-label">Despesas do Mês</div>
            <div class="metric-value">{formatar_moeda(total_despesas)}</div>
            <span class="metric-trend trend-down">Trendin ↗</span>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card metric-card-info">
            <div class="metric-label">Regras Ativas</div>
            <div class="metric-value">{num_regras} Regras</div>
            <span style="color: #94A3B8;">⚙️</span>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ===== TRANSAÇÕES PENDENTES =====
    st.markdown('<p class="section-title">Transações Pendentes</p>', unsafe_allow_html=True)
    
    # Criar dados de exemplo ou usar dados reais
    if dados.get("despesas") or dados.get("rendas"):
        # Combina e pega as últimas transações
        todas_transacoes = []
        
        for d in dados.get("despesas", [])[:3]:
            todas_transacoes.append({
                "Data": d.get("data", ""),
                "Descrição": d.get("descricao", ""),
                "Categoria": "Despesa",
                "Valor": f'-{formatar_moeda(processar_valor(d.get("valor", 0)))}'
            })
        
        for r in dados.get("rendas", [])[:3]:
            todas_transacoes.append({
                "Data": r.get("data", ""),
                "Descrição": r.get("descricao", ""),
                "Categoria": "Receitas",
                "Valor": formatar_moeda(processar_valor(r.get("valor", 0)))
            })
        
        if todas_transacoes:
            df_pendentes = pd.DataFrame(todas_transacoes)
            
            # Estilizar valores
            def style_valor(val):
                if val.startswith('-'):
                    return 'color: #EF4444; font-weight: 600;'
                return 'color: #10B981; font-weight: 600;'
            
            st.dataframe(
                df_pendentes,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Data": st.column_config.TextColumn("Data", width="small"),
                    "Descrição": st.column_config.TextColumn("Descrição", width="medium"),
                    "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                    "Valor": st.column_config.TextColumn("Valor", width="small"),
                }
            )
    else:
        st.info("📋 Nenhuma transação pendente. Adicione suas primeiras transações!")
    
    # ===== GRÁFICOS DE PIZZA =====
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-title">Distribuição por Categoria</p>', unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gráfico de Despesas por Categoria
        if dados.get("despesas"):
            despesas_por_cat = {}
            for d in dados.get("despesas", []):
                cat = d.get("categoria", "Outros")
                valor = processar_valor(d.get("valor", 0))
                despesas_por_cat[cat] = despesas_por_cat.get(cat, 0) + valor
            
            if despesas_por_cat:
                df_desp = pd.DataFrame({
                    "Categoria": list(despesas_por_cat.keys()),
                    "Valor": list(despesas_por_cat.values())
                })
                
                fig_desp = px.pie(
                    df_desp,
                    values="Valor",
                    names="Categoria",
                    title="💸 Despesas por Categoria",
                    color_discrete_sequence=px.colors.sequential.Reds_r,
                    hole=0.4
                )
                fig_desp.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#E2E8F0",
                    title_font_size=16,
                    showlegend=True,
                    legend=dict(font=dict(size=10))
                )
                st.plotly_chart(fig_desp, use_container_width=True)
        else:
            st.markdown('''
            <div class="cyber-card" style="height: 250px; display: flex; align-items: center; justify-content: center;">
                <div style="text-align: center;">
                    <span style="font-size: 2rem;">💸</span>
                    <p style="color: #94A3B8; margin-top: 0.5rem;">Sem despesas registradas</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    with col_chart2:
        # Gráfico de Rendas por Categoria
        if dados.get("rendas"):
            rendas_por_cat = {}
            for r in dados.get("rendas", []):
                cat = r.get("categoria", "Outros")
                valor = processar_valor(r.get("valor", 0))
                rendas_por_cat[cat] = rendas_por_cat.get(cat, 0) + valor
            
            if rendas_por_cat:
                df_rend = pd.DataFrame({
                    "Categoria": list(rendas_por_cat.keys()),
                    "Valor": list(rendas_por_cat.values())
                })
                
                fig_rend = px.pie(
                    df_rend,
                    values="Valor",
                    names="Categoria",
                    title="💰 Rendas por Categoria",
                    color_discrete_sequence=px.colors.sequential.Greens_r,
                    hole=0.4
                )
                fig_rend.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#E2E8F0",
                    title_font_size=16,
                    showlegend=True,
                    legend=dict(font=dict(size=10))
                )
                st.plotly_chart(fig_rend, use_container_width=True)
        else:
            st.markdown('''
            <div class="cyber-card" style="height: 250px; display: flex; align-items: center; justify-content: center;">
                <div style="text-align: center;">
                    <span style="font-size: 2rem;">💰</span>
                    <p style="color: #94A3B8; margin-top: 0.5rem;">Sem rendas registradas</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)

# ============================================================
# PÁGINA: CHAT AI
# ============================================================

elif pagina == "Chat AI":
    st.markdown('<h1 class="main-title">Chat AI Financeiro</h1>', unsafe_allow_html=True)
    
    # Função para processar mensagem e gerar resposta
    def processar_mensagem_chat(mensagem: str) -> str:
        try:
            classificacao = classificar_mensagem(mensagem)
            rota = classificacao.get("rota", "assunto")
            
            if rota == "dados":
                dados_extraidos = extrair_dados(mensagem)
                transacoes = dados_extraidos.get("transacoes", {})
                despesas = transacoes.get("despesas", [])
                rendas = transacoes.get("rendas", [])
                
                if despesas or rendas:
                    resposta = "📊 **Transações identificadas:**\n\n"
                    sucesso = 0
                    
                    for d in despesas:
                        data = d.get("Data", datetime.now().strftime("%d/%m/%Y"))
                        valor = d.get("Valor", 0) or 0
                        desc = d.get("Descricao", "Sem descrição")
                        cat = d.get("Categoria", "Outros")
                        
                        if registrar_despesa(data, valor, desc, cat):
                            resposta += f"✅ **Despesa:** {desc} - {formatar_moeda(valor)} [{cat}]\n"
                            sucesso += 1
                    
                    for r in rendas:
                        data = r.get("Data", datetime.now().strftime("%d/%m/%Y"))
                        valor = r.get("Valor", 0) or 0
                        desc = r.get("Descricao", "Sem descrição")
                        cat = r.get("Categoria", "Outros")
                        
                        if registrar_renda(data, valor, desc, cat):
                            resposta += f"✅ **Renda:** {desc} - {formatar_moeda(valor)} [{cat}]\n"
                            sucesso += 1
                    
                    resposta += f"\n📝 Total: {sucesso} transação(ões) registrada(s)!"
                    return resposta
                else:
                    return "⚠️ Não consegui identificar transações. Tente ser mais específico."
            else:
                resultado = analise_mensagem(mensagem)
                return resultado.get("resposta_texto", "Desculpe, não consegui processar sua pergunta.")
        except Exception as e:
            return f"❌ Erro ao processar: {str(e)}"
    
    # Verificar se há mensagem pendente para processar
    if 'mensagem_pendente' not in st.session_state:
        st.session_state.mensagem_pendente = None
    
    # Processar mensagem pendente (de botões de sugestão)
    if st.session_state.mensagem_pendente:
        mensagem = st.session_state.mensagem_pendente
        st.session_state.mensagem_pendente = None
        
        with st.spinner("🔄 Analisando..."):
            resposta = processar_mensagem_chat(mensagem)
        
        st.session_state.historico_chat.append({'tipo': 'assistant', 'texto': resposta})
    
    # Container do chat
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.historico_chat:
            if msg['tipo'] == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.write(msg['texto'])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg['texto'])
    
    # Input de chat
    prompt = st.chat_input("Digite sua pergunta aqui...")
    
    if prompt:
        st.session_state.historico_chat.append({'tipo': 'user', 'texto': prompt})
        
        with st.spinner("🔄 Analisando..."):
            resposta = processar_mensagem_chat(prompt)
        
        st.session_state.historico_chat.append({'tipo': 'assistant', 'texto': resposta})
        st.rerun()
    
    # Sugestões rápidas
    st.markdown("---")
    st.markdown('<p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 0.5rem;">Sugestões rápidas:</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Resumo do Mês", use_container_width=True):
            st.session_state.historico_chat.append({'tipo': 'user', 'texto': "Me dê um resumo do mês"})
            st.session_state.mensagem_pendente = "Me dê um resumo do mês"
            st.rerun()
    
    with col2:
        if st.button("💰 Meta de Economia", use_container_width=True):
            st.session_state.historico_chat.append({'tipo': 'user', 'texto': "Como posso economizar mais?"})
            st.session_state.mensagem_pendente = "Como posso economizar mais?"
            st.rerun()
    
    with col3:
        if st.button("📈 Análise de Dívidas", use_container_width=True):
            st.session_state.historico_chat.append({'tipo': 'user', 'texto': "Analise minhas dívidas"})
            st.session_state.mensagem_pendente = "Analise minhas dívidas"
            st.rerun()
    
    with col4:
        if st.button("💡 Dicas de Investimento", use_container_width=True):
            st.session_state.historico_chat.append({'tipo': 'user', 'texto': "Me dê dicas de investimento"})
            st.session_state.mensagem_pendente = "Me dê dicas de investimento"
            st.rerun()
    
    # Botão limpar
    if st.session_state.historico_chat:
        if st.button("🗑️ Limpar Histórico"):
            st.session_state.historico_chat = []
            st.rerun()

# ============================================================
# PÁGINA: NOVA TRANSAÇÃO
# ============================================================

elif pagina == "Nova Transação":
    st.markdown('<h1 class="main-title">Nova Transação / Lançamento</h1>', unsafe_allow_html=True)
    
    # Botões de tipo de transação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💰 Renda", use_container_width=True, type="primary" if st.session_state.tipo_transacao == "receita" else "secondary"):
            st.session_state.tipo_transacao = "receita"
            st.rerun()
    
    with col2:
        if st.button("🛑 Despesa", use_container_width=True, type="primary" if st.session_state.tipo_transacao == "despesa" else "secondary"):
            st.session_state.tipo_transacao = "despesa"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Descrição
    descricao = st.text_input("Descrição", placeholder="Ex: Supermercado")
    
    # Linha com Montante e Categoria
    col1, col2 = st.columns(2)
    
    with col1:
        valor = st.number_input("Montante (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    with col2:
        if st.session_state.tipo_transacao == "receita":
            categoria = st.selectbox("Categoria", ["Selecione..."] + CATEGORIAS_RENDAS)
        else:
            categoria = st.selectbox("Categoria", ["Selecione..."] + CATEGORIAS_DESPESAS)
    
    # Data
    data_transacao = st.date_input("Data", datetime.now())
    
    # Botão de salvar
    if st.button("✅ Salvar Transação", use_container_width=True, type="primary"):
        if valor > 0 and descricao and categoria != "Selecione...":
            data_formatada = data_transacao.strftime("%d/%m/%Y")
            
            if st.session_state.tipo_transacao == "receita":
                sucesso = registrar_renda(data_formatada, valor, descricao, categoria)
            else:
                sucesso = registrar_despesa(data_formatada, valor, descricao, categoria)
            
            if sucesso:
                st.success(f"✅ {st.session_state.tipo_transacao.title()} registrada: {descricao} - {formatar_moeda(valor)}")
                registrar_log(st.session_state.tipo_transacao.upper(), f"Transação registrada: {descricao}", {
                    "data": data_formatada,
                    "valor": valor,
                    "categoria": categoria
                })
            else:
                st.error("❌ Erro ao registrar. Verifique a conexão.")
        else:
            st.warning("⚠️ Preencha todos os campos obrigatórios.")
    
    # Seção de importar arquivo
    st.markdown("---")
    st.markdown('<p class="section-title">Importar Arquivo</p>', unsafe_allow_html=True)
    
    arquivo = st.file_uploader(
        "Arraste ou clique para importar",
        type=["pdf", "png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )
    
    if st.button("Confirmar Importação", type="primary", use_container_width=True):
        if arquivo:
            with st.spinner("Processando arquivo..."):
                try:
                    from agente_leitor import processar_arquivo, registrar_transacoes_extraidas
                    
                    arquivo_bytes = arquivo.read()
                    dados_extraidos = processar_arquivo(arquivo_bytes, arquivo.name)
                    transacoes = dados_extraidos.get("transacoes", [])
                    
                    if transacoes:
                        resultado = registrar_transacoes_extraidas(transacoes)
                        
                        # Mostrar resultados abaixo
                        st.markdown("---")
                        st.markdown('<p class="section-title">Resultado da Importação</p>', unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("✅ Importadas", resultado['adicionadas'])
                        with col2:
                            st.metric("⚠️ Duplicadas", resultado['duplicatas'])
                        with col3:
                            st.metric("❌ Erros", resultado['erros'])
                        
                        if resultado['adicionadas'] > 0:
                            st.success(f"🎉 {resultado['adicionadas']} transação(ões) importada(s) com sucesso!")
                        
                        if resultado['duplicatas'] > 0:
                            st.warning(f"⚠️ {resultado['duplicatas']} transação(ões) já existiam (ignoradas).")
                        
                        if resultado['erros'] > 0:
                            st.error(f"❌ {resultado['erros']} erro(s) durante a importação.")
                            with st.expander("Ver detalhes dos erros"):
                                for d in resultado.get('detalhes', []):
                                    if d.get('status') == 'erro':
                                        t = d.get('transacao', {})
                                        st.write(f"• {t.get('data')} | R$ {t.get('valor', 0):.2f} | {t.get('descricao')}")
                    else:
                        st.warning("Nenhuma transação encontrada no arquivo.")
                except Exception as e:
                    st.error(f"Erro ao processar: {str(e)}")
        else:
            st.warning("Selecione um arquivo primeiro.")

# ============================================================
# PÁGINA: HISTÓRICO
# ============================================================

elif pagina == "Histórico":
    st.markdown('<h1 class="main-title">Histórico Completo de Transações</h1>', unsafe_allow_html=True)
    
    # Barra de filtros
    col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
    
    with col1:
        data_filtro = st.date_input("Data", datetime.now(), key="filtro_data")
    
    with col2:
        categoria_filtro = st.selectbox("Categoria", ["Todas"] + CATEGORIAS_DESPESAS + CATEGORIAS_RENDAS)
    
    with col3:
        status_filtro = st.selectbox("Status", ["Ativas", "Pendentes", "Concluídas"])
    
    with col4:
        busca = st.text_input("🔍 Buscar", placeholder="Buscar transação...")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Carregar dados
    dados = carregar_dados_planilha()
    
    # Preparar DataFrame combinado
    todas_transacoes = []
    
    for d in dados.get("despesas", []):
        valor = processar_valor(d.get("valor", 0))
        todas_transacoes.append({
            "Data": d.get("data", ""),
            "Descrição": d.get("descricao", ""),
            "Categoria": d.get("categoria", "Outros"),
            "Valor": f"-{formatar_moeda(valor)}",
            "Tipo": "Despesa"
        })
    
    for r in dados.get("rendas", []):
        valor = processar_valor(r.get("valor", 0))
        todas_transacoes.append({
            "Data": r.get("data", ""),
            "Descrição": r.get("descricao", ""),
            "Categoria": r.get("categoria", "Outros"),
            "Valor": formatar_moeda(valor),
            "Tipo": "Receita"
        })
    
    if todas_transacoes:
        df = pd.DataFrame(todas_transacoes)
        
        # Aplicar filtro de busca
        if busca:
            df = df[df['Descrição'].str.contains(busca, case=False, na=False)]
        
        # Aplicar filtro de categoria
        if categoria_filtro != "Todas":
            df = df[df['Categoria'] == categoria_filtro]
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Totais
        col1, col2 = st.columns(2)
        with col1:
            total_desp = sum(processar_valor(d.get("valor", 0)) for d in dados.get("despesas", []))
            st.markdown(f'<p style="color: #EF4444;">Total Despesas: <strong>{formatar_moeda(total_desp)}</strong></p>', unsafe_allow_html=True)
        with col2:
            total_rend = sum(processar_valor(r.get("valor", 0)) for r in dados.get("rendas", []))
            st.markdown(f'<p style="color: #10B981;">Total Receitas: <strong>{formatar_moeda(total_rend)}</strong></p>', unsafe_allow_html=True)
    else:
        st.info("📋 Nenhuma transação registrada ainda.")

# ============================================================
# PÁGINA: ADMIN (LOGS)
# ============================================================

elif pagina == "Admin (Logs)":
    st.markdown('<h1 class="main-title">Painel Admin & Logs do Sistema</h1>', unsafe_allow_html=True)

    if not ADMIN_PASSWORD:
        st.error("Senha de administrador não configurada.")
        st.info("Configure ADMIN_PASSWORD no arquivo .env para liberar o acesso ao painel Admin.")
        st.stop()

    if not st.session_state.admin_autenticado:
        st.markdown('<p class="section-title">Login Admin</p>', unsafe_allow_html=True)
        with st.form("admin_login_form"):
            senha_admin = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if entrar:
            if senha_admin == ADMIN_PASSWORD:
                st.session_state.admin_autenticado = True
                registrar_log("SUCESSO", "Login admin realizado")
                st.rerun()
            else:
                registrar_log("ERRO", "Tentativa de login admin com senha inválida")
                st.error("Senha inválida.")

        st.stop()

    col_sair, col_spacer = st.columns([1, 5])
    with col_sair:
        if st.button("Sair", use_container_width=True):
            st.session_state.admin_autenticado = False
            st.rerun()
    
    # Layout em duas colunas
    col_logs, col_config = st.columns([6, 4])
    
    with col_logs:
        st.markdown('<p class="section-title">Logs de Sistema</p>', unsafe_allow_html=True)
        
        # Filtros de log
        col1, col2 = st.columns(2)
        with col1:
            nivel_log = st.selectbox("Nível de log", ["Todos", "INFO", "SUCESSO", "ERRO"])
        with col2:
            st.selectbox("Nível de logs", ["Todos", "Debug", "Warning", "Error"])
        
        # Tabela de logs
        logs = obter_logs()
        
        if logs:
            logs_data = []
            for log in reversed(logs[-20:]):
                tipo = log.get("tipo", "INFO")
                
                # Badge de status
                if tipo in ["SUCESSO", "DESPESA", "RENDA"]:
                    status = "🟢"
                elif tipo == "ERRO":
                    status = "🔴"
                else:
                    status = "🟡"
                
                logs_data.append({
                    "Timestamp": log.get("timestamp", ""),
                    "Evento": log.get("mensagem", "")[:40] + "...",
                    "Status": status
                })
            
            df_logs = pd.DataFrame(logs_data)
            st.dataframe(df_logs, use_container_width=True, hide_index=True, height=350)
        else:
            st.info("Nenhum log registrado.")
    
    with col_config:
        st.markdown('<p class="section-title">Configurações Globais</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
        
        # Items de configuração
        st.markdown("""
        <div class="config-item">
            <div class="config-icon" style="background-color: #1E3A8A;">⚙️</div>
            <div>
                <div class="config-label">Parâmetros: 69</div>
                <div class="config-value">Parâmetros sistema: 10%</div>
            </div>
        </div>
        
        <div class="config-item">
            <div class="config-icon" style="background-color: #7C3AED;">📍</div>
            <div>
                <div class="config-label">Rolos de Estadoria</div>
                <div class="config-value">Configurado</div>
            </div>
        </div>
        
        <div class="config-item">
            <div class="config-icon" style="background-color: #059669;">👥</div>
            <div>
                <div class="config-label">Roles de usuários</div>
                <div class="config-value">Rolarels de (disable): Usuário</div>
            </div>
        </div>
        
        <div class="config-item">
            <div class="config-icon" style="background-color: #DC2626;">🤖</div>
            <div>
                <div class="config-label">Regras de automatização</div>
                <div class="config-value">Regras de IA: Ativas</div>
            </div>
        </div>
        
        <div class="config-item" style="border-bottom: none;">
            <div class="config-icon" style="background-color: #F59E0B;">🧠</div>
            <div>
                <div class="config-label">Regras de IA: Ativas</div>
                <div class="config-value">5 regras configuradas</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão de relatório
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Gerar Relatório de Auditoria", use_container_width=True, type="primary"):
            st.success("Relatório gerado com sucesso!")
    
    # Botões de ação
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col2:
        if st.button("🗑️ Limpar Logs"):
            if limpar_logs():
                st.success("Logs limpos!")
                st.rerun()

# ============================================================
# RODAPÉ
# ============================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <p style="color: #64748B; font-size: 0.8rem; margin: 0;">
        💰Agente Financeiro Inteligente | MykAI
    </p>
</div>
""", unsafe_allow_html=True)
