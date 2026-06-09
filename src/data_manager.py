"""
Data Manager - Gerenciador Central de Dados
============================================
Coordena o salvamento de transações em múltiplos destinos:
- Google Sheets (planilha online)
- SQL Server (banco de dados local)

Uso:
    from data_manager import registrar_despesa, registrar_renda
"""

from typing import Dict, List, Optional


# =============================================================================
# CATEGORIAS (exportadas para uso externo)
# =============================================================================

CATEGORIAS_DESPESAS = [
    "Alimentação", "Presentes", "Saúde", "Moradia", "Transporte",
    "Pessoal", "Animais de estimação", "Serviços de utilidade pública",
    "Viagens", "Débito", "Outros"
]

CATEGORIAS_RENDAS = ["Poupança", "Pagamento", "Bônus", "Juros", "Outros"]


# =============================================================================
# FUNÇÕES INTERNAS - GOOGLE SHEETS
# =============================================================================

def _salvar_google_sheets(data: str, valor: float, descricao: str, 
                          categoria: str, tipo: str, verificar_duplicata: bool = False) -> dict:
    """Salva no Google Sheets."""
    try:
        from google_sheets_connector import GoogleSheetsConnector
        
        connector = GoogleSheetsConnector()
        if not connector.conectado:
            return {"sucesso": False, "duplicata": False, "mensagem": "Google Sheets não conectado"}
        
        if tipo.lower() in ["renda", "receita", "income"]:
            if verificar_duplicata:
                return connector.adicionar_renda_sem_duplicar(data, valor, descricao, categoria)
            else:
                sucesso, erro = connector.adicionar_renda(data, valor, descricao, categoria)
                return {"sucesso": sucesso, "duplicata": False, "mensagem": erro or "OK"}
        else:
            if verificar_duplicata:
                return connector.adicionar_despesa_sem_duplicar(data, valor, descricao, categoria)
            else:
                sucesso, erro = connector.adicionar_despesa(data, valor, descricao, categoria)
                return {"sucesso": sucesso, "duplicata": False, "mensagem": erro or "OK"}
                
    except Exception as e:
        return {"sucesso": False, "duplicata": False, "mensagem": f"Erro Sheets: {type(e).__name__}: {e}"}


# =============================================================================
# FUNÇÕES INTERNAS - SQL SERVER
# =============================================================================

def _salvar_sql_server(data: str, valor: float, descricao: str, 
                       categoria: str, tipo: str, verificar_duplicata: bool = False) -> dict:
    """Salva no SQL Server (silencioso se não disponível)."""
    try:
        from sql_server_connector import SQLServerConnector
        
        connector = SQLServerConnector()
        if not connector.conectado:
            return {"sucesso": False, "erro": "SQL Server não conectado"}
        
        if tipo.lower() in ["renda", "receita", "income"]:
            if verificar_duplicata:
                return connector.adicionar_renda_sem_duplicar(data, valor, descricao, categoria)
            else:
                resultado = connector.adicionar_renda(data, valor, descricao, categoria)
                return {"sucesso": resultado.sucesso, "mensagem": resultado.mensagem}
        else:
            if verificar_duplicata:
                return connector.adicionar_despesa_sem_duplicar(data, valor, descricao, categoria)
            else:
                resultado = connector.adicionar_despesa(data, valor, descricao, categoria)
                return {"sucesso": resultado.sucesso, "mensagem": resultado.mensagem}
                
    except ImportError:
        # SQL Server não configurado - silencioso
        return {"sucesso": False, "erro": "pyodbc não instalado"}
    except Exception as e:
        print(f"⚠️ SQL Server: {e}")
        return {"sucesso": False, "erro": str(e)}


# =============================================================================
# INTERFACE PÚBLICA - REGISTRO SIMPLES
# =============================================================================

def registrar_despesa(data: str, valor: float, descricao: str, categoria: str) -> bool:
    """
    Registra uma despesa em todos os destinos configurados.
    
    Args:
        data: Data no formato DD/MM/AAAA
        valor: Valor da despesa
        descricao: Descrição da despesa
        categoria: Categoria da despesa
        
    Returns:
        True se salvou no Google Sheets com sucesso
    """
    # Salva no SQL Server (não bloqueia se falhar)
    _salvar_sql_server(data, valor, descricao, categoria, "despesa")
    
    # Salva no Google Sheets (principal)
    resultado = _salvar_google_sheets(data, valor, descricao, categoria, "despesa")
    return resultado.get("sucesso", False)


