import os
import json
from datetime import datetime
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION
)
from utils import normalizar_data

# Cliente Azure OpenAI
client = AzureOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

# Deployment para usar nas chamadas
deployment = AZURE_OPENAI_DEPLOYMENT


SYSTEM_PROMPT = """
Você é um AGENTE DE EXTRAÇÃO FINANCEIRA.

==================== CONTEXTO ====================
O usuário fornecerá texto com despesas e/ou rendas.

==================== OBJETIVO ====================
Extrair e estruturar os dados em JSON, classificando automaticamente cada transação.

==================== CATEGORIAS PERMITIDAS ====================

**DESPESAS** - Use EXATAMENTE uma destas categorias:
| Categoria | Exemplos |
|-----------|----------|
| Alimentação | mercado, supermercado, restaurante, lanche, ifood, delivery, padaria |
| Presentes | presente, gift, aniversário, natal |
| Saúde | farmácia, médico, consulta, exame, hospital, remédio, plano de saúde |
| Moradia | aluguel, condomínio, IPTU, manutenção casa, móveis |
| Transporte | Uber, 99, gasolina, combustível, estacionamento, ônibus, metrô, pedágio |
| Pessoal | roupa, calçado, academia, salão, beleza, lazer, cinema, streaming |
| Animais de estimação | ração, veterinário, pet shop, banho e tosa |
| Serviços de utilidade pública | luz, água, gás, internet, telefone, celular |
| Viagens | passagem, hotel, hospedagem, turismo |
| Débito | parcela, empréstimo, financiamento, cartão de crédito, dívida |
| Outros | qualquer despesa que não se encaixe acima |

**RENDAS** - Use EXATAMENTE uma destas categorias:
| Categoria | Exemplos |
|-----------|----------|
| Pagamento | salário, freelance, trabalho, serviço prestado |
| Poupança | rendimento poupança, resgate |
| Bônus | bônus, 13º, PLR, comissão, gratificação |
| Juros | rendimento investimento, dividendos, juros recebidos |
| Outros | qualquer renda que não se encaixe acima |

==================== INSTRUÇÕES ====================
1. Identifique se é DESPESA ou RENDA
2. Classifique automaticamente na categoria mais apropriada
3. Extraia data, valor e descrição
4. Se não souber a data, deixe vazio ""
5. Se não souber a categoria, use "Outros"

==================== REGRAS ====================
- Data: formato DD/MM/AAAA ou "" se não informada
- Valor: número decimal positivo (sem R$)
- Descrição: texto curto e claro
- Categoria: OBRIGATÓRIO usar uma da lista acima
- Não inventar dados
- Campos ausentes → null ou ""

==================== OUTPUT ====================
{
  "tipo_saida": "extracao_financeira",
  "transacoes": {
    "despesas": [
      {
        "Data": "",
        "Valor": null,
        "Descricao": "",
        "Categoria": ""
      }
    ],
    "rendas": [
      {
        "Data": "",
        "Valor": null,
        "Descricao": "",
        "Categoria": ""
      }
    ]
  },
  "resumo": {
    "Despesas": {
      "Planejado": null,
      "Real": null,
      "Diferenca": null
    },
    "Renda": {
      "Planejado": null,
      "Real": null,
      "Diferenca": null
    }
  },
  "observacoes": []
}
"""


