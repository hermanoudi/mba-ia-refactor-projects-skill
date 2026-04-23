# Criação de Skills — Refatoração Arquitetural Automatizada

---

## A) Análise Manual

Antes de construir a skill, os 3 projetos foram analisados manualmente para entender os problemas que ela precisaria detectar e corrigir.

### Projeto 1 — code-smells-project (Python/Flask)

| # | Problema | Severidade | Localização |
|---|----------|-----------|-------------|
| 1 | SQL Injection | **CRITICAL** | `models.py` — todas as queries |
| 2 | Credenciais Hardcoded | **CRITICAL** | `app.py:7` — SECRET_KEY |
| 3 | Violação SRP nos Controllers | **HIGH** | `controllers.py` — todas as funções |
| 4 | Estado Global Mutável | **HIGH** | `database.py` — conexão global |
| 5 | Queries N+1 em Pedidos | **MEDIUM** | `models.py` — get_pedidos |
| 6 | Duplicação de Validação | **MEDIUM** | `controllers.py` — criar/atualizar produto |
| 7 | Magic Numbers e Strings Hardcoded | **LOW** | `controllers.py` / `models.py` |
| 8 | Nomenclatura de Variáveis Pobre | **LOW** | Vários arquivos — `dados`, `row`, `result` |

**Justificativas:**
- **SQL Injection:** permite bypass de autenticação (`' OR '1'='1`) e destruição de dados; ponto de login em `models.py:109` é especialmente crítico.
- **Credenciais Hardcoded:** qualquer clone do repositório expõe a chave; `GET /health` retornava `secret_key` na resposta.
- **Violação SRP:** controllers realizam validação + lógica de negócio + acesso a dados — impossível testar em isolamento.
- **Estado Global Mutável:** `check_same_thread=False` + conexão compartilhada = race conditions com múltiplos workers.
- **N+1 Queries:** para 10 pedidos com 5 itens: 61 queries em vez de 1 JOIN.
- **Duplicação de Validação:** bug corrigido em `criar_produto` não é propagado para `atualizar_produto`.

---

### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

| # | Problema | Severidade | Localização |
|---|----------|-----------|-------------|
| 1 | Credenciais Hardcoded | **CRITICAL** | `src/utils.js:1-7` — DB, SMTP, gateway |
| 2 | God Class | **CRITICAL** | `src/AppManager.js` — 141 linhas, 3 domínios |
| 3 | Business Logic in Controller | **HIGH** | `AppManager.js:28-78` — rota POST /checkout |
| 4 | Hard Coupling / Sem Injeção de Dependência | **HIGH** | `AppManager.js:5-7` — construtor |
| 5 | Global Mutable State | **HIGH** | `src/utils.js:9-10` — globalCache, totalRevenue |
| 6 | Missing Abstraction Layer | **HIGH** | Todo o arquivo — chamadas diretas ao SQLite |
| 7 | Deprecated API (callback hell) | **HIGH** | `AppManager.js:43-78` |
| 8 | N+1 Query Problem | **MEDIUM** | `AppManager.js:89-127` — financial-report |
| 9 | Missing Input Validation | **MEDIUM** | `AppManager.js:29-35` |
| 10 | Improper Error Handling | **MEDIUM** | Múltiplos handlers sem logging |
| 11 | Magic Numbers | **LOW** | `utils.js:19` — `10000` |
| 12 | Poor Naming | **LOW** | `AppManager.js:29-34` — u, e, p, cid, cc |
| 13 | Dead Code | **LOW** | `utils.js:10` — `totalRevenue` nunca usado |

**Justificativas:**
- **Credenciais Hardcoded:** viola PCI-DSS; credenciais de gateway de pagamento e SMTP expostas em repositório.
- **God Class:** impossível testar checkout sem instanciar o gerenciador inteiro; mudança em pagamento quebra definição de rotas.
- **N+1 Queries:** 10 cursos × 50 matrículas = 111 queries em vez de 1 JOIN.

---

### Projeto 3 — task-manager-api (Python/Flask)

| # | Problema | Severidade | Localização |
|---|----------|-----------|-------------|
| 1 | Credenciais Hardcoded | **CRITICAL** | `app.py:13`, `services/notification_service.py:9-10` |
| 2 | Hashing Inseguro (MD5) | **CRITICAL** | `routes/user_routes.py` — hash sem salt |
| 3 | Fat Routes / Violação SRP | **HIGH** | `routes/` — lógica de negócio em route handlers |
| 4 | Ausência de Abstração de Serviço | **HIGH** | Acesso a dados direto nas rotas |
| 5 | N+1 Queries | **MEDIUM** | Relatórios e listagens sem eager loading |
| 6 | Validação Dispersa | **MEDIUM** | Validações espalhadas em múltiplos lugares |
| 7 | Tratamento de Erro Inadequado | **MEDIUM** | `bare except:` em 8+ pontos |
| 8-13 | Magic Numbers, Naming Pobre, Imports Mortos | **LOW** | Vários arquivos |

