# app/routes/api_auth.py
from flask import Blueprint, jsonify, g
import logging

api_auth_bp = Blueprint('api_auth', __name__)
logger = logging.getLogger(__name__)

from ..utils.auth_decorators import require_auth_api

@api_auth_bp.route('/auth/status', methods=['GET'])
@require_auth_api
def auth_status():
    """Retorna status da autenticação e informações do usuário"""
    try:
        from ..utils.AuthManager import AuthManager
        auth_manager = AuthManager.get_instance()
        
        return jsonify({
            'autenticado': True,
            'usuario': g.current_user,
            'cache_valido': not auth_manager._cache_expirado(),
            'ultima_atualizacao': auth_manager.cache.get('ultima_atualizacao')
        })
    except Exception as e:
        logger.error(f"Erro ao obter status de autenticação: {e}")
        return jsonify({'erro': str(e)}), 500

@api_auth_bp.route('/auth/cache/atualizar', methods=['POST'])
@require_auth_api
def atualizar_cache():
    """Força atualização do cache de usuários autorizados"""
    try:
        from ..utils.AuthManager import AuthManager
        auth_manager = AuthManager.get_instance()
        
        sucesso = auth_manager._atualizar_cache_da_api()
        
        if sucesso:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Cache atualizado com sucesso',
                'usuarios_autorizados': len(auth_manager.cache.get('usuarios', [])),
                'ultima_atualizacao': auth_manager.cache.get('ultima_atualizacao')
            })
        else:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Falha ao atualizar cache da API'
            }), 500
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {e}")
        return jsonify({'erro': str(e)}), 500

@api_auth_bp.route('/auth/usuarios', methods=['GET'])
@require_auth_api
def listar_usuarios_autorizados():
    """Lista usuários autorizados (do cache)"""
    try:
        from ..utils.AuthManager import AuthManager
        auth_manager = AuthManager.get_instance()
        
        usuarios = auth_manager.cache.get('usuarios', [])
        
        return jsonify({
            'usuarios': usuarios,
            'total': len(usuarios),
            'cache_valido': not auth_manager._cache_expirado(),
            'ultima_atualizacao': auth_manager.cache.get('ultima_atualizacao')
        })
    except Exception as e:
        logger.error(f"Erro ao listar usuários autorizados: {e}")
        return jsonify({'erro': str(e)}), 500

@api_auth_bp.route('/auth/cache/limpar', methods=['POST'])
@require_auth_api
def limpar_cache():
    """Limpa o cache forçando recarga na próxima autenticação"""
    try:
        from ..utils.AuthManager import AuthManager
        auth_manager = AuthManager.get_instance()
        
        # Limpa o cache
        auth_manager.cache = {
            'usuarios': [],
            'ultima_atualizacao': None
        }
        auth_manager._salvar_cache()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Cache limpo com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        return jsonify({'erro': str(e)}), 500
