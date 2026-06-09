"""
Google Sheets Connector - Orçamento Mensal
==========================================
Gerencia transações financeiras em uma planilha Google Sheets.

Planilha: https://docs.google.com/spreadsheets/d/1NnujOuZiEZPYhMHlZlOb7G27zNtmgsiH4ckLyQdOFM0
"""

import os
import time
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SPREADSHEET_ID


# =============================================================================
# CONSTANTES E CONFIGURAÇÕES
# =============================================================================

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Rate limiting
DELAY_ENTRE_OPERACOES = 1.0  # segundos
MAX_LINHAS_LEITURA = 1000

# Categorias
CATEGORIAS_DESPESAS = [
    "Alimentação", "Presentes", "Saúde", "Moradia", "Transporte",
    "Pessoal", "Animais de estimação", "Serviços de utilidade pública",
    "Viagens", "Débito", "Outros"
]

CATEGORIAS_RENDAS = ["Poupança", "Pagamento", "Bônus", "Juros", "Outros"]


# =============================================================================
# ENUMS E DATACLASSES
# =============================================================================

class TipoTransacao(Enum):
    DESPESA = "despesa"
    RENDA = "renda"


@dataclass
class ConfigColunas:
    """Configuração das colunas na planilha."""
    col_data: str
    col_valor: str
    col_descricao: str
    col_categoria: str
    linha_inicio: int = 5


@dataclass
class ResultadoOperacao:
    """Resultado de uma operação de registro."""
    sucesso: bool
    duplicata: bool = False
    mensagem: str = ""
    
    def to_dict(self) -> dict:
        return {
            "sucesso": self.sucesso,
            "duplicata": self.duplicata,
            "mensagem": self.mensagem
        }


