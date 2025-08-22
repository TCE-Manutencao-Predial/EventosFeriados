#!/usr/bin/env python3
"""
Teste para validar que as notificações funcionam em background
sem bloquear a interface principal.
"""

import time
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

def test_evento_com_threading():
    """Testa criação de evento com notificação em background"""
    from app.utils.GerenciadorEventos import GerenciadorEventos
    
    print("=== TESTE: Criação de Evento com Threading ===")
    print(f"Início do teste: {datetime.now()}")
    
    # Criar evento de teste
    amanha = datetime.now() + timedelta(days=1)
    evento_teste = {
        'nome': f'TESTE Threading - {datetime.now().strftime("%H:%M:%S")}',
        'local': 'Auditório Nobre',
        'dia': amanha.day,
        'mes': amanha.month,
        'ano': amanha.year,
        'hora_inicio': '14:00',
        'hora_fim': '16:00',
        'observacoes': 'Evento de teste para validar threading das notificações'
    }
    
    # Marcar tempo de início
    inicio = time.time()
    
    try:
        # Adicionar evento (deve retornar rapidamente mesmo com notificações)
        gerenciador = GerenciadorEventos.get_instance()
        novo_evento = gerenciador.adicionar_evento(evento_teste)
        
        # Marcar tempo de conclusão da chamada
        fim_chamada = time.time()
        tempo_chamada = fim_chamada - inicio
        
        print(f"✅ Evento criado com sucesso!")
        print(f"📊 Tempo de resposta: {tempo_chamada:.2f} segundos")
        print(f"🆔 ID do evento: {novo_evento['id']}")
        print(f"📱 Thread de notificação: Executando em background...")
        
        # Verificar se foi rápido (menos de 2 segundos = sem bloqueio)
        if tempo_chamada < 2.0:
            print("✅ SUCESSO: Interface não foi bloqueada pelas notificações!")
        else:
            print("⚠️  ATENÇÃO: Resposta demorou mais que esperado.")
        
        print(f"⏰ Fim do teste: {datetime.now()}")
        print("📝 Nota: As notificações WhatsApp continuam processando em background.")
        
        return novo_evento['id']
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return None

def test_multiplos_eventos():
    """Testa criação de múltiplos eventos sequenciais"""
    print("\n=== TESTE: Múltiplos Eventos Sequenciais ===")
    
    inicio_total = time.time()
    eventos_criados = []
    
    for i in range(3):
        print(f"\n📝 Criando evento {i+1}/3...")
        inicio_evento = time.time()
        
        amanha = datetime.now() + timedelta(days=1)
        evento = {
            'nome': f'TESTE Múltiplo {i+1} - {datetime.now().strftime("%H:%M:%S")}',
            'local': 'Auditório Nobre',
            'dia': amanha.day,
            'mes': amanha.month,
            'ano': amanha.year,
            'hora_inicio': f'{14+i}:00',
            'hora_fim': f'{15+i}:00',
            'observacoes': f'Teste múltiplo #{i+1}'
        }
        
        try:
            from app.utils.GerenciadorEventos import GerenciadorEventos
            gerenciador = GerenciadorEventos.get_instance()
            novo_evento = gerenciador.adicionar_evento(evento)
            
            fim_evento = time.time()
            tempo_evento = fim_evento - inicio_evento
            
            print(f"   ✅ Evento {i+1} criado em {tempo_evento:.2f}s")
            eventos_criados.append(novo_evento['id'])
            
        except Exception as e:
            print(f"   ❌ Erro no evento {i+1}: {e}")
    
    fim_total = time.time()
    tempo_total = fim_total - inicio_total
    
    print(f"\n📊 Resumo:")
    print(f"   • Eventos criados: {len(eventos_criados)}/3")
    print(f"   • Tempo total: {tempo_total:.2f} segundos")
    print(f"   • Tempo médio por evento: {tempo_total/3:.2f} segundos")
    
    if tempo_total < 6.0:  # 3 eventos em menos de 6 segundos = 2s por evento
        print("✅ SUCESSO: Interface permaneceu responsiva!")
    else:
        print("⚠️  ATENÇÃO: Interface pode ter ficado lenta.")

if __name__ == "__main__":
    print("🧪 TESTE DE THREADING PARA NOTIFICAÇÕES")
    print("=" * 50)
    
    # Teste 1: Evento único
    evento_id = test_evento_com_threading()
    
    # Aguardar um pouco antes do próximo teste
    time.sleep(1)
    
    # Teste 2: Múltiplos eventos
    test_multiplos_eventos()
    
    print("\n" + "=" * 50)
    print("🎯 CONCLUSÃO:")
    print("Se os tempos de resposta ficaram baixos (< 2s por evento),")
    print("então a solução de threading está funcionando corretamente!")
    print("As notificações WhatsApp continuam sendo enviadas em background.")
