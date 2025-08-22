#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar o endpoint de agendamento automático do TCE
"""

import requests
import json

def teste_endpoint_agendamento():
    """Testa o endpoint de agendamento automático"""
    print("🔧 Testando endpoint de agendamento automático TCE...")
    
    url = "http://127.0.0.1:5045/EventosFeriados/api/tce/teste-agendamento"
    
    try:
        print(f"📡 Fazendo requisição POST para: {url}")
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            print("✅ Sucesso!")
            print(f"📋 Resposta completa:")
            print(json.dumps(dados, indent=2, ensure_ascii=False))
            
            # Extrair dados importantes
            if dados.get('status') == 'sucesso':
                resultado = dados.get('dados', {})
                print(f"\n🎯 Resumo:")
                print(f"   - Simulação: {resultado.get('simulacao')}")
                print(f"   - Eventos processados: {resultado.get('eventos_processados')}")
                print(f"   - Timestamp: {resultado.get('timestamp')}")
                
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor.")
        print("   Verifique se o servidor Flask está rodando.")
    except requests.exceptions.Timeout:
        print("❌ Erro: Timeout na requisição.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    teste_endpoint_agendamento()
