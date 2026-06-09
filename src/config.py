"""
Configuração centralizada - Carrega variáveis do .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")


def validar_config() -> tuple:
    """
    Valida se as configurações necessárias estão presentes.
    
    Returns:
        Tuple[bool, List[str]]: (sucesso, lista_de_erros)
    """
    erros = []
    
    if not AZURE_OPENAI_ENDPOINT:
        erros.append("AZURE_OPENAI_ENDPOINT não configurado")
    if not AZURE_OPENAI_API_KEY:
        erros.append("AZURE_OPENAI_API_KEY não configurado")
    if not GOOGLE_SPREADSHEET_ID:
        erros.append("GOOGLE_SPREADSHEET_ID não configurado")
    
    if erros:
        print("⚠️ Erros de configuração:")
        for erro in erros:
            print(f"   - {erro}")
        print("\n📋 Configure as variáveis no arquivo .env")
    
    return len(erros) == 0, erros
