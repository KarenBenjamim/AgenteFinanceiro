"""
Fluxo Principal do Agente Financeiro
=====================================
Sistema de gerenciamento financeiro pessoal com IA.

Fluxo:
1. Recebe mensagem do usuário
2. Orquestrador classifica: 'dados' ou 'assunto'
3. Direciona para agente apropriado
4. Se extração: valida dados e salva na planilha
5. Se conselho: lê planilha e gera análise

Autor: Sistema de IA
Versão: 1.0.0
"""

import sys
import os

# Adiciona o diretório atual ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from config import validar_config
from agente_orquestrador import classificar_mensagem
from agente_extracao import extrair_dados
from agente_conselheiro import analise_mensagem
from data_manager import (
    registrar_despesa, registrar_renda,
    CATEGORIAS_DESPESAS, CATEGORIAS_RENDAS
)

# ============================================================
# FUNÇÕES DE INTERFACE
# ============================================================

def exibir_boas_vindas():
    """Exibe mensagem de boas-vindas."""
    print("\n" + "=" * 60)
    print("💰 ASSISTENTE FINANCEIRO INTELIGENTE")
    print("=" * 60)
    print("""
Posso te ajudar a:
  📊 Registrar despesas e rendas
  📝 Classificar transações por categoria
  💡 Dar conselhos financeiros
  📈 Fazer previsões baseadas no seu histórico

Exemplos de comandos:
  • "Recebi 3500 de salário e gastei 200 no mercado"
  • "Gastei 120 com Uber ontem"
  • "Paguei R$150 de luz e R$80 de internet"
  • "Como posso economizar mais?"
  • "Qual minha situação financeira?"
  • "Quero juntar R$5000, me ajude"

Digite 'sair' para encerrar.
""")
    print("-" * 60)


def solicitar_dados_faltantes(transacao: dict, tipo: str) -> dict:
    """
    Solicita dados faltantes de uma transação ao usuário.
    
    Args:
        transacao: Dicionário com dados parciais
        tipo: "despesa" ou "renda"
        
    Returns:
        Transação completa com dados preenchidos
    """
    print(f"\n⚠️  Dados incompletos para {tipo}:")
    
    # Data
    data = transacao.get("Data", "")
    if not data:
        data_input = input("📅 Data (DD/MM/AAAA) [Enter = hoje]: ").strip()
        data = data_input if data_input else datetime.now().strftime("%d/%m/%Y")
    transacao["Data"] = data
    
    # Valor
    valor = transacao.get("Valor")
    if valor is None or valor == 0:
        while True:
            valor_input = input("💵 Valor (ex: 150.00): ").strip()
            valor_input = valor_input.replace(",", ".").replace("R$", "").strip()
            try:
                valor = float(valor_input)
                if valor > 0:
                    break
                print("   ❌ Valor deve ser maior que zero.")
            except:
                print("   ❌ Digite um número válido.")
    transacao["Valor"] = valor
    
    # Descrição
    descricao = transacao.get("Descricao", "")
    if not descricao:
        descricao = input("📝 Descrição: ").strip()
        if not descricao:
            descricao = "Transação sem descrição"
    transacao["Descricao"] = descricao
    
    # Categoria
    categoria = transacao.get("Categoria", "")
    categorias = CATEGORIAS_DESPESAS if tipo == "despesa" else CATEGORIAS_RENDAS
    
    if not categoria or categoria not in categorias:
        print(f"\n🏷️  Categorias disponíveis para {tipo}:")
        for i, cat in enumerate(categorias, 1):
            print(f"   {i}. {cat}")
        
        while True:
            cat_input = input("Escolha (número ou nome): ").strip()
            try:
                idx = int(cat_input) - 1
                if 0 <= idx < len(categorias):
                    categoria = categorias[idx]
                    break
            except ValueError:
                # Verifica se digitou o nome da categoria
                for cat in categorias:
                    if cat.lower() == cat_input.lower():
                        categoria = cat
                        break
                if categoria and categoria in categorias:
                    break
            print("   ❌ Opção inválida. Tente novamente.")
    
    transacao["Categoria"] = categoria
    return transacao


def validar_transacao(transacao: dict) -> bool:
    """Verifica se a transação tem todos os campos necessários."""
    data = transacao.get("Data", "")
    valor = transacao.get("Valor")
    descricao = transacao.get("Descricao", "")
    categoria = transacao.get("Categoria", "")
    
    return bool(data and valor and valor > 0 and descricao and categoria)


