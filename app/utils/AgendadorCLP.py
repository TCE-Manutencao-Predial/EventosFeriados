# app/utils/AgendadorCLP.py
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from .SincronizadorCLP import SincronizadorCLP

class AgendadorCLP:
    """
    Classe responsável por agendar e executar sincronizações automáticas com CLP
    Executa em thread separada para não bloquear a aplicação
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.AgendadorCLP')
        self.sincronizador = SincronizadorCLP.get_instance()
        self.thread_agendador: Optional[threading.Thread] = None
        self.executando = False
        self.gerenciador_feriados = None
        self.gerenciador_eventos = None
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do agendador (Singleton)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def inicializar_gerenciadores(self, gerenciador_feriados, gerenciador_eventos):
        """Inicializa as referências aos gerenciadores"""
        self.gerenciador_feriados = gerenciador_feriados
        self.gerenciador_eventos = gerenciador_eventos
        self.logger.info("Gerenciadores inicializados no agendador CLP")
    
    def _loop_agendador(self):
        """Loop principal do agendador executado em thread separada"""
        self.logger.info("Agendador CLP iniciado")
        
        while self.executando:
            try:
                # Verificar se deve executar sincronização
                if self.sincronizador.deve_sincronizar_automaticamente():
                    if self.gerenciador_feriados and self.gerenciador_eventos:
                        self.logger.info("Executando sincronização automática")
                        resultado = self.sincronizador.sincronizar_manual(
                            self.gerenciador_feriados, 
                            self.gerenciador_eventos
                        )
                        
                        if resultado['sucesso']:
                            self.logger.info(f"Sincronização automática concluída: {resultado['dados_sincronizados']} itens")
                        else:
                            self.logger.error(f"Falha na sincronização automática: {resultado.get('erro', 'Erro desconhecido')}")
                    else:
                        self.logger.warning("Gerenciadores não inicializados para sincronização automática")
                
                # Dormir por 1 minuto antes da próxima verificação
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Erro no loop do agendador: {e}")
                time.sleep(60)  # Continuar mesmo com erro
        
        self.logger.info("Agendador CLP finalizado")
    
    def iniciar(self):
        """Inicia o agendador em thread separada"""
        if self.executando:
            self.logger.warning("Agendador já está executando")
            return
        
        self.executando = True
        self.thread_agendador = threading.Thread(
            target=self._loop_agendador,
            name="AgendadorCLP",
            daemon=True
        )
        self.thread_agendador.start()
        self.logger.info("Agendador CLP iniciado em thread separada")
    
    def parar(self):
        """Para o agendador"""
        if not self.executando:
            self.logger.warning("Agendador não está executando")
            return
        
        self.executando = False
        if self.thread_agendador and self.thread_agendador.is_alive():
            self.thread_agendador.join(timeout=5)
        
        self.logger.info("Agendador CLP parado")
    
    def status(self) -> dict:
        """Retorna o status do agendador"""
        return {
            'executando': self.executando,
            'thread_ativa': self.thread_agendador.is_alive() if self.thread_agendador else False,
            'gerenciadores_inicializados': bool(self.gerenciador_feriados and self.gerenciador_eventos),
            'proximo_horario': self._calcular_proximo_horario()
        }
    
    def _calcular_proximo_horario(self) -> Optional[str]:
        """Calcula o próximo horário de sincronização"""
        if not self.sincronizador.config['SYNC_ENABLED']:
            return None
        
        agora = datetime.now()
        horarios = self.sincronizador.config['SYNC_TIMES']
        
        for horario in horarios:
            hora, minuto = map(int, horario.split(':'))
            proximo = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            
            if proximo > agora:
                return proximo.strftime('%H:%M')
        
        # Se não há horário hoje, pegar o primeiro de amanhã
        if horarios:
            hora, minuto = map(int, horarios[0].split(':'))
            proximo = (agora + timedelta(days=1)).replace(hour=hora, minute=minuto, second=0, microsecond=0)
            return proximo.strftime('%H:%M (amanhã)')
        
        return None
