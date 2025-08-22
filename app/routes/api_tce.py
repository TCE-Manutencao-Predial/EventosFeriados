# app/routes/api_tce.py
from flask import Blueprint, jsonify, request
import logging
from ..utils.SincronizadorTCE import SincronizadorTCE
from ..utils.AgendadorCLP import AgendadorCLP

api_tce = Blueprint('api_tce', __name__)
logger = logging.getLogger('EventosFeriados.api_tce')

@api_tce.route('/sincronizar', methods=['POST'])
def sincronizar_tce():
    """Executa sincronização manual dos eventos do TCE"""
    try:
        data = request.get_json() or {}
        mes = data.get('mes')
        ano = data.get('ano')
        
        sincronizador = SincronizadorTCE.get_instance()
        
        if mes and ano:
            # Sincronizar mês específico
            resultado = sincronizador.sincronizar_mes(mes, ano)
        else:
            # Sincronizar período atual (mês atual + próximo)
            resultado = sincronizador.sincronizar_periodo_atual()
        
        if resultado['sucesso']:
            logger.info("Sincronização TCE executada via API")
            return jsonify({
                'status': 'sucesso',
                'dados': resultado
            }), 200
        else:
            logger.error(f"Erro na sincronização TCE via API: {resultado.get('erro')}")
            return jsonify({
                'status': 'erro',
                'erro': resultado.get('erro', 'Erro desconhecido')
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao executar sincronização TCE via API: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        }), 500

@api_tce.route('/status', methods=['GET'])
def status_tce():
    """Retorna o status da sincronização do TCE"""
    try:
        agendador = AgendadorCLP.get_instance()
        status = agendador.status()
        
        return jsonify({
            'status': 'sucesso',
            'dados': {
                'configuracao': status['status_tce'],
                'proximo_horario': status['proximo_horario_tce'],
                'agendador_ativo': status['executando']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter status TCE via API: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        }), 500

@api_tce.route('/configurar', methods=['POST'])
def configurar_tce():
    """Configura a sincronização automática do TCE"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'erro',
                'erro': 'Dados JSON obrigatórios'
            }), 400
        
        habilitado = data.get('habilitado', True)
        horario = data.get('horario', '08:00')
        
        # Validar formato do horário
        try:
            from datetime import datetime
            datetime.strptime(horario, '%H:%M')
        except ValueError:
            return jsonify({
                'status': 'erro',
                'erro': 'Formato de horário inválido. Use HH:MM'
            }), 400
        
        agendador = AgendadorCLP.get_instance()
        agendador.configurar_tce(habilitado, horario)
        
        logger.info(f"Configuração TCE atualizada via API - Habilitado: {habilitado}, Horário: {horario}")
        
        return jsonify({
            'status': 'sucesso',
            'dados': {
                'habilitado': habilitado,
                'horario': horario
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao configurar TCE via API: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        }), 500

@api_tce.route('/eventos', methods=['GET'])
def listar_eventos_tce():
    """Lista eventos sincronizados do TCE"""
    try:
        from ..utils.GerenciadorEventos import GerenciadorEventos
        
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        gerenciador = GerenciadorEventos.get_instance()
        eventos = gerenciador.listar_eventos(ano=ano, mes=mes, local='Plenário')
        
        # Filtrar apenas eventos do TCE
        eventos_tce = [e for e in eventos if e.get('fonte_tce', False)]
        
        return jsonify({
            'status': 'sucesso',
            'dados': {
                'total': len(eventos_tce),
                'eventos': eventos_tce
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar eventos TCE via API: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        }), 500

@api_tce.route('/eventos/<evento_id>', methods=['DELETE'])
def remover_evento_tce(evento_id):
    """Remove um evento específico do TCE"""
    try:
        from ..utils.GerenciadorEventos import GerenciadorEventos
        
        # Verificar se é um evento do TCE
        if not evento_id.startswith('tce_tribunal_pleno'):
            return jsonify({
                'status': 'erro',
                'erro': 'Este endpoint só permite remover eventos do TCE'
            }), 400
        
        gerenciador = GerenciadorEventos.get_instance()
        evento = gerenciador.obter_evento(evento_id)
        
        if not evento:
            return jsonify({
                'status': 'erro',
                'erro': 'Evento não encontrado'
            }), 404
        
        if not evento.get('fonte_tce', False):
            return jsonify({
                'status': 'erro',
                'erro': 'Este não é um evento do TCE'
            }), 400
        
        sucesso = gerenciador.remover_evento(evento_id)
        
        if sucesso:
            logger.info(f"Evento TCE removido via API: {evento_id}")
            return jsonify({
                'status': 'sucesso',
                'dados': {
                    'evento_removido': evento_id
                }
            }), 200
        else:
            return jsonify({
                'status': 'erro',
                'erro': 'Falha ao remover evento'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao remover evento TCE via API: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        }), 500

@api_tce.route('/teste-tce', methods=['GET'])
def teste_tce():
    """Endpoint simples para testar agendamento automático TCE no servidor"""
    try:
        from ..utils.AgendadorCLP import AgendadorCLP
        
        # Obter instância do agendador
        agendador = AgendadorCLP.get_instance()
        
        if not agendador:
            return jsonify({
                'status': 'erro',
                'erro': 'Agendador não está disponível'
            }), 500
        
        # Executar sincronização TCE manual
        logger.info("Executando teste TCE via API /teste-tce")
        resultado = agendador.sincronizar_tce_manual()
        
        return jsonify({
            'status': 'sucesso',
            'dados': resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao executar teste TCE via API: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        }), 500

@api_tce.route('/teste-agendamento', methods=['GET'])
def teste_agendamento_tce():
    """Executa um teste do agendamento automático do TCE (simula execução às 8h)"""
    try:
        from ..utils.AgendadorCLP import AgendadorCLP
        
        # Obter instância do agendador
        agendador = AgendadorCLP.get_instance()
        
        if not agendador:
            return jsonify({
                'status': 'erro',
                'erro': 'Agendador não está disponível'
            }), 500
        
        # Executar sincronização TCE (simula a execução automática das 8h)
        logger.info("Executando teste de agendamento automático TCE via API")
        resultado = agendador.sincronizar_tce_manual()
        
        return jsonify({
            'status': 'sucesso',
            'dados': {
                'teste_agendamento': True,
                'resultado_sincronizacao': resultado,
                'simulacao': 'Execução automática das 8h',
                'timestamp': resultado.get('timestamp'),
                'eventos_processados': resultado.get('eventos_processados', 0),
                'detalhes': resultado.get('detalhes', {})
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao executar teste de agendamento TCE via API: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e),
            'detalhes': 'Falha ao simular agendamento automático'
        }), 500
