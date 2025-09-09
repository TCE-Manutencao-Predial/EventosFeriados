import logging
from datetime import datetime
from app.alarmes.ClassesSistema import Tecnico, MetodoContato, FuncoesTecnicos, ConfigNotificacao
from app.utils.GerenciadorFeriados import GerenciadorFeriados
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import threading
import time
import socket
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
        tecnicos (List[Tecnico]): Lista de técnicos que podem receber as notificações.
        metodo_notificacao (MetodoContato): Método de contato a ser utilizado.
    """

    def __init__(
        self,
        config_notificacao: ConfigNotificacao,
        tecnicos: List[Tecnico],
        metodo_notificacao: MetodoContato = MetodoContato.WHATSAPP
    ):
        """
        Construtor da classe NotificacaoEventos.

        Args:
            config_notificacao (ConfigNotificacao): Objeto com configurações de notificação.
            tecnicos (List[Tecnico]): Lista de instâncias da classe Tecnico.
            metodo_notificacao (MetodoContato, optional): Método de contato (Enum). 
                Por padrão, utiliza 'MetodoContato.WHATSAPP'.
        """
        self.config_notificacao = config_notificacao
        self.tecnicos = tecnicos
        self.metodo_notificacao = metodo_notificacao
        self.gerenciador_feriados = GerenciadorFeriados()

    def verificar_disponibilidade_tecnico(self, tecnico: Tecnico, agora: datetime) -> bool:
        """
        Verifica se o técnico está disponível no momento atual, considerando:
            - Se está de férias (ferias=True).
            - Se há horários (jornada) definidos e se o horário atual está dentro de algum
              dos intervalos válidos, inclusive levando em conta turnos que ultrapassam a meia-noite.
        
        Args:
            tecnico (Tecnico): O técnico a ser verificado.
            agora (datetime): Data e hora de referência para a checagem.
        
        Returns:
            bool: True se o técnico está disponível, False caso contrário.
        """
        if tecnico.ferias:
            logger.debug(f"Técnico {tecnico.nome} está de férias.")
            return False
        if not tecnico.jornada:
            logger.debug(f"Técnico {tecnico.nome} não tem jornada definida, assumindo disponível.")
            return True

        now_time = agora.time()
        for inicio_str, fim_str in tecnico.jornada:
            inicio = datetime.strptime(inicio_str, '%H:%M').time()
            fim = datetime.strptime(fim_str, '%H:%M').time()

            if inicio <= fim:
                if inicio <= now_time <= fim:
                    logger.debug(f"Técnico {tecnico.nome} está disponível no intervalo {inicio} - {fim}.")
                    return True
            else:
                if now_time >= inicio or now_time <= fim:
                    logger.debug(f"Técnico {tecnico.nome} está disponível no turno noturno {inicio} - {fim}.")
                    return True

        logger.debug(f"Técnico {tecnico.nome} não está disponível agora.")
        return False

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

        # Filtra técnicos com função EVENTOS
        tecnicos_eventos = [
            tecnico for tecnico in self.tecnicos 
            if FuncoesTecnicos.EVENTOS in tecnico.funcoes
        ]

        if not tecnicos_eventos:
            logger.info("Nenhum técnico com função EVENTOS encontrado.")
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

        self.enviar_notificacao_para_tecnicos(mensagem, tecnicos_eventos)

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

        # Filtra técnicos com função EVENTOS
        tecnicos_eventos = [
            tecnico for tecnico in self.tecnicos 
            if FuncoesTecnicos.EVENTOS in tecnico.funcoes
        ]

        if not tecnicos_eventos:
            logger.info("Nenhum técnico com função EVENTOS encontrado.")
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

        self.enviar_notificacao_para_tecnicos(mensagem, tecnicos_eventos)

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

        # Filtra técnicos com função EVENTOS
        tecnicos_eventos = [
            tecnico for tecnico in self.tecnicos 
            if FuncoesTecnicos.EVENTOS in tecnico.funcoes
        ]

        if not tecnicos_eventos:
            logger.info("Nenhum técnico com função EVENTOS encontrado para lembrete.")
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

        self.enviar_notificacao_para_tecnicos(mensagem, tecnicos_eventos)

    def enviar_notificacao_para_tecnicos(self, mensagem: str, tecnicos_lista: List[Tecnico]) -> None:
        """
        Envia a notificação para uma lista específica de técnicos.
        
        Args:
            mensagem (str): Mensagem a ser enviada.
            tecnicos_lista (List[Tecnico]): Lista de técnicos para notificar.
        """
        agora = datetime.now()

        # Filtra técnicos pela disponibilidade atual
        tecnicos_para_notificar = [
            tecnico for tecnico in tecnicos_lista
            if self.verificar_disponibilidade_tecnico(tecnico, agora)
        ]

        if not tecnicos_para_notificar:
            logger.info("Nenhum técnico disponível para notificação no momento.")
            return

        logger.debug(f"Método de notificação escolhido: {self.metodo_notificacao.name}")

        # Novo fluxo: WhatsApp será enviado em lote por função via API externa.
        # Emails (se houver) continuam individuais.

        # 1) WhatsApp por função (EVENTOS) usando API externa
        if any(t.metodo_contato_preferencial == MetodoContato.WHATSAPP for t in tecnicos_para_notificar):
            try:
                self.enviar_whatsapp_por_funcao(mensagem, apenas_disponiveis=True)
            except Exception as e:
                logger.error(f"Erro ao enviar WhatsApp por função: {e}")

        # 2) Email individual para quem preferir EMAIL
        for tecnico in tecnicos_para_notificar:
            if tecnico.metodo_contato_preferencial == MetodoContato.EMAIL and tecnico.email:
                msg_log = (
                    f"Enviando notificação de evento para {tecnico.nome} via EMAIL ({tecnico.email})"
                )
                print(msg_log)
                logger.info(msg_log)
                self.enviar_email(tecnico.email, mensagem)

    def enviar_mensagem(self, contato: str, metodo: MetodoContato, mensagem: str) -> None:
        """
        Encaminha a mensagem para o método apropriado.
        
        Args:
            contato (str): Telefone ou e-mail do destinatário.
            metodo (MetodoContato): Método de envio (WhatsApp ou EMAIL).
            mensagem (str): Texto da mensagem a ser enviada.
        """
        hostname = socket.gethostname()
        mensagem = f"[{hostname}] {mensagem}"
        
        if metodo == MetodoContato.WHATSAPP:
            # Mantido por compatibilidade, mas agora delegamos ao envio por função
            logger.debug("Preparando envio via WhatsApp por função (compat)")
            self.enviar_whatsapp_por_funcao(mensagem, apenas_disponiveis=True)
        elif metodo == MetodoContato.EMAIL:
            logger.debug(f"Preparando envio de email para {contato}")
            self.enviar_email(contato, mensagem)
        else:
            logger.warning(f"Método de contato desconhecido: {metodo}")

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
        NUM_MAX_TENTATIVAS = 3
        TEMPO_ATRASO_RETRIES = 5

        url = f"{WHATSAPP_API['HOST']}/helpdeskmonitor/api/whatsapp/send-by-function"
        headers = {
            'Authorization': f"Bearer {WHATSAPP_API['TOKEN']}",
            'Content-Type': 'application/json'
        }

        hostname = socket.gethostname()
        payload = {
            'funcao': 'EVENTOS',
            'mensagem': f"[{hostname}] {mensagem}",
            'origem': WHATSAPP_API.get('ORIGEM') or 'EVENTOS_FERIADOS',
            'apenas_disponiveis': apenas_disponiveis if apenas_disponiveis is not None else WHATSAPP_API.get('APENAS_DISPONIVEIS', True)
        }

        with self._lock_api_whatsapp:
            now = datetime.now()
            if self._tempo_ultima_chamada_whatsapp is not None:
                elapsed = (now - self._tempo_ultima_chamada_whatsapp).total_seconds()
                if elapsed < TEMPO_ATRASO_API:
                    time.sleep(TEMPO_ATRASO_API - elapsed)

            tentativa = 0
            while tentativa < NUM_MAX_TENTATIVAS:
                try:
                    logger.info(
                        f"Chamando API WhatsApp por função: POST {url} | headers=Authorization: Bearer **** | payload={{{'funcao': 'EVENTOS', 'origem': payload['origem'], 'apenas_disponiveis': payload['apenas_disponiveis'], 'mensagem_len': {len(payload['mensagem'])}}}}"
                    )
                    resp = requests.post(url, json=payload, headers=headers, timeout=WHATSAPP_API.get('TIMEOUT', 30))
                    self._tempo_ultima_chamada_whatsapp = datetime.now()

                    # Log detalhado do resultado
                    conteudo_curto = (resp.text[:500] + '...') if len(resp.text) > 500 else resp.text
                    logger.info(
                        f"Resultado API WhatsApp por função: status={resp.status_code} | ok={resp.ok} | resposta={conteudo_curto}"
                    )

                    if resp.ok:
                        return

                    # Em caso de status não-OK, tenta novamente com backoff
                    tentativa += 1
                    if tentativa < NUM_MAX_TENTATIVAS:
                        logger.warning(f"Falha no envio (status {resp.status_code}). Nova tentativa em {TEMPO_ATRASO_RETRIES}s...")
                        time.sleep(TEMPO_ATRASO_RETRIES)
                except requests.RequestException as e:
                    tentativa += 1
                    logger.error(f"Erro na chamada da API WhatsApp por função (tentativa {tentativa}/{NUM_MAX_TENTATIVAS}): {e}")
                    if tentativa < NUM_MAX_TENTATIVAS:
                        time.sleep(TEMPO_ATRASO_RETRIES)

    def enviar_email(self, email: str, mensagem: str) -> None:
        """
        Envia um e-mail usando o servidor SMTP configurado.
        
        Args:
            email (str): Endereço de e-mail do destinatário.
            mensagem (str): Conteúdo da mensagem.
        """
        smtp_server = '172.17.120.1'
        smtp_port = 25
        from_email = 'automacao@tce.go.gov.br'
        subject = "Notificação de Evento - TCE-GO"

        # Converte quebras de linha para HTML
        mensagem_html = mensagem.replace('\n', '<br>')

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(mensagem_html, 'html'))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.sendmail(from_email, email, msg.as_string())
            logger.info(f"Email enviado com sucesso para {email}.")
        except Exception as e:
            logger.error(f"Erro ao enviar o email para {email}: {e}")
        finally:
            try:
                server.quit()
            except:
                pass
