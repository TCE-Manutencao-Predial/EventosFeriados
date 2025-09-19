import logging
import os
from threading import Timer, Lock
from typing import Optional
from datetime import datetime


class _DebouncedTask:
    def __init__(self, delay_seconds: float):
        self.delay = delay_seconds
        self._timer: Optional[Timer] = None
        self._lock = Lock()

    def schedule(self, func):
        with self._lock:
            if self._timer is not None:
                try:
                    self._timer.cancel()
                except Exception:
                    pass
                self._timer = None

            self._timer = Timer(self.delay, func)
            self._timer.daemon = True
            self._timer.start()


class AutoSyncCLP:
    """Gerencia disparos de sincronização de CLP com debounce por destino.

    Destinos: 'plenario', 'auditorio'.
    """

    _instance = None
    _inst_lock = Lock()

    def __init__(self, delay_seconds: Optional[float] = None):
        self.logger = logging.getLogger('EventosFeriados.AutoSyncCLP')
        # Debounce configurável por env (default 5s)
        if delay_seconds is None:
            try:
                delay_seconds = float(os.environ.get('CLP_AUTOSYNC_DEBOUNCE', '5'))
            except Exception:
                delay_seconds = 5.0
        self.delay = delay_seconds
        self.logger.info(f"AutoSyncCLP iniciado com debounce de {self.delay}s")

        self._tasks = {
            'plenario': _DebouncedTask(self.delay),
            'auditorio': _DebouncedTask(self.delay),
        }
        self._lock = Lock()

    @classmethod
    def get_instance(cls) -> 'AutoSyncCLP':
        if cls._instance is None:
            with cls._inst_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _schedule(self, destino: str, integrador):
        if integrador is None:
            self.logger.warning(f"Integrador para '{destino}' indisponível. Ignorando autosync.")
            return

        def _run():
            try:
                self.logger.info(f"Executando autosync debounced para '{destino}' às {datetime.now().isoformat()}")
                res = integrador.sincronizar_dados()
                if not res.get('sucesso', False):
                    self.logger.error(f"Autosync '{destino}' falhou: {res}")
                else:
                    self.logger.info(f"Autosync '{destino}' concluído: {res.get('dados_sincronizados')}")
            except Exception as e:
                self.logger.error(f"Erro no autosync '{destino}': {e}")

        task = self._tasks.get(destino)
        if not task:
            self.logger.error(f"Destino desconhecido para autosync: {destino}")
            return
        task.schedule(_run)

    def trigger_for_local(self, local: Optional[str], integracao_plenario, integracao_auditorio, aud_locais: Optional[list] = None):
        """Agenda sincronização para o CLP correspondente ao local do evento."""
        try:
            if not local:
                return

            # Locais do auditório podem ser passados (config) para evitar import circular
            aud_locais = aud_locais or ['Auditório Nobre', 'Foyer do Auditório']

            if local in aud_locais:
                self._schedule('auditorio', integracao_auditorio)
            elif local == 'Plenário':
                self._schedule('plenario', integracao_plenario)
            else:
                # Outros locais não são controlados pelos CLPs atuais
                self.logger.debug(f"Autosync ignorado para local '{local}' (sem CLP mapeado)")
        except Exception as e:
            self.logger.error(f"Erro ao agendar autosync para local '{local}': {e}")
