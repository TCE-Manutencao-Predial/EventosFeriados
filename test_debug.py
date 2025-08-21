#!/usr/bin/env python3
"""
Script de debug para testar as APIs dos CLPs
"""
import sys
import json
import logging
from datetime import datetime

# Adicionar o diretório da aplicação ao path
sys.path.append('.')

from app.utils.SincronizadorCLP import SincronizadorCLP
from app.utils.SincronizadorCLPAuditorio import SincronizadorCLPAuditorio

# Configurar logging
logging.basicConfig(level=logging.INFO)

def teste_clp_terreo():
    """Testa o CLP Térreo B1"""
    print("=" * 60)
    print("TESTE CLP TÉRREO B1 (172.17.85.104)")
    print("=" * 60)
    
    try:
        # Obter instância do sincronizador
        sync = SincronizadorCLP.get_instance()
        print(f"✓ Instância do SincronizadorCLP obtida: {sync}")
        
        # Teste 1: Verificar conectividade
        print("\n1. Testando conectividade...")
        conectado, mensagem = sync.verificar_conectividade_clp()
        print(f"   Conectado: {conectado}")
        print(f"   Mensagem: {mensagem}")
        
        # Teste 2: Obter status de sincronização
        print("\n2. Obtendo status de sincronização...")
        status = sync.obter_status_sincronizacao()
        print(f"   Status completo:")
        for chave, valor in status.items():
            print(f"     {chave}: {valor}")
        
        # Teste 3: Verificar configuração
        print("\n3. Verificando configuração...")
        print(f"   API_BASE_URL: {sync.config['API_BASE_URL']}")
        print(f"   CLP_IP: {sync.config['CLP_IP']}")
        print(f"   SYNC_ENABLED: {sync.config['SYNC_ENABLED']}")
        print(f"   SYNC_TIMES: {sync.config['SYNC_TIMES']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do CLP Térreo: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_clp_auditorio():
    """Testa o CLP Auditório AR"""
    print("\n" + "=" * 60)
    print("TESTE CLP AUDITÓRIO AR (172.17.85.123)")
    print("=" * 60)
    
    try:
        # Obter instância do sincronizador
        sync = SincronizadorCLPAuditorio.get_instance()
        print(f"✓ Instância do SincronizadorCLPAuditorio obtida: {sync}")
        
        # Teste 1: Verificar conectividade
        print("\n1. Testando conectividade...")
        conectado, mensagem = sync.verificar_conectividade_clp()
        print(f"   Conectado: {conectado}")
        print(f"   Mensagem: {mensagem}")
        
        # Teste 2: Obter status de sincronização
        print("\n2. Obtendo status de sincronização...")
        status = sync.obter_status_sincronizacao()
        print(f"   Status completo:")
        for chave, valor in status.items():
            print(f"     {chave}: {valor}")
        
        # Teste 3: Verificar configuração
        print("\n3. Verificando configuração...")
        print(f"   API_BASE_URL: {sync.config['API_BASE_URL']}")
        print(f"   CLP_IP: {sync.config['CLP_IP']}")
        print(f"   SYNC_ENABLED: {sync.config['SYNC_ENABLED']}")
        print(f"   SYNC_TIMES: {sync.config['SYNC_TIMES']}")
        print(f"   LOCAIS_GERENCIADOS: {sync.config.get('LOCAIS_GERENCIADOS', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do CLP Auditório: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print(f"Teste de Debug dos CLPs - {datetime.now()}")
    
    # Teste ambos os CLPs
    resultado_terreo = teste_clp_terreo()
    resultado_auditorio = teste_clp_auditorio()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    print(f"CLP Térreo B1:  {'✓ OK' if resultado_terreo else '❌ FALHOU'}")
    print(f"CLP Auditório:  {'✓ OK' if resultado_auditorio else '❌ FALHOU'}")
    
    if resultado_terreo and resultado_auditorio:
        print("\n🎉 Todos os testes passaram!")
        print("O problema deve estar na interface web ou no JavaScript.")
    else:
        print("\n⚠️ Alguns testes falharam - verificar logs acima.")

if __name__ == "__main__":
    main()
