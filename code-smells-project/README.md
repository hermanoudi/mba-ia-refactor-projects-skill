# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

---

## Como Executar

### Pré-requisitos
- Python 3.10+
- pip

### Executar a skill de auditoria

No Claude Code, dentro do diretório do projeto:

```bash
/refactor-arch
```

A skill executa em 3 fases: análise → auditoria (pausa para confirmação) → refatoração.

### Executar a versão refatorada (MVC — `src/`)

**1. Configure as variáveis de ambiente:**

```bash
cp .env.example .env
# edite .env e defina um SECRET_KEY seguro
```

**2. Instale as dependências:**

```bash
pip install -r requirements.txt
```

**3. Suba o servidor:**

```bash
SECRET_KEY=sua-chave flask --app src.app run
# ou com .env carregado automaticamente por um dotenv loader:
flask --app src.app run
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite é criado automaticamente no primeiro boot, com produtos e usuários de exemplo.

### Executar a versão original (com code smells)

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | — | **Obrigatório em produção.** Chave secreta do Flask. |
| `DATABASE` | `loja.db` | Caminho para o arquivo SQLite. |
| `DEBUG` | `false` | Habilita modo debug (`true`/`false`). |

### Validar a refatoração

```bash
# Smoke test dos endpoints principais:
curl http://localhost:5000/health
curl http://localhost:5000/produtos/
curl http://localhost:5000/usuarios     # verificar: campo "senha" ausente
```

---

## Análise Manual

### Resumo de severidades

| Severidade | Contagem | Exemplos |
|-----------|----------|----------|
| **CRITICAL** | 2 | SQL Injection, Credenciais Hardcoded |
| **HIGH** | 2 | Violação SRP, Estado Global Mutável |
| **MEDIUM** | 2 | Queries N+1, Duplicação de Validação |
| **LOW** | 2 | Magic Numbers, Nomenclatura Pobre |

### Detalhamento dos problemas

## Problema 1: Vulnerabilidade de SQL Injection **[CRITICAL]**

**Localização:** `models.py` — Todas as funções que executam queries SQL

Queries SQL são construídas por concatenação de strings com dados de entrada, permitindo bypass de autenticação (`' OR '1'='1`) e manipulação de dados. O ponto de login em `models.py:109` é especialmente crítico.

**Por que é relevante:** Exposição completa de dados, destruição de registros, comprometimento total do sistema. Qualquer aplicação com este problema em produção está sob risco imediato.

---

## Problema 2: Violação do Princípio da Responsabilidade Única (SRP) **[HIGH]**

**Localização:** `controllers.py` — Todas as funções de controller

Controllers realizam múltiplas responsabilidades: validação, lógica de negócio, acesso a dados e formatação. Função `criar_produto` acumula todas estas.

**Por que é relevante:** Impede testes unitários isolados. Mudança em um domínio quebra lógica de outro. Cada controller se torna um monolito impossível de testar em isolamento.

---

## Problema 3: Queries N+1 no Acesso a Pedidos **[MEDIUM]**

**Localização:** `models.py` — Funções `get_pedidos_usuario` e `get_todos_pedidos`

Para N pedidos com M itens: 1 + N + N×M queries. Para 10 pedidos com 5 itens cada: 61 queries em vez de 1 JOIN.

**Por que é relevante:** Performance degrada exponencialmente em produção. Relatórios de vendas com 1000 pedidos disparam 1M+ queries, travando o banco.

---

## Problema 4: Duplicação de Código de Validação **[MEDIUM]**

**Localização:** `controllers.py` — Funções `criar_produto` e `atualizar_produto`

Regras de validação de nome, preço e estoque são duplicadas. Quando um bug é corrigido em `criar_produto`, não é propagado para `atualizar_produto`.

**Por que é relevante:** Inconsistência silenciosa em regras de negócio. Produtos válidos no POST são inválidos no PUT, causando bugs sutis em clientes.

---

## Problema 5: Uso de Magic Numbers e Strings Hardcoded **[LOW]**

**Localização:** `controllers.py` — Categorias válidas; `models.py` — Percentuais de desconto

Categorias e descontos estão hardcoded em 2+ lugares. Adicionar categoria exige buscar e editar em múltiplos arquivos.

**Por que é relevante:** Mudanças de negócio (nova categoria, novo percentual) exigem alteração no código e recompilação. Sem rastreabilidade de quando valores mudaram.

---

## Problema 6: Nomenclatura de Variáveis Pobre **[LOW]**

**Localização:** Vários arquivos — `dados`, `result`, `row`, etc.

Variáveis usam nomes genéricos. `dados = request.get_json()` não carrega contexto — é produto, usuário, pedido?

**Por que é relevante:** Leitura exige rastrear o caller para entender o tipo. Refatoração fica perigosa porque não é claro qual estrutura está sendo manipulada.

---

## Problema 7: Estado Global Mutável **[HIGH]**

**Localização:** `database.py` — Variável `db_connection` global com `check_same_thread=False`

Conexão compartilhada entre requests + SQLite sem sincronização = race conditions com múltiplos workers. Impossível mockar em testes.

**Por que é relevante:** Comportamento não-determinístico em produção. Testes passam em single-threaded mas falham com gunicorn/uWSGI. Dados podem ser corrompidos ou inconsistentes.

---

## Problema 8: Credenciais Hardcoded **[CRITICAL]**

**Localização:** `app.py` — `SECRET_KEY` hardcoded

Qualquer clone do repositório expõe a chave. Em produção, `/health` retorna `secret_key` na resposta.

**Por que é relevante:** Qualquer desenvolvedor com acesso ao repo pode falsificar sessões. Se o repo é público, a chave é comprometida instantaneamente.

---

## Construção da Skill

### Decisões de design

- **3 fases com pausa obrigatória:** Phase 2 exige confirmação do usuário antes de modificar arquivos — evita refatorações não-intencionais.
- **Catálogo de anti-patterns separado** (`anti-patterns-catalog.md`): Permite evoluir detecção sem alterar o fluxo principal da skill.
- **Playbook de transformações** (`refactoring-playbook.md`): Mapeia cada anti-pattern a um padrão before/after concreto com exemplos de código.
- **Template de relatório padronizado:** Cada execução produz um artefato comparável entre projetos.

### Anti-patterns incluídos e por quê

**4 CRITICAL** (God Class, SQL Injection, Hardcoded Secrets, Flat Architecture)
- Falhas que comprometem segurança ou tornam o sistema não-testável

**5 HIGH** (Business Logic in Controller, Hard Coupling, Global Mutable State, Deprecated API, Missing Abstraction)
- Violações de SOLID que bloqueiam evolução

**3 MEDIUM** (N+1, Missing Validation, Improper Error Handling)
- Problemas de performance e segurança operacional

**3 LOW** (Magic Numbers, Poor Naming, Dead Code)
- Débito técnico de legibilidade

### Como a skill é agnóstica de tecnologia

- Referências em `mvc-guidelines.md` incluem exemplos para Flask, Express, Laravel e Rails
- Anti-patterns usam pseudocódigo + exemplos em Python, JS e PHP
- Phase 1 detecta linguagem/framework automaticamente por heurísticas (extensions, imports, package files)
- Nomes de diretórios são adaptados à convenção do framework detectado

### Desafios encontrados

- **Cache da skill na sessão:** Alterações no SKILL.md não refletem até nova sessão (comportamento do Claude Code)
- **Granularidade do relatório:** Decidir entre um finding por arquivo vs. um por ocorrência — optou-se por agrupar por tipo com lista de linhas
- **Separação model/controller em Flask sem ORM:** Sem SQLAlchemy, a linha entre "query parametrizada no model" e "lógica de negócio no controller" é manual

---

## Resultados

### Resumo do relatório de auditoria

**Arquivo gerado:** `reports/audit-project-1.md`

| Severidade | Contagem |
|-----------|----------|
| CRITICAL | 2 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 2 |
| **TOTAL** | **14 achados** |

### Comparação antes/depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Arquivos raiz | 4 arquivos flat (780 LOC) | `src/` com 12 arquivos em 6 camadas |
| Queries SQL | String concat em 18+ pontos | 100% parametrizadas com `?` |
| Senhas | Texto puro no banco | bcrypt via `werkzeug.security` |
| Conexão DB | Global mutable singleton | `flask.g` por request |
| Notificações | `print()` hardcoded no controller | `NotificationService` injetável |
| Erros | `str(e)` retornado ao cliente | Handler centralizado, log interno |
| Secret key | Hardcoded + exposta em `/health` | `os.environ.get('SECRET_KEY')` |
| N+1 queries | 3 cursors aninhados por pedido | Single LEFT JOIN |
| Endpoint `/admin/query` | Executa SQL arbitrário | Removido |

### Checklist de validação

- ✓ Aplicação boot sem erros
- ✓ `GET /health` — sem `secret_key`, `db_path` ou `debug` na resposta
- ✓ `GET/POST/PUT/DELETE /produtos` — todos os 6 endpoints respondem
- ✓ `GET /usuarios` — campo `senha` ausente da resposta
- ✓ `POST /login` — bcrypt verify; senha errada retorna 401
- ✓ `POST /pedidos` — criação com validação de estoque
- ✓ `PUT /pedidos/{id}/status` — status inválido retorna 400
- ✓ `GET /relatorios/vendas` — cálculo de desconto no controller
- ✓ SQL injection em `/produtos/busca` — retornou 0 resultados, sem crash
- ✓ SQL injection em `/login` — retornou 401
- ✓ `POST /admin/query` — 404 (endpoint removido)
- ✓ `POST /admin/reset-db` — 404 (endpoint removido)
</content>
<parameter name="filePath">/home/hermano/projetos/MBA/desafios/skill-auditoria-refatoracao-arquitetural/mba-ia-refactor-projects-skill/code-smells-project/docs/achados
