# API Pública - Eventos e Feriados TCE-GO

## Visão Geral

API REST pública para consulta de eventos e feriados do Tribunal de Contas do Estado de Goiás.

**Base URL:** `https://automacao.tce.go.gov.br/EventosFeriados/api`

**Autenticação:** Não requerida (endpoints públicos)

**Formato:** JSON

---

## Endpoints - Feriados

### 📅 Listar Feriados

```http
GET /public/feriados
```

Lista todos os feriados com filtros opcionais.

**Parâmetros Query String:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `ano` | int | Não | Filtrar por ano específico (ex: 2025) |
| `mes` | int | Não | Filtrar por mês (1-12) |
| `ano_minimo` | int | Não | Listar a partir de um ano |
| `data_inicial` | string | Não | Filtrar a partir de data (YYYY-MM-DD) |
| `data_final` | string | Não | Filtrar até data (YYYY-MM-DD) |

**Exemplos:**

```bash
# Todos os feriados de 2025
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025

# Feriados de dezembro de 2025
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025&mes=12

# Feriados entre duas datas
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?data_inicial=2025-11-01&data_final=2025-12-31"
```

**Resposta (200 OK):**

```json
{
  "sucesso": true,
  "total": 10,
  "feriados": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "nome": "Confraternização Universal",
      "data": "2025-01-01",
      "tipo": "nacional",
      "dia_semana": "Quarta-feira"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "nome": "Natal",
      "data": "2025-12-25",
      "tipo": "nacional",
      "dia_semana": "Quinta-feira"
    }
  ]
}
```

---

### 📅 Obter Feriado Específico

```http
GET /public/feriados/{id}
```

Obtém detalhes de um feriado pelo ID.

**Parâmetros de URL:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id` | string | ID do feriado (UUID) |

**Exemplo:**

```bash
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/550e8400-e29b-41d4-a716-446655440000
```

**Resposta (200 OK):**

```json
{
  "sucesso": true,
  "feriado": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nome": "Natal",
    "data": "2025-12-25",
    "tipo": "nacional",
    "dia_semana": "Quinta-feira"
  }
}
```

**Resposta (404 Not Found):**

```json
{
  "erro": "Feriado não encontrado"
}
```

---

### 📅 Verificar se Data é Feriado

```http
GET /public/feriados/verificar
```

Verifica se uma data específica é feriado.

**Parâmetros Query String:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `data` | string | Sim | Data a verificar (YYYY-MM-DD) |

**Exemplo:**

```bash
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar?data=2025-12-25"
```

**Resposta (200 OK) - É feriado:**

```json
{
  "sucesso": true,
  "data": "2025-12-25",
  "eh_feriado": true,
  "feriado": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nome": "Natal",
    "tipo": "nacional"
  }
}
```

**Resposta (200 OK) - Não é feriado:**

```json
{
  "sucesso": true,
  "data": "2025-11-15",
  "eh_feriado": false,
  "feriado": null
}
```

---

## Endpoints - Eventos

### 📆 Listar Eventos

```http
GET /public/eventos
```

Lista todos os eventos com filtros opcionais.

**Parâmetros Query String:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `ano` | int | Não | Filtrar por ano específico |
| `mes` | int | Não | Filtrar por mês (1-12) |
| `local` | string | Não | Filtrar por local ("Plenário" ou "Auditório") |
| `ano_minimo` | int | Não | Listar a partir de um ano |
| `data_inicial` | string | Não | Filtrar a partir de data (YYYY-MM-DD) |
| `data_final` | string | Não | Filtrar até data (YYYY-MM-DD) |
| `ativos_apenas` | bool | Não | Se true, retorna apenas eventos não encerrados |

**Exemplos:**

```bash
# Todos os eventos de novembro/2025
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?ano=2025&mes=11

# Eventos do Plenário ainda ativos
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?local=Plenário&ativos_apenas=true"

# Eventos entre duas datas
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?data_inicial=2025-11-01&data_final=2025-11-30"
```

**Resposta (200 OK):**

```json
{
  "sucesso": true,
  "total": 3,
  "eventos": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "titulo": "Sessão Plenária Ordinária",
      "data": "2025-11-15",
      "hora": "14:00",
      "local": "Plenário",
      "descricao": "Julgamento de processos",
      "encerrado": false
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "titulo": "Palestra TCE Transparente",
      "data": "2025-11-20",
      "hora": "10:00",
      "local": "Auditório",
      "descricao": "Palestra sobre transparência pública",
      "encerrado": false
    }
  ]
}
```

---

### 📆 Obter Evento Específico

```http
GET /public/eventos/{id}
```

Obtém detalhes de um evento pelo ID.

**Parâmetros de URL:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id` | string | ID do evento (UUID) |

**Exemplo:**

```bash
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos/660e8400-e29b-41d4-a716-446655440000
```

**Resposta (200 OK):**

```json
{
  "sucesso": true,
  "evento": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "titulo": "Sessão Plenária Ordinária",
    "data": "2025-11-15",
    "hora": "14:00",
    "local": "Plenário",
    "descricao": "Julgamento de processos administrativos",
    "encerrado": false
  }
}
```

