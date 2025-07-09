# app/routes/api_clp_auditorio.py
import logging
from flask import Blueprint, jsonify, current_app
from datetime import datetime
from ..utils.IntegracaoCLPAuditorio import IntegracaoCLPAuditorio

# Configurar logger
logger = logging.getLogger('EventosFeriados.api_clp_auditorio')

# Criar blueprint
api_clp_auditorio_bp = Blueprint('api_clp_auditorio', __name__)

def get_integracao_clp_auditorio():
    """Obtém a instância da integração CLP Auditório a partir do contexto da aplicação"""
    return current_app.config.get('INTEGRACAO_CLP_AUDITORIO')

@api_clp_auditorio_bp.route('/clp-auditorio/status', methods=['GET'])
def obter_status_auditorio():
    """Obtém status completo da sincronização com CLP Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        status = integracao.obter_status_sincronizacao()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro ao obter status CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/conectividade', methods=['GET'])
def verificar_conectividade_auditorio():
    """Verifica conectividade com CLP Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        resultado = integracao.verificar_conectividade()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao verificar conectividade CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/sincronizar', methods=['POST'])
def executar_sincronizacao_auditorio():
    """Executa sincronização manual com CLP Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        resultado = integracao.sincronizar_dados()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro na sincronização CLP Auditório: {e}")
        return jsonify({'erro': str(e)}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/data/<int:dia>/<int:mes>/<int:ano>', methods=['GET'])
def obter_status_data_auditorio(dia: int, mes: int, ano: int):
    """Obtém status de uma data específica para o Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        status = integracao.obter_status_data(dia, mes, ano)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro ao obter status da data CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/calendario/<int:mes>/<int:ano>', methods=['GET'])