def registrar_renda(data: str, valor: float, descricao: str, categoria: str) -> bool:
    """
    Registra uma renda em todos os destinos configurados.
    
    Args:
        data: Data no formato DD/MM/AAAA
        valor: Valor da renda
        descricao: Descrição da renda
        categoria: Categoria da renda
        
    Returns:
        True se salvou no Google Sheets com sucesso
    """
    # Salva no SQL Server (não bloqueia se falhar)
    _salvar_sql_server(data, valor, descricao, categoria, "renda")
    
    # Salva no Google Sheets (principal)
    resultado = _salvar_google_sheets(data, valor, descricao, categoria, "renda")
    return resultado.get("sucesso", False)


def registrar_transacao(data: str, valor: float, descricao: str, categoria: str,
                        tipo: str = "despesa") -> bool:
    """Registra uma transação (despesa ou renda)."""
    if tipo.lower() in ["renda", "receita", "income"]:
        return registrar_renda(data, valor, descricao, categoria)
    return registrar_despesa(data, valor, descricao, categoria)


# =============================================================================
# INTERFACE PÚBLICA - REGISTRO COM VERIFICAÇÃO DE DUPLICIDADE
# =============================================================================

def registrar_despesa_sem_duplicar(data: str, valor: float, descricao: str, categoria: str) -> dict:
    """
    Registra despesa verificando duplicidade.
    
    Returns:
        dict com 'sucesso', 'duplicata', 'mensagem'
    """
    # Salva no SQL Server (com verificação de duplicidade)
    _salvar_sql_server(data, valor, descricao, categoria, "despesa", verificar_duplicata=True)
    
    # Salva no Google Sheets (com verificação de duplicidade)
    return _salvar_google_sheets(data, valor, descricao, categoria, "despesa", verificar_duplicata=True)


def registrar_renda_sem_duplicar(data: str, valor: float, descricao: str, categoria: str) -> dict:
    """
    Registra renda verificando duplicidade.
    
    Returns:
        dict com 'sucesso', 'duplicata', 'mensagem'
    """
    # Salva no SQL Server (com verificação de duplicidade)
    _salvar_sql_server(data, valor, descricao, categoria, "renda", verificar_duplicata=True)
    
    # Salva no Google Sheets (com verificação de duplicidade)
    return _salvar_google_sheets(data, valor, descricao, categoria, "renda", verificar_duplicata=True)


def registrar_transacao_sem_duplicar(data: str, valor: float, descricao: str, categoria: str,
                                      tipo: str = "despesa") -> dict:
    """Registra transação verificando duplicidade."""
    if tipo.lower() in ["renda", "receita", "income"]:
        return registrar_renda_sem_duplicar(data, valor, descricao, categoria)
    return registrar_despesa_sem_duplicar(data, valor, descricao, categoria)


# =============================================================================
# INTERFACE PÚBLICA - VERIFICAÇÃO
# =============================================================================

def verificar_se_existe_despesa(data: str, valor: float, descricao: str) -> bool:
    """Verifica se despesa existe no Google Sheets."""
    try:
        from google_sheets_connector import GoogleSheetsConnector
        connector = GoogleSheetsConnector()
        return connector.verificar_duplicidade_despesa(data, valor, descricao) if connector.conectado else False
    except:
        return False


def verificar_se_existe_renda(data: str, valor: float, descricao: str) -> bool:
    """Verifica se renda existe no Google Sheets."""
    try:
        from google_sheets_connector import GoogleSheetsConnector
        connector = GoogleSheetsConnector()
        return connector.verificar_duplicidade_renda(data, valor, descricao) if connector.conectado else False
    except:
        return False


# =============================================================================
# INTERFACE PÚBLICA - ALIMENTAÇÃO EM LOTE
# =============================================================================

def alimentar_planilha(dados_extraidos: Dict) -> Dict:
    """Alimenta planilha com dados extraídos."""
    try:
        from google_sheets_connector import GoogleSheetsConnector
        
        connector = GoogleSheetsConnector()
        if not connector.conectado:
            return {"erro": "Não foi possível conectar"}
        
        transacoes = dados_extraidos.get("transacoes", {})
        if not transacoes:
            print("⚠️ Nenhuma transação para adicionar")
            return {"erro": "Nenhuma transação"}
        
        return connector.adicionar_transacoes_em_lote(transacoes)
    except Exception as e:
        return {"erro": str(e)}


# =============================================================================
# STATUS DOS CONECTORES
# =============================================================================

def status_conectores() -> Dict:
    """Retorna status dos conectores."""
    status = {
        "google_sheets": False,
        "sql_server": False
    }
    
    try:
        from google_sheets_connector import GoogleSheetsConnector
        connector = GoogleSheetsConnector()
        status["google_sheets"] = connector.conectado
    except:
        pass
    
    try:
        from sql_server_connector import SQLServerConnector
        connector = SQLServerConnector()
        status["sql_server"] = connector.conectado
    except:
        pass
    
    return status
