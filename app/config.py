# app/config.py
import os
import logging

# Configuração do diretório base
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Configuração do diretório de dados
# Usa diretório externo para persistir dados independente das atualizações do Git
DATA_DIR = '/var/softwaresTCE/dados/eventos_feriados'

# Garante que o diretório de dados existe
try:
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"✅ Diretório criado: {DATA_DIR}")
    else:
        print(f"✅ Diretório já existe: {DATA_DIR}")
except PermissionError as e:
    # Fallback para diretório local se não tiver permissão para criar em /var
    print(f"⚠️ Sem permissão para criar {DATA_DIR}: {e}")
    DATA_DIR = os.path.join(BASE_DIR, 'dados')
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    print(f"🔄 Usando diretório fallback: {DATA_DIR}")
except Exception as e:
    print(f"❌ Erro ao criar diretório {DATA_DIR}: {e}")
    # Fallback para diretório local
    DATA_DIR = os.path.join(BASE_DIR, 'dados')
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    print(f"🔄 Usando diretório fallback: {DATA_DIR}")

ROUTES_PREFIX = '/EventosFeriados'

# Configuração dos diretórios de logs
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'eventos_feriados.log')

# Configurações CLP TCE
CLP_CONFIG = {
    'API_BASE_URL': os.environ.get('CLP_API_URL', 'https://automacao.tce.go.gov.br/scadaweb/api'),
    'CLP_IP': '172.17.85.104',  # IP do CLP Térreo B1
    'AUTH_USER': 'eventosferiados',  # Usuário para autenticação básica
    'AUTH_PASS': 'WzPcMMFU',  # Senha para autenticação básica
    'TIMEOUT': int(os.environ.get('CLP_TIMEOUT', '30')),  # Timeout em segundos para requisições
    'RETRY_COUNT': int(os.environ.get('CLP_RETRY_COUNT', '3')),  # Número de tentativas em caso de falha
    'SYNC_TIMES': os.environ.get('CLP_SYNC_TIMES', '07:00,18:00').split(','),  # Horários de sincronização automática
    'MAX_FERIADOS': 20,  # Máximo de feriados (N33:0 a N33:19)
    'SYNC_ENABLED': os.environ.get('CLP_SYNC_ENABLED', 'true').lower() == 'true',  # Habilitar sincronização automática
    'STATUS_FILE': os.path.join(DATA_DIR, 'clp_status.json'),  # Arquivo de status
    'BACKUP_FILE': os.path.join(DATA_DIR, 'clp_backup.json'),   # Backup dos dados
    # Mapeamento das tags do CLP
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
    'MAX_EVENTOS': 10  # Máximo de eventos do Plenário
}

# Configurações CLP Auditório
CLP_AUDITORIO_CONFIG = {
    'API_BASE_URL': os.environ.get('CLP_API_URL', 'https://automacao.tce.go.gov.br/scadaweb/api'),
    'CLP_IP': '172.17.85.123',  # IP do CLP Auditório AR
    'AUTH_USER': 'eventosferiados',  # Usuário para autenticação básica
    'AUTH_PASS': 'WzPcMMFU',  # Senha para autenticação básica
    'TIMEOUT': int(os.environ.get('CLP_TIMEOUT', '30')),  # Timeout em segundos para requisições
    'RETRY_COUNT': int(os.environ.get('CLP_RETRY_COUNT', '3')),  # Número de tentativas em caso de falha
    'SYNC_TIMES': os.environ.get('CLP_SYNC_TIMES', '07:00,18:00').split(','),  # Horários de sincronização automática
    'SYNC_ENABLED': os.environ.get('CLP_SYNC_ENABLED', 'true').lower() == 'true',  # Habilitar sincronização automática
    'STATUS_FILE': os.path.join(DATA_DIR, 'clp_auditorio_status.json'),  # Arquivo de status
    'BACKUP_FILE': os.path.join(DATA_DIR, 'clp_auditorio_backup.json'),   # Backup dos dados
    # Mapeamento das tags do CLP Auditório para eventos
    # AJUSTE AUTOMÁTICO: TODOS os eventos do Auditório são ajustados para iniciar 1h antes e terminar 1h depois
    # para preparar infraestrutura (luzes, refrigeração) do Auditório
    'TAGS_EVENTOS_AUDITORIO': {
        'DIA': 'N91',          # N91:0-9 - dias dos eventos  
        'MES': 'N92',          # N92:0-9 - meses dos eventos
        'HORA_INICIO': 'N93',  # N93:0-9 - hora de início (com ajuste automático para todos os eventos)
        'MIN_INICIO': 'N94',   # N94:0-9 - minuto de início
        'HORA_FIM': 'N95',     # N95:0-9 - hora de fim (com ajuste automático para todos os eventos)
        'MIN_FIM': 'N96'       # N96:0-9 - minuto de fim
    },
    'MAX_EVENTOS': 10,  # Máximo de eventos do Auditório
    'LOCAIS_GERENCIADOS': ['Auditório Nobre', 'Foyer do Auditório']  # Locais gerenciados por este CLP
}

def setup_logging():
    """Configura o sistema de logging da aplicação."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('EventosFeriados')
    logger.info("Sistema de logging inicializado")
    
    return logger

# Configurações da aplicação
class Config:
    """Configurações base da aplicação"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'eventos_feriados_dev_key_2024'
    
    # Configurações de paginação
    ITEMS_PER_PAGE = 20
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de CORS (se necessário)
    CORS_ORIGINS = ['*']
    
    # Configurações de formato de data/hora
    DATE_FORMAT = '%d/%m/%Y'
    TIME_FORMAT = '%H:%M'
    DATETIME_FORMAT = '%d/%m/%Y %H:%M'

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
    'default': DevelopmentConfig
}