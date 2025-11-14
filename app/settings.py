"""
settings.py - Configuração Centralizada do Sistema Eventos e Feriados

Este módulo centraliza TODAS as configurações do sistema.
Carrega variáveis de ambiente do arquivo .env.deploy

Padrão: 12-factor app
Versão: 2.0.0
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# =============================================================================
# CARREGA VARIÁVEIS DE AMBIENTE
# =============================================================================

# Carrega .env.deploy do diretório raiz do projeto
# Busca em múltiplos locais para suportar diferentes ambientes
BASE_DIR = Path(__file__).resolve().parent.parent

# Tenta localizar .env.deploy em diferentes locais
ENV_FILE_CANDIDATES = [
    BASE_DIR / '.env.deploy',  # No diretório do módulo (dev)
    Path('/var/softwaresTCE/eventos_feriados/.env.deploy'),  # Produção
    Path.cwd() / '.env.deploy',  # Diretório de trabalho atual
]

ENV_FILE = None
for candidate in ENV_FILE_CANDIDATES:
    if candidate.exists():
        ENV_FILE = candidate
        break

if ENV_FILE is None:
    print(f"❌ ERRO: Arquivo .env.deploy não encontrado nos seguintes locais:")
    for candidate in ENV_FILE_CANDIDATES:
        print(f"   - {candidate}")
    print(f"💡 Execute: make reset-env")
    sys.exit(1)

load_dotenv(ENV_FILE)

# =============================================================================
# FUNÇÃO AUXILIAR PARA VALIDAÇÃO
# =============================================================================

def get_required_env(key: str, default=None) -> str:
    """Obtém variável de ambiente obrigatória."""
    value = os.getenv(key, default)
    if value is None:
        print(f"❌ ERRO: Variável {key} não configurada em .env.deploy")
        sys.exit(1)
    return value

def get_bool_env(key: str, default: bool = False) -> bool:
    """Obtém variável de ambiente booleana."""
    return os.getenv(key, str(default)).lower() == 'true'

def get_int_env(key: str, default: int) -> int:
    """Obtém variável de ambiente inteira."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        print(f"⚠️  AVISO: {key} inválido, usando padrão: {default}")
        return default

# =============================================================================
# CONFIGURAÇÕES DO PROJETO
# =============================================================================

PROJECT_NAME = get_required_env('PROJECT_NAME', 'eventos_feriados')
PROJECT_NAME_DISPLAY = get_required_env('PROJECT_NAME_DISPLAY', 'Sistema de Eventos e Feriados')
SERVICE_NAME = get_required_env('SERVICE_NAME', 'eventos_feriados.service')
APP_NAME = get_required_env('APP_NAME', 'eventos_feriados')
PORT = get_int_env('PORT', 5045)

# =============================================================================
# CAMINHOS DO SISTEMA
# =============================================================================

ROOT_SOFTWARES = get_required_env('ROOT_SOFTWARES', '/var/softwaresTCE')
ROOT_BACKEND = get_required_env('ROOT_BACKEND', '/var/softwaresTCE/eventos_feriados')
ROOT_DATA = get_required_env('ROOT_DATA', '/var/softwaresTCE/dados/eventos_feriados')
ROOT_LOGS = get_required_env('ROOT_LOGS', '/var/softwaresTCE/logs/eventos_feriados')
BACKUP_DIR = get_required_env('BACKUP_DIR', f'{ROOT_DATA}/backups')

# Aliases para compatibilidade com código legado
DATA_DIR = ROOT_DATA
LOG_DIR = ROOT_LOGS
LOG_FILE = f"{LOG_DIR}/eventos_feriados.log"

# =============================================================================
# CONFIGURAÇÕES FLASK
# =============================================================================

SECRET_KEY = get_required_env('SECRET_KEY')
ROUTES_PREFIX = get_required_env('ROUTES_PREFIX', '/EventosFeriados')
DEBUG = get_bool_env('DEBUG', False)

# =============================================================================
# CONFIGURAÇÕES CLP PLENÁRIO
# =============================================================================