# Configurações das colunas
CONFIG_DESPESAS = ConfigColunas("B", "C", "D", "E")
CONFIG_RENDAS = ConfigColunas("G", "H", "I", "J")
ABA_TRANSACOES = "Transações"


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def formatar_moeda(valor: float) -> str:
    """Formata valor como moeda brasileira (R$1.234,56)."""
    return f"R${valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normalizar_valor(valor_str: str) -> float:
    """Converte string de valor para float."""
    if not valor_str:
        return 0.0
    try:
        valor = str(valor_str).replace("R$", "").replace(" ", "")
        valor = valor.replace(".", "").replace(",", ".")
        return round(float(valor), 2)
    except (ValueError, AttributeError):
        return 0.0


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparação."""
    return texto.lower().strip() if texto else ""


def validar_categoria(categoria: str, categorias_validas: List[str]) -> str:
    """Valida e retorna categoria válida."""
    if not categoria:
        return "Outros"
    for cat in categorias_validas:
        if cat.lower() == categoria.lower():
            return cat
    return "Outros"


def calcular_similaridade(texto1: str, texto2: str) -> float:
    """Calcula similaridade entre dois textos (0.0 a 1.0)."""
    palavras1 = set(normalizar_texto(texto1).split())
    palavras2 = set(normalizar_texto(texto2).split())
    if not palavras1 or not palavras2:
        return 0.0
    intersecao = palavras1.intersection(palavras2)
    return len(intersecao) / max(len(palavras1), len(palavras2))


def formatar_erro(exception: Exception) -> str:
    """Formata exceção com traceback completo."""
    return f"{type(exception).__name__}: {str(exception)}\n\nTraceback:\n{traceback.format_exc()}"


# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================

class GoogleSheetsConnector:
    """Conector para Google Sheets - Gerenciamento de Transações."""
    
    _instance: Optional['GoogleSheetsConnector'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern - mantém uma única instância."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializado = False
        return cls._instance
    
    def __init__(self, credentials_path: str = CREDENTIALS_PATH):
        if self._inicializado:
            return
            
        self.credentials_path = credentials_path
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self._worksheet_cache: Dict[str, gspread.Worksheet] = {}
        self._last_request_time: float = 0
        
        self._conectar()
        self._inicializado = True
    
    # =========================================================================
    # MÉTODOS DE CONEXÃO
    # =========================================================================
    
    def _conectar(self) -> bool:
        """Estabelece conexão com Google Sheets."""
        if not os.path.exists(self.credentials_path):
            self._exibir_instrucoes_credenciais()
            return False
        
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=SCOPES
            )
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(GOOGLE_SPREADSHEET_ID)
            print(f"✅ Conectado à planilha: {self.spreadsheet.title}")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            self.client = None
            self.spreadsheet = None
            return False
    
    def _exibir_instrucoes_credenciais(self) -> None:
        """Exibe instruções para configurar credenciais."""
        print(f"⚠️ Arquivo de credenciais não encontrado: {self.credentials_path}")
        print("\n📋 Para configurar:")
        print("1. Acesse https://console.cloud.google.com/")
        print("2. Crie um projeto e ative Google Sheets API e Google Drive API")
        print("3. Crie uma Service Account e baixe o JSON")
        print("4. Salve como 'credentials.json' nesta pasta")
        print("5. Compartilhe a planilha com o email da Service Account")
    
    @property
    def conectado(self) -> bool:
        """Verifica se está conectado."""
        return self.client is not None and self.spreadsheet is not None
    
    # =========================================================================
    # RATE LIMITING E CACHE
    # =========================================================================
    
    def _aguardar_rate_limit(self) -> None:
        """Aguarda tempo mínimo entre requisições."""
        tempo_passado = time.time() - self._last_request_time
        if tempo_passado < DELAY_ENTRE_OPERACOES:
            time.sleep(DELAY_ENTRE_OPERACOES - tempo_passado)
        self._last_request_time = time.time()
    
    def _obter_worksheet(self, nome_aba: str = ABA_TRANSACOES) -> Optional[gspread.Worksheet]:
        """Obtém worksheet com cache."""
        if not self.conectado:
            return None
        
        if nome_aba in self._worksheet_cache:
            return self._worksheet_cache[nome_aba]
        
        try:
            self._aguardar_rate_limit()
            worksheet = self.spreadsheet.worksheet(nome_aba)
            self._worksheet_cache[nome_aba] = worksheet
            return worksheet
        except Exception as e:
            print(f"❌ Erro ao obter aba '{nome_aba}': {e}")
            return None
    
    # =========================================================================
    # OPERAÇÕES DE LEITURA
    # =========================================================================
    
    def _encontrar_proxima_linha(self, worksheet: gspread.Worksheet, 
                                  config: ConfigColunas) -> int:
        """Encontra próxima linha vazia. Retorna -1 em caso de erro."""
        try:
            self._aguardar_rate_limit()
            col_index = ord(config.col_data) - ord('A') + 1
            valores = worksheet.col_values(col_index)
            
            if len(valores) < config.linha_inicio:
                return config.linha_inicio
            
            for i in range(config.linha_inicio - 1, len(valores)):
                if not valores[i] or not str(valores[i]).strip():
                    return i + 1
            
            return len(valores) + 1
        except Exception as e:
            print(f"⚠️ Erro ao buscar linha: {e}")
            return -1
    
    def _ler_transacoes(self, config: ConfigColunas) -> List[Dict]:
        """Lê transações de uma seção da planilha."""
        worksheet = self._obter_worksheet()
        if not worksheet:
            return []
        
        try:
            self._aguardar_rate_limit()
            range_dados = f"{config.col_data}{config.linha_inicio}:{config.col_categoria}{MAX_LINHAS_LEITURA}"
            dados = worksheet.get(range_dados)
            
            transacoes = []
            for row in dados:
                if not row or not row[0]:
                    break
                transacoes.append({
                    "data": row[0] if len(row) > 0 else "",
                    "valor": row[1] if len(row) > 1 else "",
                    "descricao": row[2] if len(row) > 2 else "",
                    "categoria": row[3] if len(row) > 3 else ""
                })
            return transacoes
        except Exception as e:
            print(f"❌ Erro ao ler transações: {e}")
            return []
    
    def ler_despesas(self) -> List[Dict]:
        """Lê todas as despesas."""
        return self._ler_transacoes(CONFIG_DESPESAS)
    
    def ler_rendas(self) -> List[Dict]:
        """Lê todas as rendas."""
        return self._ler_transacoes(CONFIG_RENDAS)
    
    # =========================================================================
    # OPERAÇÕES DE ESCRITA
    # =========================================================================
    
    def _adicionar_transacao(self, data: str, valor: float, descricao: str,
                             categoria: str, tipo: TipoTransacao) -> Tuple[bool, Optional[str]]:
        """Adiciona uma transação na planilha."""
        worksheet = self._obter_worksheet()
        if not worksheet:
            return False, "Não foi possível acessar a planilha"
        
        config = CONFIG_DESPESAS if tipo == TipoTransacao.DESPESA else CONFIG_RENDAS
        categorias = CATEGORIAS_DESPESAS if tipo == TipoTransacao.DESPESA else CATEGORIAS_RENDAS
        
        linha = self._encontrar_proxima_linha(worksheet, config)
        if linha == -1:
            return False, "Erro ao encontrar linha disponível (limite de requisições)"
        
        try:
            valor_formatado = formatar_moeda(valor)
            categoria_validada = validar_categoria(categoria, categorias)
            
            self._aguardar_rate_limit()
            range_update = f"{config.col_data}{linha}:{config.col_categoria}{linha}"
            worksheet.update(range_update, [[data, valor_formatado, descricao, categoria_validada]])
            
            tipo_str = "Despesa" if tipo == TipoTransacao.DESPESA else "Renda"
            print(f"✅ {tipo_str} adicionada (linha {linha}): {descricao} - {valor_formatado} [{categoria_validada}]")
            return True, None
        except Exception as e:
            return False, formatar_erro(e)
    
    def adicionar_despesa(self, data: str, valor: float, descricao: str, 
                          categoria: str) -> Tuple[bool, Optional[str]]:
        """Adiciona uma despesa."""
        return self._adicionar_transacao(data, valor, descricao, categoria, TipoTransacao.DESPESA)
    
    def adicionar_renda(self, data: str, valor: float, descricao: str,
                        categoria: str) -> Tuple[bool, Optional[str]]:
        """Adiciona uma renda."""
        return self._adicionar_transacao(data, valor, descricao, categoria, TipoTransacao.RENDA)
    
    # =========================================================================
    # VERIFICAÇÃO DE DUPLICIDADE
    # =========================================================================
    
    def _verificar_duplicidade(self, data: str, valor: float, descricao: str,
                               transacoes: List[Dict]) -> bool:
        """Verifica se transação já existe."""
        valor_normalizado = round(float(valor), 2)
        desc_normalizada = normalizar_texto(descricao)
        
        for t in transacoes:
            if t.get("data") != data:
                continue
            
            valor_existente = normalizar_valor(t.get("valor", "0"))
            if abs(valor_existente - valor_normalizado) > 0.01:
                continue
            
            desc_existente = normalizar_texto(t.get("descricao", ""))
            
            # Verificação exata ou por similaridade
            if desc_existente == desc_normalizada or calcular_similaridade(descricao, t.get("descricao", "")) > 0.7:
                print(f"⚠️ Duplicata encontrada: {data} | R${valor:.2f} | {descricao}")
                return True
        
        return False
    
    def verificar_duplicidade_despesa(self, data: str, valor: float, descricao: str) -> bool:
        """Verifica se despesa já existe."""
        return self._verificar_duplicidade(data, valor, descricao, self.ler_despesas())
    
    def verificar_duplicidade_renda(self, data: str, valor: float, descricao: str) -> bool:
        """Verifica se renda já existe."""
        return self._verificar_duplicidade(data, valor, descricao, self.ler_rendas())
    
    # =========================================================================
    # OPERAÇÕES COM VERIFICAÇÃO DE DUPLICIDADE
    # =========================================================================
    
    def _adicionar_sem_duplicar(self, data: str, valor: float, descricao: str,
                                categoria: str, tipo: TipoTransacao) -> ResultadoOperacao:
        """Adiciona transação verificando duplicidade."""
        # Verifica duplicidade
        is_duplicata = (
            self.verificar_duplicidade_despesa(data, valor, descricao)
            if tipo == TipoTransacao.DESPESA
            else self.verificar_duplicidade_renda(data, valor, descricao)
        )
        
        if is_duplicata:
            return ResultadoOperacao(
                sucesso=False,
                duplicata=True,
                mensagem=f"Transação já existe: {data} | R${valor:.2f} | {descricao}"
            )
        
        # Adiciona transação
        sucesso, erro = self._adicionar_transacao(data, valor, descricao, categoria, tipo)
        
        if sucesso:
            tipo_str = "Despesa" if tipo == TipoTransacao.DESPESA else "Renda"
            return ResultadoOperacao(
                sucesso=True,
                mensagem=f"{tipo_str} adicionada: {descricao} - R${valor:.2f}"
            )
        
        return ResultadoOperacao(sucesso=False, mensagem=f"Erro: {erro}")
    
    def adicionar_despesa_sem_duplicar(self, data: str, valor: float, descricao: str,
                                        categoria: str) -> dict:
        """Adiciona despesa verificando duplicidade."""
        resultado = self._adicionar_sem_duplicar(data, valor, descricao, categoria, TipoTransacao.DESPESA)
        return resultado.to_dict()
    
    def adicionar_renda_sem_duplicar(self, data: str, valor: float, descricao: str,
                                      categoria: str) -> dict:
        """Adiciona renda verificando duplicidade."""
        resultado = self._adicionar_sem_duplicar(data, valor, descricao, categoria, TipoTransacao.RENDA)
        return resultado.to_dict()
    
    # =========================================================================
    # OPERAÇÕES EM LOTE
    # =========================================================================
    
    def adicionar_transacoes_em_lote(self, transacoes: Dict) -> Dict:
        """Adiciona múltiplas transações."""
        resultado = {"despesas_ok": 0, "rendas_ok": 0, "erros": 0, "mensagens_erro": []}
        
        for despesa in transacoes.get("despesas", []):
            sucesso, erro = self._processar_item_lote(despesa, TipoTransacao.DESPESA)
            if sucesso:
                resultado["despesas_ok"] += 1
            else:
                resultado["erros"] += 1
                if erro:
                    resultado["mensagens_erro"].append(f"Despesa: {erro}")
        
        for renda in transacoes.get("rendas", []):
            sucesso, erro = self._processar_item_lote(renda, TipoTransacao.RENDA)
            if sucesso:
                resultado["rendas_ok"] += 1
            else:
                resultado["erros"] += 1
                if erro:
                    resultado["mensagens_erro"].append(f"Renda: {erro}")
        
        self._log_resultado_lote(resultado)
        return resultado
    
    def _processar_item_lote(self, item: Dict, tipo: TipoTransacao) -> Tuple[bool, Optional[str]]:
        """Processa um item do lote."""
        data = item.get("Data", item.get("data", ""))
        valor = item.get("Valor", item.get("valor", 0)) or 0
        descricao = item.get("Descricao", item.get("descricao", ""))
        categoria = item.get("Categoria", item.get("categoria", "Outros"))
        return self._adicionar_transacao(data, valor, descricao, categoria, tipo)
    
    @staticmethod
    def _log_resultado_lote(resultado: Dict) -> None:
        """Loga resultado do processamento em lote."""
        print(f"\n📊 Resumo: {resultado['despesas_ok']} despesas, {resultado['rendas_ok']} rendas")
        if resultado["erros"] > 0:
            print(f"⚠️ {resultado['erros']} erros ocorreram")


# =============================================================================
# FUNÇÃO UTILITÁRIA - OBTER INSTÂNCIA
# =============================================================================

def get_connector() -> GoogleSheetsConnector:
    """Retorna instância do conector (singleton)."""
    return GoogleSheetsConnector()
