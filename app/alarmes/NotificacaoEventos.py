import logging
from datetime import datetime
from app.alarmes.ClassesSistema import ConfigNotificacao
from app.utils.GerenciadorFeriados import GerenciadorFeriados
import requests
import threading
import time
from app.config import WHATSAPP_API

logger = logging.getLogger('EventosFeriados')

class NotificacaoEventos:
    """
    Classe responsável por enviar notificações aos técnicos sobre eventos.
    
    A classe foi adaptada do sistema de alarmes para trabalhar especificamente
    com notificações de eventos, notificando técnicos assim que eventos são
    incluídos no sistema e também um dia antes do evento às 8h00.

    Atributos:
    config_notificacao (ConfigNotificacao): Configurações sobre a forma de notificação.
    """

    def __init__(
        self,
        config_notificacao: ConfigNotificacao,
    ):
        """
        Construtor da classe NotificacaoEventos.

        Args:
            config_notificacao (ConfigNotificacao): Objeto com configurações de notificação.
        """
        self.config_notificacao = config_notificacao
        self.gerenciador_feriados = GerenciadorFeriados()
    # A lista de técnicos e verificação de disponibilidade local foram removidas;
    # o filtro por disponibilidade é realizado pela própria API externa via parâmetro.

    def verificar_horario_data_alarme(self, agora: datetime) -> bool:
        """
        Verifica se o sistema está dentro do horário e dia configurados
        para disparar notificações. Feriados são considerados como finais de semana.

        Args:
            agora (datetime): Data e hora atuais para verificar compatibilidade com as configurações.
        
        Returns:
            bool: True se está dentro do horário de disparo, False caso contrário.
        """
        feriado = self.gerenciador_feriados.verificar_feriado(agora.day, agora.month, agora.year)
        eh_feriado = feriado is not None
        if eh_feriado:
            logger.debug(f"Data atual é feriado: {feriado.get('nome', 'Feriado')}")
            
        dia_semana = agora.weekday()
        eh_final_semana = dia_semana >= 5 or eh_feriado
        
        if eh_final_semana:
            if not self.config_notificacao.disparar_finais_semana:
                logger.debug("Config indica para não disparar em finais de semana ou feriados.")
                return False
            horario_inicio_str, horario_fim_str = self.config_notificacao.horario_finais_semana
        else:
            if not self.config_notificacao.disparar_dias_semana:
                logger.debug("Config indica para não disparar em dias de semana.")
                return False
            horario_inicio_str, horario_fim_str = self.config_notificacao.horario_dias_semana

        horario_inicio = datetime.strptime(horario_inicio_str, '%H:%M').time()
        horario_fim = datetime.strptime(horario_fim_str, '%H:%M').time()
        now_time = agora.time()

        if horario_inicio <= horario_fim:
            dentro_horario = horario_inicio <= now_time <= horario_fim
        else:
            dentro_horario = now_time >= horario_inicio or now_time <= horario_fim

        logger.debug(f"Verificando disponibilidade geral: {'dentro' if dentro_horario else 'fora'} do horário.")
        return dentro_horario

    def notificar_evento_criado(self, evento_dados: dict) -> None:
        """
        Notifica técnicos assim que um evento é criado no sistema.
        
        Args:
            evento_dados (dict): Dados do evento que foi criado.
        """
        agora = datetime.now()
        
    # Verifica se está no horário de notificação
        if not self.verificar_horario_data_alarme(agora):
            logger.info("Fora do horário de notificação para eventos criados.")
            return

        # Monta mensagem de evento criado
        data_evento = f"{evento_dados['dia']:02d}/{evento_dados['mes']:02d}/{evento_dados['ano']}"
        mensagem = (
            f"🗓️ *NOVO EVENTO CADASTRADO*\n\n"
            f"📋 *Evento:* {evento_dados['nome']}\n"
            f"📅 *Data:* {data_evento}\n"
            f"🕒 *Horário:* {evento_dados['hora_inicio']} às {evento_dados['hora_fim']}\n"
            f"📍 *Local:* {evento_dados['local']}\n"
            f"👤 *Responsável:* {evento_dados.get('responsavel', 'Não informado')}\n"
            f"👥 *Participantes:* {evento_dados.get('participantes_estimados', 'Não informado')}\n\n"
            f"ℹ️ Um lembrete será enviado 1 dia antes do evento às 08:00h."
        )

        local = (evento_dados.get('local') or '').strip()
        assunto_dinamico = f"TCE-GO: Aviso de Evento - {local}" if local else "TCE-GO: Aviso de Evento - Novo cadastro"

        self.enviar_notificacao_funcao_eventos(
            assunto=assunto_dinamico,
            mensagem=mensagem,
            apenas_disponiveis=True
        )

    def notificar_evento_cancelado(self, evento_dados: dict) -> None:
        """
        Notifica técnicos quando um evento é cancelado/removido do sistema.
        
        Args:
            evento_dados (dict): Dados do evento que foi cancelado.
        """
        agora = datetime.now()
        
    # Verifica se está no horário de notificação
        if not self.verificar_horario_data_alarme(agora):
            logger.info("Fora do horário de notificação para eventos cancelados.")
            return

        # Monta mensagem de evento cancelado
        data_evento = f"{evento_dados['dia']:02d}/{evento_dados['mes']:02d}/{evento_dados['ano']}"
        mensagem = (
            f"❌ *EVENTO CANCELADO*\n\n"
            f"📋 *Evento:* {evento_dados['nome']}\n"
            f"📅 *Data:* {data_evento}\n"
            f"🕒 *Horário:* {evento_dados['hora_inicio']} às {evento_dados['hora_fim']}\n"
            f"📍 *Local:* {evento_dados['local']}\n"
            f"👤 *Responsável:* {evento_dados.get('responsavel', 'Não informado')}\n\n"
            f"⚠️ Este evento foi removido do sistema e não acontecerá mais."
        )

        local = (evento_dados.get('local') or '').strip()
        assunto_dinamico = f"TCE-GO: Aviso de Evento - {local} (Cancelado)" if local else "TCE-GO: Aviso de Evento - Cancelado"

        self.enviar_notificacao_funcao_eventos(
            assunto=assunto_dinamico,
            mensagem=mensagem,
            apenas_disponiveis=True
        )

    def notificar_evento_alterado(self, evento_anterior: dict, evento_atual: dict) -> None:
        """
        Notifica técnicos quando um evento é alterado (data, horário, local, etc.).
        
        Args:
            evento_anterior (dict): Snapshot do evento antes da atualização.
            evento_atual (dict): Estado atual do evento após a atualização.
        """
        agora = datetime.now()
        if not self.verificar_horario_data_alarme(agora):
            logger.info("Fora do horário de notificação para eventos alterados.")
            return


        # Identificar mudanças relevantes
        def fmt_data(ev):
            return f"{ev['dia']:02d}/{ev['mes']:02d}/{ev['ano']}"

        mudancas = []
        if evento_anterior.get('nome') != evento_atual.get('nome'):
            mudancas.append(f"• Nome: {evento_anterior.get('nome','-')} → {evento_atual.get('nome','-')}")
        if (evento_anterior.get('dia'), evento_anterior.get('mes'), evento_anterior.get('ano')) != \
           (evento_atual.get('dia'), evento_atual.get('mes'), evento_atual.get('ano')):
            mudancas.append(f"• Data: {fmt_data(evento_anterior)} → {fmt_data(evento_atual)}")
        if evento_anterior.get('hora_inicio') != evento_atual.get('hora_inicio') or \
           evento_anterior.get('hora_fim') != evento_atual.get('hora_fim'):
            mudancas.append(
                f"• Horário: {evento_anterior.get('hora_inicio','--:--')}–{evento_anterior.get('hora_fim','--:--')} → "
                f"{evento_atual.get('hora_inicio','--:--')}–{evento_atual.get('hora_fim','--:--')}"
            )
        if evento_anterior.get('local') != evento_atual.get('local'):
            mudancas.append(f"• Local: {evento_anterior.get('local','-')} → {evento_atual.get('local','-')}")
        if evento_anterior.get('responsavel') != evento_atual.get('responsavel'):
            mudancas.append(f"• Responsável: {evento_anterior.get('responsavel','-')} → {evento_atual.get('responsavel','-')}")
        if evento_anterior.get('participantes_estimados') != evento_atual.get('participantes_estimados'):
            mudancas.append(
                f"• Participantes: {evento_anterior.get('participantes_estimados','-')} → {evento_atual.get('participantes_estimados','-')}"
            )

        # Montar mensagem
        data_nova = fmt_data(evento_atual)
        lista_mudancas = "\n".join(mudancas) if mudancas else "• Detalhes ajustados"
        mensagem = (
            f"🔄 *EVENTO ATUALIZADO*\n\n"
            f"📋 *Evento:* {evento_atual.get('nome','')}\n"
            f"📅 *Data:* {data_nova}\n"
            f"🕒 *Horário:* {evento_atual.get('hora_inicio','--:--')} às {evento_atual.get('hora_fim','--:--')}\n"
            f"📍 *Local:* {evento_atual.get('local','')}\n\n"
            f"Alterações:\n{lista_mudancas}"
        )

        local_atual = (evento_atual.get('local') or '').strip()
        assunto_dinamico = f"TCE-GO: Aviso de Evento - {local_atual} (Atualizado)" if local_atual else "TCE-GO: Aviso de Evento - Atualizado"

        self.enviar_notificacao_funcao_eventos(
            assunto=assunto_dinamico,
            mensagem=mensagem,
            apenas_disponiveis=True
        )

    def notificar_lembrete_evento(self, evento_dados: dict) -> None:
        """
        Envia lembrete do evento um dia antes às 8h00.
        
        Args:
            evento_dados (dict): Dados do evento que acontecerá amanhã.
        """
        agora = datetime.now()
        
    # Verifica se é aproximadamente 8h00 (tolerância de 30 minutos)
        if not (7.5 <= agora.hour + agora.minute/60 <= 8.5):
            logger.debug("Não está no horário de lembrete (08:00h ±30min).")
            return

        # Monta mensagem de lembrete
        data_evento = f"{evento_dados['dia']:02d}/{evento_dados['mes']:02d}/{evento_dados['ano']}"
        mensagem = (
            f"⏰ *LEMBRETE DE EVENTO - AMANHÃ*\n\n"
            f"📋 *Evento:* {evento_dados['nome']}\n"
            f"📅 *Data:* {data_evento} (AMANHÃ)\n"
            f"🕒 *Horário:* {evento_dados['hora_inicio']} às {evento_dados['hora_fim']}\n"
            f"📍 *Local:* {evento_dados['local']}\n"
            f"👤 *Responsável:* {evento_dados.get('responsavel', 'Não informado')}\n"
            f"👥 *Participantes:* {evento_dados.get('participantes_estimados', 'Não informado')}\n\n"
            f"⚠️ Verifique se todos os equipamentos e instalações estão funcionando adequadamente."
        )

        local = (evento_dados.get('local') or '').strip()
        assunto_dinamico = f"TCE-GO: Lembrete de Evento - {local} (Amanhã)" if local else "TCE-GO: Lembrete de Evento - Amanhã"

        self.enviar_notificacao_funcao_eventos(
            assunto=assunto_dinamico,
            mensagem=mensagem,
            apenas_disponiveis=True
        )
    def enviar_notificacao_funcao_eventos(self, assunto: str, mensagem: str, apenas_disponiveis: bool = True) -> None:
        """
        Envia a notificação para todos com a função EVENTOS via API externa (e-mail por função).
        """
        try:
            # Manter formatação de e-mail (HTML simples)
            mensagem_html = mensagem.replace('\n', '<br>')
            self.enviar_email_por_funcao(assunto=assunto, mensagem=mensagem_html, apenas_disponiveis=apenas_disponiveis)
        except Exception as e:
            logger.error(f"Erro ao enviar notificação por função EVENTOS: {e}")

    # Mantemos opcionalmente o envio via WhatsApp por função (API externa),
    # mas o fluxo principal usa e-mail por função.

    # Variáveis para controlar o intervalo entre chamadas (mantido para evitar flood)
    _tempo_ultima_chamada_whatsapp = None
    _lock_api_whatsapp = threading.Lock()

    def enviar_whatsapp_por_funcao(self, mensagem: str, apenas_disponiveis: bool = True) -> None:
        """
        Envia mensagem via WhatsApp para todos os técnicos com a função EVENTOS
        utilizando a API pública de envio por função.

        Args:
            mensagem (str): Texto a ser enviado.
            apenas_disponiveis (bool): Se True, envia apenas para quem está em jornada.
        """
        TEMPO_ATRASO_API = 2  # pequena contenção para evitar floods
        NUM_MAX_TENTATIVAS = 1  # apenas uma tentativa imediata

        url = f"{WHATSAPP_API['HOST']}/helpdeskmonitor/api/whatsapp/send-by-function"
        headers = {
            'Authorization': f"Bearer {WHATSAPP_API['TOKEN']}",
            'Content-Type': 'application/json'
        }

        payload = {
            'funcao': 'EVENTOS',
            'mensagem': mensagem,
            'origem': WHATSAPP_API.get('ORIGEM') or 'EVENTOS_FERIADOS',
            'apenas_disponiveis': apenas_disponiveis if apenas_disponiveis is not None else WHATSAPP_API.get('APENAS_DISPONIVEIS', True),
            'async': WHATSAPP_API.get('ASYNC', True)
        }
        
        with self._lock_api_whatsapp:
            now = datetime.now()
            if self._tempo_ultima_chamada_whatsapp is not None:
                elapsed = (now - self._tempo_ultima_chamada_whatsapp).total_seconds()
                if elapsed < TEMPO_ATRASO_API:
                    time.sleep(TEMPO_ATRASO_API - elapsed)

            try:
                log_payload = {
                    'funcao': 'EVENTOS',
                    'origem': payload['origem'],
                    'apenas_disponiveis': payload['apenas_disponiveis'],
                    'mensagem_len': len(payload['mensagem'])
                }
                logger.info(
                    "Chamando API WhatsApp por função: POST %s | headers=Authorization: Bearer **** | payload=%s",
                    url,
                    log_payload
                )
                resp = requests.post(url, json=payload, headers=headers, timeout=WHATSAPP_API.get('TIMEOUT', 30))
                self._tempo_ultima_chamada_whatsapp = datetime.now()

                conteudo_curto = (resp.text[:500] + '...') if len(resp.text) > 500 else resp.text
                # Se for 202 Accepted, tentar exibir task_id e status_url
                if resp.status_code == 202:
                    try:
                        body = resp.json()
                        logger.info(
                            "Envio aceito de forma assíncrona: task_id=%s | status_url=%s | detalhes=%s",
                            body.get('task_id'), body.get('status_url'), body.get('detalhes')
                        )
                    except Exception:
                        logger.info("Resposta 202 sem JSON parseável: %s", conteudo_curto)
                logger.info(
                    "Resultado API WhatsApp por função: status=%s | ok=%s | resposta=%s",
                    resp.status_code, resp.ok, conteudo_curto
                )

                if resp.ok:
                    return

                # Agendar uma segunda tentativa única para 5 minutos depois
                logger.warning("Falha no envio (status %s). Segunda tentativa será executada em 5 minutos.", resp.status_code)
                timer = threading.Timer(300, self._segunda_tentativa_whatsapp_por_funcao, args=(mensagem, apenas_disponiveis))
                timer.daemon = True
                timer.start()
            except requests.RequestException as e:
                logger.error("Erro na chamada da API WhatsApp por função (tentativa imediata): %s", e)
                # Agendar segunda tentativa em 5 minutos
                timer = threading.Timer(300, self._segunda_tentativa_whatsapp_por_funcao, args=(mensagem, apenas_disponiveis))
                timer.daemon = True
                timer.start()

    def _segunda_tentativa_whatsapp_por_funcao(self, mensagem: str, apenas_disponiveis: bool = True) -> None:
        """Executa uma segunda tentativa única após 5 minutos."""
        try:
            url = f"{WHATSAPP_API['HOST']}/helpdeskmonitor/api/whatsapp/send-by-function"
            headers = {
                'Authorization': f"Bearer {WHATSAPP_API['TOKEN']}",
                'Content-Type': 'application/json'
            }
            payload = {
                'funcao': 'EVENTOS',
                'mensagem': mensagem,
                'origem': WHATSAPP_API.get('ORIGEM') or 'EVENTOS_FERIADOS',
                'apenas_disponiveis': apenas_disponiveis if apenas_disponiveis is not None else WHATSAPP_API.get('APENAS_DISPONIVEIS', True)
            }
            log_payload = {
                'funcao': 'EVENTOS',
                'origem': payload['origem'],
                'apenas_disponiveis': payload['apenas_disponiveis'],
                'mensagem_len': len(payload['mensagem'])
            }
            logger.info(
                "(Segunda tentativa) Chamando API WhatsApp por função: POST %s | headers=Authorization: Bearer **** | payload=%s",
                url,
                log_payload
            )
            resp = requests.post(url, json=payload, headers=headers, timeout=WHATSAPP_API.get('TIMEOUT', 30))
            conteudo_curto = (resp.text[:500] + '...') if len(resp.text) > 500 else resp.text
            logger.info(
                "(Segunda tentativa) Resultado API WhatsApp por função: status=%s | ok=%s | resposta=%s",
                resp.status_code, resp.ok, conteudo_curto
            )
        except requests.RequestException as e:
            logger.error("(Segunda tentativa) Erro na chamada da API WhatsApp por função: %s", e)
    def enviar_email_por_funcao(self, assunto: str, mensagem: str, apenas_disponiveis: bool = True) -> None:
        """
        Envia e-mail via API para todos os técnicos com a função EVENTOS.
        """
        TEMPO_ATRASO_API = 2
        url = f"{WHATSAPP_API['HOST']}/helpdeskmonitor/api/email/send-by-function"
        headers = {
            'Authorization': f"Bearer {WHATSAPP_API['TOKEN']}",
            'Content-Type': 'application/json'
        }
        payload = {
            'funcao': 'EVENTOS',
            'assunto': assunto,
            'mensagem': mensagem,
            'apenas_disponiveis': apenas_disponiveis if apenas_disponiveis is not None else WHATSAPP_API.get('APENAS_DISPONIVEIS', True),
            'async': WHATSAPP_API.get('ASYNC', True)
        }

        with self._lock_api_whatsapp:
            now = datetime.now()
            if self._tempo_ultima_chamada_whatsapp is not None:
                elapsed = (now - self._tempo_ultima_chamada_whatsapp).total_seconds()
                if elapsed < TEMPO_ATRASO_API:
                    time.sleep(TEMPO_ATRASO_API - elapsed)

            try:
                log_payload = {
                    'funcao': 'EVENTOS',
                    'apenas_disponiveis': payload['apenas_disponiveis'],
                    'assunto': payload['assunto'],
                    'mensagem_len': len(payload['mensagem'])
                }
                logger.info(
                    "Chamando API Email por função: POST %s | headers=Authorization: Bearer **** | payload=%s",
                    url,
                    log_payload
                )
                resp = requests.post(url, json=payload, headers=headers, timeout=WHATSAPP_API.get('TIMEOUT', 30))
                self._tempo_ultima_chamada_whatsapp = datetime.now()

                conteudo_curto = (resp.text[:500] + '...') if len(resp.text) > 500 else resp.text
                if resp.status_code == 202:
                    try:
                        body = resp.json()
                        logger.info(
                            "Envio de e-mail aceito (assíncrono): task_id=%s | status_url=%s | detalhes=%s",
                            body.get('task_id'), body.get('status_url'), body.get('detalhes')
                        )
                    except Exception:
                        logger.info("Resposta 202 sem JSON parseável: %s", conteudo_curto)
                logger.info(
                    "Resultado API Email por função: status=%s | ok=%s | resposta=%s",
                    resp.status_code, resp.ok, conteudo_curto
                )
            except requests.RequestException as e:
                logger.error("Erro na chamada da API Email por função: %s", e)
