"""
Interface Web do Agente Financeiro
===================================
Interface gráfica usando Streamlit para interagir com o assistente financeiro.

Para executar:
    streamlit run app.py
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

# ============================================================
# SISTEMA DE LOGGING
# ============================================================

LOG_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / "logs" / "admin_logs.json"
ADMIN_PASSWORD = "141099"

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
        
        # Mantém apenas os últimos 1000 logs
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def obter_logs():
    """Obtém todos os logs."""
    try:
        inicializar_logs()
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def limpar_logs():
    """Limpa todos os logs."""
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return True
    except:
        return False
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

# CSS customizado - Tema Dark Moderno
st.markdown("""
<style>
    /* Tema Dark */
    .stApp {
        background-color: #0d1117;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #c9d1d9;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: linear-gradient(145deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #30363d;
        text-align: center;
    }
    
    .metric-card-blue {
        background: linear-gradient(145deg, #1e3a5f 0%, #0d2137 100%);
        border: 1px solid #1e4976;
    }
    
    .metric-card-green {
        background: linear-gradient(145deg, #064e3b 0%, #022c22 100%);
        border: 1px solid #047857;
    }
    
    .metric-card-purple {
        background: linear-gradient(145deg, #4c1d95 0%, #2e1065 100%);
        border: 1px solid #6b21a8;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #ffffff;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }
    
    .metric-delta-positive {
        color: #10b981;
        font-size: 0.85rem;
    }
    
    .metric-delta-negative {
        color: #ef4444;
        font-size: 0.85rem;
    }
    
    /* Títulos */
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 1.5rem;
    }
    
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    
    /* Cards de gráficos */
    .chart-container {
        background: linear-gradient(145deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #30363d;
        margin-top: 1rem;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1rem 1.5rem;
        border-radius: 15px;
        margin: 0.8rem 0;
        max-width: 80%;
        line-height: 1.5;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff !important;
        margin-left: auto;
        text-align: right;
        border-bottom-right-radius: 5px;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: #ffffff !important;
        margin-right: auto;
        text-align: left;
        border-bottom-left-radius: 5px;
    }
    
    .assistant-message strong, .user-message strong,
    .assistant-message p, .assistant-message li {
        color: #ffffff !important;
    }
    
    /* Textos gerais */
    .stMarkdown, p, span, label {
        color: #c9d1d9;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Botões */
    .stButton > button,
    .stFormSubmitButton > button,
    button[data-testid^="baseButton"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button *,
    .stFormSubmitButton > button *,
    button[data-testid^="baseButton"] * {
        color: #ffffff !important;
    }
    
    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    button[data-testid^="baseButton"]:hover {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: #ffffff !important;
    }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #21262d;
        border: 1px solid #30363d;
        color: #c9d1d9;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #161b22;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #c9d1d9;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #21262d;
        color: #c9d1d9;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #21262d;
        border: 1px solid #30363d;
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
    except:
        return {"despesas": [], "rendas": []}


# ============================================================
# SIDEBAR - NAVEGAÇÃO
# ============================================================

with st.sidebar:
    st.markdown("## 🤖 FinAI")
    st.markdown("---")
    
    pagina = st.radio(
        "Navegação",
        ["📊 Início", "💬 Chat AI", "➕ Nova Transação", "📋 Histórico", "🔐 Admin (Logs)"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Sobre")
    st.markdown("""
    Assistente financeiro inteligente com IA.
    
    **Funcionalidades:**
    - Registro de despesas/rendas
    - Classificação automática
    - Análise de gastos
    - Conselhos personalizados
    """)

# ============================================================
# PÁGINA: INÍCIO (Dashboard Principal)
# ============================================================

if pagina == "📊 Início":
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.markdown('<h1 class="main-header">Seu Início Financeiro</h1>', unsafe_allow_html=True)
    
    dados = carregar_dados_planilha()
    
    if dados.get("despesas") or dados.get("rendas"):
        analise = analisar_historico(dados)
        
        total_despesas = analise['total_despesas']
        total_rendas = analise['total_rendas']
        saldo = total_rendas - total_despesas
        
        # Cards de métricas principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delta_saldo = "↗ 1.2%" if saldo >= 0 else "↘ 1.2%"
            st.markdown(f'''
            <div class="metric-card metric-card-blue">
                <div class="metric-label">💰 Saldo Atual</div>
                <div class="metric-value">{formatar_moeda(saldo)}</div>
                <div class="metric-delta-positive">{delta_saldo}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div class="metric-card metric-card-purple">
                <div class="metric-label">💸 Gasto Mensal</div>
                <div class="metric-value">{formatar_moeda(total_despesas)}</div>
                <div class="metric-delta-negative">↘ 5%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'''
            <div class="metric-card metric-card-green">
                <div class="metric-label">📈 Renda Mensal</div>
                <div class="metric-value">{formatar_moeda(total_rendas)}</div>
                <div class="metric-delta-positive">↗ 2%</div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<p class="section-header">Despesas por Categoria</p>', unsafe_allow_html=True)
            
            if analise['despesas_por_categoria']:
                # Cria DataFrame para o gráfico
                df_desp = pd.DataFrame([
                    {"Categoria": k, "Valor": v} 
                    for k, v in analise['despesas_por_categoria'].items()
                ])
                df_desp = df_desp.sort_values("Valor", ascending=False).head(5)
                
                # Cores gradiente
                cores = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe']
                
                fig = px.bar(
                    df_desp, 
                    x='Categoria', 
                    y='Valor',
                    color='Categoria',
                    color_discrete_sequence=cores
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#c9d1d9',
                    showlegend=False,
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='#30363d')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de despesas")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<p class="section-header">Despesas vs Renda</p>', unsafe_allow_html=True)
            
            if total_rendas > 0 or total_despesas > 0:
                # Cria gráfico de rosca (donut)
                total = total_rendas + total_despesas
                pct_renda = (total_rendas / total * 100) if total > 0 else 0
                pct_despesa = (total_despesas / total * 100) if total > 0 else 0
                
                fig = go.Figure(data=[go.Pie(
                    labels=['Renda', 'Despesa'],
                    values=[total_rendas, total_despesas],
                    hole=.6,
                    marker_colors=['#10b981', '#6366f1'],
                    textinfo='percent',
                    textfont_size=14,
                    textfont_color='#ffffff'
                )])
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#c9d1d9',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                        font=dict(color='#c9d1d9')
                    ),
                    margin=dict(l=20, r=20, t=20, b=40),
                    annotations=[dict(
                        text=f'Líquido:<br>{formatar_moeda(saldo)}',
                        x=0.5, y=0.5,
                        font_size=14,
                        font_color='#ffffff',
                        showarrow=False
                    )]
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados para exibir")
            st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.info("📋 Nenhuma transação registrada ainda. Comece adicionando suas despesas e rendas!")
        
        # Cards informativos para novos usuários
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('''
            <div class="metric-card">
                <div class="metric-label">📊 Registre Transações</div>
                <p style="color: #9ca3af; font-size: 0.9rem;">Adicione suas despesas e rendas de forma rápida.</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown('''
            <div class="metric-card">
                <div class="metric-label">💬 Converse com a IA</div>
                <p style="color: #9ca3af; font-size: 0.9rem;">Pergunte sobre suas finanças em linguagem natural.</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            st.markdown('''
            <div class="metric-card">
                <div class="metric-label">📈 Visualize Dados</div>
                <p style="color: #9ca3af; font-size: 0.9rem;">Acompanhe seus gastos com gráficos e relatórios.</p>
            </div>
            ''', unsafe_allow_html=True)

# ============================================================
# PÁGINA: CHAT
# ============================================================

elif pagina == "💬 Chat AI":
    st.markdown("## 💬 Chat com Assistente")
    st.markdown("Converse comigo sobre suas finanças!")
    
    # Container para o histórico de chat
    chat_container = st.container()
    
    # Exibe histórico usando componente nativo do Streamlit
    with chat_container:
        for msg in st.session_state.historico_chat:
            if msg['tipo'] == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.write(msg['texto'])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg['texto'])
    
    # Input do usuário
    st.markdown("---")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        mensagem_usuario = st.text_input(
            "Sua mensagem",
            placeholder="Ex: Gastei R$200 no mercado hoje...",
            label_visibility="collapsed"
        )
    
    with col2:
        enviar = st.button("Enviar 📤", use_container_width=True)
    
    # Sugestões rápidas
    st.markdown("**Sugestões:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Como estão minhas finanças?"):
            mensagem_usuario = "Como estão minhas finanças?"
            enviar = True
    
    with col2:
        if st.button("💡 Onde economizar?"):
            mensagem_usuario = "Onde posso economizar?"
            enviar = True
    
    with col3:
        if st.button("📈 Previsão do mês"):
            mensagem_usuario = "Qual a previsão para o próximo mês?"
            enviar = True
    
    with col4:
        if st.button("🔝 Maiores gastos"):
            mensagem_usuario = "Quais são meus maiores gastos?"
            enviar = True
    
    # Processa a mensagem
    if enviar and mensagem_usuario:
        # Adiciona mensagem do usuário ao histórico
        st.session_state.historico_chat.append({
            'tipo': 'user',
            'texto': mensagem_usuario
        })
        
        with st.spinner("🔄 Analisando..."):
            # Classifica a mensagem
            classificacao = classificar_mensagem(mensagem_usuario)
            rota = classificacao.get("rota", "assunto")
            
            if rota == "dados":
                # Extrai dados
                dados_extraidos = extrair_dados(mensagem_usuario)
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
                        else:
                            resposta += f"⚠️ **Despesa (não salva):** {desc} - {formatar_moeda(valor)}\n"
                    
                    for r in rendas:
                        data = r.get("Data", datetime.now().strftime("%d/%m/%Y"))
                        valor = r.get("Valor", 0) or 0
                        desc = r.get("Descricao", "Sem descrição")
                        cat = r.get("Categoria", "Outros")
                        
                        if registrar_renda(data, valor, desc, cat):
                            resposta += f"✅ **Renda:** {desc} - {formatar_moeda(valor)} [{cat}]\n"
                            sucesso += 1
                        else:
                            resposta += f"⚠️ **Renda (não salva):** {desc} - {formatar_moeda(valor)}\n"
                    
                    resposta += f"\n📝 Total de {sucesso} transação(ões) salva(s) na planilha!"
                else:
                    resposta = "⚠️ Não consegui identificar transações claras. Tente fornecer: data, valor, descrição e categoria."
            else:
                # Análise/conselho
                resultado = analise_mensagem(mensagem_usuario)
                resposta = resultado.get("resposta_texto", "Desculpe, não consegui processar sua pergunta.")
        
        # Adiciona resposta ao histórico
        st.session_state.historico_chat.append({
            'tipo': 'assistant',
            'texto': resposta
        })
        
        st.rerun()
    
    # Botão para limpar histórico
    if st.session_state.historico_chat:
        if st.button("🗑️ Limpar Histórico"):
            st.session_state.historico_chat = []
            st.rerun()

# ============================================================
# PÁGINA: NOVA TRANSAÇÃO
# ============================================================

elif pagina == "➕ Nova Transação":
    st.markdown("## ➕ Registrar Nova Transação")
    
    tab1, tab2 = st.tabs(["💸 Despesa", "💰 Renda"])
    
    with tab1:
        st.markdown("### Adicionar Despesa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            desp_data = st.date_input("📅 Data", datetime.now(), key="desp_data")
            desp_valor = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, key="desp_valor")
        
        with col2:
            desp_desc = st.text_input("📝 Descrição", key="desp_desc")
            desp_cat = st.selectbox("🏷️ Categoria", CATEGORIAS_DESPESAS, key="desp_cat")
        
        if st.button("✅ Registrar Despesa", use_container_width=True, type="primary"):
            if desp_valor > 0 and desp_desc:
                data_formatada = desp_data.strftime("%d/%m/%Y")
                if registrar_despesa(data_formatada, desp_valor, desp_desc, desp_cat):
                    st.success(f"✅ Despesa registrada: {desp_desc} - {formatar_moeda(desp_valor)} [{desp_cat}]")
                    registrar_log("DESPESA", f"Despesa registrada: {desp_desc}", {
                        "data": data_formatada,
                        "valor": desp_valor,
                        "descricao": desp_desc,
                        "categoria": desp_cat,
                        "origem": "formulario_manual"
                    })
                else:
                    st.error("❌ Erro ao registrar despesa. Verifique a conexão com a planilha.")
                    registrar_log("ERRO", f"Falha ao registrar despesa: {desp_desc}", {
                        "data": data_formatada,
                        "valor": desp_valor,
                        "descricao": desp_desc,
                        "categoria": desp_cat
                    })
            else:
                st.warning("⚠️ Preencha valor e descrição.")
    
    with tab2:
        st.markdown("### Adicionar Renda")
        
        col1, col2 = st.columns(2)
        
        with col1:
            rend_data = st.date_input("📅 Data", datetime.now(), key="rend_data")
            rend_valor = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, key="rend_valor")
        
        with col2:
            rend_desc = st.text_input("📝 Descrição", key="rend_desc")
            rend_cat = st.selectbox("🏷️ Categoria", CATEGORIAS_RENDAS, key="rend_cat")
        
        if st.button("✅ Registrar Renda", use_container_width=True, type="primary"):
            if rend_valor > 0 and rend_desc:
                data_formatada = rend_data.strftime("%d/%m/%Y")
                if registrar_renda(data_formatada, rend_valor, rend_desc, rend_cat):
                    st.success(f"✅ Renda registrada: {rend_desc} - {formatar_moeda(rend_valor)} [{rend_cat}]")
                    registrar_log("RENDA", f"Renda registrada: {rend_desc}", {
                        "data": data_formatada,
                        "valor": rend_valor,
                        "descricao": rend_desc,
                        "categoria": rend_cat,
                        "origem": "formulario_manual"
                    })
                else:
                    st.error("❌ Erro ao registrar renda. Verifique a conexão com a planilha.")
                    registrar_log("ERRO", f"Falha ao registrar renda: {rend_desc}", {
                        "data": data_formatada,
                        "valor": rend_valor,
                        "descricao": rend_desc,
                        "categoria": rend_cat
                    })
            else:
                st.warning("⚠️ Preencha valor e descrição.")
    
    st.markdown("---")
    st.markdown("### 🚀 Registro Rápido por Texto")
    st.markdown("Descreva suas transações em linguagem natural:")
    
    texto_rapido = st.text_area(
        "Exemplo: 'Gastei R$200 no mercado e R$50 no Uber. Recebi R$3500 de salário.'",
        height=100
    )
    
    if st.button("📤 Processar Texto", use_container_width=True):
        if texto_rapido:
            with st.spinner("🔄 Extraindo transações..."):
                registrar_log("EXTRAÇÃO", "Iniciando extração de texto", {"texto": texto_rapido[:200]})
                dados_extraidos = extrair_dados(texto_rapido)
                transacoes = dados_extraidos.get("transacoes", {})
                despesas = transacoes.get("despesas", [])
                rendas = transacoes.get("rendas", [])
                
                if despesas or rendas:
                    st.markdown("#### Transações Encontradas:")
                    registrar_log("SUCESSO", f"Extração concluída: {len(despesas)} despesas, {len(rendas)} rendas", {
                        "despesas": despesas,
                        "rendas": rendas
                    })
                    
                    for d in despesas:
                        data = d.get("Data", datetime.now().strftime("%d/%m/%Y"))
                        valor = d.get("Valor", 0) or 0
                        desc = d.get("Descricao", "")
                        cat = d.get("Categoria", "Outros")
                        
                        if registrar_despesa(data, valor, desc, cat):
                            st.success(f"✅ Despesa: {desc} - {formatar_moeda(valor)} [{cat}]")
                            registrar_log("DESPESA", f"Despesa de texto: {desc}", {"data": data, "valor": valor, "categoria": cat, "origem": "texto_rapido"})
                        else:
                            registrar_log("ERRO", f"Falha ao registrar despesa de texto: {desc}", {"data": data, "valor": valor, "categoria": cat})
                    
                    for r in rendas:
                        data = r.get("Data", datetime.now().strftime("%d/%m/%Y"))
                        valor = r.get("Valor", 0) or 0
                        desc = r.get("Descricao", "")
                        cat = r.get("Categoria", "Outros")
                        
                        if registrar_renda(data, valor, desc, cat):
                            st.success(f"✅ Renda: {desc} - {formatar_moeda(valor)} [{cat}]")
                            registrar_log("RENDA", f"Renda de texto: {desc}", {"data": data, "valor": valor, "categoria": cat, "origem": "texto_rapido"})
                        else:
                            registrar_log("ERRO", f"Falha ao registrar renda de texto: {desc}", {"data": data, "valor": valor, "categoria": cat})
                else:
                    st.warning("⚠️ Não encontrei transações no texto. Tente ser mais específico.")
                    registrar_log("INFO", "Nenhuma transação encontrada no texto", {"texto": texto_rapido[:200]})
        else:
            st.warning("⚠️ Digite algo para processar.")
    
    # =========================================================
    # UPLOAD DE ARQUIVOS (PDF e Imagens)
    # =========================================================
    st.markdown("---")
    st.markdown("### 📂 Importar de Arquivo")
    st.markdown("""
    Envie um **extrato bancário (PDF)** ou **print de movimentações (imagem)**.
    O sistema irá extrair automaticamente as transações e registrar na planilha.
    
    ⚠️ **Verificação de duplicidade:** Transações já existentes não serão adicionadas novamente.
    """)
    
    arquivo_upload = st.file_uploader(
        "Arraste ou selecione um arquivo",
        type=["pdf", "png", "jpg", "jpeg", "gif", "webp"],
        help="Formatos suportados: PDF, PNG, JPG, JPEG, GIF, WEBP"
    )
    
    if arquivo_upload is not None:
        # Mostra preview para imagens
        if arquivo_upload.type.startswith("image/"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(arquivo_upload, caption="Preview", width=200)
            with col2:
                st.info(f"📄 Arquivo: {arquivo_upload.name}\n\n📊 Tamanho: {arquivo_upload.size / 1024:.1f} KB")
        else:
            st.info(f"📄 Arquivo: {arquivo_upload.name} | 📊 Tamanho: {arquivo_upload.size / 1024:.1f} KB")
        
        if st.button("🔍 Extrair e Registrar Transações", use_container_width=True, type="primary"):
            with st.spinner("🔄 Processando arquivo... Isso pode levar alguns segundos."):
                try:
                    # Importa o agente leitor
                    from agente_leitor import processar_arquivo, registrar_transacoes_extraidas
                    
                    registrar_log("EXTRAÇÃO", f"Iniciando processamento de arquivo: {arquivo_upload.name}", {
                        "arquivo": arquivo_upload.name,
                        "tipo": arquivo_upload.type,
                        "tamanho_kb": arquivo_upload.size / 1024
                    })
                    
                    # Processa o arquivo
                    arquivo_bytes = arquivo_upload.read()
                    dados_extraidos = processar_arquivo(arquivo_bytes, arquivo_upload.name)
                    
                    transacoes = dados_extraidos.get("transacoes", [])
                    observacoes = dados_extraidos.get("observacoes", [])
                    
                    registrar_log("EXTRAÇÃO", f"Extração concluída: {len(transacoes)} transações", {
                        "arquivo": arquivo_upload.name,
                        "transacoes_encontradas": len(transacoes),
                        "transacoes": transacoes
                    })
                    
                    if transacoes:
                        st.markdown(f"#### ✅ Encontradas {len(transacoes)} transações:")
                        
                        # Mostra preview das transações
                        for i, t in enumerate(transacoes, 1):
                            tipo_emoji = "💰" if t.get("tipo") == "renda" else "💸"
                            st.write(f"{i}. {tipo_emoji} {t.get('data')} | R$ {t.get('valor', 0):.2f} | {t.get('descricao')} [{t.get('categoria')}]")
                        
                        st.markdown("---")
                        
                        # Registra as transações
                        resultado = registrar_transacoes_extraidas(transacoes)
                        
                        # Loga o resultado
                        registrar_log("SUCESSO", f"Registro de {resultado['adicionadas']} transações do arquivo", {
                            "arquivo": arquivo_upload.name,
                            "adicionadas": resultado['adicionadas'],
                            "duplicatas": resultado['duplicatas'],
                            "erros": resultado['erros'],
                            "detalhes": resultado['detalhes']
                        })
                        
                        # Loga erros individuais
                        for d in resultado['detalhes']:
                            if d['status'] == 'erro':
                                registrar_log("ERRO", f"Falha ao salvar transação de arquivo", {
                                    "arquivo": arquivo_upload.name,
                                    "transacao": d['transacao'],
                                    "erro": d.get('mensagem', 'Erro desconhecido')
                                })
                        
                        # Mostra resultados
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("✅ Adicionadas", resultado['adicionadas'])
                        with col2:
                            st.metric("⚠️ Duplicatas", resultado['duplicatas'])
                        with col3:
                            st.metric("❌ Erros", resultado['erros'])
                        
                        # Detalhes de duplicatas
                        if resultado['duplicatas'] > 0:
                            with st.expander("⚠️ Ver transações duplicadas"):
                                for d in resultado['detalhes']:
                                    if d['status'] == 'duplicata':
                                        t = d['transacao']
                                        st.write(f"• {t.get('data')} | R$ {t.get('valor', 0):.2f} | {t.get('descricao')}")
                        
                        # Detalhes de erros
                        if resultado['erros'] > 0:
                            with st.expander("❌ Ver detalhes dos erros"):
                                for d in resultado['detalhes']:
                                    if d['status'] == 'erro':
                                        t = d['transacao']
                                        st.error(f"• {t.get('data')} | R$ {t.get('valor', 0):.2f} | {t.get('descricao')}")
                                        st.caption(f"   Erro: {d.get('mensagem', 'Erro desconhecido')}")
                        
                        if resultado['adicionadas'] > 0:
                            st.success(f"🎉 {resultado['adicionadas']} transação(ões) adicionada(s) com sucesso!")
                        
                        if resultado['duplicatas'] > 0:
                            st.warning(f"⚠️ {resultado['duplicatas']} transação(ões) já existiam e foram ignoradas.")
                        
                        if resultado['erros'] > 0:
                            st.error(f"❌ {resultado['erros']} erro(s) ao salvar. Veja os detalhes acima.")
                    else:
                        st.warning("⚠️ Não foram encontradas transações no arquivo.")
                        registrar_log("INFO", "Nenhuma transação encontrada no arquivo", {"arquivo": arquivo_upload.name})
                        if observacoes:
                            for obs in observacoes:
                                st.info(f"📝 {obs}")
                                
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                    st.info("💡 Dica: Certifique-se de que o arquivo contém movimentações financeiras visíveis.")
                    registrar_log("ERRO", f"Erro crítico ao processar arquivo: {arquivo_upload.name}", {
                        "arquivo": arquivo_upload.name,
                        "erro": str(e),
                        "tipo_erro": type(e).__name__
                    })

# ============================================================
# PÁGINA: HISTÓRICO
# ============================================================

elif pagina == "📋 Histórico":
    st.markdown("## 📋 Histórico de Transações")
    
    dados = carregar_dados_planilha()
    
    tab1, tab2 = st.tabs(["💸 Despesas", "💰 Rendas"])
    
    with tab1:
        st.markdown("### Despesas Registradas")
        despesas = dados.get("despesas", [])
        
        if despesas:
            import pandas as pd
            df = pd.DataFrame(despesas)
            df.columns = ["Data", "Valor", "Descrição", "Categoria"]
            st.dataframe(df, use_container_width=True)
            
            # Total
            total = sum(processar_valor(d.get("valor", "0")) for d in despesas)
            st.markdown(f"**Total:** {formatar_moeda(total)}")
        else:
            st.info("Nenhuma despesa registrada")
    
    with tab2:
        st.markdown("### Rendas Registradas")
        rendas = dados.get("rendas", [])
        
        if rendas:
            import pandas as pd
            df = pd.DataFrame(rendas)
            df.columns = ["Data", "Valor", "Descrição", "Categoria"]
            st.dataframe(df, use_container_width=True)
            
            # Total
            total = sum(processar_valor(r.get("valor", "0")) for r in rendas)
            st.markdown(f"**Total:** {formatar_moeda(total)}")
        else:
            st.info("Nenhuma renda registrada")

# ============================================================
# PÁGINA: ADMIN
# ============================================================

elif pagina == "🔐 Admin (Logs)":
    st.markdown("## 🔐 Painel de Administração")
    
    # Inicializa estado de autenticação
    if 'admin_autenticado' not in st.session_state:
        st.session_state.admin_autenticado = False
    
    # Tela de login
    if not st.session_state.admin_autenticado:
        st.markdown("### Acesso Restrito")
        st.warning("Esta área requer autenticação.")
        
        senha = st.text_input("Senha:", type="password", key="admin_senha")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔓 Entrar", type="primary"):
                if senha == ADMIN_PASSWORD:
                    st.session_state.admin_autenticado = True
                    registrar_log("INFO", "Login admin realizado com sucesso")
                    st.rerun()
                else:
                    registrar_log("ERRO", "Tentativa de login admin com senha incorreta")
                    st.error("❌ Senha incorreta!")
    
    else:
        # Botão de logout
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🚪 Sair"):
                st.session_state.admin_autenticado = False
                st.rerun()
        with col2:
            if st.button("🗑️ Limpar Logs"):
                if limpar_logs():
                    st.success("Logs limpos!")
                    st.rerun()
        
        st.markdown("---")
        
        # Tabs de administração
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Todos os Logs", "✅ Sucessos", "❌ Erros", "📊 Estatísticas"])
        
        logs = obter_logs()
        
        with tab1:
            st.markdown("### 📋 Todos os Logs")
            st.markdown(f"**Total de registros:** {len(logs)}")
            
            # Filtros
            filtro_tipo = st.selectbox(
                "Filtrar por tipo:",
                ["Todos", "INFO", "SUCESSO", "ERRO", "DESPESA", "RENDA", "EXTRAÇÃO", "API"]
            )
            
            filtro_busca = st.text_input("🔍 Buscar nos logs:", "")
            
            # Filtra logs
            logs_filtrados = logs
            if filtro_tipo != "Todos":
                logs_filtrados = [l for l in logs_filtrados if l.get("tipo") == filtro_tipo]
            if filtro_busca:
                logs_filtrados = [l for l in logs_filtrados if filtro_busca.lower() in str(l).lower()]
            
            # Mostra logs (mais recentes primeiro)
            for log in reversed(logs_filtrados[-100:]):
                tipo = log.get("tipo", "INFO")
                timestamp = log.get("timestamp", "")
                mensagem = log.get("mensagem", "")
                detalhes = log.get("detalhes", {})
                
                # Define cor do badge
                cores = {
                    "INFO": "🔵",
                    "SUCESSO": "🟢",
                    "ERRO": "🔴",
                    "DESPESA": "💸",
                    "RENDA": "💰",
                    "EXTRAÇÃO": "📄",
                    "API": "🌐"
                }
                badge = cores.get(tipo, "⚪")
                
                with st.expander(f"{badge} [{timestamp}] {tipo}: {mensagem[:60]}..."):
                    st.markdown(f"**Tipo:** {tipo}")
                    st.markdown(f"**Timestamp:** {timestamp}")
                    st.markdown(f"**Mensagem:** {mensagem}")
                    if detalhes:
                        st.markdown("**Detalhes:**")
                        st.json(detalhes)
        
        with tab2:
            st.markdown("### ✅ Operações de Sucesso")
            sucessos = [l for l in logs if l.get("tipo") in ["SUCESSO", "DESPESA", "RENDA"]]
            st.markdown(f"**Total:** {len(sucessos)} registros")
            
            for log in reversed(sucessos[-50:]):
                tipo = log.get("tipo", "")
                timestamp = log.get("timestamp", "")
                mensagem = log.get("mensagem", "")
                detalhes = log.get("detalhes", {})
                
                badge = "💸" if tipo == "DESPESA" else "💰" if tipo == "RENDA" else "✅"
                
                with st.expander(f"{badge} [{timestamp}] {mensagem[:60]}..."):
                    st.markdown(f"**Mensagem:** {mensagem}")
                    if detalhes:
                        st.json(detalhes)
        
        with tab3:
            st.markdown("### ❌ Erros e Falhas")
            erros = [l for l in logs if l.get("tipo") == "ERRO"]
            st.markdown(f"**Total:** {len(erros)} erros")
            
            if erros:
                st.error(f"⚠️ {len(erros)} erros registrados no sistema")
                
                for log in reversed(erros[-50:]):
                    timestamp = log.get("timestamp", "")
                    mensagem = log.get("mensagem", "")
                    detalhes = log.get("detalhes", {})
                    
                    with st.expander(f"🔴 [{timestamp}] {mensagem[:60]}..."):
                        st.markdown(f"**Erro:** {mensagem}")
                        if detalhes:
                            st.markdown("**Detalhes Técnicos:**")
                            # Mostra erro da API separadamente se existir
                            erro_api = detalhes.get("erro", "")
                            if erro_api:
                                st.markdown("**Erro da API (sem tratamento):**")
                                st.code(erro_api, language="text")
                            # Mostra todos os detalhes
                            st.markdown("**JSON completo:**")
                            st.code(json.dumps(detalhes, indent=2, ensure_ascii=False))
            else:
                st.success("✅ Nenhum erro registrado!")
        
        with tab4:
            st.markdown("### 📊 Estatísticas")
            
            if logs:
                # Contagem por tipo
                tipos_count = {}
                for log in logs:
                    tipo = log.get("tipo", "OUTRO")
                    tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Logs", len(logs))
                with col2:
                    st.metric("Erros", tipos_count.get("ERRO", 0))
                with col3:
                    st.metric("Sucessos", tipos_count.get("SUCESSO", 0) + tipos_count.get("DESPESA", 0) + tipos_count.get("RENDA", 0))
                
                st.markdown("#### Distribuição por Tipo")
                import pandas as pd
                df = pd.DataFrame(list(tipos_count.items()), columns=["Tipo", "Quantidade"])
                st.bar_chart(df.set_index("Tipo"))
                
                # Últimas 24h
                st.markdown("#### Atividade Recente")
                hoje = datetime.now().strftime("%Y-%m-%d")
                logs_hoje = [l for l in logs if l.get("timestamp", "").startswith(hoje)]
                st.info(f"📅 {len(logs_hoje)} operações hoje ({hoje})")
            else:
                st.info("Nenhum log registrado ainda.")

# ============================================================
# RODAPÉ
# ============================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "💰Agente Financeiro Inteligente | MykAI"
    "</div>",
    unsafe_allow_html=True
)
