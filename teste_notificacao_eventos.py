#!/usr/bin/env python3
"""
Script de teste para o sistema de notificações de eventos.

Este script permite testar:
1. O envio de notificações quando um evento é criado
2. O envio de lembretes de eventos
3. A listagem de técnicos com função EVENTOS
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
from app.alarmes.ClassesSistema import FuncoesTecnicos

def testar_listagem_tecnicos():
    """Testa a listagem de técnicos com função EVENTOS"""
    print("=" * 60)
    print("TESTE: Listagem de técnicos com função EVENTOS")
    print("=" * 60)
    
    gerenciador = GerenciadorNotificacaoEventos.get_instance()
    tecnicos_eventos = gerenciador.obter_tecnicos_eventos()
    
    if not tecnicos_eventos:
        print("❌ Nenhum técnico com função EVENTOS encontrado!")
        return False
    
    print(f"✅ Encontrados {len(tecnicos_eventos)} técnicos com função EVENTOS:")
    for i, tecnico in enumerate(tecnicos_eventos, 1):
        print(f"  {i}. {tecnico.nome}")
        print(f"     📞 {tecnico.telefone}")
        print(f"     ✉️  {tecnico.email}")
        print(f"     🕒 Jornada: {tecnico.jornada}")
        print(f"     📲 Método preferencial: {tecnico.metodo_contato_preferencial.name}")
        print()
    
    return True

def criar_evento_teste():
    """Cria um evento de teste para as notificações"""
    amanha = datetime.now() + timedelta(days=1)
    
    evento_teste = {
        'id': f"teste_{int(datetime.now().timestamp())}",
        'nome': 'Reunião de Teste - Sistema de Notificações',
        'descricao': 'Evento criado para testar o sistema de notificações automáticas.',
        'local': 'Auditório Nobre',
        'dia': amanha.day,
        'mes': amanha.month,
        'ano': amanha.year,
        'hora_inicio': '14:00',
        'hora_fim': '16:00',
        'responsavel': 'Sistema de Testes',
        'participantes_estimados': 50,
        'criado_em': datetime.now().isoformat(),
        'atualizado_em': datetime.now().isoformat()
    }
    
    return evento_teste

def testar_notificacao_evento_criado():
    """Testa o envio de notificação quando um evento é criado"""
    print("=" * 60)
    print("TESTE: Notificação de evento criado")
    print("=" * 60)
    
    evento_teste = criar_evento_teste()
    
    print(f"📅 Evento de teste:")
    print(f"   Nome: {evento_teste['nome']}")
    print(f"   Data: {evento_teste['dia']:02d}/{evento_teste['mes']:02d}/{evento_teste['ano']}")
    print(f"   Horário: {evento_teste['hora_inicio']} às {evento_teste['hora_fim']}")
    print(f"   Local: {evento_teste['local']}")
    print()
    
    gerenciador = GerenciadorNotificacaoEventos.get_instance()
    sucesso = gerenciador.notificar_evento_criado(evento_teste)
    
    if sucesso:
        print("✅ Notificação de evento criado enviada com sucesso!")
    else:
        print("❌ Falha ao enviar notificação de evento criado!")
    
    return sucesso

def testar_lembrete_evento():
    """Testa o envio de lembrete de evento"""
    print("=" * 60)
    print("TESTE: Lembrete de evento")
    print("=" * 60)
    
    evento_teste = criar_evento_teste()
    
    print(f"📅 Evento de teste para lembrete:")
    print(f"   Nome: {evento_teste['nome']}")
    print(f"   Data: {evento_teste['dia']:02d}/{evento_teste['mes']:02d}/{evento_teste['ano']}")
    print(f"   Horário: {evento_teste['hora_inicio']} às {evento_teste['hora_fim']}")
    print(f"   Local: {evento_teste['local']}")
    print()
    
    gerenciador = GerenciadorNotificacaoEventos.get_instance()
    
    # Simula o envio de lembrete (normalmente seria às 8h do dia anterior)
    print("⚠️  ATENÇÃO: Este teste simula o envio de lembrete independente do horário atual.")
    print("   Em produção, lembretes são enviados apenas às 8h00 do dia anterior ao evento.")
    print()
    
    try:
        if gerenciador.notificacao_eventos:
            gerenciador.notificacao_eventos.notificar_lembrete_evento(evento_teste)
            print("✅ Lembrete de evento enviado com sucesso!")
            return True
        else:
            print("❌ Sistema de notificação não está inicializado!")
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar lembrete: {e}")
        return False

def testar_verificacao_manual_lembretes():
    """Testa a verificação manual de lembretes para amanhã"""
    print("=" * 60)
    print("TESTE: Verificação manual de lembretes")
    print("=" * 60)
    
    print("🔍 Verificando eventos para amanhã...")
    
    gerenciador = GerenciadorNotificacaoEventos.get_instance()
    
    try:
        gerenciador.verificar_lembretes_manualmente()
        print("✅ Verificação manual de lembretes executada!")
        print("   (Se houver eventos para amanhã, os lembretes foram enviados)")
        return True
    except Exception as e:
        print(f"❌ Erro na verificação manual: {e}")
        return False

def main():
    """Função principal do script de teste"""
    print("🧪 SISTEMA DE TESTE - NOTIFICAÇÕES DE EVENTOS")
    print("=" * 60)
    print("Este script testará o sistema de notificações de eventos.")
    print("As notificações serão enviadas apenas para técnicos com função EVENTOS.")
    print()
    
    # Lista os testes disponíveis
    testes = [
        ("1", "Listar técnicos com função EVENTOS", testar_listagem_tecnicos),
        ("2", "Testar notificação de evento criado", testar_notificacao_evento_criado),
        ("3", "Testar lembrete de evento", testar_lembrete_evento),
        ("4", "Verificar lembretes para amanhã", testar_verificacao_manual_lembretes),
        ("5", "Executar todos os testes", None)
    ]
    
    while True:
        print("\n📋 TESTES DISPONÍVEIS:")
        for opcao, descricao, _ in testes:
            print(f"   {opcao}. {descricao}")
        print("   0. Sair")
        
        escolha = input("\n🔢 Escolha uma opção: ").strip()
        
        if escolha == "0":
            print("\n👋 Saindo do sistema de testes...")
            break
        elif escolha == "5":
            print("\n🚀 Executando todos os testes...")
            for opcao, descricao, funcao in testes[:-1]:  # Exclui a opção "todos"
                if funcao:
                    print(f"\n▶️  Executando: {descricao}")
                    funcao()
                    input("\n⏸️  Pressione Enter para continuar...")
        else:
            # Procura o teste específico
            teste_encontrado = False
            for opcao, descricao, funcao in testes:
                if escolha == opcao and funcao:
                    print(f"\n▶️  Executando: {descricao}")
                    funcao()
                    teste_encontrado = True
                    break
            
            if not teste_encontrado:
                print("\n❌ Opção inválida! Tente novamente.")
            else:
                input("\n⏸️  Pressione Enter para continuar...")

if __name__ == "__main__":
    main()
