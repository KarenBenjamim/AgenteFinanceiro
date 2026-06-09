"""
SQL Server Connector - Salva transações em banco de dados local
================================================================
Database: AgenteFinanceiro
Tabelas: Despesas, Renda
Autenticação: Windows Authentication
"""

import pyodbc
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

SQL_SERVER_CONFIG = {
    "server": "localhost",
    "database": "AgenteFinanceiro",
    "driver": "{ODBC Driver 17 for SQL Server}",
    "trusted_connection": "yes"  # Windows Authentication
}

# Categorias (mesmas do Google Sheets)
CATEGORIAS_DESPESAS = [
    "Alimentação", "Presentes", "Saúde", "Moradia", "Transporte",
    "Pessoal", "Animais de estimação", "Serviços de utilidade pública",
    "Viagens", "Débito", "Outros"
]

CATEGORIAS_RENDAS = ["Poupança", "Pagamento", "Bônus", "Juros", "Outros"]


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class ResultadoSQL:
    """Resultado de uma operação SQL."""
    sucesso: bool
    mensagem: str = ""
    erro: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "sucesso": self.sucesso,
            "mensagem": self.mensagem,
            "erro": self.erro
        }


# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================

class SQLServerConnector:
    """Conector para SQL Server - Gerenciamento de Transações."""
    
    _instance: Optional['SQLServerConnector'] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializado = False
        return cls._instance
    
    def __init__(self):
        if self._inicializado:
            return
        
        self.config = SQL_SERVER_CONFIG
        self.connection: Optional[pyodbc.Connection] = None
        self._conectar()
        self._criar_tabelas_se_necessario()
        self._inicializado = True
    
    # =========================================================================
    # CONEXÃO
    # =========================================================================
    
    def _get_connection_string(self) -> str:
        """Retorna string de conexão."""
        params = {
            "DRIVER": self.config['driver'],
            "SERVER": self.config['server'],
            "DATABASE": self.config['database'],
            "Trusted_Connection": self.config['trusted_connection']
        }
        return ";".join(f"{k}={v}" for k, v in params.items())
    
    def _conectar(self) -> bool:
        """Estabelece conexão com SQL Server."""
        try:
            # Primeiro tenta conectar ao master para criar o banco se necessário
            conn_master = (
                f"DRIVER={self.config['driver']};"
                f"SERVER={self.config['server']};"
                f"DATABASE=master;"
                f"Trusted_Connection={self.config['trusted_connection']};"
            )
            
            conn = pyodbc.connect(conn_master, autocommit=True)
            cursor = conn.cursor()
            
            # Verifica se o banco existe, se não, cria
            cursor.execute(f"""
                IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{self.config['database']}')
                BEGIN
                    CREATE DATABASE [{self.config['database']}]
                END
            """)
            conn.close()
            
            # Agora conecta ao banco correto
            self.connection = pyodbc.connect(self._get_connection_string())
            print(f"✅ SQL Server conectado: {self.config['server']}/{self.config['database']}")
            return True
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao conectar SQL Server: {e}")
            self.connection = None
            return False
    
    @property
    def conectado(self) -> bool:
        """Verifica se está conectado."""
        if self.connection is None:
            return False
        try:
            self.connection.cursor().execute("SELECT 1")
            return True
        except:
            return False
    
    def _reconectar(self) -> bool:
        """Tenta reconectar."""
        self.connection = None
        return self._conectar()
    
    # =========================================================================
    # CRIAÇÃO DE TABELAS
    # =========================================================================
    
    def _criar_tabelas_se_necessario(self) -> None:
        """Cria as tabelas se não existirem."""
        if not self.conectado:
            return
        
        try:
            cursor = self.connection.cursor()
            
            # Tabela Despesas
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Despesas' AND xtype='U')
                CREATE TABLE Despesas (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    Data DATE NOT NULL,
                    Valor DECIMAL(18,2) NOT NULL,
                    Descricao NVARCHAR(500) NOT NULL,
                    Tipo NVARCHAR(50) DEFAULT 'Despesa',
                    Categoria NVARCHAR(100) NOT NULL,
                    DataCriacao DATETIME DEFAULT GETDATE()
                )
            """)
            
            # Tabela Renda
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Renda' AND xtype='U')
                CREATE TABLE Renda (
                    Id INT IDENTITY(1,1) PRIMARY KEY,
                    Data DATE NOT NULL,
                    Valor DECIMAL(18,2) NOT NULL,
                    Descricao NVARCHAR(500) NOT NULL,
                    Tipo NVARCHAR(50) DEFAULT 'Renda',
                    Categoria NVARCHAR(100) NOT NULL,
                    DataCriacao DATETIME DEFAULT GETDATE()
                )
            """)
            
            self.connection.commit()
            print("✅ Tabelas SQL Server verificadas/criadas")
            
        except pyodbc.Error as e:
            print(f"❌ Erro ao criar tabelas: {e}")
    
    # =========================================================================
    # OPERAÇÕES DE ESCRITA
    # =========================================================================
    
    def _converter_data(self, data_str: str) -> str:
        """Converte data DD/MM/AAAA para YYYY-MM-DD."""
        try:
            partes = data_str.split("/")
            if len(partes) == 3:
                dia, mes, ano = partes
                return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
            return datetime.now().strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")
    
    def adicionar_despesa(self, data: str, valor: float, descricao: str, 
                          categoria: str) -> ResultadoSQL:
        """Adiciona uma despesa no SQL Server."""
        if not self.conectado:
            if not self._reconectar():
                return ResultadoSQL(False, erro="Sem conexão com SQL Server")
        
        try:
            cursor = self.connection.cursor()
            data_sql = self._converter_data(data)
            
            cursor.execute("""
                INSERT INTO Despesas (Data, Valor, Descricao, Tipo, Categoria)
                VALUES (?, ?, ?, 'Despesa', ?)
            """, (data_sql, valor, descricao, categoria))
            
            self.connection.commit()
            print(f"✅ [SQL] Despesa salva: {descricao} - R${valor:.2f}")
            return ResultadoSQL(True, f"Despesa salva no SQL Server")
            
        except pyodbc.Error as e:
            erro = str(e)
            print(f"❌ [SQL] Erro ao salvar despesa: {erro}")
            return ResultadoSQL(False, erro=erro)
    
    def adicionar_renda(self, data: str, valor: float, descricao: str,
                        categoria: str) -> ResultadoSQL:
        """Adiciona uma renda no SQL Server."""
        if not self.conectado:
            if not self._reconectar():
                return ResultadoSQL(False, erro="Sem conexão com SQL Server")
        
        try:
            cursor = self.connection.cursor()
            data_sql = self._converter_data(data)
            
            cursor.execute("""
                INSERT INTO Renda (Data, Valor, Descricao, Tipo, Categoria)
                VALUES (?, ?, ?, 'Renda', ?)
            """, (data_sql, valor, descricao, categoria))
            
            self.connection.commit()
            print(f"✅ [SQL] Renda salva: {descricao} - R${valor:.2f}")
            return ResultadoSQL(True, f"Renda salva no SQL Server")
            
        except pyodbc.Error as e:
            erro = str(e)
            print(f"❌ [SQL] Erro ao salvar renda: {erro}")
            return ResultadoSQL(False, erro=erro)
    
    # =========================================================================
    # VERIFICAÇÃO DE DUPLICIDADE
    # =========================================================================
    
    def verificar_duplicidade_despesa(self, data: str, valor: float, descricao: str) -> bool:
        """Verifica se despesa já existe."""
        if not self.conectado:
            return False
        
        try:
            cursor = self.connection.cursor()
            data_sql = self._converter_data(data)
            
            cursor.execute("""
                SELECT COUNT(*) FROM Despesas 
                WHERE Data = ? AND ABS(Valor - ?) < 0.01 AND LOWER(Descricao) = LOWER(?)
            """, (data_sql, valor, descricao))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except pyodbc.Error:
            return False
    
    def verificar_duplicidade_renda(self, data: str, valor: float, descricao: str) -> bool:
        """Verifica se renda já existe."""
        if not self.conectado:
            return False
        
        try:
            cursor = self.connection.cursor()
            data_sql = self._converter_data(data)
            
            cursor.execute("""
                SELECT COUNT(*) FROM Renda 
                WHERE Data = ? AND ABS(Valor - ?) < 0.01 AND LOWER(Descricao) = LOWER(?)
            """, (data_sql, valor, descricao))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except pyodbc.Error:
            return False
    
    # =========================================================================
    # OPERAÇÕES COM VERIFICAÇÃO DE DUPLICIDADE
    # =========================================================================
    
    def adicionar_despesa_sem_duplicar(self, data: str, valor: float, descricao: str,
                                        categoria: str) -> dict:
        """Adiciona despesa verificando duplicidade."""
        if self.verificar_duplicidade_despesa(data, valor, descricao):
            return {
                "sucesso": False,
                "duplicata": True,
                "mensagem": f"[SQL] Duplicata: {data} | R${valor:.2f} | {descricao}"
            }
        
        resultado = self.adicionar_despesa(data, valor, descricao, categoria)
        return {
            "sucesso": resultado.sucesso,
            "duplicata": False,
            "mensagem": resultado.mensagem if resultado.sucesso else resultado.erro
        }
    
    def adicionar_renda_sem_duplicar(self, data: str, valor: float, descricao: str,
                                      categoria: str) -> dict:
        """Adiciona renda verificando duplicidade."""
        if self.verificar_duplicidade_renda(data, valor, descricao):
            return {
                "sucesso": False,
                "duplicata": True,
                "mensagem": f"[SQL] Duplicata: {data} | R${valor:.2f} | {descricao}"
            }
        
        resultado = self.adicionar_renda(data, valor, descricao, categoria)
        return {
            "sucesso": resultado.sucesso,
            "duplicata": False,
            "mensagem": resultado.mensagem if resultado.sucesso else resultado.erro
        }
    
    # =========================================================================
    # LEITURA
    # =========================================================================
    
    def ler_despesas(self, limite: int = 1000) -> List[Dict]:
        """Lê despesas do banco."""
        if not self.conectado:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT TOP {limite} Data, Valor, Descricao, Categoria 
                FROM Despesas 
                ORDER BY Data DESC, Id DESC
            """)
            
            return [
                {
                    "data": row.Data.strftime("%d/%m/%Y") if row.Data else "",
                    "valor": f"R${row.Valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "descricao": row.Descricao,
                    "categoria": row.Categoria
                }
                for row in cursor.fetchall()
            ]
        except pyodbc.Error as e:
            print(f"❌ [SQL] Erro ao ler despesas: {e}")
            return []
    
    def ler_rendas(self, limite: int = 1000) -> List[Dict]:
        """Lê rendas do banco."""
        if not self.conectado:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT TOP {limite} Data, Valor, Descricao, Categoria 
                FROM Renda 
                ORDER BY Data DESC, Id DESC
            """)
            
            return [
                {
                    "data": row.Data.strftime("%d/%m/%Y") if row.Data else "",
                    "valor": f"R${row.Valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "descricao": row.Descricao,
                    "categoria": row.Categoria
                }
                for row in cursor.fetchall()
            ]
        except pyodbc.Error as e:
            print(f"❌ [SQL] Erro ao ler rendas: {e}")
            return []


