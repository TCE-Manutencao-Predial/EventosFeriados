# app/routes/api_clp.py
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import requests
import time
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

@api_clp_bp.route('/clp/sincronizacao/status', methods=['GET'])
def status_sincronizacao():
    """Obtém status da sincronização com CLP"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        status = integracao.obter_status_sincronizacao()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro ao obter status de sincronização: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/sincronizacao/executar', methods=['POST'])
def executar_sincronizacao():
    """Executa sincronização manual com CLP"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        resultado = integracao.sincronizar_dados()
        
        if resultado['sucesso']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        logger.error(f"Erro ao executar sincronização: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/conectividade', methods=['GET'])
def verificar_conectividade():
    """Verifica conectividade com CLP"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        conectividade = integracao.verificar_conectividade()
        return jsonify(conectividade)
        
    except Exception as e:
        logger.error(f"Erro ao verificar conectividade: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/dados-clp', methods=['GET'])
def obter_dados_clp():
    """Lê dados atuais do CLP"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        dados = integracao.ler_dados_do_clp()
        return jsonify(dados)
        
    except Exception as e:
        logger.error(f"Erro ao ler dados do CLP: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/agendador/status', methods=['GET'])
def status_agendador():
    """Obtém status do agendador automático"""
    try:
        from ..utils.AgendadorCLP import AgendadorCLP
        agendador = AgendadorCLP.get_instance()
        status = agendador.status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erro ao obter status do agendador: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/teste-tag', methods=['GET'])
def teste_tag():
    """Testa leitura/escrita de uma tag específica do CLP"""
    try:
        from requests.auth import HTTPBasicAuth
        
        tag = request.args.get('tag', 'N33:0')
        valor = request.args.get('valor', type=int)
        
        # Obter configurações do integrador
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        sincronizador = integracao.sincronizador
        api_base = sincronizador.config['API_BASE_URL']
        clp_ip = sincronizador.config['CLP_IP']
        auth = HTTPBasicAuth(sincronizador.config['AUTH_USER'], sincronizador.config['AUTH_PASS'])
        
        if valor is not None:
            # Escrever valor na tag
            url_escrita = f"{api_base}/tag_write/{clp_ip}/{tag.replace(':', '%253A')}/{valor}"
            response = requests.get(url_escrita, auth=auth, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    'operacao': 'escrita',
                    'tag': tag,
                    'valor_escrito': valor,
                    'sucesso': data.get('sucesso', False),
                    'resposta_clp': data
                })
            else:
                return jsonify({
                    'erro': f'Erro HTTP na escrita: {response.status_code}',
                    'tag': tag,
                    'valor': valor
                }), 400
        else:
            # Ler valor da tag
            url_leitura = f"{api_base}/tag_read/{clp_ip}/{tag.replace(':', '%253A')}"
            response = requests.get(url_leitura, auth=auth, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    'operacao': 'leitura',
                    'tag': tag,
                    'valor_lido': data.get('valor'),
                    'resposta_clp': data
                })
            else:
                return jsonify({
                    'erro': f'Erro HTTP na leitura: {response.status_code}',
                    'tag': tag
                }), 400
                
    except Exception as e:
        logger.error(f"Erro no teste de tag: {e}")
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@api_clp_bp.route('/clp/limpar-feriados', methods=['POST'])
def limpar_feriados():
    """Limpa todos os feriados do CLP (zera N33 e N34)"""
    try:
        from requests.auth import HTTPBasicAuth
        
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        # Acessar o sincronizador diretamente
        sincronizador = integracao.sincronizador
        api_base = sincronizador.config['API_BASE_URL']
        clp_ip = sincronizador.config['CLP_IP']
        max_feriados = sincronizador.config['MAX_FERIADOS']
        auth = HTTPBasicAuth(sincronizador.config['AUTH_USER'], sincronizador.config['AUTH_PASS'])
        
        slots_limpos = 0
        erros = []
        
        for i in range(max_feriados):
            try:
                # Limpar dia (N33:i)
                url_dia = f"{api_base}/tag_write/{clp_ip}/N33%253A{i}/0"
                response_dia = requests.get(url_dia, auth=auth, timeout=30)
                
                # Limpar mês (N34:i)
                url_mes = f"{api_base}/tag_write/{clp_ip}/N34%253A{i}/0"
                response_mes = requests.get(url_mes, auth=auth, timeout=30)
                
                if response_dia.status_code == 200 and response_mes.status_code == 200:
                    data_dia = response_dia.json()
                    data_mes = response_mes.json()
                    
                    if data_dia.get('sucesso') and data_mes.get('sucesso'):
                        slots_limpos += 1
                    else:
                        erros.append(f"Slot {i}: falha na operação (sucesso=false)")
                else:
                    erros.append(f"Slot {i}: erro HTTP (dia={response_dia.status_code}, mês={response_mes.status_code})")
                
                time.sleep(0.1)  # Pausa entre operações
                
            except Exception as e:
                erros.append(f"Slot {i}: {str(e)}")
        
        return jsonify({
            'sucesso': len(erros) == 0,
            'slots_limpos': slots_limpos,
            'total_slots': max_feriados,
            'erros': erros,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar feriados: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@api_clp_bp.route('/clp/limpar-completo', methods=['POST'])
def limpar_dados_completo():
    """Limpa todos os dados do CLP (feriados e eventos)"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        resultado = integracao.limpar_todos_dados_clp()
        
        if resultado['sucesso']:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Todos os dados do CLP foram limpos com sucesso',
                'timestamp': resultado['timestamp']
            })
        else:
            return jsonify({
                'sucesso': False,
                'erro': 'Falha na limpeza dos dados',
                'detalhes': resultado['erros'],
                'timestamp': resultado['timestamp']
            }), 500
    
    except Exception as e:
        logger.error(f"Erro ao limpar dados completos: {e}")
        return jsonify({'erro': str(e)}), 500

@api_clp_bp.route('/clp/eventos-plenario', methods=['GET'])
def listar_eventos_plenario_clp():
    """Lista eventos do Plenário armazenados no CLP"""
    try:
        integracao = get_integracao_clp()
        if not integracao:
            return jsonify({'erro': 'Serviço indisponível'}), 503
        
        resultado = integracao.ler_dados_do_clp()
        
        if resultado['sucesso']:
            eventos = resultado['dados'].get('eventos_plenario', [])
            return jsonify({
                'sucesso': True,
                'total': len(eventos),
                'eventos': eventos,
                'timestamp': resultado['timestamp']
            })
        else:
            return jsonify({
                'sucesso': False,
                'erro': 'Falha ao ler dados do CLP',
                'detalhes': resultado['dados'],
                'timestamp': resultado['timestamp']
            }), 500
    
    except Exception as e:
        logger.error(f"Erro ao listar eventos do Plenário: {e}")
        return jsonify({'erro': str(e)}), 500