CLP_CONFIG = {
    'API_BASE_URL': get_required_env('CLP_API_URL', 'https://automacao.tce.go.gov.br/scadaweb/api'),
    'CLP_IP': get_required_env('CLP_IP', '172.17.85.104'),
    'AUTH_USER': get_required_env('CLP_AUTH_USER', 'eventosferiados'),
    'AUTH_PASS': get_required_env('CLP_AUTH_PASS'),
    'TIMEOUT': get_int_env('CLP_TIMEOUT', 30),
    'RETRY_COUNT': get_int_env('CLP_RETRY_COUNT', 3),
    'SYNC_TIMES': os.getenv('CLP_SYNC_TIMES', '07:00,20:00').split(','),
    'MAX_FERIADOS': get_int_env('CLP_MAX_FERIADOS', 20),
    'SYNC_ENABLED': get_bool_env('CLP_SYNC_ENABLED', True),
    'STATUS_FILE': f"{ROOT_DATA}/clp_status.json",
    'BACKUP_FILE': f"{ROOT_DATA}/clp_backup.json",
    
    # Mapeamento das tags do CLP (hardcoded - estrutura do CLP)
    'TAGS_FERIADOS': {
        'DIA': 'N33',   # N33:0 a N33:19 - dias dos feriados
        'MES': 'N34'    # N34:0 a N34:19 - meses dos feriados
    },
    'TAGS_EVENTOS_PLENARIO': {
        'DIA': 'N60',          # N60:0-9 - dias dos eventos  
        'MES': 'N61',          # N61:0-9 - meses dos eventos
        'HORA_INICIO': 'N62',  # N62:0-9 - hora de início
        'MIN_INICIO': 'N63',   # N63:0-9 - minuto de início
        'HORA_FIM': 'N64',     # N64:0-9 - hora de fim
        'MIN_FIM': 'N65'       # N65:0-9 - minuto de fim
    },
    'MAX_EVENTOS': get_int_env('CLP_MAX_EVENTOS_PLENARIO', 10)
}

# =============================================================================
# CONFIGURAÇÕES CLP AUDITÓRIO
# =============================================================================

CLP_AUDITORIO_CONFIG = {
    'API_BASE_URL': get_required_env('CLP_API_URL', 'https://automacao.tce.go.gov.br/scadaweb/api'),
    'CLP_IP': get_required_env('CLP_AUDITORIO_IP', '172.17.85.123'),
    'AUTH_USER': get_required_env('CLP_AUTH_USER', 'eventosferiados'),
    'AUTH_PASS': get_required_env('CLP_AUTH_PASS'),
    'TIMEOUT': get_int_env('CLP_TIMEOUT', 30),
    'RETRY_COUNT': get_int_env('CLP_RETRY_COUNT', 3),
    'SYNC_TIMES': os.getenv('CLP_SYNC_TIMES', '07:00,20:00').split(','),
    'SYNC_ENABLED': get_bool_env('CLP_SYNC_ENABLED', True),
    'STATUS_FILE': f"{ROOT_DATA}/clp_auditorio_status.json",
    'BACKUP_FILE': f"{ROOT_DATA}/clp_auditorio_backup.json",
    
    # Mapeamento das tags do CLP Auditório (hardcoded - estrutura do CLP)
    'TAGS_EVENTOS_AUDITORIO': {
        'DIA': 'N91',          # N91:0-9 - dias dos eventos  
        'MES': 'N92',          # N92:0-9 - meses dos eventos
        'HORA_INICIO': 'N93',  # N93:0-9 - hora de início (ajustado -1h)
        'MIN_INICIO': 'N94',   # N94:0-9 - minuto de início
        'HORA_FIM': 'N95',     # N95:0-9 - hora de fim (ajustado +1h)
        'MIN_FIM': 'N96'       # N96:0-9 - minuto de fim
    },
    
    'AUDITORIO_HORA_MINIMA': os.getenv('CLP_AUD_MIN_HORA', '05:30'),
    'MAX_EVENTOS': get_int_env('CLP_MAX_EVENTOS_AUDITORIO', 10),
    'LOCAIS_GERENCIADOS': os.getenv('CLP_AUD_LOCAIS', 'Auditório Nobre,Foyer do Auditório').split(',')
}

# =============================================================================
# CONFIGURAÇÕES API WHATSAPP (HelpDeskMonitor)
# =============================================================================

