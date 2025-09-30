# app/config.py
import os
import logging
from logging.handlers import RotatingFileHandler

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
# Prioridade: variavel ambiente EVENTOS_FERIADOS_LOG_DIR > /var/softwaresTCE/logs/EventosFeriados > fallback local
_LOG_DIR_ENV = os.environ.get('EVENTOS_FERIADOS_LOG_DIR')
LOG_DIR = _LOG_DIR_ENV or '/var/softwaresTCE/logs/EventosFeriados'

try:
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
except PermissionError:
    # Fallback local caso não tenha permissão em /var ou caminho customizado
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    # Qualquer erro inesperado também leva ao fallback local
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

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
    # LIMITES DE SEGURANÇA (configurável via env CLP_AUD_MIN_HORA): 05:30 às 23:59 (mantém intervalos válidos para o CLP)
    'TAGS_EVENTOS_AUDITORIO': {
        'DIA': 'N91',          # N91:0-9 - dias dos eventos  
        'MES': 'N92',          # N92:0-9 - meses dos eventos
        'HORA_INICIO': 'N93',  # N93:0-9 - hora de início (com ajuste automático para todos os eventos)
        'MIN_INICIO': 'N94',   # N94:0-9 - minuto de início
        'HORA_FIM': 'N95',     # N95:0-9 - hora de fim (com ajuste automático para todos os eventos)
        'MIN_FIM': 'N96'       # N96:0-9 - minuto de fim
    },
    # Hora mínima para início após ajuste no Auditório (formato HH:MM)
    # Pode ser definido por variável de ambiente CLP_AUD_MIN_HORA (ex.: '05:30')
    'AUDITORIO_HORA_MINIMA': os.environ.get('CLP_AUD_MIN_HORA', '05:30'),
    'MAX_EVENTOS': 10,  # Máximo de eventos do Auditório
    'LOCAIS_GERENCIADOS': ['Auditório Nobre', 'Foyer do Auditório']  # Locais gerenciados por este CLP
}

def setup_logging():
    """Configura o sistema de logging da aplicação.

    Evita adicionar handlers duplicados se chamada múltiplas vezes (ex.: em ambientes WSGI com vários workers).
    """
    global LOG_DIR, LOG_FILE
    logger = logging.getLogger('EventosFeriados')

    if not logger.handlers:
        # Garante diretório (caso algo tenha removido após import)
        try:
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR, exist_ok=True)
        except Exception as e:
            fallback_dir = os.path.join(BASE_DIR, 'logs')
            try:
                os.makedirs(fallback_dir, exist_ok=True)
                logger.warning(f"Falha ao garantir LOG_DIR '{LOG_DIR}': {e}. Usando fallback '{fallback_dir}'.")
                LOG_DIR = fallback_dir
                LOG_FILE = os.path.join(LOG_DIR, 'eventos_feriados.log')
            except Exception:
                pass

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

# Configuração da API de WhatsApp (HelpDeskMonitor) usada para notificar por função
# Valores podem (e devem) ser definidos por variáveis de ambiente em produção
#   WHATSAPP_API_HOST, WHATSAPP_API_TOKEN, WHATSAPP_API_ORIGEM, WHATSAPP_APENAS_DISPONIVEIS, WHATSAPP_API_TIMEOUT
WHATSAPP_API = {
    # Host padrão definido em código para dispensar variáveis de ambiente
    'HOST': os.environ.get('WHATSAPP_API_HOST', 'https://automacao.tce.go.gov.br').rstrip('/'),
    # Token padrão definido em código (substitua se necessário)
    'TOKEN': os.environ.get('WHATSAPP_API_TOKEN', 'whatsapp_api_token_2025_helpdeskmonitor_tce'),
    'ORIGEM': os.environ.get('WHATSAPP_API_ORIGEM', 'EVENTOS_FERIADOS'),
    'APENAS_DISPONIVEIS': os.environ.get('WHATSAPP_APENAS_DISPONIVEIS', 'true').lower() == 'true',
        # Preferir processamento assíncrono no backend
        'ASYNC': os.getenv('WHATSAPP_API_ASYNC', 'true').lower() == 'true',
    'TIMEOUT': int(os.environ.get('WHATSAPP_API_TIMEOUT', '60')),
}