"""
Utilitários compartilhados - Funções comuns utilizadas por múltiplos módulos
"""

from datetime import datetime
from typing import Tuple, List


def normalizar_data(data: str) -> str:
    """
    Normaliza uma data, adicionando o ano atual se não estiver presente.
    
    Formatos aceitos:
        - DD/MM/AAAA -> mantém
        - DD/MM/AA -> converte para DD/MM/20AA
        - DD/MM -> adiciona ano atual
        - DD-MM-AAAA, DD.MM.AAAA -> converte para DD/MM/AAAA
        - "AAAA" como ano -> substitui pelo ano atual
        
    Args:
        data: String com a data
        
    Returns:
        Data no formato DD/MM/AAAA
    """
    if not data:
        return datetime.now().strftime("%d/%m/%Y")
    
    # Remove espaços extras
    data = data.strip()
    
    # Substitui separadores por /
    data = data.replace("-", "/").replace(".", "/")
    
    # Tenta extrair partes da data
    partes = data.split("/")
    
    if len(partes) == 2:
        # Formato DD/MM - adiciona ano atual
        dia, mes = partes
        ano_atual = datetime.now().year
        return f"{dia.zfill(2)}/{mes.zfill(2)}/{ano_atual}"
    
    elif len(partes) == 3:
        dia, mes, ano = partes
        
        # Se o ano é inválido (ex: "AAAA" ou não numérico), usa o ano atual
        if not ano.isdigit() or ano.upper() == "AAAA":
            ano = str(datetime.now().year)
        # Se o ano tem 2 dígitos, converte para 4
        elif len(ano) == 2:
            ano = f"20{ano}"
        
        return f"{dia.zfill(2)}/{mes.zfill(2)}/{ano}"
    
    # Se não conseguiu processar, retorna data atual
    return datetime.now().strftime("%d/%m/%Y")


def formatar_moeda(valor: float) -> str:
    """
    Formata valor como moeda brasileira (R$ 1.234,56).
    
    Args:
        valor: Valor numérico
        
    Returns:
        String formatada como moeda brasileira
    """
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def processar_valor(valor_str: str) -> float:
    """
    Converte string de valor para float.
    
    Args:
        valor_str: String contendo o valor (pode ter R$, pontos, vírgulas)
        
    Returns:
        Valor como float
    """
    if not valor_str:
        return 0.0
    try:
        valor = str(valor_str).replace("R$", "").replace(" ", "")
        valor = valor.replace(".", "").replace(",", ".")
        return float(valor)
    except (ValueError, AttributeError):
        return 0.0
