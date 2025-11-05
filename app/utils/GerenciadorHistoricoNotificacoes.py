# app/utils/GerenciadorHistoricoNotificacoes.py
"""
Gerenciador de Histórico de Notificações
Rastreia todas as notificações enviadas via WhatsApp e Email
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional, List, Dict, Any

logger = logging.getLogger('EventosFeriados.historico_notificacoes')

class GerenciadorHistoricoNotificacoes:
    """Gerencia o histórico de notificações em um banco SQLite"""
    
    _instance = None
    _lock = Lock()
    
    def __init__(self, db_path: str = None):
        """
        Inicializa o gerenciador de histórico de notificações
        
        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        if db_path is None:
            from ..config import DATA_DIR
            db_path = Path(DATA_DIR) / 'historico_notificacoes.db'
        
        self.db_path = str(db_path)
        self._init_database()
        logger.info(f"Gerenciador de histórico de notificações inicializado: {self.db_path}")
    
    @classmethod
    def get_instance(cls, db_path: str = None) -> 'GerenciadorHistoricoNotificacoes':
        """Retorna a instância singleton do gerenciador"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance
    
    def _init_database(self):
        """Inicializa o banco de dados e cria as tabelas se não existirem"""
        try:
            # Garantir que o diretório existe
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela de histórico de notificações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historico_notificacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    canal TEXT NOT NULL,
                    destinatarios TEXT,
                    assunto TEXT,
                    mensagem TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detalhes TEXT,
                    evento_id INTEGER,
                    evento_titulo TEXT,
                    duracao_ms INTEGER,
                    response_code INTEGER,
                    error_message TEXT
                )
            ''')
            
            # Índices para melhorar performance de consultas
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON historico_notificacoes(timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status 
                ON historico_notificacoes(status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tipo 
                ON historico_notificacoes(tipo)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_canal 
                ON historico_notificacoes(canal)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Banco de dados de histórico de notificações inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados de notificações: {e}")
            raise
    
    def registrar_notificacao(
        self,
        tipo: str,
        canal: str,
        mensagem: str,
        status: str,
        destinatarios: Optional[List[str]] = None,
        assunto: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None,
        evento_id: Optional[int] = None,
        evento_titulo: Optional[str] = None,
        duracao_ms: Optional[int] = None,
        response_code: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[int]:
        """
        Registra uma notificação no histórico
        
        Args:
            tipo: Tipo de notificação (lembrete_1h, lembrete_30min, evento_hoje, etc.)
            canal: Canal de envio (whatsapp, email)
            mensagem: Conteúdo da mensagem enviada
            status: Status do envio (sucesso, erro, pendente)
            destinatarios: Lista de destinatários (telefones ou emails)
            assunto: Assunto (para emails)
            detalhes: Informações adicionais em formato dict
            evento_id: ID do evento relacionado
            evento_titulo: Título do evento relacionado
            duracao_ms: Tempo de resposta da API em ms
            response_code: Código HTTP de resposta
            error_message: Mensagem de erro se houver
            
        Returns:
            ID do registro criado ou None em caso de erro
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            destinatarios_json = json.dumps(destinatarios) if destinatarios else None
            detalhes_json = json.dumps(detalhes, ensure_ascii=False) if detalhes else None
            
            cursor.execute('''
                INSERT INTO historico_notificacoes (
                    timestamp, tipo, canal, destinatarios, assunto, mensagem,
                    status, detalhes, evento_id, evento_titulo, duracao_ms,
                    response_code, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, tipo, canal, destinatarios_json, assunto, mensagem,
                status, detalhes_json, evento_id, evento_titulo, duracao_ms,
                response_code, error_message
            ))
            
            notificacao_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.debug(f"Notificação registrada: ID={notificacao_id}, tipo={tipo}, canal={canal}, status={status}")
            return notificacao_id
            
        except Exception as e:
            logger.error(f"Erro ao registrar notificação: {e}")
            return None
    
    def buscar_notificacoes(
        self,
        limite: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        canal: Optional[str] = None,
        tipo: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca notificações no histórico com filtros opcionais
        
        Args:
            limite: Número máximo de registros
            offset: Deslocamento para paginação
            status: Filtrar por status
            canal: Filtrar por canal
            tipo: Filtrar por tipo
            data_inicio: Data/hora início (ISO format)
            data_fim: Data/hora fim (ISO format)
            
        Returns:
            Lista de notificações
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM historico_notificacoes WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if canal:
                query += " AND canal = ?"
                params.append(canal)
            
            if tipo:
                query += " AND tipo = ?"
                params.append(tipo)
            
            if data_inicio:
                query += " AND timestamp >= ?"
                params.append(data_inicio)
            
            if data_fim:
                query += " AND timestamp <= ?"
                params.append(data_fim)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limite, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            notificacoes = []
            for row in rows:
                notificacao = dict(row)
                # Parse JSON fields
                if notificacao['destinatarios']:
                    try:
                        notificacao['destinatarios'] = json.loads(notificacao['destinatarios'])
                    except:
                        pass
                if notificacao['detalhes']:
                    try:
                        notificacao['detalhes'] = json.loads(notificacao['detalhes'])
                    except:
                        pass
                notificacoes.append(notificacao)
            
            conn.close()
            return notificacoes
            
        except Exception as e:
            logger.error(f"Erro ao buscar notificações: {e}")
            return []
    
    def contar_notificacoes(
        self,
        status: Optional[str] = None,
        canal: Optional[str] = None,
        tipo: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> int:
        """
        Conta o número total de notificações com os filtros aplicados
        
        Returns:
            Número total de notificações
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) FROM historico_notificacoes WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if canal:
                query += " AND canal = ?"
                params.append(canal)
            
            if tipo:
                query += " AND tipo = ?"
                params.append(tipo)
            
            if data_inicio:
                query += " AND timestamp >= ?"
                params.append(data_inicio)
            
            if data_fim:
                query += " AND timestamp <= ?"
                params.append(data_fim)
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Erro ao contar notificações: {e}")
            return 0
    
    def obter_estatisticas(self, dias: int = 7) -> Dict[str, Any]:
        """
        Obtém estatísticas de notificações dos últimos N dias
        
        Args:
            dias: Número de dias para análise
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data_limite = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            data_limite = (data_limite - timedelta(days=dias)).isoformat()
            
            # Total de notificações
            cursor.execute(
                "SELECT COUNT(*) FROM historico_notificacoes WHERE timestamp >= ?",
                (data_limite,)
            )
            total = cursor.fetchone()[0]
            
            # Por status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM historico_notificacoes 
                WHERE timestamp >= ?
                GROUP BY status
            """, (data_limite,))
            por_status = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Por canal
            cursor.execute("""
                SELECT canal, COUNT(*) as count 
                FROM historico_notificacoes 
                WHERE timestamp >= ?
                GROUP BY canal
            """, (data_limite,))
            por_canal = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Por tipo
            cursor.execute("""
                SELECT tipo, COUNT(*) as count 
                FROM historico_notificacoes 
                WHERE timestamp >= ?
                GROUP BY tipo
                ORDER BY count DESC
                LIMIT 10
            """, (data_limite,))
            por_tipo = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Taxa de sucesso
            sucesso = por_status.get('sucesso', 0)
            taxa_sucesso = (sucesso / total * 100) if total > 0 else 0
            
            conn.close()
            
            return {
                'total': total,
                'por_status': por_status,
                'por_canal': por_canal,
                'por_tipo': por_tipo,
                'taxa_sucesso': round(taxa_sucesso, 2),
                'dias_analisados': dias
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def limpar_antigos(self, dias: int = 90) -> int:
        """
        Remove notificações mais antigas que N dias
        
        Args:
            dias: Dias de retenção
            
        Returns:
            Número de registros removidos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            from datetime import timedelta
            data_limite = datetime.now() - timedelta(days=dias)
            data_limite_iso = data_limite.isoformat()
            
            cursor.execute(
                "DELETE FROM historico_notificacoes WHERE timestamp < ?",
                (data_limite_iso,)
            )
            
            removidos = cursor.rowcount
            conn.commit()
            conn.close()
            
            if removidos > 0:
                logger.info(f"Removidas {removidos} notificações antigas (>{dias} dias)")
            
            return removidos
            
        except Exception as e:
            logger.error(f"Erro ao limpar notificações antigas: {e}")
            return 0