**Justificativas:**
- **MD5 sem salt:** vulnerável a rainbow table attacks; senhas de usuários comprometidas se o banco vazar.
- **Fat Routes:** 736 LOC em 3 arquivos de rotas com lógica de negócio — impossível testar controllers sem HTTP.

---

## B) Construção da Skill

### Decisões de design

A skill `refactor-arch` foi estruturada em **3 fases sequenciais com pausa obrigatória** entre a Fase 2 e a Fase 3:

- **Fase 1 — Análise:** detecta linguagem, framework, banco de dados e mapeia a arquitetura atual sem modificar nenhum arquivo.
- **Fase 2 — Auditoria:** cruza o código contra o catálogo de anti-patterns, gera relatório com arquivo e linha exatos, e **pausa para confirmação do usuário** antes de qualquer modificação.
- **Fase 3 — Refatoração:** reestrutura para MVC, elimina os anti-patterns encontrados e valida boot + endpoints.

**Arquivos de referência criados:**

| Arquivo | Propósito |
|---------|-----------|
| `SKILL.md` | Prompt principal — orquestra as 3 fases |
| `project-analysis.md` | Heurísticas de detecção de stack e mapeamento de arquitetura |
| `anti-patterns-catalog.md` | 15 anti-patterns com sinais de detecção e severidade |
| `audit-report-template.md` | Template padronizado do relatório (Fase 2) |
| `mvc-guidelines.md` | Regras e responsabilidades de cada camada MVC |
| `refactoring-playbook.md` | 10 padrões before/after com exemplos de código |

### Anti-patterns incluídos no catálogo (15 itens)

| Severidade | Anti-patterns |
|-----------|---------------|
| **CRITICAL** (4) | God Class, SQL Injection, Hardcoded Credentials, Flat Architecture |
| **HIGH** (5) | Business Logic in Controller, Hard Coupling, Global Mutable State, Deprecated API Usage, Missing Abstraction Layer |
| **MEDIUM** (3) | N+1 Query Problem, Missing Input Validation, Improper Error Handling |
| **LOW** (3) | Magic Numbers/Strings, Poor Naming, Dead Code |

### Como a skill é agnóstica de tecnologia

- `project-analysis.md` detecta linguagem por extensões de arquivo (`.py`, `.js`, `.ts`), imports e package files (`requirements.txt`, `package.json`, `composer.json`).
- `mvc-guidelines.md` inclui convenções de nomenclatura para Flask, Express, Laravel e Rails — a skill adapta os nomes de diretórios ao framework detectado.
- Anti-patterns em `anti-patterns-catalog.md` usam pseudocódigo com exemplos em Python, JavaScript e PHP.
- `refactoring-playbook.md` tem padrões agnósticos mapeados a implementações específicas por stack.

### Desafios encontrados

- **Cache da skill na sessão:** alterações no `SKILL.md` não refletem até nova sessão do Claude Code — foi necessário reiniciar o contexto entre iterações.
- **Granularidade do relatório:** optou-se por agrupar achados por tipo (com lista de localizações) em vez de um finding por ocorrência, reduzindo o ruído no relatório.
- **Projeto 3 já parcialmente organizado:** a Fase 3 precisou identificar o que já estava correto e focar apenas nas violações remanescentes, sem desfazer separação existente.
- **Flask sem ORM:** sem SQLAlchemy, a linha entre "query parametrizada no model" e "lógica de negócio no controller" é manual — o playbook foi detalhado para cobrir esse caso.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|-------|----------|------|--------|-----|-------|
| code-smells-project | Python/Flask | 4 | 4 | 3 | 3 | **14** |
| ecommerce-api-legacy | Node.js/Express | 2 | 5 | 3 | 3 | **13** |
| task-manager-api | Python/Flask | 2 | 2 | 3 | 6 | **13** |

Relatórios completos em `reports/audit-project-{1,2,3}.md`.

### Comparação antes/depois

**Projeto 1 — code-smells-project:**

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Arquivos raiz | 4 arquivos flat (~780 LOC) | `src/` com 12 arquivos em 6 camadas |
| Queries SQL | Concatenação de strings em 18+ pontos | 100% parametrizadas com `?` |
| Senhas | Texto puro no banco | bcrypt via `werkzeug.security` |
| Conexão DB | Global mutable singleton | `flask.g` por request |
| Secret key | Hardcoded + exposta em `/health` | `os.environ.get('SECRET_KEY')` |
| N+1 queries | 3 cursors aninhados por pedido | Single LEFT JOIN |
| Endpoint `/admin/query` | Executa SQL arbitrário | Removido |

