# Sistema de Histórico de Alterações

## Visão Geral

Sistema completo de auditoria que registra **todas as alterações** (criar, editar, excluir) em feriados e eventos, armazenando informações detalhadas sobre quem fez, quando fez e o que mudou.

**Banco de Dados:** SQLite (`historico_alteracoes.db`)  
**Localização:** `/var/softwaresTCE/dados/eventos_feriados/`  
**Autenticação:** Integrado com sistema de autenticação via HelpDesk Monitor

---

## Arquitetura

```
┌─────────────────────────────────────────┐
│      Gerenciador de Feriados/Eventos   │
│  ┌──────────────────────────────────┐  │
│  │ adicionar_feriado/evento()       │──┐
│  │ atualizar_feriado/evento()       │──┤
│  │ remover_feriado/evento()         │──┤
│  └──────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │ registrar_alteracao()
                  ▼
┌──────────────────────────────────────────┐
│      GerenciadorHistorico (Singleton)    │
│  ┌────────────────────────────────────┐  │
│  │ - Captura contexto do usuário     │  │
│  │ - Identifica campos alterados     │  │
│  │ - Serializa dados (JSON)          │  │
│  │ - Persiste em SQLite              │  │
│  └────────────────────────────────────┘  │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│     SQLite Database (historico.db)       │
│  ┌────────────────────────────────────┐  │
│  │ Tabela: historico                  │  │
│  │ - timestamp                        │  │
│  │ - tipo_entidade (feriado/evento)  │  │
│  │ - entidade_id                      │  │
│  │ - operacao (criar/editar/excluir) │  │
│  │ - usuario + usuario_nome           │  │
│  │ - dados_anteriores (JSON)          │  │
│  │ - dados_novos (JSON)               │  │
│  │ - campos_alterados (JSON)          │  │
│  │ - ip_origem + user_agent           │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## Estrutura do Banco de Dados

### Tabela: `historico`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER PRIMARY KEY | ID único do registro |
| `timestamp` | TIMESTAMP | Data/hora da alteração |
| `tipo_entidade` | TEXT | "feriado" ou "evento" |
| `entidade_id` | TEXT | ID do feriado/evento alterado |
| `operacao` | TEXT | "criar", "editar" ou "excluir" |
| `usuario` | TEXT | Login do usuário |
| `usuario_nome` | TEXT | Nome completo do usuário |
| `dados_anteriores` | TEXT (JSON) | Estado antes da alteração |
| `dados_novos` | TEXT (JSON) | Estado após a alteração |
| `campos_alterados` | TEXT (JSON) | Lista de campos modificados |
| `ip_origem` | TEXT | IP de onde partiu a requisição |
| `user_agent` | TEXT | Navegador/cliente utilizado |

### Índices

- `idx_timestamp` - Ordenação por data DESC
- `idx_entidade` - Busca por tipo_entidade + entidade_id
- `idx_usuario` - Busca por usuário
- `idx_operacao` - Filtro por tipo de operação

---

## API de Histórico

### 📊 Listar Histórico

```http
GET /api/historico
```

**Parâmetros Query String:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `tipo_entidade` | string | Filtrar por "feriado" ou "evento" |
| `entidade_id` | string | ID específico |
| `usuario` | string | Filtrar por login |
| `operacao` | string | "criar", "editar" ou "excluir" |
| `data_inicio` | datetime | Data/hora inicial (ISO 8601) |
| `data_fim` | datetime | Data/hora final (ISO 8601) |
| `limite` | int | Máximo de registros (padrão: 100) |
| `offset` | int | Offset para paginação (padrão: 0) |

**Exemplo:**

```bash
curl -u usuario:senha \
  "https://automacao.tce.go.gov.br/EventosFeriados/api/historico?tipo_entidade=feriado&limite=50"
