"""
Agente Leitor de Arquivos - Extrai movimentações de PDFs e Imagens
===================================================================
Utiliza GPT-4o Vision para ler prints e pdfplumber para PDFs.
Extrai transações e as registra sem duplicidade.
"""

import os
import io
import base64
import json
import logging
from typing import List, Optional, Union
import pdfplumber
from PIL import Image
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION
)
from utils import normalizar_data
from data_manager import registrar_despesa_sem_duplicar, registrar_renda_sem_duplicar

# Configuração de logging
logger = logging.getLogger(__name__)

# Constantes para tipos de transação
TIPOS_RENDA = {"renda", "receita", "credito", "entrada"}

# Mapeamento de extensões para media types
EXTENSOES_MEDIA_TYPE = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp"
}

# Cliente Azure OpenAI (lazy loading)
_client = None


def get_client() -> AzureOpenAI:
    """
    Retorna o cliente Azure OpenAI com lazy loading.
    
    Returns:
        Cliente AzureOpenAI configurado
        
    Raises:
        RuntimeError: Se falhar ao inicializar o cliente
    """
    global _client
    if _client is None:
        try:
            _client = AzureOpenAI(
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_API_KEY,
            )
        except Exception as e:
            logger.error(f"Falha ao inicializar cliente Azure OpenAI: {e}")
            raise RuntimeError(f"Falha ao inicializar cliente Azure OpenAI: {e}")
    return _client

# Prompt para extração de movimentações
EXTRACTION_PROMPT = """
Você é um AGENTE DE EXTRAÇÃO DE MOVIMENTAÇÕES BANCÁRIAS.

==================== OBJETIVO ====================
Analisar o documento/imagem fornecido e extrair TODAS as movimentações financeiras.

==================== REGRAS CRÍTICAS DE EXTRAÇÃO ====================
⚠️ ATENÇÃO MÁXIMA: Leia LINHA POR LINHA com muito cuidado!

1. Cada LINHA do extrato é UMA transação separada
2. O VALOR e a DESCRIÇÃO na MESMA LINHA pertencem à MESMA transação
3. NUNCA misture o valor de uma linha com a descrição de outra linha
4. Leia da esquerda para direita: DATA → VALOR → DESCRIÇÃO/DESTINATÁRIO

EXEMPLO CORRETO:
Se você vê:
  "04/05 - R$2,00 - PIX enviado João"
  "04/05 - R$58,98 - PIX enviado Maria"
  
Deve extrair:
  - Transação 1: data=04/05, valor=2.00, descricao=PIX enviado João
  - Transação 2: data=04/05, valor=58.98, descricao=PIX enviado Maria

EXEMPLO ERRADO (NÃO FAÇA ISSO):
  - Transação 1: data=04/05, valor=2.00, descricao=PIX enviado Maria ❌
  - Transação 2: data=04/05, valor=58.98, descricao=PIX enviado João ❌

==================== CATEGORIAS PERMITIDAS ====================

**DESPESAS** (gastos, débitos, saídas):
| Categoria | Exemplos |
|-----------|----------|
| Alimentação | mercado, supermercado, restaurante, ifood, padaria, delivery |
| Presentes | presente, gift, aniversário |
| Saúde | farmácia, médico, consulta, hospital, remédio |
| Moradia | aluguel, condomínio, IPTU, manutenção |
| Transporte | Uber, 99, gasolina, estacionamento, pedágio |
| Pessoal | roupa, academia, salão, cinema, streaming |
| Animais de estimação | ração, veterinário, pet shop |
| Serviços de utilidade pública | luz, água, gás, internet, telefone |
| Viagens | passagem, hotel, hospedagem |
| Débito | parcela, empréstimo, financiamento, cartão |
| Educação | escola, faculdade, curso, mensalidade, livro, material escolar, Ingles |
| Outros | qualquer despesa não listada |

**RENDAS** (entradas, créditos, recebimentos):
| Categoria | Exemplos |
|-----------|----------|
| Pagamento | salário, freelance, trabalho |
| Poupança | rendimento poupança, resgate |
| Bônus | 13º, PLR, comissão |
| Juros | rendimento investimento, dividendos |
| Outros | qualquer renda não listada |

==================== INSTRUÇÕES ====================
1. Leia o documento LINHA POR LINHA
2. Para CADA linha que contém uma transação:
   - Identifique a DATA dessa linha
   - Identifique o VALOR dessa linha
   - Identifique a DESCRIÇÃO/DESTINATÁRIO dessa linha
   - Classifique como despesa ou renda
   - Escolha a categoria apropriada

3. Critérios para DESPESA:
   - Débito, saída, pagamento, compra
   - PIX enviado, transferência enviada

4. Critérios para RENDA:
   - Crédito, entrada, recebimento
   - PIX recebido, transferência recebida

==================== OUTPUT ====================
Retorne APENAS JSON válido:
{
  "transacoes": [
    {
      "data": "DD/MM",
      "valor": 0.00,
      "descricao": "",
      "tipo": "despesa" ou "renda",
      "categoria": ""
    }
  ],
  "observacoes": []
}

⚠️ IMPORTANTE SOBRE DATAS:
- Se a data no documento tem apenas dia/mês (ex: 04/05), use exatamente "DD/MM" sem inventar ano
- Se a data tem ano completo (ex: 04/05/2024), use "DD/MM/AAAA"
- NUNCA invente ou assuma um ano que não está no documento
"""


