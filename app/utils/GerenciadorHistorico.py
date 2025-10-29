# app/utils/GerenciadorHistorico.py
"""
Gerenciador de Histórico de Alterações
Rastreia todas as modificações em feriados e eventos
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional, List, Dict, Any
from flask import g

logger = logging.getLogger('EventosFeriados.historico')

class GerenciadorHistorico:
    """Gerencia o histórico de alterações em um banco SQLite"""
    
    _instance = None
    _lock = Lock()
    
    def __init__(self, db_path: str = None):
        """
        Inicializa o gerenciador de histórico
        
        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        if db_path is None:
            from ..config import DATA_DIR
            db_path = Path(DATA_DIR) / 'historico_alteracoes.db'
        
        self.db_path = str(db_path)
        self._init_database()
        logger.info(f"Gerenciador de histórico inicializado: {self.db_path}")
    
    @classmethod
    def get_instance(cls, db_path: str = None) -> 'GerenciadorHistorico':
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
            
            # Tabela de histórico
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    tipo_entidade TEXT NOT NULL,
                    entidade_id TEXT NOT NULL,
                    operacao TEXT NOT NULL,
                    usuario TEXT,
                    usuario_nome TEXT,
                    dados_anteriores TEXT,
                    dados_novos TEXT,
                    campos_alterados TEXT,
                    ip_origem TEXT,
                    user_agent TEXT
                )
            ''')
            
            # Índices para melhor performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON historico(timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_entidade 
                ON historico(tipo_entidade, entidade_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_usuario 
                ON historico(usuario)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_operacao 
                ON historico(operacao)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Banco de dados de histórico inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def _get_usuario_atual(self) -> tuple:
        """
        Obtém informações do usuário atual da requisição Flask
        
        Returns:
            Tupla (usuario, usuario_nome, ip_origem, user_agent)
        """
        try:
            from flask import request, g
            
            usuario = getattr(g, 'current_user', {}).get('usuario', 'sistema')
            usuario_nome = getattr(g, 'current_user', {}).get('nome', 'Sistema')
            ip_origem = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent') if request else None
            
            return usuario, usuario_nome, ip_origem, user_agent
        except:
            return 'sistema', 'Sistema', None, None
    
    def registrar_alteracao(
        self,
        tipo_entidade: str,
        entidade_id: str,
        operacao: str,
        dados_anteriores: Optional[Dict] = None,
        dados_novos: Optional[Dict] = None,
        usuario: Optional[str] = None,
        usuario_nome: Optional[str] = None
    ) -> int:
        """
        Registra uma alteração no histórico
        
        Args:
            tipo_entidade: Tipo da entidade ('feriado' ou 'evento')
            entidade_id: ID da entidade alterada
            operacao: Tipo de operação ('criar', 'editar', 'excluir')
            dados_anteriores: Dados antes da alteração (para editar/excluir)
            dados_novos: Dados após a alteração (para criar/editar)
            usuario: Usuário responsável (opcional, obtido do contexto Flask)
            usuario_nome: Nome do usuário (opcional)
        
        Returns:
            ID do registro criado
        """
        try:
            # Obter informações do usuário se não fornecidas
            if usuario is None or usuario_nome is None:
                user, user_nome, ip, ua = self._get_usuario_atual()
                usuario = usuario or user
                usuario_nome = usuario_nome or user_nome
            else:
                ip, ua = None, None
            
            # Identificar campos alterados (para operação de edição)
            campos_alterados = []
            if operacao == 'editar' and dados_anteriores and dados_novos:
                for campo in dados_novos.keys():
                    if campo in dados_anteriores:
                        if dados_anteriores[campo] != dados_novos[campo]:
                            campos_alterados.append(campo)
                    else:
                        campos_alterados.append(campo)
            
            # Serializar dados para JSON
            dados_anteriores_json = json.dumps(dados_anteriores, ensure_ascii=False) if dados_anteriores else None
            dados_novos_json = json.dumps(dados_novos, ensure_ascii=False) if dados_novos else None
            campos_alterados_json = json.dumps(campos_alterados, ensure_ascii=False) if campos_alterados else None
            
            # Inserir no banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO historico (
                    tipo_entidade, entidade_id, operacao, usuario, usuario_nome,
                    dados_anteriores, dados_novos, campos_alterados,
                    ip_origem, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tipo_entidade,
                entidade_id,
                operacao,
                usuario,
                usuario_nome,
                dados_anteriores_json,
                dados_novos_json,
                campos_alterados_json,
                ip,
                ua
            ))
            
            registro_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Alteração registrada: {operacao} {tipo_entidade} {entidade_id} por {usuario}")
            
            return registro_id
            
        except Exception as e:
            logger.error(f"Erro ao registrar alteração: {e}")
            raise
    
    def obter_historico(
        self,
        tipo_entidade: Optional[str] = None,
        entidade_id: Optional[str] = None,
        usuario: Optional[str] = None,
        operacao: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        limite: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Consulta o histórico com filtros
        
        Args:
            tipo_entidade: Filtrar por tipo ('feriado' ou 'evento')
            entidade_id: Filtrar por ID específico
            usuario: Filtrar por usuário
            operacao: Filtrar por operação ('criar', 'editar', 'excluir')
            data_inicio: Data/hora inicial
            data_fim: Data/hora final
            limite: Número máximo de registros
            offset: Offset para paginação
        
        Returns:
            Lista de registros do histórico
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Construir query dinâmica
            query = "SELECT * FROM historico WHERE 1=1"
            params = []
            
            if tipo_entidade:
                query += " AND tipo_entidade = ?"
                params.append(tipo_entidade)
            
            if entidade_id:
                query += " AND entidade_id = ?"
                params.append(entidade_id)
            
            if usuario:
                query += " AND usuario = ?"
                params.append(usuario)
            
            if operacao:
                query += " AND operacao = ?"
                params.append(operacao)
            
            if data_inicio:
                query += " AND timestamp >= ?"
                params.append(data_inicio.isoformat())
            
            if data_fim:
                query += " AND timestamp <= ?"
                params.append(data_fim.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limite, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Converter para dicionários
            historico = []
            for row in rows:
                registro = dict(row)
                
                # Deserializar JSON
                if registro['dados_anteriores']:
                    registro['dados_anteriores'] = json.loads(registro['dados_anteriores'])
                
                if registro['dados_novos']:
                    registro['dados_novos'] = json.loads(registro['dados_novos'])
                
                if registro['campos_alterados']:
                    registro['campos_alterados'] = json.loads(registro['campos_alterados'])
                
                historico.append(registro)
            
            conn.close()
            
            return historico
            
        except Exception as e:
            logger.error(f"Erro ao consultar histórico: {e}")
            return []
    
    def obter_historico_entidade(
        self,
        tipo_entidade: str,
        entidade_id: str,
        limite: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtém o histórico completo de uma entidade específica
        
        Args:
            tipo_entidade: Tipo da entidade ('feriado' ou 'evento')
            entidade_id: ID da entidade
            limite: Número máximo de registros
        
        Returns:
            Lista de alterações da entidade
        """
        return self.obter_historico(
            tipo_entidade=tipo_entidade,
            entidade_id=entidade_id,
            limite=limite
        )
    
    def obter_estatisticas(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas do histórico
        
        Args:
            data_inicio: Data inicial para filtro
            data_fim: Data final para filtro
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Filtros de data
            where_clause = "WHERE 1=1"
            params = []
            
            if data_inicio:
                where_clause += " AND timestamp >= ?"
                params.append(data_inicio.isoformat())
            
            if data_fim:
                where_clause += " AND timestamp <= ?"
                params.append(data_fim.isoformat())
            
            # Total de alterações
            cursor.execute(f"SELECT COUNT(*) FROM historico {where_clause}", params)
            total_alteracoes = cursor.fetchone()[0]
            
            # Por tipo de entidade
            cursor.execute(f"""
                SELECT tipo_entidade, COUNT(*) as total
                FROM historico {where_clause}
                GROUP BY tipo_entidade
            """, params)
            por_tipo = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Por operação
            cursor.execute(f"""
                SELECT operacao, COUNT(*) as total
                FROM historico {where_clause}
                GROUP BY operacao
            """, params)
            por_operacao = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Por usuário (top 10)
            cursor.execute(f"""
                SELECT usuario, usuario_nome, COUNT(*) as total
                FROM historico {where_clause}
                GROUP BY usuario, usuario_nome
                ORDER BY total DESC
                LIMIT 10
            """, params)
            por_usuario = [
                {'usuario': row[0], 'nome': row[1], 'total': row[2]}
                for row in cursor.fetchall()
            ]
            
            # Últimas alterações
            cursor.execute(f"""
                SELECT timestamp, tipo_entidade, operacao, usuario_nome
                FROM historico {where_clause}
                ORDER BY timestamp DESC
                LIMIT 5
            """, params)
            ultimas = [
                {
                    'timestamp': row[0],
                    'tipo_entidade': row[1],
                    'operacao': row[2],
                    'usuario_nome': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'total_alteracoes': total_alteracoes,
                'por_tipo_entidade': por_tipo,
                'por_operacao': por_operacao,
                'top_usuarios': por_usuario,
                'ultimas_alteracoes': ultimas
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def limpar_historico_antigo(self, dias: int = 365) -> int:
        """
        Remove registros antigos do histórico
        
        Args:
            dias: Número de dias a manter (padrão: 365)
        
        Returns:
            Número de registros removidos
        """
        try:
            from datetime import timedelta
            
            data_limite = datetime.now() - timedelta(days=dias)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM historico WHERE timestamp < ?",
                (data_limite.isoformat(),)
            )
            
            registros_removidos = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Removidos {registros_removidos} registros antigos do histórico")
            
            return registros_removidos
            
        except Exception as e:
            logger.error(f"Erro ao limpar histórico antigo: {e}")
            return 0
    
    def exportar_historico(
        self,
        caminho_arquivo: str,
        formato: str = 'json',
        **filtros
    ) -> bool:
        """
        Exporta o histórico para arquivo
        
        Args:
            caminho_arquivo: Caminho do arquivo de saída
            formato: Formato de exportação ('json' ou 'csv')
            **filtros: Filtros para aplicar (mesmos de obter_historico)
        
        Returns:
            True se exportado com sucesso
        """
        try:
            historico = self.obter_historico(limite=999999, **filtros)
            
            if formato == 'json':
                with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                    json.dump(historico, f, ensure_ascii=False, indent=2)
            
            elif formato == 'csv':
                import csv
                
                if not historico:
                    return False
                
                with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as f:
                    campos = ['id', 'timestamp', 'tipo_entidade', 'entidade_id', 
                             'operacao', 'usuario', 'usuario_nome']
                    
                    writer = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(historico)
            
            else:
                raise ValueError(f"Formato não suportado: {formato}")
            
            logger.info(f"Histórico exportado: {caminho_arquivo}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar histórico: {e}")
            return False
