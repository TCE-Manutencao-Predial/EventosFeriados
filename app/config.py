# app/config.py
import os
import logging

# Configuração do diretório base
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'dados')

# Garante que o diretório de dados existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

ROUTES_PREFIX = '/EventosFeriados'

# Configuração dos diretórios de logs
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'eventos_feriados.log')

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