WHATSAPP_API = {
    'HOST': os.getenv('WHATSAPP_API_HOST', 'https://automacao.tce.go.gov.br').rstrip('/'),
    'TOKEN': get_required_env('WHATSAPP_API_TOKEN'),
    'ORIGEM': get_required_env('WHATSAPP_API_ORIGEM', 'EVENTOS_FERIADOS'),
    'APENAS_DISPONIVEIS': get_bool_env('WHATSAPP_APENAS_DISPONIVEIS', True),
    'ASYNC': get_bool_env('WHATSAPP_API_ASYNC', True),
    'TIMEOUT': get_int_env('WHATSAPP_API_TIMEOUT', 60)
}

# =============================================================================
# CONFIGURAÇÕES DE PAGINAÇÃO E CACHE
# =============================================================================

ITEMS_PER_PAGE = get_int_env('ITEMS_PER_PAGE', 20)
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
CACHE_DEFAULT_TIMEOUT = get_int_env('CACHE_DEFAULT_TIMEOUT', 300)

# =============================================================================
# CONFIGURAÇÕES DE FORMATO
# =============================================================================

DATE_FORMAT = os.getenv('DATE_FORMAT', '%d/%m/%Y')
TIME_FORMAT = os.getenv('TIME_FORMAT', '%H:%M')
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%d/%m/%Y %H:%M')

# =============================================================================
# REPOSITÓRIO GIT
# =============================================================================

GIT_REPO_NAME = get_required_env('GIT_REPO_NAME', 'eventos-feriados')
GIT_REPO_OWNER = get_required_env('GIT_REPO_OWNER', 'TCE-Manutencao-Predial')
GIT_REPO_URL = get_required_env('GIT_REPO_URL')

# =============================================================================
# CONFIGURAÇÕES DE DEPLOY
# =============================================================================

RESTART_SEC = get_int_env('RESTART_SEC', 10)
AUTO_HABILITAR_SERVICO = get_bool_env('AUTO_HABILITAR_SERVICO', True)
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# =============================================================================
# CLASSES DE CONFIGURAÇÃO FLASK
# =============================================================================

class Config:
    """Configurações base da aplicação"""
    SECRET_KEY = SECRET_KEY
    ITEMS_PER_PAGE = ITEMS_PER_PAGE
    CACHE_TYPE = CACHE_TYPE
    CACHE_DEFAULT_TIMEOUT = CACHE_DEFAULT_TIMEOUT
    CORS_ORIGINS = ['*']
    DATE_FORMAT = DATE_FORMAT
    TIME_FORMAT = TIME_FORMAT
    DATETIME_FORMAT = DATETIME_FORMAT

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Configurações para testes"""
    DEBUG = True
    TESTING = True

# Mapeamento de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig if DEBUG else ProductionConfig
}

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def ensure_directories():
    """Cria diretórios necessários se não existirem."""
    directories = [ROOT_DATA, ROOT_LOGS, BACKUP_DIR]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"⚠️  Sem permissão para criar: {directory}")
        except Exception as e:
            print(f"❌ Erro ao criar diretório {directory}: {e}")

def setup_logging():
    """Configura o sistema de logging da aplicação.
    
    Evita adicionar handlers duplicados se chamada múltiplas vezes.
    """
    global LOG_DIR, LOG_FILE
    logger = logging.getLogger('EventosFeriados')

    if not logger.handlers:
        # Garante que o diretório de logs existe
        try:
            Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            fallback_dir = BASE_DIR / 'logs'
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                logger.warning(f"Falha ao criar LOG_DIR '{LOG_DIR}': {e}. Usando fallback '{fallback_dir}'.")
                LOG_DIR = str(fallback_dir)
                LOG_FILE = f"{LOG_DIR}/eventos_feriados.log"
            except Exception:
                pass

        # Configura handlers
        file_handler = None
        try:
            file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
        except Exception as e:
            logger.warning(f"Não foi possível criar FileHandler em '{LOG_FILE}': {e}. Prosseguindo sem arquivo de log.")

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(stream_handler)
        
        if file_handler:
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        logger.propagate = False
        logger.info(f"Sistema de logging inicializado | LOG_DIR={LOG_DIR} | LOG_FILE={LOG_FILE}")
    else:
        logger.debug("setup_logging() chamado novamente - handlers já configurados")

    return logger

# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

# Garante que diretórios existem ao importar o módulo
ensure_directories()