def _parse_gpt_response(resultado: str) -> dict:
    """
    Processa resposta da API GPT e retorna dicionário de transações.
    
    Args:
        resultado: String de resposta da API
        
    Returns:
        Dicionário com transações extraídas
        
    Raises:
        json.JSONDecodeError: Se o JSON for inválido
    """
    # Remove marcadores de código se existirem
    resultado = resultado.replace("```json", "").replace("```", "").strip()
    return json.loads(resultado)


def _detectar_media_type(caminho_ou_extensao: str) -> str:
    """
    Detecta media type baseado na extensão do arquivo.
    
    Args:
        caminho_ou_extensao: Caminho do arquivo ou extensão
        
    Returns:
        Media type correspondente (default: image/png)
    """
    ext = caminho_ou_extensao.lower().split(".")[-1]
    return EXTENSOES_MEDIA_TYPE.get(ext, "image/png")


def extrair_texto_pdf(arquivo_pdf: Union[str, bytes, io.BytesIO]) -> Optional[str]:
    """
    Extrai texto de um arquivo PDF.
    
    Args:
        arquivo_pdf: Caminho do arquivo, bytes ou BytesIO
        
    Returns:
        Texto extraído do PDF ou None em caso de erro
    """
    try:
        # Normaliza entrada para BytesIO se for bytes
        if isinstance(arquivo_pdf, bytes):
            arquivo_pdf = io.BytesIO(arquivo_pdf)
        
        with pdfplumber.open(arquivo_pdf) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""
                texto += "\n\n"
            return texto.strip() or None
                
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {e}")
        return None


def imagem_para_base64(imagem: Union[str, bytes, Image.Image]) -> str:
    """
    Converte imagem para base64 para enviar à API Vision.
    
    Args:
        imagem: Caminho do arquivo, bytes ou objeto PIL Image
        
    Returns:
        String base64 da imagem
    """
    try:
        if isinstance(imagem, str):
            # É um caminho de arquivo
            with open(imagem, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        elif isinstance(imagem, bytes):
            return base64.b64encode(imagem).decode("utf-8")
        elif isinstance(imagem, Image.Image):
            buffer = io.BytesIO()
            imagem.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        else:
            raise ValueError("Tipo de imagem não suportado")
    except Exception as e:
        logger.error(f"Erro ao converter imagem: {e}")
        return ""


def extrair_transacoes_de_texto(texto: str) -> dict:
    """
    Usa GPT-4o para extrair transações de texto (PDF).
    
    Args:
        texto: Texto extraído do PDF
        
    Returns:
        Dicionário com transações extraídas
    """
    resultado = ""
    try:
        client = get_client()
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": f"Extraia as movimentações do seguinte texto:\n\n{texto}"}
            ],
            max_tokens=4096,
            temperature=0.1,
            model=AZURE_OPENAI_DEPLOYMENT
        )
        
        resultado = response.choices[0].message.content.strip()
        return _parse_gpt_response(resultado)
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao parsear JSON: {e}")
        logger.debug(f"Conteúdo recebido: {resultado[:500]}...")
        return {"transacoes": [], "observacoes": ["Erro ao processar resposta"]}
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
        return {"transacoes": [], "observacoes": [f"Erro: {str(e)}"]}


