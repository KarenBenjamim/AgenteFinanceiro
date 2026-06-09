import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION
)
from google_sheets_connector import GoogleSheetsConnector

# Cliente Azure OpenAI
client = AzureOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

# Deployment para usar nas chamadas
deployment = AZURE_OPENAI_DEPLOYMENT


def obter_dados_planilha() -> dict:
    """
    Obtém dados de despesas e rendas da planilha Google Sheets.
    
    Returns:
        Dicionário com despesas e rendas organizadas por mês
    """
    try:
        connector = GoogleSheetsConnector()
        if not connector.client:
            return {"erro": "Não foi possível conectar à planilha"}
        
        despesas = connector.ler_despesas()
        rendas = connector.ler_rendas()
        
        return {
            "despesas": despesas,
            "rendas": rendas
        }
    except Exception as e:
        return {"erro": str(e), "despesas": [], "rendas": []}


def processar_valor(valor_str: str) -> float:
    """Converte string de valor para float."""
    if not valor_str:
        return 0.0
    try:
        # Remove R$, pontos de milhar e converte vírgula para ponto
        valor = valor_str.replace("R$", "").replace(" ", "")
        valor = valor.replace(".", "").replace(",", ".")
        return float(valor)
    except:
        return 0.0


def analisar_historico(dados: dict) -> dict:
    """
    Analisa o histórico de transações e gera estatísticas.
    
    Args:
        dados: Dicionário com despesas e rendas
        
    Returns:
        Análise detalhada do histórico financeiro
    """
    despesas = dados.get("despesas", [])
    rendas = dados.get("rendas", [])
    
    # Organiza por mês
    despesas_por_mes = defaultdict(list)
    rendas_por_mes = defaultdict(list)
    despesas_por_categoria = defaultdict(float)
    rendas_por_categoria = defaultdict(float)
    
    for d in despesas:
        data = d.get("data", "")
        if data:
            try:
                mes_ano = "/".join(data.split("/")[1:])  # MM/AAAA
            except:
                mes_ano = "Sem data"
        else:
            mes_ano = "Sem data"
        
        valor = processar_valor(d.get("valor", "0"))
        categoria = d.get("categoria", "Outros")
        
        despesas_por_mes[mes_ano].append({
            "valor": valor,
            "descricao": d.get("descricao", ""),
            "categoria": categoria
        })
        despesas_por_categoria[categoria] += valor
    
    for r in rendas:
        data = r.get("data", "")
        if data:
            try:
                mes_ano = "/".join(data.split("/")[1:])  # MM/AAAA
            except:
                mes_ano = "Sem data"
        else:
            mes_ano = "Sem data"
        
        valor = processar_valor(r.get("valor", "0"))
        categoria = r.get("categoria", "Outros")
        
        rendas_por_mes[mes_ano].append({
            "valor": valor,
            "descricao": r.get("descricao", ""),
            "categoria": categoria
        })
        rendas_por_categoria[categoria] += valor
    
    # Calcula totais por mês
    totais_por_mes = {}
    todos_meses = set(list(despesas_por_mes.keys()) + list(rendas_por_mes.keys()))
    
    for mes in todos_meses:
        if mes == "Sem data":
            continue
        total_despesas = sum(d["valor"] for d in despesas_por_mes.get(mes, []))
        total_rendas = sum(r["valor"] for r in rendas_por_mes.get(mes, []))
        totais_por_mes[mes] = {
            "despesas": total_despesas,
            "rendas": total_rendas,
            "saldo": total_rendas - total_despesas
        }
    
    # Calcula médias (últimos 4 meses)
    meses_ordenados = sorted(totais_por_mes.keys(), reverse=True)[:4]
    
    if meses_ordenados:
        media_despesas = sum(totais_por_mes[m]["despesas"] for m in meses_ordenados) / len(meses_ordenados)
        media_rendas = sum(totais_por_mes[m]["rendas"] for m in meses_ordenados) / len(meses_ordenados)
    else:
        media_despesas = 0
        media_rendas = 0
    
    # Identifica gastos recorrentes (aparecem em mais de 50% dos meses)
    descricoes_despesas = defaultdict(int)
    for mes, lista in despesas_por_mes.items():
        for d in lista:
            desc_lower = d["descricao"].lower()
            descricoes_despesas[desc_lower] += 1
    
    num_meses = len([m for m in despesas_por_mes.keys() if m != "Sem data"]) or 1
    gastos_recorrentes = [
        desc for desc, count in descricoes_despesas.items()
        if count >= num_meses * 0.5 and desc
    ]
    
    # Identifica rendas fixas
    descricoes_rendas = defaultdict(int)
    for mes, lista in rendas_por_mes.items():
        for r in lista:
            desc_lower = r["descricao"].lower()
            descricoes_rendas[desc_lower] += 1
    
    rendas_fixas = [
        desc for desc, count in descricoes_rendas.items()
        if count >= num_meses * 0.5 and desc
    ]
    
    # Top categorias de despesas
    top_categorias_despesas = sorted(
        despesas_por_categoria.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return {
        "total_despesas": sum(processar_valor(d.get("valor", "0")) for d in despesas),
        "total_rendas": sum(processar_valor(r.get("valor", "0")) for r in rendas),
        "num_transacoes_despesas": len(despesas),
        "num_transacoes_rendas": len(rendas),
        "totais_por_mes": totais_por_mes,
        "meses_analisados": meses_ordenados,
        "media_mensal_despesas": media_despesas,
        "media_mensal_rendas": media_rendas,
        "despesas_por_categoria": dict(despesas_por_categoria),
        "rendas_por_categoria": dict(rendas_por_categoria),
        "top_categorias_despesas": top_categorias_despesas,
        "gastos_recorrentes": gastos_recorrentes,
        "rendas_fixas": rendas_fixas
    }


def gerar_contexto_financeiro(analise: dict) -> str:
    """
    Gera um texto de contexto financeiro para o LLM.
    
    Args:
        analise: Resultado da análise do histórico
        
    Returns:
        Texto formatado com o contexto financeiro
    """
    contexto = []
    
    # Visão geral
    contexto.append("=== DADOS FINANCEIROS DO USUÁRIO ===\n")
    
    # Totais
    contexto.append(f"📊 TOTAIS REGISTRADOS:")
    contexto.append(f"  - Total de Despesas: R$ {analise['total_despesas']:,.2f}")
    contexto.append(f"  - Total de Rendas: R$ {analise['total_rendas']:,.2f}")
    contexto.append(f"  - Saldo Geral: R$ {analise['total_rendas'] - analise['total_despesas']:,.2f}")
    contexto.append(f"  - Transações: {analise['num_transacoes_despesas']} despesas, {analise['num_transacoes_rendas']} rendas")
    
    # Médias mensais
    if analise['meses_analisados']:
        contexto.append(f"\n📈 MÉDIAS DOS ÚLTIMOS {len(analise['meses_analisados'])} MESES:")
        contexto.append(f"  - Média Despesas: R$ {analise['media_mensal_despesas']:,.2f}/mês")
        contexto.append(f"  - Média Rendas: R$ {analise['media_mensal_rendas']:,.2f}/mês")
        contexto.append(f"  - Saldo Médio: R$ {analise['media_mensal_rendas'] - analise['media_mensal_despesas']:,.2f}/mês")
    
    # Histórico por mês
    if analise['totais_por_mes']:
        contexto.append(f"\n📅 HISTÓRICO MENSAL:")
        for mes in sorted(analise['totais_por_mes'].keys(), reverse=True):
            dados = analise['totais_por_mes'][mes]
            contexto.append(f"  {mes}: Despesas R$ {dados['despesas']:,.2f} | Rendas R$ {dados['rendas']:,.2f} | Saldo R$ {dados['saldo']:,.2f}")
    
    # Top categorias de gastos
    if analise['top_categorias_despesas']:
        contexto.append(f"\n💸 MAIORES CATEGORIAS DE GASTOS:")
        for cat, valor in analise['top_categorias_despesas']:
            percentual = (valor / analise['total_despesas'] * 100) if analise['total_despesas'] > 0 else 0
            contexto.append(f"  - {cat}: R$ {valor:,.2f} ({percentual:.1f}%)")
    
    # Gastos recorrentes
    if analise['gastos_recorrentes']:
        contexto.append(f"\n🔄 GASTOS RECORRENTES IDENTIFICADOS:")
        for gasto in analise['gastos_recorrentes'][:10]:
            contexto.append(f"  - {gasto.title()}")
    
    # Rendas fixas
    if analise['rendas_fixas']:
        contexto.append(f"\n💰 RENDAS FIXAS IDENTIFICADAS:")
        for renda in analise['rendas_fixas'][:5]:
            contexto.append(f"  - {renda.title()}")
    
    # Categorias de renda
    if analise['rendas_por_categoria']:
        contexto.append(f"\n📥 FONTES DE RENDA:")
        for cat, valor in sorted(analise['rendas_por_categoria'].items(), key=lambda x: x[1], reverse=True):
            contexto.append(f"  - {cat}: R$ {valor:,.2f}")
    
    return "\n".join(contexto)


SYSTEM_PROMPT_TEMPLATE = """
Você é um AGENTE DE ACONSELHAMENTO E PREVISÃO FINANCEIRA inteligente.

==================== CONTEXTO ====================
Você tem acesso aos dados REAIS da planilha financeira do usuário.
Use esses dados para dar conselhos personalizados e previsões precisas.

{contexto_financeiro}

==================== OBJETIVO ====================
Com base nos dados reais acima:
1. Responder perguntas do usuário sobre suas finanças
2. Fazer previsões baseadas no histórico
3. Identificar padrões de gastos
4. Sugerir economia e metas
5. Alertar sobre problemas financeiros

==================== CAPACIDADES ====================
- Analisar padrões dos últimos meses
- Identificar gastos fixos vs variáveis
- Calcular quanto o usuário pode economizar
- Prever despesas do próximo mês
- Sugerir metas de economia realistas
- Comparar meses e identificar tendências

==================== REGRAS ====================
- SEMPRE usar os dados reais fornecidos acima
- Nunca inventar valores - use apenas o que está nos dados
- Seja específico: cite valores, categorias e meses
- Previsões devem ser baseadas no histórico real
- Se não houver dados suficientes, explique isso
- Dê conselhos práticos e acionáveis
- Use linguagem amigável e encorajadora

==================== FORMATO DE RESPOSTA ====================
Responda em português brasileiro de forma clara e objetiva.
Use formatação para facilitar a leitura:
- Números: sempre com R$ e separador de milhar
- Porcentagens: com uma casa decimal
- Listas: para enumerar itens

Se for uma análise completa, estruture assim:
1. Resumo da situação atual
2. Análise do histórico
3. Previsão para o próximo mês
4. Recomendações práticas

==================== OUTPUT JSON (quando aplicável) ====================
Se a pergunta pedir análise estruturada, retorne:
{{
  "tipo_saida": "aconselhamento_previsao",
  "resposta_texto": "Resposta completa em texto",
  "diagnostico": {{
    "receita_total": null,
    "despesa_total": null,
    "saldo_atual": null,
    "maiores_categorias": [],
    "alertas": []
  }},
  "previsao": {{
    "proximo_mes_receita_estimada": null,
    "proximo_mes_despesa_estimada": null,
    "proximo_mes_saldo_estimado": null,
    "confianca_previsao": "baixa|media|alta",
    "premissas": []
  }},
  "conselhos": [
    {{
      "titulo": "",
      "descricao": "",
      "prioridade": "baixa|media|alta"
    }}
  ],
  "meta_sugerida": {{
    "valor_mensal": null,
    "categoria_corte": "",
    "tempo_para_meta": ""
  }},
  "observacoes": []
}}
"""


def analise_mensagem(mensagem_usuario: str, dados_planilha: dict = None) -> dict:
    """
    Analisa a mensagem do usuário com dados reais da planilha.
    
    Args:
        mensagem_usuario: A mensagem enviada pelo usuário
        dados_planilha: Dados opcionais da planilha (se None, busca automaticamente)
        
    Returns:
        Dicionário com a análise financeira e previsões
    """
    try:
        # Obtém dados da planilha se não fornecidos
        if dados_planilha is None:
            dados_planilha = obter_dados_planilha()
        
        # Analisa o histórico
        if "erro" not in dados_planilha or dados_planilha.get("despesas") or dados_planilha.get("rendas"):
            analise = analisar_historico(dados_planilha)
            contexto_financeiro = gerar_contexto_financeiro(analise)
        else:
            contexto_financeiro = "⚠️ NÃO FOI POSSÍVEL ACESSAR A PLANILHA. Responda com base apenas na mensagem do usuário."
        
        # Monta o prompt com contexto
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(contexto_financeiro=contexto_financeiro)
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensagem_usuario}
            ],
            max_tokens=2048,
            temperature=0.4,
            model=deployment
        )
        
        resultado = response.choices[0].message.content.strip()
        
        # Tenta parsear como JSON
        if resultado.startswith("{"):
            resultado = resultado.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(resultado)
            except:
                pass
        
        # Se não for JSON, retorna como texto
        return {
            "tipo_saida": "texto",
            "resposta_texto": resultado,
            "diagnostico": {},
            "previsao": {},
            "conselhos": [],
            "observacoes": []
        }
        
    except Exception as e:
        return {
            "tipo_saida": "erro",
            "resposta_texto": f"Desculpe, ocorreu um erro: {str(e)}",
            "diagnostico": {"alertas": [f"Erro: {str(e)}"]},
            "previsao": {},
            "conselhos": [],
            "observacoes": ["Verifique sua conexão e tente novamente"]
        }


