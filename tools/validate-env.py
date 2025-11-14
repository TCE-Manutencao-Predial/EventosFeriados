#!/usr/bin/env python3
"""
Validador de Variáveis de Ambiente - Eventos e Feriados
===========================================================
Valida se todas as variáveis obrigatórias estão configuradas no .env.deploy
Versão: 2.0.0
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# Configuração
# ============================================================

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent

# Carregar .env.deploy
env_file = PROJECT_ROOT / '.env.deploy'
if not env_file.exists():
    print(f"❌ ERRO: Arquivo .env.deploy não encontrado em {PROJECT_ROOT}")
    print(f"   Copie .env.deploy.template para .env.deploy e configure os valores.")
    sys.exit(1)

load_dotenv(env_file)

# ============================================================
# Variáveis Obrigatórias
# ============================================================

REQUIRED_VARS = {
    # Identificação do Projeto
    'PROJECT_NAME': 'Nome do projeto',
    'PROJECT_NAME_DISPLAY': 'Nome de exibição do projeto',
    'SERVICE_NAME': 'Nome do serviço systemd',
    'APP_NAME': 'Nome do módulo Python',
    'PORT': 'Porta do servidor',
    
    # Caminhos
    'ROOT_SOFTWARES': 'Diretório raiz dos softwares',
    'ROOT_BACKEND': 'Diretório do backend',
    'ROOT_DATA': 'Diretório de dados',
    'ROOT_LOGS': 'Diretório de logs',
    'BACKUP_DIR': 'Diretório de backups',
    
    # Flask
    'SECRET_KEY': 'Chave secreta do Flask',
    'ROUTES_PREFIX': 'Prefixo das rotas',
    'DEBUG': 'Modo debug',
    
    # CLP
    'CLP_API_URL': 'URL da API do CLP',
    'CLP_IP': 'IP do CLP Plenário',
    'CLP_AUTH_USER': 'Usuário de autenticação do CLP',
    'CLP_AUTH_PASS': 'Senha de autenticação do CLP',
    'CLP_AUDITORIO_IP': 'IP do CLP Auditório',
    
    # WhatsApp API
    'WHATSAPP_API_TOKEN': 'Token da API WhatsApp',
    'WHATSAPP_API_ORIGEM': 'Origem das mensagens',
    
    # Git
    'GIT_REPO_NAME': 'Nome do repositório Git',
    'GIT_REPO_OWNER': 'Proprietário do repositório',
    'GIT_REPO_URL': 'URL do repositório',
}

OPTIONAL_VARS = {
    'CLP_TIMEOUT': 'Timeout para requisições CLP',
    'CLP_RETRY_COUNT': 'Tentativas de retry',
    'CLP_SYNC_TIMES': 'Horários de sincronização',
    'CLP_MAX_FERIADOS': 'Máximo de feriados',
    'CLP_MAX_EVENTOS_PLENARIO': 'Máximo de eventos Plenário',
    'CLP_MAX_EVENTOS_AUDITORIO': 'Máximo de eventos Auditório',
    'CLP_AUD_MIN_HORA': 'Hora mínima Auditório',
    'CLP_AUD_LOCAIS': 'Locais gerenciados Auditório',
    'WHATSAPP_API_HOST': 'Host da API WhatsApp',
    'WHATSAPP_APENAS_DISPONIVEIS': 'Enviar apenas para disponíveis',
    'WHATSAPP_API_ASYNC': 'Processamento assíncrono',
    'WHATSAPP_API_TIMEOUT': 'Timeout WhatsApp',
    'ITEMS_PER_PAGE': 'Itens por página',
    'CACHE_TYPE': 'Tipo de cache',
    'CACHE_DEFAULT_TIMEOUT': 'Timeout do cache',
    'DATE_FORMAT': 'Formato de data',
    'TIME_FORMAT': 'Formato de hora',
    'DATETIME_FORMAT': 'Formato de data/hora',
    'RESTART_SEC': 'Segundos para restart',
    'AUTO_HABILITAR_SERVICO': 'Habilitar serviço automaticamente',
    'FLASK_ENV': 'Ambiente Flask',
}

# ============================================================
# Funções de Validação
# ============================================================

def mask_sensitive(key: str, value: str) -> str:
    """Mascara valores sensíveis para exibição."""
    sensitive_keys = ['SECRET_KEY', 'TOKEN', 'PASS', 'PASSWORD', 'KEY']
    
    if any(s in key.upper() for s in sensitive_keys):
        if len(value) <= 8:
            return '***'
        return f"{value[:4]}...{value[-4:]}"
    return value

def validate_port(value: str) -> tuple[bool, str]:
    """Valida se a porta é válida."""
    try:
        port = int(value)
        if 1 <= port <= 65535:
            return True, ""
        return False, f"Porta deve estar entre 1 e 65535 (valor: {port})"
    except ValueError:
        return False, f"Porta deve ser um número inteiro (valor: {value})"

def validate_boolean(value: str) -> tuple[bool, str]:
    """Valida se o valor é booleano válido."""
    if value.lower() in ['true', 'false']:
        return True, ""
    return False, f"Deve ser 'true' ou 'false' (valor: {value})"

def validate_path(value: str) -> tuple[bool, str]:
    """Valida se o caminho parece válido."""
    if not value.startswith('/'):
        return False, f"Caminho deve ser absoluto (valor: {value})"
    return True, ""

def validate_url(value: str) -> tuple[bool, str]:
    """Valida se a URL parece válida."""
    if not (value.startswith('http://') or value.startswith('https://')):
        return False, f"URL deve começar com http:// ou https:// (valor: {value})"
    return True, ""

def validate_ip(value: str) -> tuple[bool, str]:
    """Valida se o IP parece válido."""
    parts = value.split('.')
    if len(parts) != 4:
        return False, f"IP deve ter 4 octetos (valor: {value})"
    
    try:
        for part in parts:
            num = int(part)
            if not (0 <= num <= 255):
                return False, f"Octeto do IP deve estar entre 0 e 255 (valor: {value})"
        return True, ""
    except ValueError:
        return False, f"IP deve conter apenas números (valor: {value})"

# ============================================================
# Validação Principal
# ============================================================

def main():
    print("=" * 60)
    print("VALIDAÇÃO DE CONFIGURAÇÕES - EVENTOS E FERIADOS")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # Valida variáveis obrigatórias
    print("📋 Variáveis Obrigatórias:")
    print("-" * 60)
    
    for var, description in REQUIRED_VARS.items():
        value = os.getenv(var)
        
        if value is None or value.strip() == '':
            errors.append(f"❌ {var}: {description} - NÃO CONFIGURADA")
            print(f"  ❌ {var}: {description}")
            print(f"     Valor: NÃO CONFIGURADA")
        else:
            masked_value = mask_sensitive(var, value)
            print(f"  ✅ {var}: {description}")
            print(f"     Valor: {masked_value}")
            
            # Validações específicas
            if var == 'PORT':
                valid, msg = validate_port(value)
                if not valid:
                    errors.append(f"❌ {var}: {msg}")
                    print(f"     ⚠️  {msg}")
            
            elif var == 'DEBUG':
                valid, msg = validate_boolean(value)
                if not valid:
                    warnings.append(f"⚠️  {var}: {msg}")
                    print(f"     ⚠️  {msg}")
            
            elif 'PATH' in var or 'DIR' in var or 'ROOT' in var:
                valid, msg = validate_path(value)
                if not valid:
                    warnings.append(f"⚠️  {var}: {msg}")
                    print(f"     ⚠️  {msg}")
            
            elif 'URL' in var:
                valid, msg = validate_url(value)
                if not valid:
                    warnings.append(f"⚠️  {var}: {msg}")
                    print(f"     ⚠️  {msg}")
            
            elif '_IP' in var:
                valid, msg = validate_ip(value)
                if not valid:
                    errors.append(f"❌ {var}: {msg}")
                    print(f"     ⚠️  {msg}")
        
        print()
    
    # Valida variáveis opcionais
    print("\n📋 Variáveis Opcionais (configuradas):")
    print("-" * 60)
    
    configured_optional = False
    for var, description in OPTIONAL_VARS.items():
        value = os.getenv(var)
        
        if value is not None and value.strip() != '':
            configured_optional = True
            masked_value = mask_sensitive(var, value)
            print(f"  ✅ {var}: {description}")
            print(f"     Valor: {masked_value}")
            print()
    
    if not configured_optional:
        print("  Nenhuma variável opcional configurada (usando padrões)")
    
    # Relatório final
    print("\n" + "=" * 60)
    print("RESULTADO DA VALIDAÇÃO")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERROS ENCONTRADOS ({len(errors)}):")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print(f"\n⚠️  AVISOS ({len(warnings)}):")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ Todas as configurações estão válidas!")
        print("   Sistema pronto para deploy.")
        sys.exit(0)
    elif errors:
        print("\n❌ Configuração INVÁLIDA!")
        print("   Corrija os erros antes de fazer o deploy.")
        sys.exit(1)
    else:
        print("\n⚠️  Configuração válida, mas com avisos.")
        print("   Revise os avisos antes de fazer o deploy.")
        sys.exit(0)

if __name__ == '__main__':
    main()