def extrair_transacoes_de_imagem(imagem: Union[str, bytes, Image.Image]) -> dict:
    """
    Usa GPT-4o Vision para extrair transações de uma imagem.
    
    Args:
        imagem: Caminho do arquivo, bytes ou objeto PIL Image
        
    Returns:
        Dicionário com transações extraídas
    """
    resultado = ""
    try:
        imagem_base64 = imagem_para_base64(imagem)
        
        if not imagem_base64:
            return {"transacoes": [], "observacoes": ["Erro ao processar imagem"]}
        
        # Detecta o tipo de imagem
        media_type = _detectar_media_type(imagem) if isinstance(imagem, str) else "image/png"
        
        client = get_client()
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analise esta imagem e extraia TODAS as movimentações financeiras visíveis:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{imagem_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096,
            temperature=0.1,
            model=AZURE_OPENAI_DEPLOYMENT
        )
        
        resultado = response.choices[0].message.content.strip()
        return _parse_gpt_response(resultado)
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao parsear JSON: {e}")
        logger.debug(f"Conteúdo recebido: {resultado[:500]}...")
        return {"transacoes": [], "observacoes": ["Erro ao processar resposta da IA"]}
    except Exception as e:
        logger.error(f"Erro na extração de imagem: {e}")
        return {"transacoes": [], "observacoes": [f"Erro: {str(e)}"]}


def processar_arquivo(arquivo: Union[str, bytes], nome_arquivo: str = "") -> dict:
    """
    Processa um arquivo (PDF ou imagem) e extrai transações.
    
    Args:
        arquivo: Caminho do arquivo ou bytes
        nome_arquivo: Nome do arquivo (para detectar tipo)
        
    Returns:
        Dicionário com transações extraídas
    """
    # Detecta o tipo de arquivo
    if isinstance(arquivo, str):
        nome_arquivo = arquivo.lower()
    else:
        nome_arquivo = nome_arquivo.lower()
    
    if nome_arquivo.endswith(".pdf"):
        logger.info("Processando PDF...")
        texto = extrair_texto_pdf(arquivo)
        if texto:
            logger.info(f"Extraído {len(texto)} caracteres de texto")
            return extrair_transacoes_de_texto(texto)
        else:
            return {"transacoes": [], "observacoes": ["PDF vazio ou não legível"]}
    
    elif nome_arquivo.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        logger.info("Processando imagem...")
        return extrair_transacoes_de_imagem(arquivo)
    
    else:
        logger.warning(f"Tipo de arquivo não suportado: {nome_arquivo}")
        return {"transacoes": [], "observacoes": ["Tipo de arquivo não suportado"]}


def registrar_transacoes_extraidas(transacoes: List[dict]) -> dict:
    """
    Registra as transações extraídas na planilha, verificando duplicidade.
    
    Args:
        transacoes: Lista de transações extraídas
        
    Returns:
        Estatísticas do registro
    """
    resultado = {
        "total": len(transacoes),
        "adicionadas": 0,
        "duplicatas": 0,
        "erros": 0,
        "detalhes": []
    }
    
    for t in transacoes:
        data = t.get("data", "")
        valor_raw = t.get("valor")
        descricao = t.get("descricao", "")
        categoria = t.get("categoria", "Outros")
        tipo = t.get("tipo", "despesa").lower()
        
        # Valida e converte valor
        if not isinstance(valor_raw, (int, float)) or valor_raw <= 0:
            resultado["erros"] += 1
            resultado["detalhes"].append({
                "transacao": t,
                "status": "erro",
                "mensagem": f"Valor inválido: {valor_raw}"
            })
            continue
        
        valor = float(valor_raw)
        
        # Normaliza a data (adiciona ano atual se não tiver)
        data = normalizar_data(data)
        
        # Valida dados mínimos
        if not data:
            resultado["erros"] += 1
            resultado["detalhes"].append({
                "transacao": t,
                "status": "erro",
                "mensagem": "Data inválida ou ausente"
            })
            continue
        
        # Registra conforme o tipo
        if tipo in TIPOS_RENDA:
            res = registrar_renda_sem_duplicar(data, valor, descricao, categoria)
        else:
            res = registrar_despesa_sem_duplicar(data, valor, descricao, categoria)
        
        if res["duplicata"]:
            resultado["duplicatas"] += 1
            resultado["detalhes"].append({
                "transacao": t,
                "status": "duplicata",
                "mensagem": res["mensagem"]
            })
        elif res["sucesso"]:
            resultado["adicionadas"] += 1
            resultado["detalhes"].append({
                "transacao": t,
                "status": "adicionada",
                "mensagem": res["mensagem"]
            })
        else:
            resultado["erros"] += 1
            resultado["detalhes"].append({
                "transacao": t,
                "status": "erro",
                "mensagem": res["mensagem"]
            })
    
    return resultado


