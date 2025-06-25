# app/routes/api_feriados.py
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

api_feriados_bp = Blueprint('api_feriados', __name__)
logger = logging.getLogger('EventosFeriados.api_feriados')

@api_feriados_bp.route('/feriados', methods=['GET'])
def listar_feriados():
    """Lista todos os feriados ou filtra por ano/mês"""
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de feriados não disponível'}), 503
        
        # Obter parâmetros de filtro
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        
        feriados = gerenciador.listar_feriados(ano=ano, mes=mes)
        
        return jsonify({
            'sucesso': True,
            'total': len(feriados),
            'feriados': feriados
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar feriados: {e}")
        return jsonify({'erro': str(e)}), 500

@api_feriados_bp.route('/feriados/<feriado_id>', methods=['GET'])
def obter_feriado(feriado_id):
    """Obtém um feriado específico"""
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de feriados não disponível'}), 503
        
        feriado = gerenciador.obter_feriado(feriado_id)
        
        if not feriado:
            return jsonify({'erro': 'Feriado não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'feriado': feriado
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter feriado: {e}")
        return jsonify({'erro': str(e)}), 500

@api_feriados_bp.route('/feriados', methods=['POST'])
def adicionar_feriado():
    """Adiciona um novo feriado"""
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de feriados não disponível'}), 503
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome', 'dia', 'mes', 'ano', 'hora_inicio', 'hora_fim']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({'erro': f'Campo obrigatório ausente: {campo}'}), 400
        
        # Adicionar feriado
        novo_feriado = gerenciador.adicionar_feriado(dados)
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Feriado adicionado com sucesso',
            'feriado': novo_feriado
        }), 201
        
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao adicionar feriado: {e}")
        return jsonify({'erro': str(e)}), 500

@api_feriados_bp.route('/feriados/<feriado_id>', methods=['PUT'])
def atualizar_feriado(feriado_id):
    """Atualiza um feriado existente"""
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de feriados não disponível'}), 503
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualizar feriado
        feriado_atualizado = gerenciador.atualizar_feriado(feriado_id, dados)
        
        if not feriado_atualizado:
            return jsonify({'erro': 'Feriado não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Feriado atualizado com sucesso',
            'feriado': feriado_atualizado
        })
        
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar feriado: {e}")
        return jsonify({'erro': str(e)}), 500

@api_feriados_bp.route('/feriados/<feriado_id>', methods=['DELETE'])
def remover_feriado(feriado_id):
    """Remove um feriado"""
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de feriados não disponível'}), 503
        
        sucesso = gerenciador.remover_feriado(feriado_id)
        
        if not sucesso:
            return jsonify({'erro': 'Feriado não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Feriado removido com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover feriado: {e}")
        return jsonify({'erro': str(e)}), 500

@api_feriados_bp.route('/feriados/verificar', methods=['GET'])
def verificar_feriado():
    """Verifica se uma data específica é feriado"""
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de feriados não disponível'}), 503
        
        # Obter parâmetros
        dia = request.args.get('dia', type=int)
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        if not all([dia, mes, ano]):
            return jsonify({'erro': 'Parâmetros dia, mes e ano são obrigatórios'}), 400
        
        feriado = gerenciador.verificar_feriado(dia, mes, ano)
        
        return jsonify({
            'sucesso': True,
            'e_feriado': feriado is not None,
            'feriado': feriado
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar feriado: {e}")
        return jsonify({'erro': str(e)}), 500