def obter_calendario_auditorio(mes: int, ano: int):
    """Obtém calendário resumido para CLPs do Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        calendario = integracao.obter_calendario_resumido(mes, ano)
        return jsonify(calendario)
        
    except Exception as e:
        logger.error(f"Erro ao obter calendário CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/proximo-evento', methods=['GET'])
def proximo_evento_auditorio():
    """Obtém próximo evento do Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        from flask import request
        local = request.args.get('local')
        
        evento = integracao.obter_proximo_evento(local)
        
        if evento:
            return jsonify({
                'encontrado': True,
                'evento': evento
            })
        else:
            return jsonify({
                'encontrado': False,
                'mensagem': 'Nenhum evento futuro encontrado'
            })
        
    except Exception as e:
        logger.error(f"Erro ao obter próximo evento CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/verificar-disponibilidade', methods=['POST'])
def verificar_disponibilidade_auditorio():
    """Verifica disponibilidade de local do Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        from flask import request
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        campos_obrigatorios = ['local', 'dia', 'mes', 'ano', 'hora_inicio', 'hora_fim']
        for campo in campos_obrigatorios:
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
        logger.error(f"Erro ao verificar disponibilidade CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/exportar', methods=['GET'])
def exportar_dados_auditorio():
    """Exporta dados em formato otimizado para CLPs do Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        from flask import request
        formato = request.args.get('formato', 'compacto')
        
        dados = integracao.exportar_dados_clp(formato)
        return jsonify(dados)
        
    except Exception as e:
        logger.error(f"Erro ao exportar dados CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/hoje', methods=['GET'])
def status_hoje_auditorio():
    """Atalho para obter status do dia atual para o Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        hoje = datetime.now()
        status = integracao.obter_status_data(hoje.day, hoje.month, hoje.year)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro ao obter status hoje CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/locais', methods=['GET'])
def listar_locais_auditorio():
    """Lista locais disponíveis gerenciados pelo CLP Auditório"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        locais = integracao.sincronizador.config['LOCAIS_GERENCIADOS']
        
        return jsonify({
            'total': len(locais),
            'locais': locais,
            'codigos': {
                'Auditório Nobre': 'AN',
                'Foyer do Auditório': 'FA'
            },
            'clp_ip': integracao.sincronizador.config['CLP_IP'],
            'tags_eventos': integracao.sincronizador.config['TAGS_EVENTOS_AUDITORIO']
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar locais CLP Auditório: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/limpar-eventos', methods=['POST'])
def limpar_eventos_auditorio():
    """Limpa apenas os eventos do Auditório do CLP (N91:0-N96:9)"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        # Usar a funcionalidade de limpeza completa do sincronizador
        sucesso, erros = integracao.sincronizador.limpar_todos_dados_clp()
        
        return jsonify({
            'sucesso': sucesso,
            'eventos_limpos': integracao.sincronizador.config['MAX_EVENTOS'] if sucesso else 0,
            'total_slots': integracao.sincronizador.config['MAX_EVENTOS'],
            'erros': erros,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar eventos CLP Auditório: {e}")
        return jsonify({'erro': str(e)}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/limpar-completo', methods=['POST'])
def limpar_dados_completo_auditorio():
    """Limpa todos os dados do CLP Auditório (eventos)"""
    try:
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        resultado = integracao.limpar_todos_dados_clp()
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao limpar dados completos CLP Auditório: {e}")
        return jsonify({'erro': str(e)}), 500

@api_clp_auditorio_bp.route('/clp-auditorio/testar-tag', methods=['POST'])
def testar_tag_auditorio():
    """Testa leitura/escrita de uma tag específica no CLP Auditório"""
    try:
        from flask import request
        from requests.auth import HTTPBasicAuth
        import requests
        
        integracao = get_integracao_clp_auditorio()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        dados = request.get_json()
        if not dados or 'tag' not in dados:
            return jsonify({'erro': 'Tag não especificada'}), 400
        
        tag = dados['tag']
        valor = dados.get('valor')
        operacao = dados.get('operacao', 'read')  # 'read' ou 'write'
        
        sincronizador = integracao.sincronizador
        api_base = sincronizador.config['API_BASE_URL']
        clp_ip = sincronizador.config['CLP_IP']
        auth = HTTPBasicAuth(sincronizador.config['AUTH_USER'], sincronizador.config['AUTH_PASS'])
        
        if operacao == 'write' and valor is not None:
            # Escrita
            url = f"{api_base}/tag_write/{clp_ip}/{tag.replace(':', '%253A')}/{valor}"
            response = requests.get(url, auth=auth, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('sucesso'):
                        return jsonify({
                            'sucesso': True,
                            'operacao': 'escrita',
                            'tag': tag,
                            'valor_escrito': valor,
                            'resposta': data
                        })
                    else:
                        return jsonify({
                            'sucesso': False,
                            'erro': f"Falha na escrita: {data}",
                            'tag': tag
                        })
                except:
                    return jsonify({
                        'sucesso': False,
                        'erro': f"Resposta inválida: {response.text}",
                        'tag': tag
                    })
            else:
                return jsonify({
                    'sucesso': False,
                    'erro': f"HTTP {response.status_code}: {response.text}",
                    'tag': tag
                })
        else:
            # Leitura
            url = f"{api_base}/tag_read/{clp_ip}/{tag.replace(':', '%253A')}"
            response = requests.get(url, auth=auth, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return jsonify({
                        'sucesso': True,
                        'operacao': 'leitura',
                        'tag': tag,
                        'valor_lido': data.get('valor'),
                        'resposta': data
                    })
                except:
                    return jsonify({
                        'sucesso': False,
                        'erro': f"Resposta inválida: {response.text}",
                        'tag': tag
                    })
            else:
                return jsonify({
                    'sucesso': False,
                    'erro': f"HTTP {response.status_code}: {response.text}",
                    'tag': tag
                })
        
    except Exception as e:
        logger.error(f"Erro ao testar tag CLP Auditório: {e}")
        return jsonify({'erro': str(e)}), 500