def extrair_dados(mensagem_usuario: str) -> dict:
    """
    Extrai dados financeiros da mensagem do usuário.
    
    Args:
        mensagem_usuario: Texto contendo despesas e/ou rendas
        
    Returns:
        Dicionário com transações extraídas e estruturadas
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensagem_usuario}
            ],
            max_tokens=2048,
            temperature=0.2,  # Baixa temperatura para extração precisa
            model=deployment
        )
        
        resultado = response.choices[0].message.content.strip()
        
        # Remove marcadores de código se existirem
        resultado = resultado.replace("```json", "").replace("```", "").strip()
        
        dados = json.loads(resultado)
        
        # Normaliza as datas (adiciona ano atual se não tiver)
        transacoes = dados.get("transacoes", {})
        
        for despesa in transacoes.get("despesas", []):
            if "Data" in despesa:
                despesa["Data"] = normalizar_data(despesa["Data"])
        
        for renda in transacoes.get("rendas", []):
            if "Data" in renda:
                renda["Data"] = normalizar_data(renda["Data"])
        
        return dados
        
    except json.JSONDecodeError:
        return {
            "tipo_saida": "erro",
            "transacoes": {"despesas": [], "rendas": []},
            "resumo": {
                "Despesas": {"Planejado": None, "Real": None, "Diferenca": None},
                "Renda": {"Planejado": None, "Real": None, "Diferenca": None}
            },
            "observacoes": ["Erro ao processar resposta. Tente reformular sua mensagem."]
        }
    except Exception as e:
        return {
            "tipo_saida": "erro",
            "transacoes": {"despesas": [], "rendas": []},
            "resumo": {
                "Despesas": {"Planejado": None, "Real": None, "Diferenca": None},
                "Renda": {"Planejado": None, "Real": None, "Diferenca": None}
            },
            "observacoes": [f"Erro: {str(e)}"]
        }


def formatar_valor(valor) -> str:
    """Formata valor para exibição."""
    if valor is None:
        return "N/A"
    try:
        return f"R$ {float(valor):,.2f}"
    except:
        return str(valor)


def processar_entrada(mensagem_usuario: str) -> dict:
    """
    Processa a entrada do usuário e exibe dados extraídos.
    
    Args:
        mensagem_usuario: Texto contendo despesas e/ou rendas
        
    Returns:
        Dicionário com transações extraídas
    """
    print(f"\n📩 Mensagem: {mensagem_usuario}")
    print("-" * 50)
    
    resultado = extrair_dados(mensagem_usuario)
    
    transacoes = resultado.get("transacoes", {})
    despesas = transacoes.get("despesas", [])
    rendas = transacoes.get("rendas", [])
    
    # Exibe Despesas
    print(f"\n💸 DESPESAS EXTRAÍDAS ({len(despesas)} itens):")
    print("-" * 50)
    if despesas:
        total_despesas = 0
        for i, d in enumerate(despesas, 1):
            valor = d.get("Valor", 0) or 0
            total_despesas += valor
            print(f"  {i}. {d.get('Descricao', 'N/A')}")
            print(f"     📅 Data: {d.get('Data', 'N/A')}")
            print(f"     💵 Valor: {formatar_valor(valor)}")
            print(f"     🏷️  Categoria: {d.get('Categoria', 'N/A')}")
            print()
        print(f"  📊 Total Despesas: {formatar_valor(total_despesas)}")
    else:
        print("  Nenhuma despesa encontrada.")
    
    # Exibe Rendas
    print(f"\n💰 RENDAS EXTRAÍDAS ({len(rendas)} itens):")
    print("-" * 50)
    if rendas:
        total_rendas = 0
        for i, r in enumerate(rendas, 1):
            valor = r.get("Valor", 0) or 0
            total_rendas += valor
            print(f"  {i}. {r.get('Descricao', 'N/A')}")
            print(f"     📅 Data: {r.get('Data', 'N/A')}")
            print(f"     💵 Valor: {formatar_valor(valor)}")
            print(f"     🏷️  Categoria: {r.get('Categoria', 'N/A')}")
            print()
        print(f"  📊 Total Rendas: {formatar_valor(total_rendas)}")
    else:
        print("  Nenhuma renda encontrada.")
    
    # Exibe Resumo
    resumo = resultado.get("resumo", {})
    print(f"\n📈 RESUMO:")
    print("-" * 50)
    desp_resumo = resumo.get("Despesas", {})
    rend_resumo = resumo.get("Renda", {})
    print(f"  Despesas - Real: {formatar_valor(desp_resumo.get('Real'))}")
    print(f"  Rendas - Real: {formatar_valor(rend_resumo.get('Real'))}")
    
    # Calcula saldo
    try:
        total_r = sum(r.get("Valor", 0) or 0 for r in rendas)
        total_d = sum(d.get("Valor", 0) or 0 for d in despesas)
        saldo = total_r - total_d
        emoji = "✅" if saldo >= 0 else "❌"
        print(f"  {emoji} Saldo: {formatar_valor(saldo)}")
    except:
        pass
    
    # Observações
    obs = resultado.get("observacoes", [])
    if obs:
        print(f"\n📝 OBSERVAÇÕES:")
        for o in obs:
            print(f"  • {o}")
    
    return resultado


def exportar_json(dados: dict, arquivo: str = "dados_extraidos.json") -> None:
    """Exporta dados extraídos para arquivo JSON."""
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Dados exportados para: {arquivo}")


if __name__ == '__main__':
    print("🤖 Agente Extrator - Extração de Dados Financeiros")
    print("=" * 50)
    print("Digite suas despesas e rendas em texto livre.")
    print("Digite 'sair' para encerrar\n")
    
    while True:
        mensagem = input("💬 Sua mensagem: ").strip()
        
        if mensagem.lower() == 'sair':
            print("\n👋 Até logo!")
            break
            
        if not mensagem:
            continue
            
        resultado = processar_entrada(mensagem)
        
        exportar = input("\n📁 Exportar para JSON? (s/n): ").strip().lower()
        if exportar == 's':
            exportar_json(resultado)
