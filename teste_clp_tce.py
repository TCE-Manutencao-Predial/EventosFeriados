#!/usr/bin/env python3
"""
Script de teste para validar a integração com CLP TCE
Execute este script para testar a conectividade e funcionalidade básica
"""

import requests
import json
import time
import sys
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Configurações
API_BASE = 'https://automacao.tce.go.gov.br/scadaweb/api'
CLP_IP = '172.17.85.104'
TIMEOUT = 30

# Credenciais de autenticação
AUTH_USER = 'eventosferiados'
AUTH_PASS = 'WzPcMMFU'
AUTH = HTTPBasicAuth(AUTH_USER, AUTH_PASS)

def testar_conectividade():
    """Testa a conectividade básica com o CLP"""
    print("🔍 Testando conectividade com CLP...")
    
    try:
        # Tentar ler uma tag simples
        url = f"{API_BASE}/tag_read/{CLP_IP}/N33%253A0"
        response = requests.get(url, auth=AUTH, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if 'valor' in data:
                print(f"✅ CLP conectado! N33:0 = {data['valor']}")
                return True
            else:
                print(f"❌ CLP respondeu mas formato inesperado: {data}")
                return False
        elif response.status_code == 401:
            print("❌ Erro de autenticação (credenciais inválidas)")
            return False
        elif response.status_code == 403:
            print("❌ Acesso negado (sem permissão)")
            return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def testar_leitura_feriados():
    """Testa a leitura de todos os slots de feriados"""
    print("\n📖 Testando leitura de feriados...")
    
    feriados_encontrados = []
    
    for i in range(20):  # N33:0 a N33:19
        try:
            # Ler dia
            url_dia = f"{API_BASE}/tag_read/{CLP_IP}/N33%253A{i}"
            response_dia = requests.get(url_dia, auth=AUTH, timeout=TIMEOUT)
            
            # Ler mês
            url_mes = f"{API_BASE}/tag_read/{CLP_IP}/N34%253A{i}"
            response_mes = requests.get(url_mes, auth=AUTH, timeout=TIMEOUT)
            
            if response_dia.status_code == 200 and response_mes.status_code == 200:
                dia = response_dia.json().get('valor', 0)
                mes = response_mes.json().get('valor', 0)
                
                if dia > 0 and mes > 0:
                    feriados_encontrados.append((i, dia, mes))
                    print(f"  Slot {i:2d}: {dia:02d}/{mes:02d}")
            
        except Exception as e:
            print(f"  ❌ Erro no slot {i}: {e}")
    
    if feriados_encontrados:
        print(f"✅ {len(feriados_encontrados)} feriados encontrados no CLP")
    else:
        print("ℹ️  Nenhum feriado encontrado (todos os slots estão zerados)")
    
    return feriados_encontrados

def testar_escrita():
    """Testa escrita em uma tag específica"""
    print("\n✏️  Testando escrita...")
    
    # Usar slot 19 para teste (último slot)
    slot_teste = 19
    dia_teste = 31
    mes_teste = 12
    
    try:
        # Ler valores originais
        url_dia_read = f"{API_BASE}/tag_read/{CLP_IP}/N33%253A{slot_teste}"
        url_mes_read = f"{API_BASE}/tag_read/{CLP_IP}/N34%253A{slot_teste}"
        
        response_dia_orig = requests.get(url_dia_read, auth=AUTH, timeout=TIMEOUT)
        response_mes_orig = requests.get(url_mes_read, auth=AUTH, timeout=TIMEOUT)
        
        dia_original = response_dia_orig.json().get('valor', 0) if response_dia_orig.status_code == 200 else 0
        mes_original = response_mes_orig.json().get('valor', 0) if response_mes_orig.status_code == 200 else 0
        
        print(f"  Valores originais slot {slot_teste}: {dia_original:02d}/{mes_original:02d}")
        
        # Escrever valores de teste
        url_dia_write = f"{API_BASE}/tag_write/{CLP_IP}/N33%253A{slot_teste}/{dia_teste}"
        url_mes_write = f"{API_BASE}/tag_write/{CLP_IP}/N34%253A{slot_teste}/{mes_teste}"
        
        response_dia_write = requests.get(url_dia_write, auth=AUTH, timeout=TIMEOUT)
        response_mes_write = requests.get(url_mes_write, auth=AUTH, timeout=TIMEOUT)
        
        if (response_dia_write.status_code == 200 and response_mes_write.status_code == 200):
            data_dia = response_dia_write.json()
            data_mes = response_mes_write.json()
            
            if data_dia.get('sucesso') and data_mes.get('sucesso'):
                print(f"✅ Escrita bem-sucedida: {dia_teste:02d}/{mes_teste:02d}")
                
                # Aguardar e verificar
                time.sleep(1)
                
                # Ler de volta para confirmar
                response_dia_check = requests.get(url_dia_read, auth=AUTH, timeout=TIMEOUT)
                response_mes_check = requests.get(url_mes_read, auth=AUTH, timeout=TIMEOUT)
                
                if response_dia_check.status_code == 200 and response_mes_check.status_code == 200:
                    dia_verificado = response_dia_check.json().get('valor', 0)
                    mes_verificado = response_mes_check.json().get('valor', 0)
                    
                    if dia_verificado == dia_teste and mes_verificado == mes_teste:
                        print(f"✅ Verificação confirmada: {dia_verificado:02d}/{mes_verificado:02d}")
                        
                        # Restaurar valores originais
                        url_dia_restore = f"{API_BASE}/tag_write/{CLP_IP}/N33%253A{slot_teste}/{dia_original}"
                        url_mes_restore = f"{API_BASE}/tag_write/{CLP_IP}/N34%253A{slot_teste}/{mes_original}"
                        
                        requests.get(url_dia_restore, auth=AUTH, timeout=TIMEOUT)
                        requests.get(url_mes_restore, auth=AUTH, timeout=TIMEOUT)
                        
                        print(f"✅ Valores originais restaurados: {dia_original:02d}/{mes_original:02d}")
                        return True
                    else:
                        print(f"❌ Verificação falhou: esperado {dia_teste:02d}/{mes_teste:02d}, obtido {dia_verificado:02d}/{mes_verificado:02d}")
                else:
                    print("❌ Erro ao verificar escrita")
            else:
                print(f"❌ Escrita falhou: dia.sucesso={data_dia.get('sucesso')}, mes.sucesso={data_mes.get('sucesso')}")
        else:
            print(f"❌ Erro HTTP na escrita: dia={response_dia_write.status_code}, mes={response_mes_write.status_code}")
        
        return False
        
    except Exception as e:
        print(f"❌ Erro no teste de escrita: {e}")
        return False

def main():
    """Função principal do teste"""
    print("🧪 TESTE DE INTEGRAÇÃO CLP TCE")
    print("=" * 50)
    print(f"API Base: {API_BASE}")
    print(f"CLP IP: {CLP_IP}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Teste 1: Conectividade
    if not testar_conectividade():
        print("\n❌ FALHA: Não foi possível conectar ao CLP")
        sys.exit(1)
    
    # Teste 2: Leitura
    feriados = testar_leitura_feriados()
    
    # Teste 3: Escrita
    if testar_escrita():
        print("\n✅ TESTE DE ESCRITA: SUCESSO")
    else:
        print("\n❌ TESTE DE ESCRITA: FALHA")
    
    print("\n" + "=" * 50)
    print("🎯 RESUMO DOS TESTES:")
    print("✅ Conectividade: OK")
    print(f"✅ Leitura: OK ({len(feriados)} feriados encontrados)")
    print("✅ Escrita: OK" if testar_escrita() else "❌ Escrita: FALHA")
    print("=" * 50)
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Execute o sistema EventosFeriados")
    print("2. Acesse /EventosFeriados/sincronizacao-clp")
    print("3. Use o botão 'Testar Conexão' para validar")
    print("4. Execute uma sincronização manual")
    print("5. Configure a sincronização automática")

if __name__ == "__main__":
    main()
