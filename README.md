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
- ✅ **Extrair transações de PDFs e imagens** (extratos bancários, prints)
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
│                    ou arquivo PDF/imagem                    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│    AGENTE LEITOR        │     │    AGENTE ORQUESTRADOR      │
│                         │     │                             │
│  • Processa PDF/Imagem  │     │  Classifica: "dados"        │
│  • Extrai via Vision    │     │         ou "assunto"        │
│  • GPT-4o para OCR      │     │                             │
│  • Valida duplicatas    │     │  • dados → transações       │
│                         │     │  • assunto → conselhos      │
└─────────────────────────┘     └─────────────────────────────┘
              │                               │
              │               ┌───────────────┴───────────────┐
              │               │                               │
              │               ▼                               ▼
              │     ┌─────────────────────────┐     ┌─────────────────────────┐
              │     │   AGENTE DE EXTRAÇÃO    │     │    AGENTE CONSELHEIRO   │
              │     │                         │     │                         │
              │     │  • Extrai Data          │     │  • Lê dados da planilha │
              │     │  • Extrai Valor         │     │  • Analisa histórico    │
              │     │  • Extrai Descrição     │     │  • Identifica padrões   │
              │     │  • Classifica Categoria │     │  • Faz previsões        │
              │     │                         │     │  • Sugere economia      │
              │     └─────────────────────────┘     └─────────────────────────┘
              │               │                               │
              └───────────────┼───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA MANAGER                             │
│         Gerencia múltiplos destinos de dados                │
│                                                              │
│  ┌────────────────────┐    ┌────────────────────┐          │
│  │   GOOGLE SHEETS    │    │    SQL SERVER      │          │
│  │                    │    │    (opcional)      │          │
│  │  ┌──────────────┐  │    │                    │          │
│  │  │  DESPESAS    │  │    │  ┌──────────────┐  │          │
│  │  │  B5: Data    │  │    │  │  Despesas    │  │          │
│  │  │  C5: Valor   │  │    │  │  Rendas      │  │          │
│  │  │  D5: Desc    │  │    │  └──────────────┘  │          │
│  │  │  E5: Cat     │  │    │                    │          │
│  │  └──────────────┘  │    │                    │          │
│  │  ┌──────────────┐  │    │                    │          │
│  │  │   RENDAS     │  │    │                    │          │
│  │  │  G5: Data    │  │    │                    │          │
│  │  │  H5: Valor   │  │    │                    │          │
│  │  │  I5: Desc    │  │    │                    │          │
│  │  │  J5: Cat     │  │    │                    │          │
│  │  └──────────────┘  │    │                    │          │
│  └────────────────────┘    └────────────────────┘          │
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
streamlit>=1.28.0
pdfplumber>=0.10.0
Pillow>=10.0.0
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
cd src
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
7. Salve como `credentials.json` na pasta `src/`
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

### Interface Web (Recomendado)

```bash
cd src
streamlit run app.py
```

A interface abrirá automaticamente no navegador em `http://localhost:8501`

**Funcionalidades da Interface:**
- 🏠 **Início** - Resumo rápido das suas finanças
- 💬 **Chat** - Converse com a IA em linguagem natural
- ➕ **Nova Transação** - Formulário para adicionar despesas/rendas
- 📊 **Dashboard** - Gráficos e análises visuais
- 📋 **Histórico** - Lista completa de transações

### Terminal (Alternativo)

```bash
cd src
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
├── src/
│   ├── .env                    # Variáveis de ambiente (NÃO COMMITAR!)
│   ├── .env.example            # Template das variáveis
│   ├── config.py               # Carrega configurações do .env
│   ├── credentials.json        # Credenciais Google (NÃO COMMITAR!)
│   ├── Main.py                 # Fluxo principal do assistente
│   ├── app.py                  # Interface web Streamlit
│   ├── agente_orquestrador.py  # Classifica mensagens
│   ├── agente_extracao.py      # Extrai dados financeiros de texto
│   ├── agente_leitor.py        # Extrai transações de PDFs e imagens
│   ├── agente_conselheiro.py   # Análise e conselhos
│   ├── data_manager.py         # Gerenciador central de dados
│   ├── google_sheets_connector.py  # Integração com Google Sheets
│   ├── sql_server_connector.py # Integração com SQL Server (opcional)
│   ├── utils.py                # Funções utilitárias compartilhadas
│   └── logs/                   # Logs de administração
├── .gitignore
├── requirements.txt
└── README.md
```

