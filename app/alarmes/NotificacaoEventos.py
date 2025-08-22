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

        for tecnico in tecnicos_para_notificar:
            # Usa o método preferencial do técnico se disponível
            metodo_usar = tecnico.metodo_contato_preferencial

            if metodo_usar == MetodoContato.WHATSAPP:
                contato = tecnico.telefone
            elif metodo_usar == MetodoContato.EMAIL:
                contato = tecnico.email
            else:
                logger.warning(f"Método de contato desconhecido: {metodo_usar}")
                continue

            msg_log = (
                f"Enviando notificação de evento para {tecnico.nome} via "
                f"{metodo_usar.name} ({contato})"
            )
            print(msg_log)
            logger.info(msg_log)

            self.enviar_mensagem(contato, metodo_usar, mensagem)

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
            logger.debug(f"Preparando envio via WhatsApp para {contato}")
            self.enviar_whatsapp(contato, mensagem)
        elif metodo == MetodoContato.EMAIL:
            logger.debug(f"Preparando envio de email para {contato}")
            self.enviar_email(contato, mensagem)
        else:
            logger.warning(f"Método de contato desconhecido: {metodo}")

    # Variáveis de classe para controlar o atraso entre as chamadas
    _tempo_ultima_chamada_whatsapp = None
    _lock_api_whatsapp = threading.Lock()

    # Configurações para API de WhatsApp (textmebot) 
    API_TEXTMEBOT_BASE_URL = "http://api.textmebot.com/send.php"
    API_TEXMEBOT_KEY = "pF7RP5Zcgdnw"

    @classmethod
    def __chamar_api_textmebot(cls, params):
        """
        Envia uma requisição para a API de WhatsApp (textmebot), garantindo um intervalo mínimo
        entre as chamadas.
        
        Args:
            params (dict): Parâmetros necessários para a chamada da API.
        
        Returns:
            requests.Response ou None: Retorna o objeto de resposta em caso de sucesso ou None se falhar.
        """
        TEMPO_ATRASO_API = 7
        NUM_MAX_TENTATIVAS = 5
        TEMPO_ATRASO_RETRIES = 10

        with cls._lock_api_whatsapp:
            now = datetime.now()
            if cls._tempo_ultima_chamada_whatsapp is not None:
                elapsed = (now - cls._tempo_ultima_chamada_whatsapp).total_seconds()
                if elapsed < TEMPO_ATRASO_API:
                    sleep_time = TEMPO_ATRASO_API - elapsed
                    logger.info(f"Aguardando {sleep_time:.0f}s antes de enviar a próxima mensagem.")
                    time.sleep(sleep_time)

            tentativa_atual = 0
            while tentativa_atual < NUM_MAX_TENTATIVAS:
                try:
                    url_debug = requests.Request('GET', cls.API_TEXTMEBOT_BASE_URL, params=params).prepare().url
                    logger.info(f"Chamando a URL: {url_debug}")

                    response = requests.get(cls.API_TEXTMEBOT_BASE_URL, params=params)
                    cls._tempo_ultima_chamada_whatsapp = datetime.now()
                    return response
                except requests.RequestException as e:
                    tentativa_atual += 1
                    logger.error(f"Erro na requisição (tentativa {tentativa_atual} de {NUM_MAX_TENTATIVAS}): {e}")
                    if tentativa_atual < NUM_MAX_TENTATIVAS:
                        logger.info(f"Aguardando {TEMPO_ATRASO_RETRIES}s antes da próxima tentativa.")
                        time.sleep(TEMPO_ATRASO_RETRIES)
        return None

    def enviar_whatsapp(self, telefone: str, mensagem: str) -> None:
        """
        Implementa envio de mensagem via WhatsApp usando uma API externa.
        
        Args:
            telefone (str): Número em formato E.164 ou ID de grupo.
            mensagem (str): Texto a ser enviado via WhatsApp.
        """
        if not telefone.startswith('+') and '@g.us' not in telefone:
            telefone = '+' + telefone

        params = {
            'recipient': telefone,
            'apikey': self.API_TEXMEBOT_KEY,
            'text': mensagem
        }
        response = self.__chamar_api_textmebot(params)
        if response and response.status_code == 200:
            logger.info(f"WhatsApp enviado com sucesso para {telefone}.")
        else:
            status_code = response.status_code if response else '???'
            logger.error(f"Falha ao enviar WhatsApp para {telefone}. Status: {status_code}")

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
