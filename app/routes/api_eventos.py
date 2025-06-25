# app/routes/api_eventos.py
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

api_eventos_bp = Blueprint('api_eventos', __name__)
logger = logging.getLogger('EventosFeriados.api_eventos')

@api_eventos_bp.route('/eventos', methods=['GET'])
def listar_eventos():
    """Lista todos os eventos ou filtra por ano/mês/local"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        # Obter parâmetros de filtro
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        local = request.args.get('local')
        
        eventos = gerenciador.listar_eventos(ano=ano, mes=mes, local=local)
        
        return jsonify({
            'sucesso': True,
            'total': len(eventos),
            'eventos': eventos
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/<evento_id>', methods=['GET'])
def obter_evento(evento_id):
    """Obtém um evento específico"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        evento = gerenciador.obter_evento(evento_id)
        
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'evento': evento
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter evento: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos', methods=['POST'])
def adicionar_evento():
    """Adiciona um novo evento"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome', 'local', 'dia', 'mes', 'ano', 'hora_inicio', 'hora_fim']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({'erro': f'Campo obrigatório ausente: {campo}'}), 400
        
        # Adicionar evento
        novo_evento = gerenciador.adicionar_evento(dados)
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Evento adicionado com sucesso',
            'evento': novo_evento
        }), 201
        
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao adicionar evento: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/<evento_id>', methods=['PUT'])
def atualizar_evento(evento_id):
    """Atualiza um evento existente"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualizar evento
        evento_atualizado = gerenciador.atualizar_evento(evento_id, dados)
        
        if not evento_atualizado:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Evento atualizado com sucesso',
            'evento': evento_atualizado
        })
        
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar evento: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/<evento_id>', methods=['DELETE'])
def remover_evento(evento_id):
    """Remove um evento"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        sucesso = gerenciador.remover_evento(evento_id)
        
        if not sucesso:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Evento removido com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover evento: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/por-data', methods=['GET'])
def eventos_por_data():
    """Lista eventos de uma data específica"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        # Obter parâmetros
        dia = request.args.get('dia', type=int)
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        if not all([dia, mes, ano]):
            return jsonify({'erro': 'Parâmetros dia, mes e ano são obrigatórios'}), 400
        
        eventos = gerenciador.obter_eventos_por_data(dia, mes, ano)
        
        return jsonify({
            'sucesso': True,
            'total': len(eventos),
            'data': f'{dia:02d}/{mes:02d}/{ano}',
            'eventos': eventos
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar eventos por data: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/por-local/<local>', methods=['GET'])
def eventos_por_local(local):
    """Lista eventos de um local específico"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        # Obter parâmetros opcionais
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        eventos = gerenciador.obter_eventos_por_local(local, mes=mes, ano=ano)
        
        return jsonify({
            'sucesso': True,
            'total': len(eventos),
            'local': local,
            'eventos': eventos
        })
        
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao buscar eventos por local: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/locais', methods=['GET'])
def listar_locais():
    """Lista todos os locais disponíveis para eventos"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        locais = gerenciador.obter_locais_disponiveis()
        
        return jsonify({
            'sucesso': True,
            'locais': locais
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar locais: {e}")
        return jsonify({'erro': str(e)}), 500