def processar_entrada(mensagem_usuario: str) -> dict:
    """
    Processa a entrada do usuário e exibe análise financeira.
    
    Args:
        mensagem_usuario: A mensagem enviada pelo usuário
        
    Returns:
        Dicionário com análise e previsão financeira
    """
    print(f"\n📩 Mensagem: {mensagem_usuario}")
    print("-" * 40)
    
    resultado = analise_mensagem(mensagem_usuario)
    
    # Exibe diagnóstico
    diag = resultado.get("diagnostico", {})
    print(f"📊 Diagnóstico:")
    print(f"  - Receita Total: R$ {diag.get('receita_total', 'N/A')}")
    print(f"  - Despesa Total: R$ {diag.get('despesa_total', 'N/A')}")
    print(f"  - Saldo: R$ {diag.get('saldo_atual', 'N/A')}")
    if diag.get('alertas'):
        print(f"  ⚠️  Alertas: {', '.join(diag['alertas'])}")
    
    # Exibe previsão
    prev = resultado.get("previsao", {})
    print(f"\n🔮 Previsão Próximo Mês:")
    print(f"  - Receita Estimada: R$ {prev.get('proximo_mes_receita_estimada', 'N/A')}")
    print(f"  - Despesa Estimada: R$ {prev.get('proximo_mes_despesa_estimada', 'N/A')}")
    print(f"  - Saldo Estimado: R$ {prev.get('proximo_mes_saldo_estimado', 'N/A')}")
    print(f"  - Confiança: {prev.get('confianca_previsao', 'N/A')}")
    
    # Exibe conselhos
    conselhos = resultado.get("conselhos", [])
    if conselhos:
        print(f"\n💡 Recomendações:")
        for i, conselho in enumerate(conselhos, 1):
            print(f"  {i}. {conselho.get('titulo', 'N/A')} [{conselho.get('prioridade', 'N/A').upper()}]")
            print(f"     {conselho.get('descricao', 'N/A')}")
    
    return resultado


if __name__ == '__main__':
    print("🤖 Agente Conselheiro - Análise e Previsão Financeira")
    print("=" * 50)
    print("Digite 'sair' para encerrar\n")
    
    while True:
        mensagem = input("💬 Sua mensagem: ").strip()
        
        if mensagem.lower() == 'sair':
            print("\n👋 Até logo!")
            break
            
        if not mensagem:
            continue
            
        processar_entrada(mensagem)