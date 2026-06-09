import os
import json
from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION
)

# Cliente Azure OpenAI
client = AzureOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

# Deployment para usar nas chamadas
deployment = AZURE_OPENAI_DEPLOYMENT

SYSTEM_PROMPT = """
Você é um AGENTE ORQUESTRADOR responsável por classificar mensagens financeiras de usuários.

==================================================
OBJETIVO
==================================================
Classificar a entrada do usuário em:

- 'dados' → quando contém transações financeiras ou informações para registro
- 'assunto' → quando contém perguntas, análises ou pedidos de conselho financeiro

==================================================
CRITÉRIOS DE CLASSIFICAÇÃO
==================================================

Classifique como 'dados' quando houver:
- valores monetários (R$, números)
- datas
- palavras como:
  'recebi', 'gastei', 'paguei', 'entrou', 'ganhei', 'salário',
  'mercado', 'Uber', 'aluguel', 'conta', 'pix', 'boleto'
- listas de despesas ou rendas
- extratos ou registros financeiros

Classifique como 'assunto' quando houver:
- perguntas financeiras
- pedidos de conselho
- análise de gastos
- planejamento financeiro
- previsão de saldo

Exemplos:
'Recebi 3000 e gastei 500' → dados  
'Como posso economizar?' → assunto  

==================================================
REGRAS
==================================================
- Classifique com base na intenção principal
- Não misturar classificação
- Não inventar informações
- Retornar SOMENTE JSON válido

==================================================
OUTPUT
==================================================
{
  "rota": "dados" | "assunto",
  "justificativa_curta": ""
}

==================================================
INSTRUÇÃO FINAL
==================================================
Analise a mensagem e retorne apenas o JSON.
"""


def classificar_mensagem(mensagem_usuario: str) -> dict:
    """
    Classifica a mensagem do usuário em 'dados' ou 'assunto'.
    
    Args:
        mensagem_usuario: A mensagem enviada pelo usuário
        
    Returns:
        Dicionário com 'rota' ('dados' ou 'assunto') e 'justificativa_curta'
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensagem_usuario}
            ],
            max_tokens=256,
            temperature=0.3,
            model=deployment,
            timeout=30
        )
        
        resultado = response.choices[0].message.content.strip()
        
        # Remove marcadores de código se existirem
        resultado = resultado.replace("```json", "").replace("```", "").strip()
        
        return json.loads(resultado)
        
    except json.JSONDecodeError:
        return {"rota": "assunto", "justificativa_curta": "Erro ao processar resposta JSON"}
    except TimeoutError:
        return {"rota": "assunto", "justificativa_curta": "Timeout na conexão com API"}
    except ConnectionError:
        return {"rota": "assunto", "justificativa_curta": "Erro de conexão com API"}
    except Exception as e:
        return {"rota": "assunto", "justificativa_curta": f"Erro: {type(e).__name__}"}


def processar_entrada(mensagem_usuario: str) -> dict:
    """
    Processa a entrada do usuário e exibe a classificação.
    
    Args:
        mensagem_usuario: A mensagem enviada pelo usuário
        
    Returns:
        Dicionário com a classificação
    """
    print(f"\n📩 Mensagem: {mensagem_usuario}")
    print("-" * 40)
    
    classificacao = classificar_mensagem(mensagem_usuario)
    
    rota = classificacao.get("rota", "desconhecido")
    justificativa = classificacao.get("justificativa_curta", "")
    
    emoji = "📊" if rota == "dados" else "💬"
    print(f"{emoji} Rota: {rota.upper()}")
    print(f"📝 Justificativa: {justificativa}")
    
    return classificacao


if __name__ == '__main__':
    print("🤖 Agente Orquestrador - Classificador de Mensagens")
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