def processar_e_registrar(arquivo: Union[str, bytes], nome_arquivo: str = "") -> dict:
    """
    Processa um arquivo e registra as transações encontradas.
    
    Args:
        arquivo: Caminho do arquivo ou bytes
        nome_arquivo: Nome do arquivo (para detectar tipo)
        
    Returns:
        Resultado completo do processamento
    """
    logger.info("=" * 50)
    logger.info("PROCESSANDO ARQUIVO")
    logger.info("=" * 50)
    
    # Extrai transações
    dados = processar_arquivo(arquivo, nome_arquivo)
    transacoes = dados.get("transacoes", [])
    observacoes = dados.get("observacoes", [])
    
    if not transacoes:
        logger.warning("Nenhuma transação encontrada no arquivo")
        return {
            "extraidas": 0,
            "registradas": 0,
            "duplicatas": 0,
            "erros": 0,
            "observacoes": observacoes
        }
    
    logger.info(f"Encontradas {len(transacoes)} transações")
    
    # Mostra preview
    logger.info("Preview das transações:")
    for i, t in enumerate(transacoes[:5], 1):
        tipo_str = "RENDA" if t.get("tipo") == "renda" else "DESPESA"
        logger.info(f"   {i}. [{tipo_str}] {t.get('data')} | R${t.get('valor', 0):.2f} | {t.get('descricao')} [{t.get('categoria')}]")
    
    if len(transacoes) > 5:
        logger.info(f"   ... e mais {len(transacoes) - 5} transações")
    
    # Registra na planilha
    logger.info("Registrando na planilha...")
    resultado_registro = registrar_transacoes_extraidas(transacoes)
    
    # Mostra resumo
    logger.info("-" * 40)
    logger.info("RESUMO:")
    logger.info(f"   Adicionadas: {resultado_registro['adicionadas']}")
    logger.info(f"   Duplicatas: {resultado_registro['duplicatas']}")
    logger.info(f"   Erros: {resultado_registro['erros']}")
    
    if observacoes:
        logger.info("Observações:")
        for obs in observacoes:
            logger.info(f"   - {obs}")
    
    return {
        "extraidas": len(transacoes),
        "registradas": resultado_registro["adicionadas"],
        "duplicatas": resultado_registro["duplicatas"],
        "erros": resultado_registro["erros"],
        "observacoes": observacoes,
        "detalhes": resultado_registro["detalhes"]
    }


if __name__ == "__main__":
    # Configura logging para console
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )
    
    print("🤖 Agente Leitor de Arquivos")
    print("=" * 50)
    print("\nFormatos suportados: PDF, PNG, JPG, JPEG, GIF, WEBP")
    print("Digite 'sair' para encerrar\n")
    
    while True:
        caminho = input("📂 Caminho do arquivo: ").strip().strip('"')
        
        if caminho.lower() == "sair":
            print("\n👋 Até logo!")
            break
        
        if not caminho:
            continue
        
        if not os.path.exists(caminho):
            print(f"❌ Arquivo não encontrado: {caminho}")
            continue
        
        resultado = processar_e_registrar(caminho)
        print("\n")