def processar_extracao(dados_extraidos: dict) -> dict:
    """
    Processa dados extraídos, solicitando informações faltantes.
    
    Args:
        dados_extraidos: Resultado do agente de extração
        
    Returns:
        Dicionário com estatísticas do processamento
    """
    transacoes = dados_extraidos.get("transacoes", {})
    despesas = transacoes.get("despesas", [])
    rendas = transacoes.get("rendas", [])
    
    resultado = {"despesas_ok": 0, "rendas_ok": 0, "erros": 0}
    
    # Processa despesas
    for i, despesa in enumerate(despesas):
        print(f"\n📊 Despesa {i+1}:")
        print(f"   Data: {despesa.get('Data', '❓')}")
        print(f"   Valor: {despesa.get('Valor', '❓')}")
        print(f"   Descrição: {despesa.get('Descricao', '❓')}")
        print(f"   Categoria: {despesa.get('Categoria', '❓')}")
        
        if not validar_transacao(despesa):
            despesa = solicitar_dados_faltantes(despesa, "despesa")
        
        # Salva na planilha
        if registrar_despesa(
            despesa["Data"],
            despesa["Valor"],
            despesa["Descricao"],
            despesa["Categoria"]
        ):
            resultado["despesas_ok"] += 1
        else:
            resultado["erros"] += 1
    
    # Processa rendas
    for i, renda in enumerate(rendas):
        print(f"\n💰 Renda {i+1}:")
        print(f"   Data: {renda.get('Data', '❓')}")
        print(f"   Valor: {renda.get('Valor', '❓')}")
        print(f"   Descrição: {renda.get('Descricao', '❓')}")
        print(f"   Categoria: {renda.get('Categoria', '❓')}")
        
        if not validar_transacao(renda):
            renda = solicitar_dados_faltantes(renda, "renda")
        
        # Salva na planilha
        if registrar_renda(
            renda["Data"],
            renda["Valor"],
            renda["Descricao"],
            renda["Categoria"]
        ):
            resultado["rendas_ok"] += 1
        else:
            resultado["erros"] += 1
    
    return resultado


def processar_analise(dados_analise: dict):
    """
    Exibe os resultados da análise/conselho financeiro.
    
    Args:
        dados_analise: Resultado do agente conselheiro
    """
    print("\n" + "=" * 50)
    print("💡 ANÁLISE FINANCEIRA")
    print("=" * 50)
    
    # Se for resposta em texto, exibe diretamente
    resposta_texto = dados_analise.get("resposta_texto", "")
    if resposta_texto:
        print(f"\n{resposta_texto}")
        return
    
    # Diagnóstico
    diagnostico = dados_analise.get("diagnostico", {})
    if diagnostico:
        print("\n📊 DIAGNÓSTICO:")
        if diagnostico.get("receita_total"):
            print(f"   Receita Total: R$ {diagnostico['receita_total']:,.2f}")
        if diagnostico.get("despesa_total"):
            print(f"   Despesa Total: R$ {diagnostico['despesa_total']:,.2f}")
        if diagnostico.get("saldo_atual"):
            print(f"   Saldo Atual: R$ {diagnostico['saldo_atual']:,.2f}")
        
        alertas = diagnostico.get("alertas", [])
        if alertas:
            print("\n   ⚠️  Alertas:")
            for alerta in alertas:
                print(f"      • {alerta}")
    
    # Previsão
    previsao = dados_analise.get("previsao", {})
    if previsao and previsao.get("proximo_mes_saldo_estimado"):
        print("\n📈 PREVISÃO PRÓXIMO MÊS:")
        if previsao.get("proximo_mes_receita_estimada"):
            print(f"   Receita Estimada: R$ {previsao['proximo_mes_receita_estimada']:,.2f}")
        if previsao.get("proximo_mes_despesa_estimada"):
            print(f"   Despesa Estimada: R$ {previsao['proximo_mes_despesa_estimada']:,.2f}")
        if previsao.get("proximo_mes_saldo_estimado"):
            print(f"   Saldo Estimado: R$ {previsao['proximo_mes_saldo_estimado']:,.2f}")
        print(f"   Confiança: {previsao.get('confianca_previsao', 'N/A')}")
    
    # Meta sugerida
    meta = dados_analise.get("meta_sugerida", {})
    if meta and meta.get("valor_mensal"):
        print("\n🎯 META SUGERIDA:")
        print(f"   Economizar: R$ {meta['valor_mensal']:,.2f}/mês")
        if meta.get("categoria_corte"):
            print(f"   Onde cortar: {meta['categoria_corte']}")
        if meta.get("tempo_para_meta"):
            print(f"   Tempo estimado: {meta['tempo_para_meta']}")
    
    # Conselhos
    conselhos = dados_analise.get("conselhos", [])
    if conselhos:
        print("\n💡 CONSELHOS:")
        for i, conselho in enumerate(conselhos, 1):
            titulo = conselho.get("titulo", "")
            descricao = conselho.get("descricao", "")
            prioridade = conselho.get("prioridade", "")
            print(f"\n   {i}. {titulo} [{prioridade.upper()}]")
            print(f"      {descricao}")
    
    # Observações
    observacoes = dados_analise.get("observacoes", [])
    if observacoes:
        print("\n📝 OBSERVAÇÕES:")
        for obs in observacoes:
            print(f"   • {obs}")
    
    # Perguntas faltantes
    perguntas = dados_analise.get("perguntas_faltantes", [])
    if perguntas:
        print("\n❓ Para uma análise mais completa, preciso saber:")
        for p in perguntas:
            print(f"   • {p}")


