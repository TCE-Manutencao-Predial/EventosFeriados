import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Optional
from app.alarmes.NotificacaoEventos import NotificacaoEventos
from app.alarmes.ClassesSistema import ConfigNotificacao
from app.utils.GerenciadorEventos import GerenciadorEventos

logger = logging.getLogger('EventosFeriados')

class GerenciadorNotificacaoEventos:
    """
    Gerenciador responsável por coordenar as notificações de eventos.
    
    Esta classe gerencia:
    - notificações imediatas (criado/alterado/cancelado → e-mail por função)
    - lembrete 1 dia antes às 08:00 → WhatsApp por função EVENTOS
    - lembrete 1 hora antes do início → WhatsApp por função EVENTOS
    - notificação de limpeza 1 dia após às 08:00 → WhatsApp por função LIMPEZA
    """
    
    _instance = None
    
    def __init__(self):
        self.notificacao_eventos: Optional[NotificacaoEventos] = None
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        # Controle simples para evitar lembretes 1h duplicados (por execução)
        # Mapeia id do evento → timestamp do último envio
        self._ultimo_envio_1h = {}
        self._inicializar_notificacao()
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do gerenciador (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _inicializar_notificacao(self):
        """Inicializa o sistema de notificação com as configurações padrão"""
        try:
            # Configuração padrão para notificações de eventos
            config = ConfigNotificacao(
                disparar_dias_semana=True,
                disparar_finais_semana=True,
                horario_dias_semana=("07:00", "19:00"),
                horario_finais_semana=("08:00", "18:00"),
                repetir_notificacao=False
            )
            
            # Cria a instância de notificação (sem técnicos locais; API externa cuida do envio por função)
            self.notificacao_eventos = NotificacaoEventos(
                config_notificacao=config
            )
            
            logger.info("Sistema de notificação de eventos inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de notificação: {e}")
            self.notificacao_eventos = None
    
    def notificar_evento_criado(self, evento_dados: dict) -> bool:
        """
        Notifica técnicos sobre um evento recém-criado.
        
        Args:
            evento_dados (dict): Dados do evento que foi criado
            
        Returns:
            bool: True se a notificação foi enviada, False caso contrário
        """
        if not self.notificacao_eventos:
            logger.error("Sistema de notificação não está inicializado")
            return False
            
        try:
            self.notificacao_eventos.notificar_evento_criado(evento_dados)
            logger.info(f"Notificação de evento criado enviada: {evento_dados['nome']}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de evento criado: {e}")
            return False
    
    def notificar_evento_cancelado(self, evento_dados: dict) -> bool:
        """
        Notifica técnicos sobre um evento que foi cancelado/removido.
        
        Args:
            evento_dados (dict): Dados do evento que foi cancelado
            
        Returns:
            bool: True se a notificação foi enviada, False caso contrário
        """
        if not self.notificacao_eventos:
            logger.error("Sistema de notificação não está inicializado")
            return False
        try:
            self.notificacao_eventos.notificar_evento_cancelado(evento_dados)
            logger.info(f"Notificação de evento cancelado enviada: {evento_dados['nome']}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de evento cancelado: {e}")
            return False

    def notificar_evento_alterado(self, evento_anterior: dict, evento_atual: dict) -> bool:
        """
        Notifica técnicos sobre um evento que foi alterado.
        """
        if not self.notificacao_eventos:
            logger.error("Sistema de notificação não está inicializado")
            return False
        try:
            self.notificacao_eventos.notificar_evento_alterado(evento_anterior, evento_atual)
            logger.info(f"Notificação de evento alterado enviada: {evento_atual.get('nome','')} ")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de evento alterado: {e}")
            return False
    
    def iniciar_scheduler_lembretes(self):
        """Inicia o agendador para envio de lembretes diários"""
        if self.running:
            logger.warning("Scheduler de lembretes já está em execução")
            return
            
        # Agenda verificação diária às 9:30 (lembrete 1 dia antes)
        schedule.every().day.at("09:30").do(self._verificar_eventos_amanha)
        # Agenda verificação minuciosa para lembretes 1h antes
        schedule.every(1).minutes.do(self._verificar_eventos_1h)
        # Agenda notificação de limpeza pós-evento às 9:30 (eventos de ontem)
        schedule.every().day.at("09:30").do(self._verificar_eventos_ontem_limpeza)
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._executar_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler de lembretes iniciado: amanhã 09:30, 1h antes, limpeza pós-evento 09:30")
    
    def parar_scheduler_lembretes(self):
        """Para o agendador de lembretes"""
        if not self.running:
            return
            
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            
        logger.info("Scheduler de lembretes de eventos parado")
    
    def _executar_scheduler(self):
        """Executa o loop do agendador em thread separada"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
            except Exception as e:
                logger.error(f"Erro no scheduler de lembretes: {e}")
                time.sleep(60)
    
    def _verificar_eventos_amanha(self):
        """Verifica se há eventos para amanhã e envia lembretes"""
        if not self.notificacao_eventos:
            logger.error("Sistema de notificação não está disponível para lembretes")
            return
            
        try:
            # Calcula a data de amanhã
            amanha = datetime.now() + timedelta(days=1)
            
            # Busca eventos para amanhã
            gerenciador_eventos = GerenciadorEventos.get_instance()
            eventos_amanha = gerenciador_eventos.obter_eventos_por_data(
                dia=amanha.day,
                mes=amanha.month,
                ano=amanha.year
            )
            
            if not eventos_amanha:
                logger.debug("Nenhum evento encontrado para amanhã")
                return
                
            logger.info(f"Encontrados {len(eventos_amanha)} eventos para amanhã. Enviando lembretes...")
            
            # Envia lembrete para cada evento
            for evento in eventos_amanha:
                try:
                    self.notificacao_eventos.notificar_lembrete_evento(evento)
                    logger.info(f"Lembrete enviado para evento: {evento['nome']}")
                    
                    # Pequena pausa entre as notificações
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar lembrete para evento {evento['nome']}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar eventos de amanhã: {e}")

    def _verificar_eventos_1h(self):
        """Verifica eventos que iniciarão em ~1 hora e envia lembrete via WhatsApp."""
        if not self.notificacao_eventos:
            logger.error("Sistema de notificação não está disponível para lembretes 1h")
            return

        try:
            agora = datetime.now()
            gerenciador_eventos = GerenciadorEventos.get_instance()
            eventos_hoje = gerenciador_eventos.obter_eventos_por_data(
                dia=agora.day,
                mes=agora.month,
                ano=agora.year
            )

            if not eventos_hoje:
                return

            TOLERANCIA_MINUTOS = 2

            # Limpeza simples do mapa de envios (remover envios com mais de 6 horas)
            try:
                limite = agora - timedelta(hours=6)
                self._ultimo_envio_1h = {
                    k: v for k, v in self._ultimo_envio_1h.items() if v >= limite
                }
            except Exception:
                pass

            for evento in eventos_hoje:
                try:
                    # Monta datetime do início do evento
                    hora, minuto = evento['hora_inicio'].split(':')
                    dt_inicio = datetime(evento['ano'], evento['mes'], evento['dia'], int(hora), int(minuto))
                    minutos_para_inicio = (dt_inicio - agora).total_seconds() / 60.0

                    if 60 - TOLERANCIA_MINUTOS <= minutos_para_inicio <= 60 + TOLERANCIA_MINUTOS:
                        ultimo_envio = self._ultimo_envio_1h.get(evento['id'])
                        if ultimo_envio and (agora - ultimo_envio).total_seconds() < 60 * 55:
                            # Já enviou nos últimos 55 minutos; evita duplicidade
                            continue

                        self.notificacao_eventos.notificar_lembrete_evento_1h(evento)
                        self._ultimo_envio_1h[evento['id']] = agora
                        logger.info(f"Lembrete 1h enviado para evento: {evento['nome']}")

                except Exception as e:
                    logger.error(f"Erro ao processar lembrete 1h do evento {evento.get('nome','')}: {e}")
        except Exception as e:
            logger.error(f"Erro ao verificar eventos 1h: {e}")
    
    def _verificar_eventos_ontem_limpeza(self):
        """Verifica eventos que ocorreram ontem e notifica equipe de limpeza às 08:00."""
        if not self.notificacao_eventos:
            logger.error("Sistema de notificação não está disponível para notificação de limpeza")
            return

        try:
            # Calcula a data de ontem
            ontem = datetime.now() - timedelta(days=1)
            
            # Busca eventos de ontem
            gerenciador_eventos = GerenciadorEventos.get_instance()
            eventos_ontem = gerenciador_eventos.obter_eventos_por_data(
                dia=ontem.day,
                mes=ontem.month,
                ano=ontem.year
            )
            
            if not eventos_ontem:
                logger.debug("Nenhum evento encontrado ontem para notificação de limpeza")
                return
                
            logger.info(f"Encontrados {len(eventos_ontem)} eventos de ontem. Notificando equipe de limpeza...")
            
            # Envia notificação para cada evento que ocorreu ontem
            for evento in eventos_ontem:
                try:
                    self.notificacao_eventos.notificar_limpeza_pos_evento(evento)
                    logger.info(f"Notificação de limpeza enviada para evento: {evento['nome']}")
                    
                    # Pequena pausa entre as notificações
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notificação de limpeza para evento {evento['nome']}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar eventos de ontem para limpeza: {e}")
    
    def verificar_lembretes_manualmente(self):
        """
        Permite verificar manualmente se há eventos para amanhã.
        Útil para testes ou execução manual.
        """
        logger.info("Verificação manual de lembretes solicitada")
        self._verificar_eventos_amanha()
    
    def testar_notificacao(self, evento_teste: dict):
        """
        Testa o sistema de notificação com um evento de exemplo.
        
        Args:
            evento_teste (dict): Dados do evento para teste
        """
        if not self.notificacao_eventos:
            logger.error("Sistema de notificação não está inicializado")
            return False
            
        try:
            logger.info("Testando notificação de evento criado...")
            self.notificacao_eventos.notificar_evento_criado(evento_teste)
            
            logger.info("Testando lembrete de evento...")
            self.notificacao_eventos.notificar_lembrete_evento(evento_teste)
            
            return True
        except Exception as e:
            logger.error(f"Erro no teste de notificação: {e}")
            return False
    
    def obter_tecnicos_eventos(self):
        """
        Depreciado: não mantemos mais técnicos localmente; envio é por função via API externa.
        Retorna lista vazia por compatibilidade.
        """
        return []
