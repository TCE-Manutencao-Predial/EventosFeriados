# app/routes/api_eventos.py
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from ..utils.auth_decorators import require_auth_api
from app.utils.GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
from app.utils.AutoSyncCLP import AutoSyncCLP

api_eventos_bp = Blueprint('api_eventos', __name__)
logger = logging.getLogger('EventosFeriados.api_eventos')

@api_eventos_bp.route('/eventos', methods=['GET'])
@require_auth_api
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
        ano_minimo = request.args.get('ano_minimo', type=int)
        
        eventos = gerenciador.listar_eventos(ano=ano, mes=mes, local=local, ano_minimo=ano_minimo)
        
        return jsonify({
            'sucesso': True,
            'total': len(eventos),
            'eventos': eventos
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/<evento_id>', methods=['GET'])
@require_auth_api
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
@require_auth_api
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

        # Disparar autosync debounced para o CLP do local
        try:
            integracao_plenario = current_app.config.get('INTEGRACAO_CLP')
            integracao_auditorio = current_app.config.get('INTEGRACAO_CLP_AUDITORIO')
            aud_locais = []
            if integracao_auditorio and getattr(integracao_auditorio, 'sincronizador', None):
                aud_locais = integracao_auditorio.sincronizador.config.get('LOCAIS_GERENCIADOS', [])
            AutoSyncCLP.get_instance().trigger_for_local(novo_evento.get('local'), integracao_plenario, integracao_auditorio, aud_locais)
        except Exception as e:
            logger.error(f"Falha ao agendar autosync após adicionar evento: {e}")
        
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
@require_auth_api
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
        
        # Disparar autosync debounced para o CLP do local
        try:
            integracao_plenario = current_app.config.get('INTEGRACAO_CLP')
            integracao_auditorio = current_app.config.get('INTEGRACAO_CLP_AUDITORIO')
            aud_locais = []
            if integracao_auditorio and getattr(integracao_auditorio, 'sincronizador', None):
                aud_locais = integracao_auditorio.sincronizador.config.get('LOCAIS_GERENCIADOS', [])
            AutoSyncCLP.get_instance().trigger_for_local(evento_atualizado.get('local'), integracao_plenario, integracao_auditorio, aud_locais)
        except Exception as e:
            logger.error(f"Falha ao agendar autosync após atualizar evento: {e}")

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
@require_auth_api
def remover_evento(evento_id):
    """Remove um evento"""
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503

        # Capturar local antes da remoção para disparar autosync
        evento = gerenciador.obter_evento(evento_id)
        local_evento = evento.get('local') if evento else None

        sucesso = gerenciador.remover_evento(evento_id)

        if not sucesso:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        # Disparar autosync debounced para o CLP do local
        try:
            if sucesso and local_evento:
                integracao_plenario = current_app.config.get('INTEGRACAO_CLP')
                integracao_auditorio = current_app.config.get('INTEGRACAO_CLP_AUDITORIO')
                aud_locais = []
                if integracao_auditorio and getattr(integracao_auditorio, 'sincronizador', None):
                    aud_locais = integracao_auditorio.sincronizador.config.get('LOCAIS_GERENCIADOS', [])
                AutoSyncCLP.get_instance().trigger_for_local(local_evento, integracao_plenario, integracao_auditorio, aud_locais)
        except Exception as e:
            logger.error(f"Falha ao agendar autosync após remover evento: {e}")

        return jsonify({
            'sucesso': True,
            'mensagem': 'Evento removido com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover evento: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/por-data', methods=['GET'])
@require_auth_api
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
@require_auth_api
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
@require_auth_api
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

@api_eventos_bp.route('/eventos/<evento_id>/forcar-notificacao-whatsapp', methods=['POST'])
@require_auth_api
def forcar_notificacao_whatsapp(evento_id):
    """Dispara manualmente uma notificação via WhatsApp por função EVENTOS para um evento específico.

    Parâmetros (query):
      - tipo: 'detalhes' (padrão) | 'amanha' | '1h'
    """
    try:
        gerenciador = current_app.config.get('GERENCIADOR_EVENTOS')
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503

        evento = gerenciador.obter_evento(evento_id)
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404

        tipo = request.args.get('tipo', 'detalhes')

        # Construir mensagem conforme tipo solicitado
        data_evento = f"{evento['dia']:02d}/{evento['mes']:02d}/{evento['ano']}"
        if tipo == 'amanha':
            mensagem = (
                f"⏰ *LEMBRETE DE EVENTO - AMANHÃ*\n\n"
                f"📋 *Evento:* {evento['nome']}\n"
                f"📅 *Data:* {data_evento} (AMANHÃ)\n"
                f"🕒 *Horário:* {evento['hora_inicio']} às {evento['hora_fim']}\n"
                f"📍 *Local:* {evento['local']}\n"
                f"👤 *Responsável:* {evento.get('responsavel', 'Não informado')}\n"
                f"👥 *Participantes:* {evento.get('participantes_estimados', 'Não informado')}\n\n"
                f"⚠️ Verifique se todos os equipamentos e instalações estão prontos."
            )
        elif tipo == '1h':
            mensagem = (
                f"⏰ *LEMBRETE DE EVENTO - EM 1 HORA*\n\n"
                f"📋 *Evento:* {evento['nome']}\n"
                f"📅 *Data:* {data_evento}\n"
                f"🕒 *Horário:* {evento['hora_inicio']} às {evento['hora_fim']}\n"
                f"📍 *Local:* {evento['local']}\n"
                f"👤 *Responsável:* {evento.get('responsavel', 'Não informado')}\n"
                f"👥 *Participantes:* {evento.get('participantes_estimados', 'Não informado')}\n\n"
                f"⚠️ Preparar infraestrutura e checagens finais."
            )
        else:
            mensagem = (
                f"📣 *AVISO MANUAL DE EVENTO*\n\n"
                f"📋 *Evento:* {evento['nome']}\n"
                f"📅 *Data:* {data_evento}\n"
                f"🕒 *Horário:* {evento['hora_inicio']} às {evento['hora_fim']}\n"
                f"📍 *Local:* {evento['local']}\n"
                f"👤 *Responsável:* {evento.get('responsavel', 'Não informado')}\n"
                f"👥 *Participantes:* {evento.get('participantes_estimados', 'Não informado')}\n\n"
                f"ℹ️ Notificação disparada manualmente pelo sistema."
            )

        # Enviar via WhatsApp por função EVENTOS
        ger_notif = GerenciadorNotificacaoEventos.get_instance()
        if not ger_notif or not ger_notif.notificacao_eventos:
            return jsonify({'erro': 'Sistema de notificação indisponível'}), 503

        logger.info(
            "FORCAR_WHATSAPP | preparando envio | evento_id=%s | tipo=%s | len_msg=%s",
            evento_id, tipo, len(mensagem)
        )
        ger_notif.notificacao_eventos.enviar_whatsapp_por_funcao(mensagem=mensagem)
        logger.info(
            "FORCAR_WHATSAPP | envio solicitado com sucesso | evento_id=%s | tipo=%s",
            evento_id, tipo
        )
        return jsonify({'sucesso': True, 'mensagem': 'Notificação WhatsApp enviada com sucesso', 'tipo': tipo})
    except Exception as e:
        logger.error(f"Erro ao forçar notificação WhatsApp: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/<evento_id>/encerrar', methods=['POST'])
@require_auth_api
def encerrar_evento(evento_id):
    """Encerra um evento mais cedo removendo o dia atual dos CLPs envolvidos.
    
    Isso faz com que o CLP desligue luzes e ar condicionado imediatamente,
    permitindo que o evento seja encerrado antes do horário programado.
    """
    try:
        gerenciador = current_app.config.get('GERENCIADOR_EVENTOS')
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        # Obter informações do evento e validar se pode ser encerrado
        resultado = gerenciador.encerrar_evento_agora(evento_id)
        
        if not resultado:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        evento = resultado['evento']
        local = resultado['local']
        dia = resultado['dia']
        mes = resultado['mes']
        
        logger.info(f"Encerrando evento '{evento['nome']}' do local '{local}'...")
        
        # Determinar qual CLP gerencia este local
        integracao_plenario = current_app.config.get('INTEGRACAO_CLP')
        integracao_auditorio = current_app.config.get('INTEGRACAO_CLP_AUDITORIO')
        
        locais_auditorio = []
        if integracao_auditorio and hasattr(integracao_auditorio, 'sincronizador'):
            locais_auditorio = integracao_auditorio.sincronizador.config.get('LOCAIS_GERENCIADOS', [])
        
        sucesso = False
        erros = []
        clp_afetado = None
        
        # Remover eventos do CLP correspondente ao local
        if local in locais_auditorio:
            # CLP Auditório
            clp_afetado = 'Auditório'
            if integracao_auditorio and hasattr(integracao_auditorio, 'sincronizador'):
                sucesso, erros = integracao_auditorio.sincronizador.remover_eventos_do_dia(dia, mes)
                logger.info(f"Resultado remoção CLP Auditório: sucesso={sucesso}, erros={erros}")
            else:
                erros.append('Integração com CLP Auditório não disponível')
                logger.error('Integração com CLP Auditório não disponível')
        elif local == 'Plenário':
            # CLP Plenário
            clp_afetado = 'Plenário'
            if integracao_plenario and hasattr(integracao_plenario, 'sincronizador'):
                sucesso, erros = integracao_plenario.sincronizador.remover_eventos_do_dia(dia, mes)
                logger.info(f"Resultado remoção CLP Plenário: sucesso={sucesso}, erros={erros}")
            else:
                erros.append('Integração com CLP Plenário não disponível')
                logger.error('Integração com CLP Plenário não disponível')
        else:
            # Local sem automação predial
            logger.info(f"Local '{local}' não possui automação predial integrada ao sistema")
            return jsonify({
                'sucesso': True,
                'mensagem': f'Evento marcado como encerrado. O local "{local}" não possui automação predial integrada ao sistema.',
                'evento': evento['nome'],
                'local': local,
                'sem_automacao': True
            })
        
        if sucesso:
            logger.info(f"Evento '{evento['nome']}' encerrado com sucesso no CLP {clp_afetado}")
            return jsonify({
                'sucesso': True,
                'mensagem': f'Evento encerrado com sucesso! O CLP {clp_afetado} foi atualizado e as luzes/ar condicionado serão desligados.',
                'evento': evento['nome'],
                'local': local,
                'clp_afetado': clp_afetado
            })
        else:
            logger.error(f"Falha ao encerrar evento '{evento['nome']}' no CLP {clp_afetado}: {erros}")
            return jsonify({
                'erro': f'Erro ao atualizar CLP {clp_afetado}: {", ".join(erros)}',
                'evento': evento['nome'],
                'local': local,
                'clp_afetado': clp_afetado
            }), 500
        
    except ValueError as e:
        logger.error(f"Erro de validação ao encerrar evento: {e}")
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao encerrar evento: {e}")
        return jsonify({'erro': str(e)}), 500

@api_eventos_bp.route('/eventos/<evento_id>/reativar', methods=['POST'])
@require_auth_api
def reativar_evento(evento_id):
    """Reativa um evento que foi encerrado mais cedo.
    
    Remove a marca de encerramento para que o evento volte a ser sincronizado com o CLP
    na próxima sincronização automática (7h ou 18h) ou manual.
    """
    try:
        gerenciador = current_app.config.get('GERENCIADOR_EVENTOS')
        if not gerenciador:
            return jsonify({'erro': 'Gerenciador de eventos não disponível'}), 503
        
        # Reativar evento
        evento = gerenciador.reativar_evento(evento_id)
        
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        logger.info(f"Evento '{evento['nome']}' reativado com sucesso")
        
        # Disparar autosync para reprogramar no CLP
        try:
            integracao_plenario = current_app.config.get('INTEGRACAO_CLP')
            integracao_auditorio = current_app.config.get('INTEGRACAO_CLP_AUDITORIO')
            aud_locais = []
            if integracao_auditorio and getattr(integracao_auditorio, 'sincronizador', None):
                aud_locais = integracao_auditorio.sincronizador.config.get('LOCAIS_GERENCIADOS', [])
            AutoSyncCLP.get_instance().trigger_for_local(evento.get('local'), integracao_plenario, integracao_auditorio, aud_locais)
        except Exception as e:
            logger.error(f"Falha ao agendar autosync após reativar evento: {e}")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Evento "{evento["nome"]}" reativado com sucesso! Será reprogramado no CLP na próxima sincronização.',
            'evento': evento
        })
        
    except ValueError as e:
        logger.error(f"Erro de validação ao reativar evento: {e}")
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao reativar evento: {e}")
        return jsonify({'erro': str(e)}), 500
