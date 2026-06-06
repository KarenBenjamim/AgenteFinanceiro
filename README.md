# 💰 Agente Financeiro Inteligente

Sistema de gerenciamento financeiro pessoal com IA, integrado ao Google Sheets.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Categorias](#-categorias)
- [Exemplos](#-exemplos)
- [API Reference](#-api-reference)

---

## 🎯 Visão Geral

O Agente Financeiro é um assistente inteligente que utiliza **Azure OpenAI GPT-4o** para:

- ✅ **Registrar transações** automaticamente (despesas e rendas)
- ✅ **Classificar gastos** em categorias predefinidas
- ✅ **Analisar padrões** de consumo
- ✅ **Fazer previsões** financeiras baseadas no histórico
- ✅ **Dar conselhos** personalizados de economia
- ✅ **Sincronizar** com Google Sheets em tempo real

---

## 🏗 Arquitetura

O sistema utiliza uma arquitetura de **multi-agentes** orquestrados:

```
┌─────────────────────────────────────────────────────────────┐
│                      USUÁRIO                                 │
│              "Gastei R$200 no mercado ontem"                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  AGENTE ORQUESTRADOR                        │
│         Classifica: "dados" ou "assunto"                    │
│                                                              │
│  • dados → transações financeiras para registro             │
│  • assunto → perguntas, análises, conselhos                │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│   AGENTE DE EXTRAÇÃO    │     │    AGENTE CONSELHEIRO       │
│                         │     │                             │
│  • Extrai Data          │     │  • Lê dados da planilha     │
│  • Extrai Valor         │     │  • Analisa histórico        │
│  • Extrai Descrição     │     │  • Identifica padrões       │
│  • Classifica Categoria │     │  • Faz previsões            │
│                         │     │  • Sugere economia          │
└─────────────────────────┘     └─────────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE SHEETS                            │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────┐      │
│  │    DESPESAS      │    │         RENDAS           │      │
│  │  B5: Data        │    │      G5: Data            │      │
│  │  C5: Valor       │    │      H5: Valor           │      │
│  │  D5: Descrição   │    │      I5: Descrição       │      │
│  │  E5: Categoria   │    │      J5: Categoria       │      │
│  └──────────────────┘    └──────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Requisitos

- Python 3.10+
- Conta Azure com Azure OpenAI Service
- Conta Google Cloud com API do Sheets habilitada
- Service Account do Google configurada

### Dependências Python

```
pandas>=2.0.0
openpyxl>=3.1.0
openai>=1.0.0
gspread>=5.10.0
google-auth>=2.20.0
google-auth-oauthlib>=1.0.0
python-dotenv>=1.0.0
```

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd "Agente finaceiro"
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
cd .venv\scr
copy .env.example .env
```

Edite o arquivo `.env`:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://seu-recurso.cognitiveservices.azure.com/
AZURE_OPENAI_MODEL=gpt-4o
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_KEY=sua-chave-aqui
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Google Sheets
GOOGLE_SPREADSHEET_ID=id-da-sua-planilha
```

### 2. Google Service Account

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou selecione existente
3. Ative as APIs:
   - Google Sheets API
   - Google Drive API
4. Vá em **IAM & Admin > Service Accounts**
5. Crie uma Service Account
6. Gere uma chave JSON
7. Salve como `credentials.json` na pasta `.venv\scr\`
8. Compartilhe sua planilha com o email da Service Account

### 3. Estrutura da Planilha

Crie uma aba chamada **"Transações"** com a estrutura:

| Coluna | B-E (Despesas) | G-J (Rendas) |
|--------|----------------|--------------|
| Linha 4 | Cabeçalho | Cabeçalho |
| Linha 5+ | Dados | Dados |

```
     B        C        D           E          |      G        H        I           J
   Data     Valor   Descrição   Categoria    |    Data     Valor   Descrição   Categoria
05/06/2026  R$200   Mercado     Alimentação  | 05/06/2026  R$3500  Salário     Pagamento
```

---

## 🎮 Como Usar

### Executar o Assistente

```bash
cd .venv\scr
python Main.py
```

### Interação

```
💰 ASSISTENTE FINANCEIRO INTELIGENTE
============================================================

💬 Você: Gastei R$150 no mercado e R$50 no Uber hoje

🔄 Analisando sua mensagem...
   Classificado como: DADOS

📊 Extraindo dados financeiros...
✅ Encontrado: 2 despesa(s) e 0 renda(s)

📊 Despesa 1:
   Data: 05/06/2026
   Valor: 150.0
   Descrição: Mercado
   Categoria: Alimentação
✅ Despesa adicionada na planilha!

📊 Despesa 2:
   Data: 05/06/2026
   Valor: 50.0
   Descrição: Uber
   Categoria: Transporte
✅ Despesa adicionada na planilha!
```

```
💬 Você: Como estão minhas finanças?

🔄 Analisando sua mensagem...
   Classificado como: ASSUNTO

💡 Analisando sua situação financeira...

📊 Com base nos seus dados dos últimos 4 meses:

RESUMO:
- Total de Despesas: R$ 8.500,00
- Total de Rendas: R$ 14.000,00
- Saldo: R$ 5.500,00

MAIORES GASTOS:
1. Alimentação: R$ 2.400,00 (28%)
2. Moradia: R$ 2.000,00 (24%)
3. Transporte: R$ 1.200,00 (14%)

PREVISÃO PRÓXIMO MÊS:
- Despesas estimadas: R$ 2.125,00
- Receita estimada: R$ 3.500,00
- Saldo previsto: R$ 1.375,00

💡 DICA: Você pode economizar R$ 300/mês reduzindo
gastos com Alimentação (delivery/restaurantes).
```

---

## 📁 Estrutura do Projeto

```
Agente finaceiro/
├── .venv/
│   └── scr/
│       ├── .env                    # Variáveis de ambiente (NÃO COMMITAR!)
│       ├── .env.example            # Template das variáveis
│       ├── config.py               # Carrega configurações do .env
│       ├── credentials.json        # Credenciais Google (NÃO COMMITAR!)
│       ├── Main.py                 # Fluxo principal do assistente
│       ├── agente_orquestrador.py  # Classifica mensagens
│       ├── agente_extracao.py      # Extrai dados financeiros
│       ├── agente_concelheiro.py   # Análise e conselhos
│       └── google_sheets_connector.py  # Integração com Sheets
├── .gitignore
├── requirements.txt
└── README.md
```

### Descrição dos Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `Main.py` | Ponto de entrada. Orquestra o fluxo entre agentes |
| `agente_orquestrador.py` | Classifica input como "dados" ou "assunto" |
| `agente_extracao.py` | Extrai Data, Valor, Descrição, Categoria do texto |
| `agente_concelheiro.py` | Lê planilha e dá conselhos baseados no histórico |
| `google_sheets_connector.py` | CRUD na planilha Google Sheets |
| `config.py` | Centraliza carregamento de variáveis de ambiente |

---

## 🏷️ Categorias

### Despesas

| Categoria | Exemplos |
|-----------|----------|
| **Alimentação** | Mercado, restaurante, iFood, padaria, delivery |
| **Transporte** | Uber, 99, gasolina, estacionamento, ônibus |
| **Saúde** | Farmácia, médico, exame, plano de saúde |
| **Moradia** | Aluguel, condomínio, IPTU, manutenção |
| **Serviços de utilidade pública** | Luz, água, gás, internet, telefone |
| **Pessoal** | Roupa, academia, salão, cinema, streaming |
| **Viagens** | Passagem, hotel, turismo |
| **Presentes** | Presente, aniversário, natal |
| **Animais de estimação** | Ração, veterinário, pet shop |
| **Débito** | Parcela, empréstimo, financiamento |
| **Outros** | Não classificados |

### Rendas

| Categoria | Exemplos |
|-----------|----------|
| **Pagamento** | Salário, freelance, serviço prestado |
| **Bônus** | 13º, PLR, comissão, gratificação |
| **Juros** | Rendimento investimento, dividendos |
| **Poupança** | Rendimento poupança, resgate |
| **Outros** | Não classificados |

---

## 💬 Exemplos de Uso

### Registrar Transações

```
"Gastei R$200 no mercado ontem"
"Recebi R$3500 de salário dia 05"
"Paguei R$150 de luz e R$80 de internet"
"Comprei um presente de R$100 para minha mãe"
```

### Fazer Perguntas

```
"Qual minha situação financeira?"
"Quais são meus gastos fixos?"
"Quanto vou gastar no próximo mês?"
"Onde posso economizar?"
"Quero juntar R$5000, como faço?"
"Compare meus gastos dos últimos 3 meses"
"Quais minhas maiores despesas?"
```

---

## 📚 API Reference

### google_sheets_connector.py

```python
# Registrar uma despesa
registrar_despesa(data: str, valor: float, descricao: str, categoria: str) -> bool

# Registrar uma renda
registrar_renda(data: str, valor: float, descricao: str, categoria: str) -> bool

# Registrar transação genérica
registrar_transacao(data: str, valor: float, descricao: str, categoria: str, tipo: str) -> bool
```

**Exemplo:**
```python
from google_sheets_connector import registrar_despesa, registrar_renda

# Adicionar despesa
registrar_despesa("05/06/2026", 150.00, "Supermercado", "Alimentação")

# Adicionar renda
registrar_renda("05/06/2026", 5000.00, "Salário", "Pagamento")
```

### agente_extracao.py

```python
# Extrair dados financeiros de texto
extrair_dados(mensagem_usuario: str) -> dict
```

**Retorno:**
```json
{
  "tipo_saida": "extracao_financeira",
  "transacoes": {
    "despesas": [
      {"Data": "05/06/2026", "Valor": 150.0, "Descricao": "Mercado", "Categoria": "Alimentação"}
    ],
    "rendas": []
  }
}
```

### agente_concelheiro.py

```python
# Analisar finanças e dar conselhos
analise_mensagem(mensagem_usuario: str, dados_planilha: dict = None) -> dict
```

**Retorno:**
```json
{
  "tipo_saida": "texto",
  "resposta_texto": "Análise completa...",
  "diagnostico": {...},
  "previsao": {...},
  "conselhos": [...]
}
```

---

## 🔒 Segurança

⚠️ **NUNCA** commite os seguintes arquivos:
- `.env` (contém chaves de API)
- `credentials.json` (credenciais do Google)

O `.gitignore` já está configurado para ignorá-los.

---

## 🐛 Troubleshooting

### Erro: "Não foi possível conectar à planilha"

1. Verifique se `credentials.json` existe
2. Confirme que é uma **Service Account** (não OAuth)
3. Verifique se a planilha foi compartilhada com o email da Service Account

### Erro: "Não foi possível resolver a importação"

Execute o script de dentro da pasta `scr`:
```bash
cd .venv\scr
python Main.py
```

### Erro de API do Azure OpenAI

1. Verifique as variáveis no `.env`
2. Confirme que o deployment `gpt-4o` existe no seu recurso
3. Verifique se a chave de API está correta

---

## 📄 Licença

Este projeto é para uso pessoal/educacional.

---

## 👤 Autor

Desenvolvido com ❤️ e IA
