# app/routes/api_clp.py
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from ..utils.IntegracaoCLP import IntegracaoCLP

api_clp_bp = Blueprint('api_clp', __name__)
logger = logging.getLogger('EventosFeriados.api_clp')

def get_integracao_clp():
    """Obtém instância do integrador CLP"""
    gerenciador_feriados = current_app.config['GERENCIADOR_FERIADOS']
    gerenciador_eventos = current_app.config['GERENCIADOR_EVENTOS']
    
    if not gerenciador_feriados or not gerenciador_eventos:
        return None
    
    return IntegracaoCLP(gerenciador_feriados, gerenciador_eventos)

@api_clp_bp.route('/clp/status', methods=['GET'])
def status_clp():
    """Endpoint de verificação de status para CLPs"""
    try:
        return jsonify({
            'online': True,
            'timestamp': int(datetime.now().timestamp()),
            'versao': '1.0'
        })
    except Exception as e:
        logger.error(f"Erro no status CLP: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/data/<int:dia>/<int:mes>/<int:ano>', methods=['GET'])
def status_data_clp(dia, mes, ano):
    """Obtém status de uma data específica para CLPs"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        status = integracao.obter_status_data(dia, mes, ano)
        return jsonify(status)
        
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao obter status da data: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/calendario/<int:mes>/<int:ano>', methods=['GET'])
def calendario_clp(mes, ano):
    """Obtém calendário resumido para CLPs"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        if mes < 1 or mes > 12:
            return jsonify({'erro': 'Mês inválido'}), 400
        
        calendario = integracao.obter_calendario_resumido(mes, ano)
        return jsonify(calendario)
        
    except Exception as e:
        logger.error(f"Erro ao obter calendário: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/proximo-evento', methods=['GET'])
def proximo_evento_clp():
    """Obtém próximo evento (geral ou por local)"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        local = request.args.get('local')
        proximo = integracao.obter_proximo_evento(local)
        
        if not proximo:
            return jsonify({
                'encontrado': False,
                'evento': None
            })
        
        return jsonify({
            'encontrado': True,
            'evento': proximo
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter próximo evento: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/verificar-disponibilidade', methods=['POST'])
def verificar_disponibilidade_clp():
    """Verifica disponibilidade de local para CLPs"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Validar campos obrigatórios
        campos = ['local', 'dia', 'mes', 'ano', 'hora_inicio', 'hora_fim']
        for campo in campos:
            if campo not in dados:
                return jsonify({'erro': f'Campo obrigatório: {campo}'}), 400
        
        resultado = integracao.verificar_local_disponivel(
            dados['local'],
            dados['dia'],
            dados['mes'],
            dados['ano'],
            dados['hora_inicio'],
            dados['hora_fim']
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao verificar disponibilidade: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/exportar', methods=['GET'])
def exportar_dados_clp():
    """Exporta dados em formato otimizado para CLPs"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        formato = request.args.get('formato', 'compacto')
        if formato not in ['compacto', 'completo']:
            return jsonify({'erro': 'Formato inválido. Use: compacto ou completo'}), 400
        
        dados = integracao.exportar_dados_clp(formato)
        return jsonify(dados)
        
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/hoje', methods=['GET'])
def status_hoje_clp():
    """Atalho para obter status do dia atual"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        hoje = datetime.now()
        status = integracao.obter_status_data(hoje.day, hoje.month, hoje.year)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro ao obter status de hoje: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/locais', methods=['GET'])
def listar_locais_clp():
    """Lista locais disponíveis em formato simplificado"""
    try:
        gerenciador_eventos = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador_eventos:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        locais = gerenciador_eventos.obter_locais_disponiveis()
        
        return jsonify({
            'total': len(locais),
            'locais': locais,
            'codigos': {
                'Auditório Nobre': 'AN',
                'Átrio': 'AT',
                'Plenário': 'PL',
                'Creche': 'CR',
                'Foyer do Auditório': 'FA'
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar locais: {e}")
        return jsonify({'erro': 'Erro interno'}), 500