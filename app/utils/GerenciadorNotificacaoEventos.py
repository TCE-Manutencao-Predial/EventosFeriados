import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Optional
from app.alarmes.NotificacaoEventos import NotificacaoEventos
from app.alarmes.ClassesSistema import ConfigNotificacao, MetodoContato
from app.alarmes.agenda_contatos import inicializar_tecnicos
from app.utils.GerenciadorEventos import GerenciadorEventos

logger = logging.getLogger('EventosFeriados')

class GerenciadorNotificacaoEventos:
    """
    Gerenciador responsável por coordenar as notificações de eventos.
    
    Esta classe gerencia tanto as notificações imediatas (quando um evento é criado)
    quanto os lembretes programados (um dia antes do evento às 8h00).
    """
    
    _instance = None
    
    def __init__(self):
        self.notificacao_eventos: Optional[NotificacaoEventos] = None
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
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
            
            # Carrega a lista de técnicos
            tecnicos = inicializar_tecnicos()
            
            # Cria a instância de notificação
            self.notificacao_eventos = NotificacaoEventos(
                config_notificacao=config,
                tecnicos=tecnicos,
                metodo_notificacao=MetodoContato.WHATSAPP
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
    
    def iniciar_scheduler_lembretes(self):
        """Inicia o agendador para envio de lembretes diários"""
        if self.running:
            logger.warning("Scheduler de lembretes já está em execução")
            return
            
        # Agenda verificação diária às 8:00
        schedule.every().day.at("08:00").do(self._verificar_eventos_amanha)
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._executar_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler de lembretes de eventos iniciado (verificação diária às 08:00)")
    
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
        Retorna a lista de técnicos que têm a função EVENTOS.
        
        Returns:
            list: Lista de técnicos com função EVENTOS
        """
        if not self.notificacao_eventos:
            return []
            
        from app.alarmes.ClassesSistema import FuncoesTecnicos
        
        tecnicos_eventos = [
            tecnico for tecnico in self.notificacao_eventos.tecnicos
            if FuncoesTecnicos.EVENTOS in tecnico.funcoes
        ]
        
        return tecnicos_eventos
