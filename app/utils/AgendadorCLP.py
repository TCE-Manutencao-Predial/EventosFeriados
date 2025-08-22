# app/utils/AgendadorCLP.py
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from .SincronizadorCLP import SincronizadorCLP
from .SincronizadorCLPAuditorio import SincronizadorCLPAuditorio
from .SincronizadorTCE import SincronizadorTCE

class AgendadorCLP:
    """
    Classe responsável por agendar e executar sincronizações automáticas com CLPs e TCE
    Executa em thread separada para não bloquear a aplicação
    Gerencia tanto o CLP do Plenário quanto o CLP do Auditório e eventos do TCE
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.AgendadorCLP')
        self.sincronizador_plenario = SincronizadorCLP.get_instance()
        self.sincronizador_auditorio = SincronizadorCLPAuditorio.get_instance()
        self.sincronizador_tce = SincronizadorTCE.get_instance()
        self.thread_agendador: Optional[threading.Thread] = None
        self.executando = False
        self.gerenciador_feriados = None
        self.gerenciador_eventos = None
        
        # Configuração de sincronização TCE
        self.tce_config = {
            'SYNC_ENABLED': True,
            'SYNC_TIME': '08:00',  # Sincronizar às 8h da manhã
            'ultima_sincronizacao': None
        }
        
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
    
    def _deve_sincronizar_tce(self) -> bool:
        """Verifica se deve executar sincronização do TCE"""
        if not self.tce_config['SYNC_ENABLED']:
            return False
        
        agora = datetime.now()
        hora_sync = datetime.strptime(self.tce_config['SYNC_TIME'], '%H:%M').time()
        
        # Verificar se estamos no horário de sincronização (com tolerância de 1 minuto)
        if not (agora.time().hour == hora_sync.hour and 
                abs(agora.time().minute - hora_sync.minute) <= 1):
            return False
        
        # Verificar se já sincronizou hoje neste horário
        ultima_sync = self.tce_config['ultima_sincronizacao']
        if ultima_sync:
            try:
                dt_ultima = datetime.fromisoformat(ultima_sync)
                if (dt_ultima.date() == agora.date() and 
                    dt_ultima.time().hour == hora_sync.hour):
                    return False  # Já sincronizou hoje neste horário
            except:
                pass  # Se der erro no parse, continua para sincronizar
        
        return True
    
    def _loop_agendador(self):
        """Loop principal do agendador executado em thread separada"""
        self.logger.info("Agendador iniciado (CLP Plenário + CLP Auditório + TCE)")
        
        while self.executando:
            try:
                # Verificar se deve executar sincronização do TCE
                if self._deve_sincronizar_tce():
                    self.logger.info("Executando sincronização automática TCE")
                    resultado = self.sincronizador_tce.sincronizar_periodo_atual()
                    
                    if resultado['sucesso']:
                        self.logger.info(f"Sincronização automática TCE concluída: {resultado['total_eventos_criados']} eventos processados")
                        self.tce_config['ultima_sincronizacao'] = datetime.now().isoformat()
                    else:
                        self.logger.error(f"Falha na sincronização automática TCE: {resultado.get('erro', 'Erro desconhecido')}")
                
                # Verificar se deve executar sincronização do CLP Plenário
                if self.sincronizador_plenario.deve_sincronizar_automaticamente():
                    if self.gerenciador_feriados and self.gerenciador_eventos:
                        self.logger.info("Executando sincronização automática CLP Plenário")
                        resultado = self.sincronizador_plenario.sincronizar_manual(
                            self.gerenciador_feriados, 
                            self.gerenciador_eventos
                        )
                        
                        if resultado['sucesso']:
                            self.logger.info(f"Sincronização automática CLP Plenário concluída: {resultado['dados_sincronizados']} itens")
                        else:
                            self.logger.error(f"Falha na sincronização automática CLP Plenário: {resultado.get('erro', 'Erro desconhecido')}")
                    else:
                        self.logger.warning("Gerenciadores não inicializados para sincronização automática CLP Plenário")
                
                # Verificar se deve executar sincronização do CLP Auditório
                if self.sincronizador_auditorio.config['SYNC_ENABLED']:
                    # Usar a mesma lógica de horários do CLP Plenário
                    deve_sincronizar = False
                    agora = datetime.now()
                    
                    for horario in self.sincronizador_auditorio.config['SYNC_TIMES']:
                        try:
                            hora_sync = datetime.strptime(horario.strip(), '%H:%M').time()
                            
                            # Verificar se estamos no horário de sincronização (com tolerância de 1 minuto)
                            if (agora.time().hour == hora_sync.hour and 
                                abs(agora.time().minute - hora_sync.minute) <= 1):
                                
                                # Verificar se já sincronizou hoje neste horário
                                ultima_sync = self.sincronizador_auditorio.ultimo_status.get('ultima_sincronizacao')
                                if ultima_sync:
                                    try:
                                        dt_ultima = datetime.fromisoformat(ultima_sync)
                                        if (dt_ultima.date() == agora.date() and 
                                            dt_ultima.time().hour == hora_sync.hour):
                                            continue  # Já sincronizou hoje neste horário
                                    except:
                                        pass  # Se der erro no parse, continua para sincronizar
                                
                                deve_sincronizar = True
                                break
                        except Exception as e:
                            self.logger.error(f"Erro ao processar horário de sincronização '{horario}': {e}")
                    
                    if deve_sincronizar and self.gerenciador_eventos:
                        self.logger.info("Executando sincronização automática CLP Auditório")
                        resultado = self.sincronizador_auditorio.sincronizar_manual(self.gerenciador_eventos)
                        
                        if resultado['sucesso']:
                            self.logger.info(f"Sincronização automática CLP Auditório concluída: {resultado['dados_sincronizados']} itens")
                        else:
                            self.logger.error(f"Falha na sincronização automática CLP Auditório: {resultado.get('erro', 'Erro desconhecido')}")
                
                # Dormir por 1 minuto antes da próxima verificação
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Erro no loop do agendador: {e}")
                time.sleep(60)  # Continuar mesmo com erro
        
        self.logger.info("Agendador finalizado")
    
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
        self.logger.info("Agendador iniciado em thread separada")
    
    def parar(self):
        """Para o agendador"""
        if not self.executando:
            self.logger.warning("Agendador não está executando")
            return
        
        self.executando = False
        if self.thread_agendador and self.thread_agendador.is_alive():
            self.thread_agendador.join(timeout=5)
        
        self.logger.info("Agendador parado")
    
    def configurar_tce(self, habilitado: bool = True, horario: str = '08:00'):
        """Configura a sincronização do TCE"""
        self.tce_config['SYNC_ENABLED'] = habilitado
        self.tce_config['SYNC_TIME'] = horario
        self.logger.info(f"Configuração TCE atualizada - Habilitado: {habilitado}, Horário: {horario}")
    
    def sincronizar_tce_manual(self) -> dict:
        """Executa sincronização manual do TCE"""
        self.logger.info("Executando sincronização manual TCE")
        resultado = self.sincronizador_tce.sincronizar_periodo_atual()
        
        if resultado['sucesso']:
            self.tce_config['ultima_sincronizacao'] = datetime.now().isoformat()
            self.logger.info(f"Sincronização manual TCE concluída: {resultado['total_eventos_criados']} eventos processados")
        else:
            self.logger.error(f"Falha na sincronização manual TCE: {resultado.get('erro', 'Erro desconhecido')}")
        
        return resultado
    
    def status(self) -> dict:
        """Retorna o status do agendador"""
        return {
            'executando': self.executando,
            'thread_ativa': self.thread_agendador.is_alive() if self.thread_agendador else False,
            'gerenciadores_inicializados': bool(self.gerenciador_feriados and self.gerenciador_eventos),
            'proximo_horario_plenario': self._calcular_proximo_horario('plenario'),
            'proximo_horario_auditorio': self._calcular_proximo_horario('auditorio'),
            'proximo_horario_tce': self._calcular_proximo_horario('tce'),
            'status_plenario': self.sincronizador_plenario.ultimo_status,
            'status_auditorio': self.sincronizador_auditorio.ultimo_status,
            'status_tce': self.tce_config
        }
    
    def _calcular_proximo_horario(self, clp_tipo: str) -> Optional[str]:
        """Calcula o próximo horário de sincronização"""
        agora = datetime.now()
        
        if clp_tipo == 'tce':
            if not self.tce_config['SYNC_ENABLED']:
                return None
            
            hora, minuto = map(int, self.tce_config['SYNC_TIME'].split(':'))
            proximo = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            
            if proximo <= agora:
                proximo += timedelta(days=1)
            
            return proximo.strftime('%H:%M' + (' (amanhã)' if proximo.date() > agora.date() else ''))
        
        elif clp_tipo == 'plenario':
            sincronizador = self.sincronizador_plenario
        else:  # auditorio
            sincronizador = self.sincronizador_auditorio
            
        if not sincronizador.config['SYNC_ENABLED']:
            return None
        
        horarios = sincronizador.config['SYNC_TIMES']
        
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
