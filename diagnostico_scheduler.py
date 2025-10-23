#!/usr/bin/env python3
"""
Script de diagnóstico do sistema de notificações de eventos
Verifica se o scheduler está rodando corretamente
"""

import sys
import time
from datetime import datetime

def diagnosticar_scheduler():
    """Verifica o estado do scheduler de notificações"""
    print("=" * 70)
    print("DIAGNÓSTICO DO SCHEDULER DE NOTIFICAÇÕES DE EVENTOS")
    print("=" * 70)
    print()
    
    try:
        from app.utils.GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
        
        # Obtém a instância do gerenciador
        gerenciador = GerenciadorNotificacaoEventos.get_instance()
        
        # Verificar se está rodando
        print(f"✓ Instância do gerenciador criada com sucesso")
        print(f"  - Scheduler rodando: {'SIM ✓' if gerenciador.running else 'NÃO ✗'}")
        print(f"  - Thread ativa: {'SIM ✓' if gerenciador.scheduler_thread and gerenciador.scheduler_thread.is_alive() else 'NÃO ✗'}")
        print(f"  - Sistema de notificação: {'OK ✓' if gerenciador.notificacao_eventos else 'FALHOU ✗'}")
        print()
        
        if not gerenciador.running:
            print("⚠️  PROBLEMA DETECTADO: Scheduler NÃO está rodando!")
            print()
            print("Possíveis causas:")
            print("  1. iniciar_scheduler_lembretes() nunca foi chamado")
            print("  2. Aplicação rodando em produção (uWSGI/Gunicorn) sem inicialização adequada")
            print("  3. Thread foi encerrada por erro")
            print()
            
            resposta = input("Deseja tentar iniciar o scheduler agora? (s/n): ")
            if resposta.lower() == 's':
                print()
                print("Iniciando scheduler...")
                gerenciador.iniciar_scheduler_lembretes()
                time.sleep(2)
                
                if gerenciador.running and gerenciador.scheduler_thread.is_alive():
                    print("✓ Scheduler iniciado com sucesso!")
                else:
                    print("✗ Falha ao iniciar scheduler")
        else:
            print("✓ Scheduler está RODANDO corretamente!")
            print()
            
            # Verificar schedule jobs
            import schedule
            jobs = schedule.get_jobs()
            print(f"Jobs agendados: {len(jobs)}")
            for i, job in enumerate(jobs, 1):
                print(f"  {i}. {job}")
            print()
            
        # Verificar eventos de amanhã
        print("-" * 70)
        print("VERIFICAÇÃO DE EVENTOS DE AMANHÃ")
        print("-" * 70)
        
        from datetime import timedelta
        from app.utils.GerenciadorEventos import GerenciadorEventos
        
        amanha = datetime.now() + timedelta(days=1)
        ger_eventos = GerenciadorEventos.get_instance()
        eventos_amanha = ger_eventos.obter_eventos_por_data(
            dia=amanha.day,
            mes=amanha.month,
            ano=amanha.year
        )
        
        print(f"Data de amanhã: {amanha.strftime('%d/%m/%Y')}")
        print(f"Eventos encontrados: {len(eventos_amanha)}")
        
        if eventos_amanha:
            print()
            for evento in eventos_amanha:
                print(f"  • {evento['nome']}")
                print(f"    Local: {evento['local']}")
                print(f"    Horário: {evento['hora_inicio']} - {evento['hora_fim']}")
                print()
        else:
            print("  (Nenhum evento agendado para amanhã)")
        
        print()
        print("-" * 70)
        print("TESTE DE VERIFICAÇÃO MANUAL")
        print("-" * 70)
        
        resposta = input("Deseja executar verificação manual de lembretes? (s/n): ")
        if resposta.lower() == 's':
            print()
            print("Executando verificação manual...")
            gerenciador.verificar_lembretes_manualmente()
            print("✓ Verificação concluída. Verifique os logs para mais detalhes.")
        
        print()
        print("=" * 70)
        print("DIAGNÓSTICO CONCLUÍDO")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"✗ ERRO ao executar diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    diagnosticar_scheduler()