# =============================================================================
# FUNÇÕES DE INTERFACE PÚBLICA
# =============================================================================

_sql_connector: Optional[SQLServerConnector] = None

def _get_sql_connector() -> Optional[SQLServerConnector]:
    """Retorna instância do conector SQL (singleton)."""
    global _sql_connector
    try:
        if _sql_connector is None:
            _sql_connector = SQLServerConnector()
        return _sql_connector
    except Exception as e:
        print(f"⚠️ SQL Server não disponível: {e}")
        return None


def salvar_despesa_sql(data: str, valor: float, descricao: str, categoria: str) -> dict:
    """Salva despesa no SQL Server."""
    connector = _get_sql_connector()
    if not connector or not connector.conectado:
        return {"sucesso": False, "erro": "SQL Server não disponível"}
    return connector.adicionar_despesa_sem_duplicar(data, valor, descricao, categoria)


def salvar_renda_sql(data: str, valor: float, descricao: str, categoria: str) -> dict:
    """Salva renda no SQL Server."""
    connector = _get_sql_connector()
    if not connector or not connector.conectado:
        return {"sucesso": False, "erro": "SQL Server não disponível"}
    return connector.adicionar_renda_sem_duplicar(data, valor, descricao, categoria)


def sql_disponivel() -> bool:
    """Verifica se SQL Server está disponível."""
    connector = _get_sql_connector()
    return connector is not None and connector.conectado
