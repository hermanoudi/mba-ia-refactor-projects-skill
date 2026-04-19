# Architecture Audit Report

**Project:** code-smells-project  
**Date:** 2026-04-18  
**Stack:** Python 3.12 + Flask 3.1.1  
**Files Analyzed:** 4 | **Lines of Code:** ~780  
**Audited By:** refactor-arch skill

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 4     |
| HIGH     | 4     |
| MEDIUM   | 3     |
| LOW      | 3     |
| **TOTAL**| **14** |

---

## Findings

---

### [CRITICAL] C2 — Hardcoded Secret Key
**File:** `app.py:7`  
**Description:** `SECRET_KEY` hardcoded diretamente no código-fonte: `"minha-chave-super-secreta-123"`.  
**Impact:** Qualquer pessoa com acesso ao repositório pode forjar sessões ou tokens JWT assinados com essa chave. Em produção, representa exposição grave de segurança.  
**Recommendation:** Mover para variável de ambiente: `os.environ.get("SECRET_KEY")` com `RuntimeError` se ausente.

---

### [CRITICAL] C3 — SQL Injection via String Concatenation (múltiplos pontos)
**File:** `models.py:28-29, 48-50, 57-60, 66, 68, 92, 109-111, 127-129, 140, 148-151, 155-161, 163-166, 174, 188, 192, 220, 279-281, 291-296`  
**Description:** Praticamente todas as queries SQL são construídas por concatenação de strings com dados externos (IDs de URL, campos do body, query params). Exemplos críticos:
- `models.py:28` — `"SELECT * FROM produtos WHERE id = " + str(id)`
- `models.py:109-111` — `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (login!)
- `models.py:291` — `query += " AND (nome LIKE '%" + termo + "%'..."` (busca de produtos)
- `models.py:48-50` — INSERT de produto com todos os campos concatenados

**Impact:** Qualquer campo de entrada pode ser usado para extrair dados, destruir tabelas ou bypassar autenticação (ex: `email = "' OR '1'='1`).  
**Recommendation:** Substituir todas as concatenações por queries parametrizadas com `?` placeholder do sqlite3.

---

### [CRITICAL] C2 — Secret Key Exposta no Endpoint /health
**File:** `controllers.py:289`  
**Description:** O endpoint `/health` retorna `"secret_key": "minha-chave-super-secreta-123"` no JSON de resposta, expondo ativamente a chave secreta para qualquer cliente HTTP sem autenticação.  
**Impact:** Exposição direta de credencial via API pública.  
**Recommendation:** Remover `secret_key` da resposta do health check. Nunca retornar secrets em respostas de API.

---

### [CRITICAL] C3 — Endpoint /admin/query Executa SQL Arbitrário
**File:** `app.py:59-78`  
**Description:** Endpoint `POST /admin/query` recebe uma string SQL do body da requisição e a executa diretamente no banco sem qualquer validação, autenticação ou autorização: `cursor.execute(query)`.  
**Impact:** Acesso irrestrito para leitura e escrita no banco de dados para qualquer cliente. Equivale a uma backdoor completa.  
**Recommendation:** Remover o endpoint completamente. Se necessário para operações administrativas, proteger com autenticação forte e permitir apenas queries pré-definidas.

---

### [HIGH] H1 — Business Logic in Controller: Notificações Hardcoded
**File:** `controllers.py:208-210, 247-250`  
**Description:** Lógica de notificação (email, SMS, push) embutida diretamente nos handlers de pedido com `print()` simulando envios. Ao atualizar status, regras de negócio (devolver estoque, preparar envio) são tratadas no controller com prints.  
**Impact:** Impossível testar notificações em isolamento; acoplamento direto entre HTTP handler e lógica de negócio; substituição real de provedores de notificação exige mexer no controller.  
**Recommendation:** Extrair para um `NotificationService` injetável; o controller apenas chama `notification_service.order_created(order_id)`.

---

### [HIGH] H3 — Global Mutable Database Connection
**File:** `database.py:4, 9-10`  
**Description:** `db_connection = None` em escopo de módulo, modificada dentro de `get_db()`. Conexão SQLite criada com `check_same_thread=False`, compartilhando um único objeto de conexão entre todas as requisições simultâneas.  
**Impact:** Race conditions em ambiente com múltiplos workers; estado global torna testes unitários impossíveis sem monkey-patching; vazamento de conexão entre requests.  
**Recommendation:** Usar `flask.g` para conexão por-request ou `connection_pool`; remover variável global.

---

### [HIGH] H2 — Hard Coupling: Controllers Importam Database Diretamente
**File:** `controllers.py:3`, `models.py:1`  
**Description:** Tanto `controllers.py` quanto `models.py` importam `get_db` diretamente de `database.py`. O `health_check` em controllers.py executa queries SQL diretamente sem passar pelo modelo.  
**Impact:** Qualquer mudança no mecanismo de persistência exige alterações em múltiplos arquivos; impossível mockar o banco em testes sem alterar imports.  
**Recommendation:** Centralizar acesso ao banco somente em `models/`; controllers jamais devem importar `database`.

---

