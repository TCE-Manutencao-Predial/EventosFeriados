# app/utils/auth_decorators.py
from functools import wraps
from flask import request, Response, jsonify, g
import logging
from .AuthManager import AuthManager
import base64

logger = logging.getLogger('EventosFeriados.auth_decorators')

def require_auth(f):
    """
    Decorador que requer autenticação HTTP Basic
    Valida credenciais contra a API externa do HelpDesk Monitor
    Verifica se o usuário possui a função EVENTOS_FERIADOS
    Usa cache persistente quando a API está indisponível
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        
        # Verificar se há credenciais Basic Auth
        if not auth or not auth.username:
            logger.warning("Tentativa de acesso sem credenciais")
            return Response(
                'Acesso negado. Autenticação necessária.\n'
                'Por favor, forneça usuário e senha.',
                401,
                {'WWW-Authenticate': 'Basic realm="EventosFeriados - Acesso Restrito"'}
            )
        
        username = auth.username
        
        # Verificar autorização via AuthManager
        auth_manager = AuthManager.get_instance()
        autorizado, dados_usuario = auth_manager.verificar_autorizacao(username)
        
        if not autorizado:
            logger.warning(f"Acesso negado para usuário: {username} (não possui função EVENTOS_FERIADOS)")
            return Response(
                f'Acesso negado.\n'
                f'Usuário "{username}" não possui permissão para acessar este sistema.\n'
                f'Apenas usuários com a função EVENTOS_FERIADOS podem acessar.',
                403,
                {'WWW-Authenticate': 'Basic realm="EventosFeriados - Acesso Restrito"'}
            )
        
        # Armazenar dados do usuário no contexto da requisição
        g.current_user = {
            'username': username,
            'nome': dados_usuario.get('nome', username) if dados_usuario else username,
            'cargo': dados_usuario.get('cargo', '') if dados_usuario else '',
            'email': dados_usuario.get('email', '') if dados_usuario else ''
        }
        
        # Log removido para reduzir verbosidade
        # logger.info(f"Acesso autorizado para usuário: {username} ({g.current_user['nome']})")
        
        # Executar a função decorada
        return f(*args, **kwargs)
    
    return decorated_function


def require_auth_api(f):
    """
    Decorador específico para rotas de API
    Retorna JSON em caso de erro de autenticação
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        
        # Verificar se há credenciais Basic Auth
        if not auth or not auth.username:
            logger.warning("Tentativa de acesso à API sem credenciais")
            return jsonify({
                'erro': 'Autenticação necessária',
                'mensagem': 'Por favor, forneça usuário e senha via HTTP Basic Auth'
            }), 401
        
        username = auth.username
        
        # Verificar autorização via AuthManager
        auth_manager = AuthManager.get_instance()
        autorizado, dados_usuario = auth_manager.verificar_autorizacao(username)
        
        if not autorizado:
            logger.warning(f"Acesso negado à API para usuário: {username}")
            return jsonify({
                'erro': 'Acesso negado',
                'mensagem': f'Usuário "{username}" não possui permissão para acessar este sistema',
                'funcao_requerida': 'EVENTOS_FERIADOS'
            }), 403
        
        # Armazenar dados do usuário no contexto da requisição
        g.current_user = {
            'username': username,
            'nome': dados_usuario.get('nome', username) if dados_usuario else username,
            'cargo': dados_usuario.get('cargo', '') if dados_usuario else '',
            'email': dados_usuario.get('email', '') if dados_usuario else ''
        }
        
        logger.info(f"Acesso à API autorizado para usuário: {username}")
        
        # Executar a função decorada
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    Decorador que tenta autenticar, mas não bloqueia se não houver credenciais
    Usado para endpoints que podem funcionar com ou sem autenticação
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        
        if auth and auth.username:
            username = auth.username
            auth_manager = AuthManager.get_instance()
            autorizado, dados_usuario = auth_manager.verificar_autorizacao(username)
            
            if autorizado:
                g.current_user = {
                    'username': username,
                    'nome': dados_usuario.get('nome', username) if dados_usuario else username,
                    'cargo': dados_usuario.get('cargo', '') if dados_usuario else '',
                    'email': dados_usuario.get('email', '') if dados_usuario else ''
                }
                logger.info(f"Usuário autenticado: {username}")
            else:
                g.current_user = None
        else:
            g.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function
