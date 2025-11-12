# Documentação - EventosFeriados TCE-GO

## 📚 Índice de Documentação

Esta pasta contém toda a documentação do sistema de Eventos e Feriados do TCE-GO.

### API Pública

- **[API_PUBLICA.md](API_PUBLICA.md)** - Documentação completa da API pública REST
  - Endpoints disponíveis
  - Exemplos de uso em Python, JavaScript, PowerShell e cURL
  - Filtros e parâmetros
  - Códigos de status HTTP

- **[exemplo_api_publica.html](exemplo_api_publica.html)** - Demonstração interativa da API
  - Interface visual para testar os endpoints
  - Exemplos práticos de integração
  - Visualização de respostas em tempo real

### Documentação Adicional

- **[app/docs/API_EXTERNA.md](../app/docs/API_EXTERNA.md)** - Documentação de APIs externas integradas ao sistema

## 🚀 Início Rápido

### Consultar Feriados

```bash
# Listar todos os feriados de 2025
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados?ano=2025"

# Verificar se uma data é feriado
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/feriados/verificar?data=2025-12-25"
```

### Consultar Eventos

```bash
# Listar eventos do Plenário
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos?local=Plenário"

# Eventos de uma data específica
curl "https://automacao.tce.go.gov.br/EventosFeriados/api/public/eventos/por-data?data=2025-11-15"
```

## 🔗 Links Úteis

- **API Base URL:** `https://automacao.tce.go.gov.br/EventosFeriados/api/public`
- **Demonstração Interativa:** [exemplo_api_publica.html](exemplo_api_publica.html)
- **Informações da API:** `GET /api/public/info`

## 📝 Observações

- A API pública **não requer autenticação**
- Todos os endpoints retornam dados em formato JSON
- Operações disponíveis: apenas leitura (GET)
- Para operações de escrita (CRUD), é necessário usar a API privada com autenticação

## 💡 Suporte

Para dúvidas ou problemas:
- **Email:** ti@tce.go.gov.br
- **Repositório:** TCE-Manutencao-Predial/eventos-feriados