**Projeto 2 — ecommerce-api-legacy:**

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Arquivos | 3 arquivos flat (~180 LOC) | `src/` com 18 arquivos em 7 camadas |
| Credenciais | Hardcoded em utils.js | `.env` com fallbacks seguros |
| Acesso a dados | Direto em route handlers | Repository pattern com 5 modelos |
| Queries SQL | N+1 aninhadas (~111 queries) | Single LEFT JOIN (1 query) |
| Async | Callback hell | Promise-based abstraction |
| Nomes | u, e, p, cid, cc | userName, email, password, courseId, cardNumber |

**Projeto 3 — task-manager-api:**

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Linhas em routes | 736 LOC em 3 arquivos | ~450 LOC (39% redução) |
| Queries N+1 | ~202 queries para 100 registros | 3 queries com eager loading |
| Senhas | MD5 sem salt | PBKDF2-SHA256 com werkzeug |
| Secrets | Hardcoded no código | Variáveis de ambiente (.env) |
| Tratamento de erro | `bare except:` em 8+ pontos | Logging estruturado centralizado |

### Checklist de validação

**Projeto 1 — code-smells-project:**
- [x] Linguagem detectada corretamente (Python 3.12)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio descrito corretamente (E-commerce API)
- [x] 4 arquivos analisados
- [x] Relatório segue template definido
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade
- [x] 14 findings identificados (mínimo: 5)
- [x] Skill pausou e pediu confirmação antes da Fase 3
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para variáveis de ambiente
- [x] Aplicação inicia sem erros
- [x] Todos os endpoints respondem corretamente

**Projeto 2 — ecommerce-api-legacy:**
- [x] Linguagem detectada corretamente (Node.js)
- [x] Framework detectado corretamente (Express)
- [x] Domínio descrito corretamente (LMS com checkout)
- [x] 3 arquivos analisados
- [x] 13 findings identificados
- [x] Skill pausou e pediu confirmação antes da Fase 3
- [x] Estrutura MVC com Controllers, Models, Routes
- [x] Aplicação inicia sem erros
- [x] POST /checkout, GET /financial-report, DELETE /users/:id respondem

**Projeto 3 — task-manager-api:**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask)
- [x] Domínio descrito corretamente (Task Manager)
- [x] 13 findings identificados
- [x] Skill identificou problemas mesmo em projeto parcialmente organizado
- [x] Estrutura MVC melhorada sem quebrar endpoints existentes
- [x] Aplicação inicia sem erros
- [x] GET /tasks, /users, /categories, /reports/summary respondem

### Observações sobre a skill em stacks diferentes

- **Python/Flask vs Node.js/Express:** a Fase 1 detectou corretamente ambas as stacks sem configuração adicional.
- **Projeto já organizado (task-manager-api):** a Fase 3 operou de forma cirúrgica — corrigiu segurança e moveu lógica de negócio sem desfazer a separação de camadas já existente.
- **Callback hell em Node.js:** identificado como "Deprecated API Usage" no catálogo — a skill sugeriu migração para async/await com exemplos concretos.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado e configurado
- Python 3.10+ (projetos 1 e 3)
- Node.js 14+ e npm (projeto 2)

### Executar a skill em cada projeto

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask)
cd ../task-manager-api
claude "/refactor-arch"
```

A skill executa em 3 fases: análise → auditoria (pausa para confirmação) → refatoração.

### Executar as versões refatoradas

**Projeto 1 (Python/Flask):**
```bash
cd code-smells-project
pip install -r requirements.txt
cp .env.example .env   # defina SECRET_KEY
flask --app src.app run
```

**Projeto 2 (Node.js/Express):**
```bash
cd ecommerce-api-legacy
npm install
cp .env.example .env   # defina PAYMENT_GATEWAY_KEY
npm start
```

**Projeto 3 (Python/Flask):**
```bash
cd task-manager-api
pip install -r requirements.txt
cp .env.example .env   # defina SECRET_KEY e credenciais SMTP
python seed.py
python app.py
```

### Validar que a refatoração funcionou

```bash
# Projeto 1
curl http://localhost:5000/health
curl http://localhost:5000/produtos/
curl http://localhost:5000/usuarios     # "senha" deve estar ausente da resposta

# Projeto 2
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@test.com","pwd":"pwd","c_id":1,"card":"4111222233334444"}'
curl http://localhost:3000/api/admin/financial-report

# Projeto 3
curl http://localhost:5000/health
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
```

---



Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.