### [HIGH] H1 — Business Logic in Model: Cálculo de Desconto de Relatório
**File:** `models.py:256-263`  
**Description:** Lógica de negócio de cálculo de desconto progressivo (10%/5%/2% por faixas de faturamento) embutida dentro da função de acesso a dados `relatorio_vendas()` em `models.py`.  
**Impact:** Lógica de negócio acoplada à camada de dados; impossível alterar regras de desconto sem mexer no modelo; dificulta testes unitários da regra de negócio isolada.  
**Recommendation:** Extrair o cálculo de desconto para `controllers/relatorio_controller.py`; o model apenas retorna os dados brutos.

---

### [MEDIUM] M1 — N+1 Query Problem em Listagem de Pedidos
**File:** `models.py:185-199, 219-232`  
**Description:** `get_pedidos_usuario()` e `get_todos_pedidos()` executam queries aninhadas em loops: para cada pedido → query de itens; para cada item → query do nome do produto. Para N pedidos com M itens cada, executa `1 + N + (N×M)` queries.  
**Impact:** Performance degrada exponencialmente com volume de dados; sob carga, pode causar timeout do banco.  
**Recommendation:** Substituir por `JOIN` único: `SELECT p.*, ip.*, pr.nome FROM pedidos p JOIN itens_pedido ip ... JOIN produtos pr ...`.

---

### [MEDIUM] M2 — Senhas Armazenadas em Texto Puro
**File:** `database.py:75-83`, `models.py:122-131`  
**Description:** Usuários de seed e usuários criados via API têm senhas inseridas e armazenadas diretamente como texto simples no banco (ex: `"admin123"`, `"123456"`).  
**Impact:** Vazamento do banco expõe todas as senhas imediatamente; viola OWASP A02:2021 (Cryptographic Failures).  
**Recommendation:** Usar `werkzeug.security.generate_password_hash` / `check_password_hash` antes de qualquer inserção.

---

### [MEDIUM] M3 — Erro Interno Exposto ao Cliente
**File:** `controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 185, 220, 228, 235, 255, 261, 292`  
**Description:** Todos os blocos `except` retornam `str(e)` diretamente no JSON de resposta ao cliente (`{"erro": str(e)}`), expondo stack traces, nomes de tabelas, paths de arquivo e detalhes de infraestrutura.  
**Impact:** Facilita reconhecimento do sistema por atacantes; viola OWASP A05:2021 (Security Misconfiguration).  
**Recommendation:** Logar internamente com `app.logger.exception()`; retornar mensagem genérica `{"erro": "Internal server error"}` ao cliente.

---

### [LOW] L1 — Magic Strings: Categorias de Produto Hardcoded
**File:** `controllers.py:52-54`  
**Description:** Lista `["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]` definida inline dentro do handler de criação de produto.  
**Impact:** Lista duplicada se aparecer em outros lugares; manutenção manual; erro de digitação silencioso.  
**Recommendation:** Extrair para constante em `config/settings.py`: `VALID_CATEGORIES = [...]`.

---

### [LOW] L2 — Magic Strings: Status de Pedido Hardcoded
**File:** `controllers.py:242`  
**Description:** Lista `["pendente", "aprovado", "enviado", "entregue", "cancelado"]` definida inline na validação de status.  
**Impact:** Mesma lista precisaria ser duplicada em qualquer outro lugar que precise validar status.  
**Recommendation:** Extrair para constante ou `Enum` em `config/settings.py`.

---

### [LOW] L3 — Dados Sensíveis Expostos na Listagem de Usuários
**File:** `models.py:78-86`, `controllers.py:128-133`  
**Description:** `get_todos_usuarios()` retorna o campo `senha` de todos os usuários na resposta da API `GET /usuarios`.  
**Impact:** Qualquer chamada à rota `/usuarios` expõe as senhas (em texto puro) de todos os usuários cadastrados.  
**Recommendation:** Remover o campo `senha` do dict de retorno em `get_todos_usuarios()` e `get_usuario_por_id()`.

---

## Proposed MVC Structure

```
src/
├── config/
│   └── settings.py              # SECRET_KEY, VALID_CATEGORIES, ORDER_STATUSES
├── models/
│   ├── produto_model.py         # queries parametrizadas de produtos
│   ├── usuario_model.py         # queries de usuários + hash de senha
│   └── pedido_model.py          # queries de pedidos com JOIN (sem N+1)
├── controllers/
│   ├── produto_controller.py    # lógica de validação de produto
│   ├── usuario_controller.py    # lógica de autenticação
│   ├── pedido_controller.py     # lógica de pedido + notificações
│   └── relatorio_controller.py  # cálculo de desconto + agregações
├── views/
│   ├── produto_routes.py        # Blueprint /produtos
│   ├── usuario_routes.py        # Blueprint /usuarios + /login
│   └── pedido_routes.py         # Blueprint /pedidos + /relatorios
├── middlewares/
│   └── error_handler.py         # handler centralizado de erros
└── app.py                       # composition root — registra blueprints
```

---

## Next Step

Fase 3 irá reestruturar o projeto para esta arquitetura, eliminando todos os 14 findings acima.