```

**Resposta:**

```json
{
  "sucesso": true,
  "total": 50,
  "limite": 50,
  "offset": 0,
  "registros": [
    {
      "id": 123,
      "timestamp": "2025-10-29T14:30:00",
      "tipo_entidade": "feriado",
      "entidade_id": "20251225_natal_1730217600",
      "operacao": "editar",
      "usuario": "joao.silva",
      "usuario_nome": "João da Silva",
      "dados_anteriores": {
        "nome": "Natal",
        "hora_inicio": "00:00",
        "hora_fim": "23:59"
      },
      "dados_novos": {
        "nome": "Natal",
        "hora_inicio": "06:00",
        "hora_fim": "18:00"
      },
      "campos_alterados": ["hora_inicio", "hora_fim"],
      "ip_origem": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

---

### 📊 Histórico de Entidade Específica

```http
GET /api/historico/entidade/{tipo_entidade}/{entidade_id}
```

Obtém todo o histórico de um feriado ou evento específico.

**Exemplo:**

```bash
curl -u usuario:senha \
  "https://automacao.tce.go.gov.br/EventosFeriados/api/historico/entidade/feriado/20251225_natal_1730217600"
```

---

### 📊 Alterações Recentes

```http
GET /api/historico/recentes
```

**Parâmetros:**
- `limite` (opcional): Número de registros (padrão: 20)

Retorna as últimas alterações no sistema.

**Exemplo:**

```bash
curl -u usuario:senha \
  "https://automacao.tce.go.gov.br/EventosFeriados/api/historico/recentes?limite=10"
```

---

### 📊 Estatísticas do Histórico

```http
GET /api/historico/estatisticas
```

**Parâmetros:**
- `periodo`: Atalho ("hoje", "semana", "mes", "ano")
- `data_inicio`: Data inicial personalizada
- `data_fim`: Data final personalizada

**Exemplo:**

```bash
curl -u usuario:senha \
  "https://automacao.tce.go.gov.br/EventosFeriados/api/historico/estatisticas?periodo=mes"
```

**Resposta:**

```json
{
  "sucesso": true,
  "periodo": {
    "data_inicio": "2025-09-29T00:00:00",
    "data_fim": null,
    "descricao": "mes"
  },
  "estatisticas": {
    "total_alteracoes": 245,
    "por_tipo_entidade": {
      "feriado": 120,
      "evento": 125
    },
    "por_operacao": {
      "criar": 80,
      "editar": 145,
      "excluir": 20
    },
    "top_usuarios": [
      {
        "usuario": "joao.silva",
        "nome": "João da Silva",
        "total": 65
      },
      {
        "usuario": "maria.santos",
        "nome": "Maria Santos",
        "total": 48
      }
    ],
    "ultimas_alteracoes": [...]
  }
}
```

---

### 💾 Exportar Histórico

```http
POST /api/historico/exportar
```

Exporta o histórico para arquivo JSON ou CSV.

**Body JSON:**

```json
{
  "formato": "json",
  "filtros": {
    "tipo_entidade": "evento",
    "data_inicio": "2025-10-01T00:00:00",
    "data_fim": "2025-10-31T23:59:59"
  }
}
```

**Resposta:** Download automático do arquivo

**Exemplo:**

```bash
curl -X POST -u usuario:senha \
  -H "Content-Type: application/json" \
  -d '{"formato":"csv","filtros":{"periodo":"mes"}}' \
  "https://automacao.tce.go.gov.br/EventosFeriados/api/historico/exportar" \
  -o historico.csv
```

---

### 🗑️ Limpar Histórico Antigo

```http
POST /api/historico/limpar-antigo
```

Remove registros com mais de X dias (padrão: 365).

**Body JSON:**

```json
{
  "dias": 730
}
```

**Exemplo:**

```bash
curl -X POST -u usuario:senha \
  -H "Content-Type: application/json" \
  -d '{"dias":365}' \
  "https://automacao.tce.go.gov.br/EventosFeriados/api/historico/limpar-antigo"
```

---

## Integração Automática

O histórico é registrado **automaticamente** em todas as operações de CRUD:

### Feriados

```python
# app/utils/GerenciadorFeriados.py

def adicionar_feriado(self, dados):
    # ... validação e criação ...
    self.feriados.append(novo_feriado)
    self._salvar_feriados()
    
    # Registro automático no histórico
    historico.registrar_alteracao(
        tipo_entidade='feriado',
        entidade_id=novo_feriado['id'],
        operacao='criar',
        dados_novos=novo_feriado
    )
```

### Eventos

```python
# app/utils/GerenciadorEventos.py

def atualizar_evento(self, evento_id, dados):
    dados_anteriores = evento.copy()  # Snapshot antes
    
    # ... atualização ...
    
    # Registro automático no histórico
    historico.registrar_alteracao(
        tipo_entidade='evento',
        entidade_id=evento_id,
        operacao='editar',
        dados_anteriores=dados_anteriores,
        dados_novos=evento
    )
```

---

## Contexto Capturado

O sistema captura automaticamente:

### Do Usuário (Flask Context)
- **Usuário**: Login do técnico autenticado
- **Nome**: Nome completo do HelpDesk Monitor
- **IP**: Endereço IP de origem
- **User-Agent**: Navegador/cliente utilizado

### Da Alteração
- **Dados Anteriores**: Estado completo antes da mudança
- **Dados Novos**: Estado completo após a mudança
- **Campos Alterados**: Lista específica de campos modificados
- **Timestamp**: Data/hora precisa da operação

---

## Casos de Uso

### 1. Auditoria de Alterações

```bash
# Quem editou o feriado de Natal?
curl -u user:pass \
  "/api/historico/entidade/feriado/20251225_natal_1730217600"
```

### 2. Rastreamento de Usuário

```bash
# O que o usuário joão.silva fez hoje?
curl -u user:pass \
  "/api/historico?usuario=joao.silva&data_inicio=2025-10-29T00:00:00"
```

### 3. Reversão de Alterações

```python
# Obter estado anterior
historico = obter_historico(entidade_id=id)
dados_anteriores = historico[0]['dados_anteriores']

# Restaurar
atualizar_feriado(id, dados_anteriores)
```

### 4. Relatório Mensal

```bash
# Exportar todas as alterações do mês
curl -X POST -u user:pass \
  -H "Content-Type: application/json" \
  -d '{"formato":"csv","filtros":{"periodo":"mes"}}' \
  "/api/historico/exportar" -o relatorio_outubro.csv
```

### 5. Dashboard de Atividades

```bash
# Estatísticas da semana
curl -u user:pass \
  "/api/historico/estatisticas?periodo=semana"
```

---

## Performance

### Otimizações

- **Índices**: 4 índices para consultas rápidas
- **Paginação**: Limite padrão de 100 registros
- **Serialização**: JSON compacto sem dados desnecessários
- **Singleton**: Uma instância compartilhada do gerenciador

### Tamanho Estimado

- **Registro médio**: ~2KB
- **100 alterações/dia**: ~200KB/dia = ~6MB/mês
- **1 ano**: ~70MB

### Limpeza Automática

Recomendado executar periodicamente:

```python
# Manter apenas 1 ano de histórico
gerenciador.limpar_historico_antigo(dias=365)
```

---

## Segurança

### Autenticação
- Todos os endpoints exigem `@require_auth_api`
- Validação via HelpDesk Monitor API
- Função "EVENTOS_FERIADOS" requerida

### Auditoria
- Registro imutável (INSERT-only)
- Não permite edição de registros históricos
- Captura IP e User-Agent para rastreamento

### Privacidade
- Não armazena senhas
- Dados sensíveis podem ser excluídos após período

---

## Manutenção

### Backup do Banco

```bash
# Copiar banco de dados
cp /var/softwaresTCE/dados/eventos_feriados/historico_alteracoes.db \
   /backup/historico_$(date +%Y%m%d).db
```

### Verificar Tamanho

```bash
# Tamanho do banco
du -h /var/softwaresTCE/dados/eventos_feriados/historico_alteracoes.db

# Total de registros
sqlite3 historico_alteracoes.db "SELECT COUNT(*) FROM historico"
```

### Limpeza Manual

```sql
-- Remover registros com mais de 2 anos
DELETE FROM historico 
WHERE timestamp < datetime('now', '-2 years');

-- Vacuum para liberar espaço
VACUUM;
```

---

## Monitoramento

### Logs

```bash
# Ver logs do histórico
sudo journalctl -u EventosFeriados.service | grep "historico"

# Últimas inserções
sudo tail -f /var/softwaresTCE/logs/eventos_feriados/eventos_feriados.log | grep "Alteração registrada"
```

### Métricas

```python
# Via API
estatisticas = requests.get('/api/historico/estatisticas?periodo=hoje')

# Alertar se volume anormal
if estatisticas['total_alteracoes'] > 1000:
    enviar_alerta('Volume anormal de alterações')
```

---

## Troubleshooting

### Problema: Histórico não registra

**Verificar:**
1. Banco de dados existe e tem permissões corretas
2. GerenciadorHistorico inicializado no app
3. Logs de erro durante operação

```bash
# Verificar banco
ls -lh /var/softwaresTCE/dados/eventos_feriados/historico_alteracoes.db

# Testar conexão
sqlite3 historico_alteracoes.db "SELECT COUNT(*) FROM historico"
```

### Problema: Banco muito grande

**Solução:**
```python
# Limpar registros antigos
limpar_historico_antigo(dias=180)

# Exportar antes de limpar
exportar_historico('backup.json', formato='json')
```

### Problema: Consultas lentas

**Solução:**
1. Verificar índices: `PRAGMA index_list(historico)`
2. Usar filtros específicos (tipo_entidade, entidade_id)
3. Reduzir limite de registros
4. Executar VACUUM periodicamente

---

## Exemplos de Consultas

### SQL Direto

```sql
-- Top 10 usuários mais ativos
SELECT usuario_nome, COUNT(*) as total
FROM historico
WHERE timestamp >= datetime('now', '-30 days')
GROUP BY usuario_nome
ORDER BY total DESC
LIMIT 10;

-- Alterações por hora do dia
SELECT strftime('%H', timestamp) as hora, COUNT(*) as total
FROM historico
GROUP BY hora
ORDER BY hora;

-- Feriados mais editados
SELECT entidade_id, COUNT(*) as edicoes
FROM historico
WHERE tipo_entidade = 'feriado' AND operacao = 'editar'
GROUP BY entidade_id
ORDER BY edicoes DESC
LIMIT 10;
```

### Python

```python
from app.utils.GerenciadorHistorico import GerenciadorHistorico

# Obter histórico
historico = GerenciadorHistorico.get_instance()

# Últimas 50 alterações
registros = historico.obter_historico(limite=50)

# Alterações de um usuário específico
alteracoes_joao = historico.obter_historico(usuario='joao.silva')

# Estatísticas do mês
stats = historico.obter_estatisticas(periodo='mes')
```

---

## Arquivos

- **Gerenciador**: `app/utils/GerenciadorHistorico.py`
- **API**: `app/routes/api_historico.py`
- **Banco**: `/var/softwaresTCE/dados/eventos_feriados/historico_alteracoes.db`

---

## Roadmap Futuro

- [ ] Interface web para visualização do histórico
- [ ] Comparação visual (diff) entre versões
- [ ] Restauração com um clique
- [ ] Notificações de alterações suspeitas
- [ ] Exportação para Excel
- [ ] Gráficos de atividade
- [ ] Integração com sistema de backup
