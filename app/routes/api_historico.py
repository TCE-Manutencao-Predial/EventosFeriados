# app/routes/api_historico.py
"""
API para consulta de histórico de alterações
"""
from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime, timedelta
import logging
import os
from ..utils.auth_decorators import require_auth_api

api_historico_bp = Blueprint('api_historico', __name__)
logger = logging.getLogger('EventosFeriados.api_historico')

@api_historico_bp.route('/historico', methods=['GET'])
@require_auth_api
def listar_historico():
    """
    Lista o histórico de alterações com filtros
    
    Query Parameters:
    - tipo_entidade: feriado ou evento
    - entidade_id: ID específico
    - usuario: Filtrar por usuário
    - operacao: criar, editar ou excluir
    - data_inicio: Data inicial (ISO format)
    - data_fim: Data final (ISO format)
    - limite: Número de registros (padrão: 100)
    - offset: Offset para paginação (padrão: 0)
    """
    try:
        from ..utils.GerenciadorHistorico import GerenciadorHistorico
        gerenciador = GerenciadorHistorico.get_instance()
        
        # Obter parâmetros
        tipo_entidade = request.args.get('tipo_entidade')
        entidade_id = request.args.get('entidade_id')
        usuario = request.args.get('usuario')
        operacao = request.args.get('operacao')
        limite = request.args.get('limite', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Datas
        data_inicio = None
        data_fim = None
        
        if request.args.get('data_inicio'):
            try:
                data_inicio = datetime.fromisoformat(request.args.get('data_inicio'))
            except ValueError:
                return jsonify({'erro': 'Formato de data_inicio inválido'}), 400
        
        if request.args.get('data_fim'):
            try:
                data_fim = datetime.fromisoformat(request.args.get('data_fim'))
            except ValueError:
                return jsonify({'erro': 'Formato de data_fim inválido'}), 400
        
        # Consultar histórico
        historico = gerenciador.obter_historico(
            tipo_entidade=tipo_entidade,
            entidade_id=entidade_id,
            usuario=usuario,
            operacao=operacao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limite=limite,
            offset=offset
        )
        
        return jsonify({
            'sucesso': True,
            'total': len(historico),
            'limite': limite,
            'offset': offset,
            'registros': historico
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar histórico: {e}")
        return jsonify({'erro': str(e)}), 500


@api_historico_bp.route('/historico/<int:registro_id>', methods=['GET'])
@require_auth_api
def obter_registro_historico(registro_id):
    """Obtém um registro específico do histórico"""
    try:
        from ..utils.GerenciadorHistorico import GerenciadorHistorico
        gerenciador = GerenciadorHistorico.get_instance()
        
        # Buscar registro
        historico = gerenciador.obter_historico(limite=1, offset=0)
        
        # TODO: Implementar busca por ID específico
        # Por enquanto, retornar erro
        return jsonify({'erro': 'Endpoint em implementação'}), 501
        
    except Exception as e:
        logger.error(f"Erro ao obter registro {registro_id}: {e}")
        return jsonify({'erro': str(e)}), 500


@api_historico_bp.route('/historico/entidade/<tipo_entidade>/<entidade_id>', methods=['GET'])
@require_auth_api
def historico_entidade(tipo_entidade, entidade_id):
    """
    Obtém o histórico completo de uma entidade
    
    Path Parameters:
    - tipo_entidade: feriado ou evento
    - entidade_id: ID da entidade
    
    Query Parameters:
    - limite: Número de registros (padrão: 50)
    """
    try:
        if tipo_entidade not in ['feriado', 'evento']:
            return jsonify({'erro': 'tipo_entidade deve ser "feriado" ou "evento"'}), 400
        
        from ..utils.GerenciadorHistorico import GerenciadorHistorico
        gerenciador = GerenciadorHistorico.get_instance()
        
        limite = request.args.get('limite', 50, type=int)
        
        historico = gerenciador.obter_historico_entidade(
            tipo_entidade=tipo_entidade,
            entidade_id=entidade_id,
            limite=limite
        )
        
        return jsonify({
            'sucesso': True,
            'tipo_entidade': tipo_entidade,
            'entidade_id': entidade_id,
            'total_alteracoes': len(historico),
            'historico': historico
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico da entidade: {e}")
        return jsonify({'erro': str(e)}), 500


@api_historico_bp.route('/historico/estatisticas', methods=['GET'])
@require_auth_api
def estatisticas_historico():
    """
    Obtém estatísticas do histórico
    
    Query Parameters:
    - data_inicio: Data inicial (ISO format)
    - data_fim: Data final (ISO format)
    - periodo: atalho para períodos comuns (hoje, semana, mes, ano)
    """
    try:
        from ..utils.GerenciadorHistorico import GerenciadorHistorico
        gerenciador = GerenciadorHistorico.get_instance()
        
        # Definir período
        data_inicio = None
        data_fim = None
        
        periodo = request.args.get('periodo')
        
        if periodo:
            agora = datetime.now()
            if periodo == 'hoje':
                data_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
            elif periodo == 'semana':
                data_inicio = agora - timedelta(days=7)
            elif periodo == 'mes':
                data_inicio = agora - timedelta(days=30)
            elif periodo == 'ano':
                data_inicio = agora - timedelta(days=365)
        else:
            if request.args.get('data_inicio'):
                try:
                    data_inicio = datetime.fromisoformat(request.args.get('data_inicio'))
                except ValueError:
                    return jsonify({'erro': 'Formato de data_inicio inválido'}), 400
            
            if request.args.get('data_fim'):
                try:
                    data_fim = datetime.fromisoformat(request.args.get('data_fim'))
                except ValueError:
                    return jsonify({'erro': 'Formato de data_fim inválido'}), 400
        
        estatisticas = gerenciador.obter_estatisticas(
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        return jsonify({
            'sucesso': True,
            'periodo': {
                'data_inicio': data_inicio.isoformat() if data_inicio else None,
                'data_fim': data_fim.isoformat() if data_fim else None,
                'descricao': periodo or 'personalizado'
            },
            'estatisticas': estatisticas
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'erro': str(e)}), 500


@api_historico_bp.route('/historico/exportar', methods=['POST'])
@require_auth_api
def exportar_historico():
    """
    Exporta o histórico para arquivo
    
    Body JSON:
    {
        "formato": "json" ou "csv",
        "filtros": {
            "tipo_entidade": "feriado",
            "data_inicio": "2025-01-01T00:00:00",
            ...
        }
    }
    """
    try:
        from ..utils.GerenciadorHistorico import GerenciadorHistorico
        from ..config import DATA_DIR
        import uuid
        
        gerenciador = GerenciadorHistorico.get_instance()
        
        dados = request.get_json()
        formato = dados.get('formato', 'json')
        filtros = dados.get('filtros', {})
        
        if formato not in ['json', 'csv']:
            return jsonify({'erro': 'Formato deve ser "json" ou "csv"'}), 400
        
        # Processar filtros de data
        if 'data_inicio' in filtros and isinstance(filtros['data_inicio'], str):
            try:
                filtros['data_inicio'] = datetime.fromisoformat(filtros['data_inicio'])
            except:
                pass
        
        if 'data_fim' in filtros and isinstance(filtros['data_fim'], str):
            try:
                filtros['data_fim'] = datetime.fromisoformat(filtros['data_fim'])
            except:
                pass
        
        # Gerar nome de arquivo único
        arquivo_id = str(uuid.uuid4())[:8]
        nome_arquivo = f"historico_export_{arquivo_id}.{formato}"
        caminho_arquivo = os.path.join(DATA_DIR, nome_arquivo)
        
        # Exportar
        sucesso = gerenciador.exportar_historico(
            caminho_arquivo=caminho_arquivo,
            formato=formato,
            **filtros
        )
        
        if sucesso:
            # Enviar arquivo
            return send_file(
                caminho_arquivo,
                as_attachment=True,
                download_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{formato}"
            )
        else:
            return jsonify({'erro': 'Falha ao exportar histórico'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao exportar histórico: {e}")
        return jsonify({'erro': str(e)}), 500


@api_historico_bp.route('/historico/limpar-antigo', methods=['POST'])
@require_auth_api
def limpar_historico_antigo():
    """
    Remove registros antigos do histórico
    
    Body JSON:
    {
        "dias": 365
    }
    """
    try:
        from ..utils.GerenciadorHistorico import GerenciadorHistorico
        gerenciador = GerenciadorHistorico.get_instance()
        
        dados = request.get_json() or {}
        dias = dados.get('dias', 365)
        
        if not isinstance(dias, int) or dias < 1:
            return jsonify({'erro': 'Parâmetro "dias" deve ser um inteiro positivo'}), 400
        
        registros_removidos = gerenciador.limpar_historico_antigo(dias=dias)
        
        return jsonify({
            'sucesso': True,
            'registros_removidos': registros_removidos,
            'dias_mantidos': dias
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar histórico antigo: {e}")
        return jsonify({'erro': str(e)}), 500


@api_historico_bp.route('/historico/recentes', methods=['GET'])
@require_auth_api
def historico_recentes():
    """
    Obtém as alterações mais recentes
    
    Query Parameters:
    - limite: Número de registros (padrão: 20)
    """
    try:
        from ..utils.GerenciadorHistorico import GerenciadorHistorico
        gerenciador = GerenciadorHistorico.get_instance()
        
        limite = request.args.get('limite', 20, type=int)
        
        historico = gerenciador.obter_historico(limite=limite)
        
        return jsonify({
            'sucesso': True,
            'total': len(historico),
            'registros': historico
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico recente: {e}")
        return jsonify({'erro': str(e)}), 500
