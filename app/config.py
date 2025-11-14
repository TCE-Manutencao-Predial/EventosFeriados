"""
config.py - Wrapper de Compatibilidade

Este módulo mantém compatibilidade com código legado que importa de app.config.
Todas as configurações agora vêm de app.settings.py

ATENÇÃO: Este arquivo é um wrapper. A configuração real está em app/settings.py
Versão: 2.0.0 (wrapper)
"""

# Importa tudo de settings
from .settings import (
    # Diretórios
    BASE_DIR,
    DATA_DIR,
    LOG_DIR,
    LOG_FILE,
    ROOT_BACKEND,
    ROOT_DATA,
    ROOT_LOGS,
    BACKUP_DIR,
    
    # Configurações Flask
    SECRET_KEY,
    ROUTES_PREFIX,
    DEBUG,
    
    # Configurações CLP
    CLP_CONFIG,
    CLP_AUDITORIO_CONFIG,
    
    # Configurações WhatsApp
    WHATSAPP_API,
    
    # Configurações de formato
    DATE_FORMAT,
    TIME_FORMAT,
    DATETIME_FORMAT,
    
    # Configurações de paginação/cache
    ITEMS_PER_PAGE,
    CACHE_TYPE,
    CACHE_DEFAULT_TIMEOUT,
    
    # Classes de configuração
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    config,
    
    # Funções
    setup_logging,
    ensure_directories
)

# =============================================================================
# NOTA DE MIGRAÇÃO
# =============================================================================
"""
Este arquivo (app/config.py) agora é apenas um wrapper para manter compatibilidade.

MIGRAÇÃO:
- ANTES: from app.config import CLP_CONFIG, ROUTES_PREFIX
- DEPOIS: from app.settings import CLP_CONFIG, ROUTES_PREFIX

O arquivo original foi movido para: docs/legacy/config.py.obsoleto

Para novos desenvolvimentos, importe diretamente de app.settings
"""
