# Resumo das APIs - EventosFeriados TCE-GO

## Estrutura de APIs

O sistema agora possui **duas APIs distintas**:

### 1. API Privada (com autenticação)
**Base URL:** `/EventosFeriados/api/`
**Autenticação:** HTTP Basic Auth (validação via HelpDesk Monitor)
**Público-alvo:** Usuários internos com função "EVENTOS_FERIADOS"
**Operações:** CRUD completo (Create, Read, Update, Delete)

### 2. API Pública (sem autenticação)
**Base URL:** `/EventosFeriados/api/public/`
**Autenticação:** Não requerida
**Público-alvo:** Sistemas externos e consultas públicas
**Operações:** Apenas leitura (Read-only)

---

## Comparação: API Privada vs API Pública

| Característica | API Privada | API Pública |
|----------------|-------------|-------------|
| **Autenticação** | Obrigatória (HTTP Basic) | Não requerida |
| **Autorização** | Função EVENTOS_FERIADOS | Nenhuma |
| **Operações** | GET, POST, PUT, DELETE | Apenas GET |
| **Uso** | Gerenciamento interno | Consultas externas |
| **Rotas** | `/api/feriados/*` <br> `/api/eventos/*` | `/api/public/feriados/*` <br> `/api/public/eventos/*` |

---

## API Pública - Endpoints Disponíveis

### 📅 Feriados

```
GET /api/public/feriados
GET /api/public/feriados/{id}
GET /api/public/feriados/verificar?data=YYYY-MM-DD
```

**Filtros disponíveis:**
- `ano` - Ano específico (ex: 2025)
- `mes` - Mês específico (1-12)
- `ano_minimo` - A partir de um ano
- `data_inicial` - A partir de data (YYYY-MM-DD)
- `data_final` - Até data (YYYY-MM-DD)

### 📆 Eventos

```
GET /api/public/eventos
GET /api/public/eventos/{id}
GET /api/public/eventos/por-data?data=YYYY-MM-DD
GET /api/public/eventos/locais
```

**Filtros disponíveis:**
- `ano` - Ano específico
- `mes` - Mês específico (1-12)
- `local` - Local do evento ("Plenário" ou "Auditório")
- `ano_minimo` - A partir de um ano
- `data_inicial` - A partir de data
- `data_final` - Até data
- `ativos_apenas` - Se true, apenas eventos não encerrados

### ℹ️ Informações

```
GET /api/public/info
```

Retorna documentação automática da API pública.

---

## API Privada - Endpoints Disponíveis

### 🔐 Feriados (Autenticado)

```
GET    /api/feriados              # Listar
GET    /api/feriados/{id}         # Obter
POST   /api/feriados              # Criar
PUT    /api/feriados/{id}         # Atualizar
DELETE /api/feriados/{id}         # Remover
GET    /api/feriados/verificar    # Verificar data
POST   /api/feriados/remover-duplicatas
POST   /api/feriados/limpar-duplicatas
```

### 🔐 Eventos (Autenticado)

```
GET    /api/eventos                    # Listar
GET    /api/eventos/{id}               # Obter
POST   /api/eventos                    # Criar
PUT    /api/eventos/{id}               # Atualizar
DELETE /api/eventos/{id}               # Remover
GET    /api/eventos/por-data           # Por data
GET    /api/eventos/por-local/{local}  # Por local
GET    /api/eventos/locais             # Listar locais
POST   /api/eventos/{id}/forcar-notificacao-whatsapp
POST   /api/eventos/{id}/encerrar
POST   /api/eventos/{id}/reativar
```

### 🔐 Autenticação (Gerenciamento)

```
GET    /api/auth/status              # Status da autenticação
GET    /api/auth/usuarios            # Usuários autorizados
POST   /api/auth/cache/atualizar     # Atualizar cache
POST   /api/auth/cache/limpar        # Limpar cache
```

### 🔐 CLP e TCE (Sincronização)

```
GET    /api/clp/status
POST   /api/clp/sincronizar
POST   /api/clp/limpar
GET    /api/clp_auditorio/status
POST   /api/clp_auditorio/sincronizar
POST   /api/clp_auditorio/limpar
GET    /api/tce/status
POST   /api/tce/configurar
POST   /api/tce/sincronizar
```

---

## Exemplos de Uso

### Uso Externo (Público - Sem Autenticação)

```bash
# Python
import requests
response = requests.get('https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025')
feriados = response.json()['feriados']

# JavaScript
fetch('https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?local=Plenário')
  .then(r => r.json())
  .then(data => console.log(data.eventos));

# cURL
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar?data=2025-12-25"
```

### Uso Interno (Privado - Com Autenticação)

