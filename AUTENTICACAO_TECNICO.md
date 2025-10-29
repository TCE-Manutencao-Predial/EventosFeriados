# Sistema de Autenticação - Resumo Técnico

## Visão Geral

Sistema de autenticação baseado em HTTP Basic Auth validando credenciais contra API externa do HelpDesk Monitor, com cache persistente para operação offline.

## Arquitetura

```
┌─────────────────┐
│  Cliente Web    │
│  (HTTP Basic)   │
└────────┬────────┘
         │ Authorization: Basic base64(user:pass)
         ▼
┌─────────────────────────────────────────┐
│         Flask Application               │
│  ┌───────────────────────────────────┐  │
│  │  auth_decorators.py               │  │
│  │  - @require_auth (web)            │  │
│  │  - @require_auth_api (API)        │  │
│  │  - @optional_auth                 │  │
│  └───────────┬───────────────────────┘  │
│              │ verificar_autorizacao()  │
│              ▼                           │
│  ┌───────────────────────────────────┐  │
│  │  AuthManager (Singleton)          │  │
│  │  - Cache em memória (dict)        │  │
│  │  - Cache em disco (JSON)          │  │
│  │  - Validade: 24h                  │  │
│  └─────┬─────────────────────┬───────┘  │
└────────┼─────────────────────┼──────────┘
         │                     │
         │ API disponível      │ API indisponível
         ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│ HelpDesk Monitor│   │  Cache JSON      │
│ API             │   │  (24h válido)    │
│ /api/tecnicos/  │   │  usuarios_*.json │
│ por_funcao/     │   └──────────────────┘
│ EVENTOS_FERIADOS│
└─────────────────┘
```

## Componentes Principais

### 1. AuthManager (`app/utils/AuthManager.py`)

**Responsabilidades:**
- Consultar API do HelpDesk Monitor
- Gerenciar cache em memória e disco
- Validar credenciais de usuários
- Filtrar usuários por função e disponibilidade

**Métodos Principais:**
```python
verificar_autorizacao(username: str) -> Tuple[bool, Optional[Dict]]
  """Verifica se usuário tem acesso ao sistema"""
  
_atualizar_cache_da_api() -> bool
  """Consulta API e atualiza cache (se disponível)"""
  
_carregar_cache() -> Dict
  """Carrega cache do disco"""
  
_salvar_cache() -> None
  """Persiste cache em disco"""
```

**Fluxo de Validação:**
1. Verifica cache em memória
2. Se expirado (>24h), tenta atualizar da API
3. Se API falhar, usa cache em disco
4. Busca usuário no cache
5. Retorna (autorizado, dados_usuario)

### 2. Decoradores (`app/utils/auth_decorators.py`)

**@require_auth** - Rotas Web
```python
@web_bp.route('/')
@require_auth
def index():
    # g.current_user contém dados do usuário
    return render_template('index.html')
```
- Retorna WWW-Authenticate header
- Redireciona para página de erro 401/403
- Armazena usuário em `flask.g.current_user`

**@require_auth_api** - Rotas API
```python
@api_bp.route('/dados')
@require_auth_api
def obter_dados():
    return jsonify({'user': g.current_user})
```
- Retorna JSON com erro
- Códigos: 401 (sem auth), 403 (sem permissão), 500 (erro interno)

**@optional_auth** - Autenticação Opcional
```python
@api_bp.route('/public')
@optional_auth
def rota_publica():
    if g.current_user:
        # Usuário autenticado
    else:
        # Acesso público
```

### 3. API de Gerenciamento (`app/routes/api_auth.py`)

**Endpoints:**

`GET /api/auth/status`
- Status de autenticação do usuário atual
- Informações do cache

`GET /api/auth/usuarios`
- Lista todos os usuários autorizados
- Total e status do cache

`POST /api/auth/cache/atualizar`
- Força atualização do cache da API
- Retorna estatísticas

`POST /api/auth/cache/limpar`
- Limpa cache (emergência)
- Força recarga na próxima autenticação

## Formato do Cache

**Arquivo:** `/var/softwaresTCE/dados/eventos_feriados/usuarios_autorizados_cache.json`

```json
{
  "usuarios": [
    {
      "nome": "Nome Completo",
      "usuario": "login",
      "email": "email@tce.go.gov.br"
    }
  ],
  "ultima_atualizacao": "2024-01-15T10:30:00"
}
```

**Características:**
- Formato JSON legível
- Timestamp ISO 8601
- Apenas usuários disponíveis (não em férias)
- Validade: 24 horas desde `ultima_atualizacao`

## Integração com API Externa

**Base URL:** `https://automacao.tce.go.gov.br/helpdeskmonitor`

**Endpoint:** `GET /api/tecnicos/por_funcao/EVENTOS_FERIADOS`

**Resposta:**
```json
[
  {
    "nome": "NOME COMPLETO",
    "usuario": "login",
    "email": "email@tce.go.gov.br",
    "funcoes": ["EVENTOS_FERIADOS", ...],
    "de_ferias": false,
    "disponivel": true
  }
]
```

**Filtros Aplicados:**
- `funcoes` contém "EVENTOS_FERIADOS"
- `disponivel == true`
- `de_ferias == false`

**Configuração:**
```python
# app/utils/AuthManager.py
API_URL = "https://automacao.tce.go.gov.br/helpdeskmonitor"
FUNCAO_REQUERIDA = "EVENTOS_FERIADOS"
CACHE_VALIDADE_HORAS = 24
```

## Segurança