def fluxo_principal():
    """
    Executa o fluxo principal do assistente financeiro.
    
    Fluxo:
    1. Valida configurações
    2. Exibe boas-vindas
    3. Loop de interação com usuário
    4. Classifica mensagem (orquestrador)
    5. Direciona para agente correto
    """
    # Valida configurações antes de iniciar
    config_valida, erros = validar_config()
    if not config_valida:
        print("\n❌ Configure as variáveis de ambiente antes de continuar.")
        print("   Edite o arquivo .env com suas credenciais.")
        return
    
    exibir_boas_vindas()
    
    while True:
        # Recebe entrada do usuário
        try:
            mensagem = input("\n💬 Você: ").strip()
        except KeyboardInterrupt:
            print("\n\n👋 Até logo! Cuide bem das suas finanças! 💰")
            break
        except EOFError:
            break
        
        if mensagem.lower() in ['sair', 'exit', 'quit']:
            print("\n👋 Até logo! Cuide bem das suas finanças! 💰")
            break
        
        if not mensagem:
            continue
        
        # =============================================
        # PASSO 1: ORQUESTRADOR CLASSIFICA A MENSAGEM
        # =============================================
        print("\n🔄 Analisando sua mensagem...")
        classificacao = classificar_mensagem(mensagem)
        rota = classificacao.get("rota", "assunto")
        justificativa = classificacao.get("justificativa_curta", "")
        
        print(f"   Classificado como: {rota.upper()}")
        if justificativa:
            print(f"   Motivo: {justificativa}")
        
        # =============================================
        # PASSO 2: DIRECIONA PARA O AGENTE CORRETO
        # =============================================
        
        if rota == "dados":
            # -----------------------------------------
            # AGENTE DE EXTRAÇÃO
            # -----------------------------------------
            print("\n📊 Extraindo dados financeiros...")
            dados_extraidos = extrair_dados(mensagem)
            
            transacoes = dados_extraidos.get("transacoes", {})
            total_despesas = len(transacoes.get("despesas", []))
            total_rendas = len(transacoes.get("rendas", []))
            
            if total_despesas == 0 and total_rendas == 0:
                print("\n⚠️  Não consegui identificar transações claras.")
                print("Por favor, forneça os dados no formato:")
                print("   • Data, Valor, Descrição e Categoria")
                print("\nExemplo:")
                print('   "Gastei R$150 no mercado ontem, categoria Alimentação"')
                continue
            
            print(f"\n✅ Encontrado: {total_despesas} despesa(s) e {total_rendas} renda(s)")
            
            # Processa e valida cada transação
            resultado = processar_extracao(dados_extraidos)
            
            # Exibe resumo
            print("\n" + "-" * 40)
            print("📊 RESUMO DO REGISTRO:")
            print(f"   ✅ Despesas salvas: {resultado['despesas_ok']}")
            print(f"   ✅ Rendas salvas: {resultado['rendas_ok']}")
            if resultado['erros'] > 0:
                print(f"   ❌ Erros: {resultado['erros']}")
            
            # Observações do agente
            observacoes = dados_extraidos.get("observacoes", [])
            if observacoes:
                print("\n📝 Observações:")
                for obs in observacoes:
                    print(f"   • {obs}")
        
        else:
            # -----------------------------------------
            # AGENTE DE ANÁLISE/CONSELHO
            # -----------------------------------------
            print("\n💡 Analisando sua situação financeira...")
            dados_analise = analise_mensagem(mensagem)
            
            if dados_analise.get("tipo_saida") == "erro":
                print("\n❌ Ocorreu um erro na análise. Tente novamente.")
                continue
            
            processar_analise(dados_analise)
        
        print("\n" + "-" * 60)


if __name__ == '__main__':
    fluxo_principal()