### Descrição dos Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `Main.py` | Ponto de entrada. Orquestra o fluxo entre agentes |
| `app.py` | Interface web interativa com Streamlit |
| `agente_orquestrador.py` | Classifica input como "dados" ou "assunto" |
| `agente_extracao.py` | Extrai Data, Valor, Descrição, Categoria do texto |
| `agente_leitor.py` | Extrai transações de PDFs e imagens usando GPT-4o Vision |
| `agente_conselheiro.py` | Lê planilha e dá conselhos baseados no histórico |
| `data_manager.py` | Gerencia salvamento em múltiplos destinos (Sheets/SQL) |
| `google_sheets_connector.py` | CRUD na planilha Google Sheets |
| `sql_server_connector.py` | CRUD no banco SQL Server (opcional) |
| `utils.py` | Funções utilitárias (normalização de datas, formatação) |
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

### Extrair de Arquivos

O sistema suporta extração automática de transações de:
- **PDF**: Extratos bancários, faturas, comprovantes
- **Imagens**: PNG, JPG, JPEG, GIF, WEBP (prints de extratos, comprovantes)

```bash
# Via terminal
cd src
python agente_leitor.py

# Exemplo de uso
📂 Caminho do arquivo: C:\Users\fulano\Downloads\extrato.pdf
📄 Processando PDF...
✅ Encontradas 15 transações
📝 Registrando na planilha...
   Adicionadas: 12
   Duplicatas: 3
   Erros: 0
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

### agente_conselheiro.py

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

### agente_leitor.py

```python
# Processar arquivo e registrar transações encontradas
processar_e_registrar(arquivo: Union[str, bytes], nome_arquivo: str = "") -> dict

# Processar arquivo e extrair transações (sem registrar)
processar_arquivo(arquivo: Union[str, bytes], nome_arquivo: str = "") -> dict

# Extrair texto de um PDF
extrair_texto_pdf(arquivo_pdf: Union[str, bytes, BytesIO]) -> Optional[str]

# Extrair transações de uma imagem usando GPT-4o Vision
extrair_transacoes_de_imagem(imagem: Union[str, bytes, Image]) -> dict
```

**Exemplo:**
```python
from agente_leitor import processar_e_registrar

# Processar PDF de extrato bancário
resultado = processar_e_registrar("extrato_maio.pdf")
print(f"Extraídas: {resultado['extraidas']}")
print(f"Registradas: {resultado['registradas']}")
print(f"Duplicatas: {resultado['duplicatas']}")

# Processar print de extrato
resultado = processar_e_registrar("print_extrato.png")
```

**Retorno:**
```json
{
  "extraidas": 15,
  "registradas": 12,
  "duplicatas": 3,
  "erros": 0,
  "observacoes": [],
  "detalhes": [
    {"transacao": {...}, "status": "adicionada", "mensagem": "OK"},
    {"transacao": {...}, "status": "duplicata", "mensagem": "Já existe"}
  ]
}
```

### data_manager.py

```python
# Registrar despesa sem duplicar
registrar_despesa_sem_duplicar(data: str, valor: float, descricao: str, categoria: str) -> dict

# Registrar renda sem duplicar
registrar_renda_sem_duplicar(data: str, valor: float, descricao: str, categoria: str) -> dict
```

**Retorno:**
```json
{
  "sucesso": true,
  "duplicata": false,
  "mensagem": "Despesa registrada com sucesso"
}
```

### utils.py

```python
# Normalizar data (adiciona ano atual se não tiver)
normalizar_data(data: str) -> str

# Formatar valor como moeda brasileira
formatar_moeda(valor: float) -> str

# Converter string de valor para float
processar_valor(valor_str: str) -> float
```

**Exemplo:**
```python
from utils import normalizar_data, formatar_moeda

normalizar_data("05/06")        # "05/06/2026"
normalizar_data("05/06/24")     # "05/06/2024"
formatar_moeda(1500.50)         # "R$ 1.500,50"
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

Execute o script de dentro da pasta `src`:
```bash
cd src
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