---

### 📆 Listar Eventos por Data

```http
GET /public/eventos/por-data
```

Lista eventos em uma data específica.

**Parâmetros Query String:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `data` | string | Sim | Data a consultar (YYYY-MM-DD) |
| `local` | string | Não | Filtrar por local |

**Exemplo:**

```bash
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos/por-data?data=2025-11-15"
```

**Resposta (200 OK):**

```json
{
  "sucesso": true,
  "data": "2025-11-15",
  "total": 2,
  "eventos": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "titulo": "Sessão Plenária Ordinária",
      "hora": "14:00",
      "local": "Plenário"
    }
  ]
}
```

---

### 📆 Listar Locais de Eventos

```http
GET /public/eventos/locais
```

Lista todos os locais onde eventos podem ocorrer.

**Exemplo:**

```bash
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos/locais
```

**Resposta (200 OK):**

```json
{
  "sucesso": true,
  "locais": ["Plenário", "Auditório"]
}
```

---

## Endpoint - Informações da API

### ℹ️ Informações da API

```http
GET /public/info
```

Retorna informações sobre a API pública, incluindo versão e endpoints disponíveis.

**Exemplo:**

```bash
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/info
```

**Resposta (200 OK):**

```json
{
  "nome": "API Pública - Eventos e Feriados TCE-GO",
  "versao": "1.0.0",
  "descricao": "API pública para consulta de feriados e eventos",
  "autenticacao": "Não requerida",
  "base_url": "https://automacao.tce.go.gov.br/EventosFeriados/api",
  "endpoints": {
    "feriados": {
      "GET /public/feriados": "Lista todos os feriados",
      "GET /public/feriados/<id>": "Obtém detalhes de um feriado",
      "GET /public/feriados/verificar?data=YYYY-MM-DD": "Verifica se é feriado"
    },
    "eventos": {
      "GET /public/eventos": "Lista todos os eventos",
      "GET /public/eventos/<id>": "Obtém detalhes de um evento",
      "GET /public/eventos/por-data?data=YYYY-MM-DD": "Eventos em uma data",
      "GET /public/eventos/locais": "Lista locais de eventos"
    }
  },
  "exemplos": {
    "listar_feriados_2025": "/public/feriados?ano=2025",
    "verificar_natal": "/public/feriados/verificar?data=2025-12-25",
    "eventos_plenario": "/public/eventos?local=Plenário&ativos_apenas=true"
  }
}
```

---

## Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Requisição bem-sucedida |
| 400 | Requisição inválida (parâmetros faltando ou inválidos) |
| 404 | Recurso não encontrado |
| 500 | Erro interno do servidor |
| 503 | Serviço temporariamente indisponível |

---

## Exemplos de Uso

### Python

```python
import requests

# Listar feriados de 2025
response = requests.get(
    'https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados',
    params={'ano': 2025}
)
feriados = response.json()['feriados']

# Verificar se data é feriado
response = requests.get(
    'https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar',
    params={'data': '2025-12-25'}
)
eh_feriado = response.json()['eh_feriado']

# Listar eventos do Plenário
response = requests.get(
    'https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos',
    params={'local': 'Plenário', 'ativos_apenas': True}
)
eventos = response.json()['eventos']
```

### JavaScript (fetch)

```javascript
// Listar feriados de 2025
fetch('https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025')
  .then(response => response.json())
  .then(data => {
    console.log('Feriados:', data.feriados);
  });

// Verificar se é feriado
fetch('https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar?data=2025-12-25')
  .then(response => response.json())
  .then(data => {
    console.log('É feriado?', data.eh_feriado);
  });

// Listar eventos
fetch('https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?local=Plenário')
  .then(response => response.json())
  .then(data => {
    console.log('Eventos:', data.eventos);
  });
```

### PowerShell

```powershell
# Listar feriados de 2025
$response = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025"
$response.feriados

# Verificar se é feriado
$response = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar?data=2025-12-25"
$response.eh_feriado

# Listar eventos
$response = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?local=Plenário"
$response.eventos
```

### cURL

```bash
# Listar feriados de 2025 (formatado com jq)
curl -s "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025" | jq .

# Verificar se é feriado
curl -s "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar?data=2025-12-25" | jq '.eh_feriado'

# Listar eventos do Plenário
curl -s "https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?local=Plenário" | jq '.eventos'
```

---

## Rate Limiting

Atualmente não há limite de requisições, mas recomenda-se:
- Máximo de 60 requisições por minuto por IP
- Implementar cache local quando possível
- Uso responsável para não sobrecarregar o servidor

---

## Suporte

Para dúvidas ou problemas com a API:
- **Email:** ti@tce.go.gov.br
- **Documentação completa:** https://automacao.tce.go.gov.br/EventosFeriados

---

## Changelog

### v1.0.0 (2025-10-29)
- Lançamento inicial da API pública
- Endpoints para consulta de feriados
- Endpoints para consulta de eventos
- Filtros por data, ano, mês e local