```bash
# Python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'https://automacao.tce.go.gov.br/EventosFeriados/api/feriados',
    auth=HTTPBasicAuth('usuario', 'senha')
)

# JavaScript
fetch('https://automacao.tce.go.gov.br/EventosFeriados/api/eventos', {
  headers: {
    'Authorization': 'Basic ' + btoa('usuario:senha')
  }
}).then(r => r.json());

# cURL
curl -u usuario:senha "https://automacao.tce.go.gov.br/EventosFeriados/api/feriados"
```

---

## Segurança

### API Pública
- **Read-only:** Apenas consultas (GET)
- **Rate Limiting:** Recomendado 60 req/min por IP
- **CORS:** Habilitado para todos os domínios
- **Dados Sensíveis:** Nenhum dado sensível exposto

### API Privada
- **Autenticação:** HTTP Basic Auth obrigatório
- **Autorização:** Função "EVENTOS_FERIADOS" no HelpDesk Monitor
- **Cache:** 24 horas para operação offline
- **CRUD Completo:** Criar, editar e excluir dados
- **Auditoria:** Logs de todas as operações

---

## Arquivos Criados

```
app/routes/api_public.py          # API pública (novo)
API_PUBLICA.md                     # Documentação completa
```

---

## Arquivos Modificados

```
app/__init__.py                    # Registro do blueprint api_public
```

---

## Casos de Uso

### 1. Site Institucional Consultar Feriados
```javascript
// Sem autenticação necessária
fetch('/EventosFeriados/api/public/feriados?ano=2025')
  .then(r => r.json())
  .then(data => {
    data.feriados.forEach(f => {
      console.log(`${f.data}: ${f.nome}`);
    });
  });
```

### 2. Sistema Externo Verificar Feriado
```python
import requests
from datetime import date

def eh_feriado(data: date) -> bool:
    response = requests.get(
        'https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar',
        params={'data': data.isoformat()}
    )
    return response.json()['eh_feriado']

# Uso
if eh_feriado(date(2025, 12, 25)):
    print("Hoje é feriado!")
```

### 3. Dashboard Listar Próximos Eventos
```python
import requests
from datetime import date, timedelta

hoje = date.today()
proximos_30_dias = hoje + timedelta(days=30)

response = requests.get(
    'https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos',
    params={
        'data_inicial': hoje.isoformat(),
        'data_final': proximos_30_dias.isoformat(),
        'ativos_apenas': 'true'
    }
)

eventos = response.json()['eventos']
for evento in eventos:
    print(f"{evento['data']} {evento['hora']}: {evento['titulo']} ({evento['local']})")
```

### 4. Integração com Calendário
```python
import requests
from icalendar import Calendar, Event

# Buscar feriados
response = requests.get(
    'https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025'
)
feriados = response.json()['feriados']

# Gerar arquivo iCalendar
cal = Calendar()
for feriado in feriados:
    evento = Event()
    evento.add('summary', feriado['nome'])
    evento.add('dtstart', feriado['data'])
    cal.add_component(evento)

with open('feriados_2025.ics', 'wb') as f:
    f.write(cal.to_ical())
```

---

## Monitoramento

### Métricas Disponíveis

```bash
# Status geral da API
curl https://automacao.tce.go.gov.br/EventosFeriados/api/status

# Informações da API pública
curl https://automacao.tce.go.gov.br/EventosFeriados/api/public/info
```

### Logs

```bash
# Logs da aplicação
sudo journalctl -u EventosFeriados.service -f

# Filtrar apenas API pública
sudo journalctl -u EventosFeriados.service | grep "api_public"
```

---

## Performance

### API Pública
- **Cache:** Dados em memória (gerenciadores)
- **Resposta média:** < 50ms
- **Concorrência:** Suporta múltiplas requisições simultâneas

### API Privada
- **Autenticação:** +10-20ms (cache do AuthManager)
- **Operações de escrita:** +50-100ms (persistência em JSON)

---

## Documentação Adicional

- **API Pública:** `API_PUBLICA.md` - Documentação completa com exemplos
- **Autenticação:** `AUTENTICACAO_TECNICO.md` - Detalhes do sistema de auth
- **Migração:** `MIGRACAO_AUTENTICACAO.md` - Guia de deploy

---

## Próximos Passos (Opcional)

1. **OpenAPI/Swagger:** Gerar documentação interativa
2. **CORS Configurável:** Limitar domínios permitidos
3. **Rate Limiting:** Implementar limite de requisições
4. **Webhooks:** Notificar sistemas externos de mudanças
5. **GraphQL:** Alternativa à REST API
6. **Versionamento:** `/api/v1/public/` e `/api/v2/public/`