### Autenticação
- HTTP Basic Auth (RFC 7617)
- Credenciais: `Authorization: Basic base64(username:password)`
- Validação contra lista controlada (não aceita qualquer usuário)

### Autorização
- Baseada em função "EVENTOS_FERIADOS"
- Verificada a cada requisição
- Cache não armazena senhas (apenas nomes de usuário)

### Proteção de Rotas
**Todas as rotas protegidas:**
- Web: 6 rotas em `web.py`
- API Feriados: 8 rotas em `api_feriados.py`
- API Eventos: ~15 rotas em `api_eventos.py`
- API CLP: ~10 rotas em `api_clp.py`
- API CLP Auditório: ~10 rotas em `api_clp_auditorio.py`
- API Auth: 4 rotas em `api_auth.py`

### Resiliência
- Cache permite operação offline (24h)
- Falha da API não bloqueia acesso imediato
- Logs detalhados de tentativas de autenticação

## Performance

### Cache em Memória
- Singleton pattern (uma instância por processo)
- Dicionário Python (O(1) lookup)
- Validação rápida sem IO de disco

### Cache em Disco
- Leitura apenas na inicialização e após expiração
- Escrita apenas após atualização bem-sucedida da API
- JSON compacto (~1KB por 10 usuários)

### Atualização Assíncrona
- Não bloqueia requisições
- Se cache válido, requisição procede imediatamente
- Atualização ocorre em background se expirado

## Monitoramento

### Logs
```python
logger.info(f"Autenticação bem-sucedida: {username}")
logger.warning(f"Usuário sem autorização: {username}")
logger.error(f"Falha ao consultar API: {erro}")
```

### Métricas Disponíveis
- Total de usuários autorizados
- Data/hora da última atualização
- Status do cache (válido/expirado)
- Sucesso/falha de consultas à API

## Troubleshooting

### Problema: Cache não atualiza
**Causa:** API indisponível ou timeout
**Solução:** 
```bash
curl -X POST -u user:pass \
  https://.../api/auth/cache/atualizar
```

### Problema: Usuário autorizado bloqueado
**Causa:** Cache desatualizado
**Verificar:**
1. Usuário tem função no HelpDesk Monitor?
2. Usuário disponível (não de férias)?
3. Cache foi atualizado nas últimas 24h?

### Problema: Todos os usuários bloqueados
**Causa:** Cache vazio ou API inacessível
**Solução:**
```bash
# Verificar cache
cat /var/.../usuarios_autorizados_cache.json

# Verificar API
curl https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/EVENTOS_FERIADOS

# Verificar logs
journalctl -u EventosFeriados.service | grep AUTH
```

## Testes

### Teste Manual de Autenticação
```bash
# Sem credenciais - deve retornar 401
curl -I https://.../EventosFeriados/

# Com credenciais válidas - deve retornar 200
curl -I -u usuario:senha https://.../EventosFeriados/

# Com credenciais inválidas - deve retornar 403
curl -I -u invalido:senha https://.../EventosFeriados/
```

### Teste da API
```bash
# Status
curl -u user:pass https://.../api/auth/status | jq .

# Usuários
curl -u user:pass https://.../api/auth/usuarios | jq .

# Forçar atualização
curl -X POST -u user:pass https://.../api/auth/cache/atualizar | jq .
```

### Teste de Resiliência
```bash
# Simular falha da API (bloquear rede)
sudo iptables -A OUTPUT -d automacao.tce.go.gov.br -j DROP

# Tentar acessar (deve usar cache)
curl -u user:pass https://.../EventosFeriados/

# Restaurar
sudo iptables -D OUTPUT -d automacao.tce.go.gov.br -j DROP
```

## Comparação: Antes vs Depois

| Aspecto | .htpasswd (Antes) | API Auth (Depois) |
|---------|-------------------|-------------------|
| Gerenciamento | Manual (htpasswd CLI) | Centralizado (HelpDesk) |
| Sincronização | Manual | Automática (24h) |
| Auditoria | Logs Apache | Logs aplicação + API |
| Offline | Sempre disponível | Cache 24h |
| Granularidade | Usuário | Usuário + Função |
| Manutenção | Deploy .htpasswd | Editar HelpDesk Monitor |
| Integração | Nenhuma | API completa |

## Dependências

```python
# requirements.txt (já existentes)
flask>=2.3.0
requests>=2.31.0

# Bibliotecas padrão
json, datetime, os, logging, threading, base64
```

## Configuração Necessária

```python
# app/config.py
DATA_DIR = '/var/softwaresTCE/dados/eventos_feriados'

# Permissões no servidor
sudo chown -R www-data:www-data /var/softwaresTCE/dados/eventos_feriados
sudo chmod 755 /var/softwaresTCE/dados/eventos_feriados
```

## Próximos Passos (Opcional)

1. **Rate Limiting**: Limitar tentativas de autenticação
2. **Auditoria**: Registrar todas as tentativas de acesso
3. **Dashboard**: Interface web para gerenciar usuários
4. **Alertas**: Notificar quando cache expira sem atualização
5. **Múltiplas Funções**: Suportar diferentes níveis de acesso
6. **Token JWT**: Alternativa ao HTTP Basic Auth
7. **2FA**: Autenticação em dois fatores

## Referências

- RFC 7617 (HTTP Basic Auth): https://tools.ietf.org/html/rfc7617
- Flask Authentication: https://flask.palletsprojects.com/en/latest/patterns/
- Python Singleton: https://python-patterns.guide/gang-of-four/singleton/
