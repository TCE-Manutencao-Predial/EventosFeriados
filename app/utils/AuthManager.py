# app/utils/AuthManager.py
import requests
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from threading import Lock
from ..config import DATA_DIR

class AuthManager:
    """
    Gerenciador de autenticação usando API externa do HelpDesk Monitor
    Valida usuários htpasswd e verifica se possuem a função EVENTOS_FERIADOS
    Implementa cache persistente para funcionar offline
    """
    
    _instance = None
    _lock = Lock()
    
    # Configurações
    API_BASE_URL = "https://automacao.tce.go.gov.br/helpdeskmonitor"
    FUNCAO_REQUERIDA = "EVENTOS_FERIADOS"
    CACHE_FILE = os.path.join(DATA_DIR, 'usuarios_autorizados_cache.json')
    CACHE_EXPIRATION_HOURS = 24  # Cache válido por 24 horas
    REQUEST_TIMEOUT = 5  # Timeout de 5 segundos
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.AuthManager')
        self.cache = self._carregar_cache()
        self.logger.info("AuthManager inicializado")
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do gerenciador (Singleton)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _carregar_cache(self) -> Dict:
        """Carrega o cache de usuários autorizados do arquivo"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    self.logger.info(f"Cache carregado: {len(cache.get('usuarios', {}))} usuários")
                    return cache
            except Exception as e:
                self.logger.error(f"Erro ao carregar cache: {e}")
        
        return {
            'ultima_atualizacao': None,
            'usuarios': {}  # {username: {nome, cargo, email, telefone, valido_ate}}
        }
    
    def _salvar_cache(self) -> bool:
        """Salva o cache de usuários autorizados no arquivo"""
        try:
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
            
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Cache salvo: {len(self.cache.get('usuarios', {}))} usuários")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {e}")
            return False
    
    def _cache_expirado(self) -> bool:
        """Verifica se o cache está expirado"""
        if not self.cache.get('ultima_atualizacao'):
            return True
        
        try:
            ultima_atualizacao = datetime.fromisoformat(self.cache['ultima_atualizacao'])
            expiracao = ultima_atualizacao + timedelta(hours=self.CACHE_EXPIRATION_HOURS)
            return datetime.now() > expiracao
        except Exception:
            return True
    
    def _consultar_api_usuarios_funcao(self) -> Optional[Dict]:
        """
        Consulta a API para obter técnicos com a função EVENTOS_FERIADOS
        
        Returns:
            Dict com dados dos técnicos ou None em caso de erro
        """
        try:
            url = f"{self.API_BASE_URL}/api/tecnicos/por_funcao/{self.FUNCAO_REQUERIDA}"
            self.logger.info(f"Consultando API: {url}")
            
            response = requests.get(url, timeout=self.REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"API retornou {data.get('total', 0)} técnicos com função {self.FUNCAO_REQUERIDA}")
            
            return data
            
        except requests.exceptions.Timeout:
            self.logger.warning("Timeout ao consultar API - usando cache")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"Erro de conexão com API: {e} - usando cache")
            return None
        except Exception as e:
            self.logger.error(f"Erro ao consultar API: {e}")
            return None
    
    def _atualizar_cache_da_api(self) -> bool:
        """
        Atualiza o cache consultando a API externa
        
        Returns:
            True se conseguiu atualizar, False caso contrário
        """
        data = self._consultar_api_usuarios_funcao()
        
        if not data:
            return False
        
        # Processar técnicos retornados
        usuarios_autorizados = {}
        
        for tecnico in data.get('tecnicos', []):
            usuario_htpasswd = tecnico.get('usuario_htpasswd')
            
            # Apenas técnicos com htpasswd configurado
            if not usuario_htpasswd:
                continue
            
            # Verificar se está disponível (não de férias e não indisponível)
            disponivel = tecnico.get('disponivel', False)
            ferias = tecnico.get('ferias', False)
            
            if not disponivel or ferias:
                self.logger.debug(f"Técnico {tecnico.get('nome')} não está disponível ou está de férias")
                continue
            
            # Adicionar ao cache
            usuarios_autorizados[usuario_htpasswd] = {
                'nome': tecnico.get('nome', ''),
                'cargo': tecnico.get('cargo', ''),
                'email': tecnico.get('email', ''),
                'telefone': tecnico.get('telefone_principal', ''),
                'disponivel': disponivel,
                'valido_ate': (datetime.now() + timedelta(hours=self.CACHE_EXPIRATION_HOURS)).isoformat()
            }
        
        # Atualizar cache
        self.cache['usuarios'] = usuarios_autorizados
        self.cache['ultima_atualizacao'] = datetime.now().isoformat()
        self.cache['funcao'] = self.FUNCAO_REQUERIDA
        
        # Salvar no arquivo
        self._salvar_cache()
        
        self.logger.info(f"Cache atualizado com {len(usuarios_autorizados)} usuários autorizados")
        return True
    
    def verificar_autorizacao(self, username: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verifica se um usuário está autorizado a acessar o sistema
        
        Args:
            username: Nome de usuário htpasswd
            
        Returns:
            Tupla (autorizado, dados_usuario)
            - autorizado: True se o usuário tem permissão, False caso contrário
            - dados_usuario: Dict com dados do usuário ou None
        """
        if not username:
            return False, None
        
        # Normalizar username (lowercase)
        username = username.lower().strip()
        
        # Tentar atualizar cache se estiver expirado
        if self._cache_expirado():
            self.logger.info("Cache expirado, tentando atualizar da API")
            self._atualizar_cache_da_api()
        
        # Verificar no cache
        usuario = self.cache.get('usuarios', {}).get(username)
        
        if usuario:
            # Verificar se o registro do usuário ainda é válido
            try:
                valido_ate = datetime.fromisoformat(usuario.get('valido_ate', ''))
                if datetime.now() > valido_ate:
                    self.logger.warning(f"Registro do usuário {username} expirado no cache")
                    # Tentar atualizar
                    if self._atualizar_cache_da_api():
                        usuario = self.cache.get('usuarios', {}).get(username)
                        if not usuario:
                            return False, None
                    else:
                        # API indisponível, manter acesso do cache expirado por segurança
                        self.logger.info(f"API indisponível, mantendo acesso do usuário {username} via cache expirado")
            except Exception:
                pass
            
            # Log removido para reduzir verbosidade
            # self.logger.info(f"Usuário {username} autorizado via cache")
            return True, usuario
        
        # Não encontrado no cache, tentar API
        self.logger.info(f"Usuário {username} não encontrado no cache, consultando API")
        if self._atualizar_cache_da_api():
            usuario = self.cache.get('usuarios', {}).get(username)
            if usuario:
                self.logger.info(f"Usuário {username} autorizado via API")
                return True, usuario
        
        self.logger.warning(f"Usuário {username} não autorizado (não possui função {self.FUNCAO_REQUERIDA})")
        return False, None
    
    def listar_usuarios_autorizados(self) -> Dict:
        """
        Lista todos os usuários autorizados no cache
        
        Returns:
            Dict com dados do cache
        """
        return {
            'total': len(self.cache.get('usuarios', {})),
            'ultima_atualizacao': self.cache.get('ultima_atualizacao'),
            'cache_expirado': self._cache_expirado(),
            'funcao_requerida': self.FUNCAO_REQUERIDA,
            'usuarios': list(self.cache.get('usuarios', {}).values())
        }
    
    def forcar_atualizacao_cache(self) -> bool:
        """
        Força a atualização do cache consultando a API
        
        Returns:
            True se conseguiu atualizar, False caso contrário
        """
        self.logger.info("Forçando atualização do cache")
        return self._atualizar_cache_da_api()
    
    def limpar_cache(self) -> bool:
        """
        Limpa o cache de usuários autorizados
        
        Returns:
            True se conseguiu limpar, False caso contrário
        """
        try:
            self.cache = {
                'ultima_atualizacao': None,
                'usuarios': {}
            }
            self._salvar_cache()
            self.logger.info("Cache limpo com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao limpar cache: {e}")
            return False
