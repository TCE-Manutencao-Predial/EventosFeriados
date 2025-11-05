# app/routes/api_notificacoes.py
"""
API REST para Histórico de Notificações
Endpoints para consultar notificações enviadas via WhatsApp e Email
"""
from flask import Blueprint, request, jsonify
import logging
from ..utils.GerenciadorHistoricoNotificacoes import GerenciadorHistoricoNotificacoes
from ..utils.auth_decorators import require_auth

api_notificacoes_bp = Blueprint('api_notificacoes', __name__)
logger = logging.getLogger('EventosFeriados.api_notificacoes')

# Log de inicialização do blueprint
logger.info("Blueprint api_notificacoes inicializado")

@api_notificacoes_bp.route('/notificacoes/historico', methods=['GET'])
@require_auth
def listar_historico():
    """
    Lista o histórico de notificações com filtros opcionais
    
    Query Parameters:
        - limite: número máximo de registros (padrão: 100)
        - offset: deslocamento para paginação (padrão: 0)
        - status: filtrar por status (sucesso, erro, pendente)
        - canal: filtrar por canal (whatsapp, email)
        - tipo: filtrar por tipo de notificação
        - data_inicio: data/hora início (ISO format)
        - data_fim: data/hora fim (ISO format)
    """
    logger.info(f"Requisição recebida em /notificacoes/historico com params: {request.args}")
    try:
        # Parâmetros de paginação
        limite = request.args.get('limite', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Filtros opcionais
        status = request.args.get('status')
        canal = request.args.get('canal')
        tipo = request.args.get('tipo')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Limitar o máximo de registros por requisição
        if limite > 500:
            limite = 500
        
        gerenciador = GerenciadorHistoricoNotificacoes.get_instance()
        
        # Buscar notificações
        notificacoes = gerenciador.buscar_notificacoes(
            limite=limite,
            offset=offset,
            status=status,
            canal=canal,
            tipo=tipo,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        # Contar total de registros
        total = gerenciador.contar_notificacoes(
            status=status,
            canal=canal,
            tipo=tipo,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        return jsonify({
            'success': True,
            'data': notificacoes,
            'total': total,
            'limite': limite,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar histórico de notificações: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar histórico de notificações'
        }), 500

@api_notificacoes_bp.route('/notificacoes/estatisticas', methods=['GET'])
@require_auth
def obter_estatisticas():
    """
    Obtém estatísticas de notificações
    
    Query Parameters:
        - dias: número de dias para análise (padrão: 7)
    """
    logger.info(f"Requisição recebida em /notificacoes/estatisticas com params: {request.args}")
    try:
        dias = request.args.get('dias', 7, type=int)
        
        # Limitar dias
        if dias > 365:
            dias = 365
        
        gerenciador = GerenciadorHistoricoNotificacoes.get_instance()
        estatisticas = gerenciador.obter_estatisticas(dias=dias)
        
        return jsonify({
            'success': True,
            'data': estatisticas
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter estatísticas'
        }), 500

@api_notificacoes_bp.route('/notificacoes/limpar-antigos', methods=['POST'])
@require_auth
def limpar_antigos():
    """
    Remove notificações antigas
    
    JSON Body:
        - dias: dias de retenção (padrão: 90)
    """
    try:
        dados = request.get_json() or {}
        dias = dados.get('dias', 90)
        
        # Validação
        if dias < 30:
            return jsonify({
                'success': False,
                'error': 'Mínimo de 30 dias de retenção'
            }), 400
        
        gerenciador = GerenciadorHistoricoNotificacoes.get_instance()
        removidos = gerenciador.limpar_antigos(dias=dias)
        
        return jsonify({
            'success': True,
            'message': f'{removidos} notificações removidas',
            'removidos': removidos
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao limpar notificações antigas: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao limpar notificações antigas'
        }), 500

@api_notificacoes_bp.route('/notificacoes/test', methods=['GET'])
def test_route():
    """Rota de teste para verificar se o blueprint está funcionando"""
    logger.info("Rota de teste /notificacoes/test acessada!")
    return jsonify({
        'success': True,
        'message': 'Blueprint api_notificacoes está funcionando!',
        'rotas_disponiveis': [
            '/notificacoes/historico',
            '/notificacoes/estatisticas',
            '/notificacoes/limpar-antigos',
            '/notificacoes/test'
        ]
    }), 200

# Log das rotas registradas
logger.info("Rotas do blueprint api_notificacoes registradas:")
for rule in ['notificacoes/historico', 'notificacoes/estatisticas', 'notificacoes/limpar-antigos', 'notificacoes/test']:
    logger.info(f"  - {rule}")
