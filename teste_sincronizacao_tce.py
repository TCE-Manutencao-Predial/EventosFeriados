# teste_sincronizacao_tce.py
"""
Script de teste para verificar a funcionalidade de sincronização do TCE
"""
import sys
import os

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def testar_sincronizacao_tce():
    """Testa a sincronização básica do TCE"""
    print("=== Teste de Sincronização TCE ===\n")
    
    try:
        # Importar as classes necessárias
        from app.utils.SincronizadorTCE import SincronizadorTCE
        from app.utils.GerenciadorEventos import GerenciadorEventos
        
        print("1. Inicializando sincronizador TCE...")
        sincronizador = SincronizadorTCE.get_instance()
        print("   ✓ Sincronizador TCE inicializado")
        
        print("\n2. Testando obtenção de dados JSON para agosto/2025...")
        dados_json = sincronizador._obter_dados_json_tce(8, 2025)
        
        if dados_json:
            print("   ✓ Dados JSON obtidos com sucesso")
            print(f"   📊 Número de eventos: {len(dados_json)}")
            
            # Mostrar uma amostra dos dados
            if len(dados_json) > 0:
                print(f"   📄 Amostra dos dados: {dados_json[0]}")
        else:
            print("   ❌ Falha ao obter dados JSON")
            return False
        
        print("\n3. Testando processamento dos eventos...")
        eventos = sincronizador._processar_eventos_json(dados_json)
        print(f"   ✓ Processamento concluído - {len(eventos)} dias com eventos do Tribunal Pleno vespertinos encontrados")
        
        # Mostrar eventos encontrados
        if eventos:
            print("\n   📋 Eventos encontrados (consolidados por dia):")
            for i, evento in enumerate(eventos, 1):
                if evento['quantidade_eventos'] > 1:
                    print(f"      {i}. Dia {evento['dia']} - {evento['titulo']}")
                    print(f"         → {evento['quantidade_eventos']} sessões: {evento['hora_original']}")
                    for j, detalhe in enumerate(evento['eventos_detalhados'], 1):
                        print(f"         {j}. {detalhe}")
                else:
                    print(f"      {i}. Dia {evento['dia']} - {evento['titulo']} (Horário original: {evento['hora_original']})")
        
        print("\n4. Testando sincronização completa para agosto/2025...")
        resultado = sincronizador.sincronizar_mes(8, 2025)
        
        if resultado['sucesso']:
            print(f"   ✓ Sincronização concluída com sucesso!")
            print(f"   📊 Eventos criados: {resultado['eventos_criados']}")
        else:
            print(f"   ❌ Falha na sincronização: {resultado.get('erro', 'Erro desconhecido')}")
            return False
        
        print("\n5. Verificando eventos criados no sistema...")
        gerenciador_eventos = GerenciadorEventos.get_instance()
        eventos_agosto = gerenciador_eventos.listar_eventos(ano=2025, mes=8, local='Plenário')
        eventos_tce = [e for e in eventos_agosto if e.get('fonte_tce', False)]
        
        print(f"   ✓ Eventos do TCE no sistema: {len(eventos_tce)}")
        
        if eventos_tce:
            print("\n   📋 Eventos do TCE no sistema:")
            for evento in eventos_tce:
                print(f"      • {evento['dia']}/08/2025 - {evento['nome']}")
                print(f"        Horário: {evento['hora_inicio']} às {evento['hora_fim']}")
                print(f"        Horário original TCE: {evento.get('hora_original_tce', 'N/A')}")
                print(f"        Quantidade de sessões: {evento.get('quantidade_eventos_tce', 1)}")
                if evento.get('quantidade_eventos_tce', 1) > 1:
                    print(f"        Sessões detalhadas:")
                    for i, detalhe in enumerate(evento.get('eventos_detalhados_tce', []), 1):
                        print(f"          {i}. {detalhe}")
                print(f"        ID: {evento['id']}")
                print()
        
        print("\n6. Testando sincronização do período atual...")
        resultado_periodo = sincronizador.sincronizar_periodo_atual()
        
        if resultado_periodo['sucesso']:
            print(f"   ✓ Sincronização do período atual concluída!")
            print(f"   📊 Total de eventos processados: {resultado_periodo['total_eventos_criados']}")
            
            for sync in resultado_periodo['sincronizacoes']:
                print(f"      - {sync['mes']:02d}/{sync['ano']}: {sync['eventos_criados']} eventos")
        else:
            print(f"   ❌ Falha na sincronização do período: {resultado_periodo.get('erro', 'Erro desconhecido')}")
        
        print("\n=== Teste Concluído com Sucesso! ===")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("   Certifique-se de que todas as dependências estão instaladas")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def testar_agendador():
    """Testa o agendador com sincronização TCE"""
    print("\n=== Teste do Agendador com TCE ===\n")
    
    try:
        from app.utils.AgendadorCLP import AgendadorCLP
        from app.utils.GerenciadorEventos import GerenciadorEventos
        from app.utils.GerenciadorFeriados import GerenciadorFeriados
        
        print("1. Inicializando agendador...")
        agendador = AgendadorCLP.get_instance()
        
        # Inicializar gerenciadores
        gerenciador_feriados = GerenciadorFeriados.get_instance()
        gerenciador_eventos = GerenciadorEventos.get_instance()
        agendador.inicializar_gerenciadores(gerenciador_feriados, gerenciador_eventos)
        print("   ✓ Agendador inicializado")
        
        print("\n2. Verificando status do agendador...")
        status = agendador.status()
        print(f"   📊 Status:")
        print(f"      - Executando: {status['executando']}")
        print(f"      - TCE habilitado: {status['status_tce']['SYNC_ENABLED']}")
        print(f"      - Horário TCE: {status['status_tce']['SYNC_TIME']}")
        print(f"      - Próximo horário TCE: {status['proximo_horario_tce']}")
        
        print("\n3. Testando configuração do TCE...")
        agendador.configurar_tce(True, '08:00')
        print("   ✓ Configuração TCE atualizada")
        
        print("\n4. Testando sincronização manual do TCE...")
        resultado = agendador.sincronizar_tce_manual()
        
        if resultado['sucesso']:
            print(f"   ✓ Sincronização manual concluída!")
            print(f"   📊 Total de eventos processados: {resultado['total_eventos_criados']}")
        else:
            print(f"   ❌ Falha na sincronização manual: {resultado.get('erro', 'Erro desconhecido')}")
        
        print("\n=== Teste do Agendador Concluído! ===")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste do agendador: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando testes da sincronização TCE...\n")
    
    # Teste 1: Sincronização básica
    sucesso1 = testar_sincronizacao_tce()
    
    # Teste 2: Agendador
    if sucesso1:
        sucesso2 = testar_agendador()
    else:
        sucesso2 = False
    
    print(f"\n{'='*50}")
    print("RESULTADO FINAL:")
    print(f"  - Teste de Sincronização: {'✓ PASSOU' if sucesso1 else '❌ FALHOU'}")
    print(f"  - Teste de Agendador: {'✓ PASSOU' if sucesso2 else '❌ FALHOU'}")
    print(f"{'='*50}")
    
    if sucesso1 and sucesso2:
        print("\n🎉 Todos os testes passaram! A funcionalidade está pronta para uso.")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)
