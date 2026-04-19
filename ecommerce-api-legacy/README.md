# ecommerce-api-legacy

API de LMS com fluxo de checkout em Node.js/Express usada como entrada do desafio `refactor-arch`.

---

## Como Executar

### Pré-requisitos
- Node.js 14+
- npm

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
# edite .env e defina um PAYMENT_GATEWAY_KEY seguro
```

**2. Instale as dependências:**

```bash
npm install
```

**3. Suba o servidor:**

```bash
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

### Executar a versão original (com code smells)

```bash
npm install
node src/deprecated/AppManager.js
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PAYMENT_GATEWAY_KEY` | — | **Obrigatório em produção.** Chave do gateway de pagamento. |
| `DB_USER` | `admin_master` | Usuário de acesso ao banco. |
| `DB_PASS` | `senha_super_secreta_prod_123` | Senha do banco. |
| `SMTP_USER` | `no-reply@fullcycle.com.br` | Email para notificações. |
| `PORT` | `3000` | Porta do servidor. |
| `NODE_ENV` | `development` | Ambiente (`development`/`production`). |

### Validar a refatoração

```bash
# Smoke test dos endpoints principais:
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@test.com","pwd":"pwd","c_id":1,"card":"4111222233334444"}'

curl http://localhost:3000/api/admin/financial-report

curl -X DELETE http://localhost:3000/api/users/1
```

---

## Análise Manual

### Resumo de severidades

| Severidade | Contagem | Exemplos |
|-----------|----------|----------|
| **CRITICAL** | 2 | Hardcoded Credentials, God Class |
| **HIGH** | 5 | Business Logic in Controller, Hard Coupling, Global State, Deprecated API, Missing Abstraction |
| **MEDIUM** | 3 | N+1 Queries, Input Validation, Error Handling |
| **LOW** | 3 | Magic Numbers, Poor Naming, Dead Code |

### Detalhamento dos problemas

## Problema 1: Credenciais Hardcoded **[CRITICAL]**

**Localização:** `src/deprecated/utils.js` — Objeto `config` (linhas 1-7)

Credenciais de banco de dados, gateway de pagamento e SMTP estão hardcoded no código fonte. Exposição completa em repositórios públicos ou vazamentos de código.

**Por que é relevante:** Qualquer desenvolvedor com acesso ao repo pode acessar produção. Se o repo é público, as credenciais são comprometidas instantaneamente. Viola PCI-DSS e regulações de proteção de dados.

---

## Problema 2: God Class / Módulo **[CRITICAL]**

**Localização:** `src/deprecated/AppManager.js` (linhas 4-141)

Única classe `AppManager` concentra: inicialização de DB, definição de rotas, lógica de negócio (checkout), relatórios financeiros, validação e acesso a dados. Três domínios distintos (usuários, cursos, pagamentos) vivem no mesmo arquivo.

**Por que é relevante:** Impossível testar checkout sem instanciar o gerenciador inteiro. Mudança em lógica de pagamento quebra definição de rotas. Novo desenvolvedor não consegue entender o fluxo. Código não é reutilizável.

---

## Problema 3: Business Logic in Controller **[HIGH]**

**Localização:** `src/deprecated/AppManager.js:28-78` (rota POST `/api/checkout`)

Função de rota mistura HTTP (validação de request/response) com lógica de negócio: validação de cartão, criação de matrícula, processamento de pagamento, auditoria. Tudo em 51 linhas.

**Por que é relevante:** Lógica de checkout está presa dentro de uma route handler, tornando impossível testar em isolamento. Não pode ser reutilizada em batch enrollment ou CLI. Mudança em formato de resposta afeta a lógica de negócio.

---

## Problema 4: Hard Coupling / Sem Injeção de Dependência **[HIGH]**

**Localização:** `src/deprecated/AppManager.js:5-7` (construtor)

Banco de dados é instanciado diretamente (`this.db = new sqlite3.Database()`) sem injeção. Impossível mockar para testes. Trocar de SQLite para PostgreSQL requer alterar a classe.

**Por que é relevante:** Testes unitários são impossíveis — todo teste usa um banco real. Não é possível testar a lógica de negócio independente de I/O. Refatoração de infraestrutura quebra toda a aplicação.

---

## Problema 5: Global Mutable State **[HIGH]**

**Localização:** `src/deprecated/utils.js:9-10` (`globalCache` e `totalRevenue`)

Módulo exporta variáveis globais mutáveis que são modificadas por route handlers. `globalCache` é acessado por `logAndCache()` em múltiplas requests concorrentes. `totalRevenue` é declarado mas nunca usado.

**Por que é relevante:** Race conditions em produção com múltiplas requests. Cache state torna-se não-determinístico. Código-fantasma (`totalRevenue`) dificulta compreensão. Impossível testar em paralelo.

---

## Problema 6: Missing Abstraction Layer **[HIGH]**

**Localização:** `src/deprecated/AppManager.js` (todo o arquivo)

Todos os route handlers chamam diretamente `this.db.run()` e `this.db.get()` (API raw do SQLite). Nenhuma abstração de repositório ou serviço. Lógica de negócio acoplada a detalhes de implementação do banco.

**Por que é relevante:** Não é possível trocar SQLite por PostgreSQL sem reescrever todos os handlers. Lógica de negócio não é reutilizável em contextos diferentes (APIs, batch, CLI). Acesso a dados é espalhado e difícil de manter.

---

## Problema 7: N+1 Query Problem **[MEDIUM]**

**Localização:** `src/deprecated/AppManager.js:89-127` (GET `/api/admin/financial-report`)

Para cada curso, executa query de matrículas. Para cada matrícula, executa query de usuário e depois pagamento. Com 10 cursos e 50 matrículas: 1 + 10 + 50 + 50 = 111 queries em vez de 1 JOIN.

**Por que é relevante:** Performance degrada exponencialmente com crescimento de dados. 1000 cursos = 1M+ queries, travando o banco. Relatórios se tornam inutilizáveis em produção.

---

## Problema 8: Missing Input Validation **[MEDIUM]**

**Localização:** `src/deprecated/AppManager.js:29-35` (POST `/api/checkout`)

Validação apenas checa se campos existem (`!u || !e`), mas não tipo, formato ou comprimento. Sem validação de email, cartão ou senha. Request body usado diretamente.

**Por que é relevante:** Dados inválidos causam erros silenciosos ou crashes. Email inválido não é rejeitado. Cartão sem dígitos suficientes passa. Falta de `password` é aceita (padrão para "123456"). Sem proteção contra entrada maliciosa.

---

## Problema 9: Improper Error Handling **[MEDIUM]**

**Localização:** `src/deprecated/AppManager.js:38, 41, 51, 55` (múltiplos handlers de erro)

Erros retornam mensagens genéricas ("Erro DB", "Erro Matrícula") sem logging. Nenhum handler centralizado. Erros não são registrados. Detalhes de erro podem vazar ao cliente.

**Por que é relevante:** Impossível debugar em produção. Clientes não conseguem distinguir erro de input vs. erro de servidor. Detalhes de database podem vazar informações sensíveis.

---

## Problema 10: Deprecated API Usage **[HIGH]**

**Localização:** `src/deprecated/AppManager.js:43-78` (callback hell)

Uso massivo de callbacks aninhados em vez de Promises/async-await. Padrão desatualizado em Node.js moderno.

**Por que é relevante:** Callback hell reduz legibilidade. Tratamento de erro é espalhado. Refatoração fica mais difícil. Novos desenvolvedores esperam async/await.

---

## Problema 11: Magic Numbers / Magic Strings **[LOW]**

**Localização:** `src/deprecated/utils.js:19` (`10000` na função `badCrypto`)

Número 10000 é magic number sem explicação. Por que 10000? É constante de segurança? Mudar para 50000 requer buscar por "10000" no código.

**Por que é relevante:** Código menos compreensível. Tuning de performance exige busca manual. Rastreabilidade de mudanças é perdida.

---

## Problema 12: Poor Naming **[LOW]**

**Localização:** `src/deprecated/AppManager.js:29-34` (variáveis do checkout)

Variáveis usam abreviaturas: `u` (user), `e` (email), `p` (password), `cid` (course ID), `cc` (credit card).

**Por que é relevante:** Código é difícil de ler. Maiores chances de bugs durante manutenção. Onboarding de novos desenvolvedores é mais lento.

---

## Problema 13: Dead Code **[LOW]**

**Localização:** `src/deprecated/utils.js:10` (`totalRevenue`)

Variável `totalRevenue` é declarada e exportada mas nunca usada. Nunca é incrementada.

**Por que é relevante:** Code clutter. Desenvolvedores podem achar que é funcionalidade incompleta. Dificulta compreensão.

---

## Construção da Skill

### Decisões de design

- **3 fases com pausa obrigatória:** Phase 2 exige confirmação do usuário antes de modificar arquivos — evita refatorações não-intencionais.
- **Catálogo de anti-patterns separado** (`anti-patterns-catalog.md`): Permite evoluir detecção sem alterar o fluxo principal da skill.
- **Playbook de transformações** (`refactoring-playbook.md`): Mapeia cada anti-pattern a um padrão before/after concreto com exemplos de código.
- **Template de relatório padronizado:** Cada execução produz um artefato comparável entre projetos.

### Anti-patterns incluídos e por quê

**2 CRITICAL** (Hardcoded Credentials, God Class)
- Falhas que comprometem segurança ou tornam o sistema não-testável

**5 HIGH** (Business Logic in Controller, Hard Coupling, Global Mutable State, Deprecated API, Missing Abstraction)
- Violações de SOLID que bloqueiam evolução

**3 MEDIUM** (N+1 Queries, Missing Validation, Improper Error Handling)
- Problemas de performance e segurança operacional

**3 LOW** (Magic Numbers, Poor Naming, Dead Code)
- Débito técnico de legibilidade

### Como a skill é agnóstica de tecnologia

- Referências em `mvc-guidelines.md` incluem exemplos para Python/Flask, Node.js/Express, PHP/Laravel e Ruby/Rails
- Anti-patterns usam pseudocódigo + exemplos em múltiplas linguagens
- Phase 1 detecta linguagem/framework automaticamente por heurísticas (extensões, imports, package files)
- Nomes de diretórios são adaptados à convenção do framework detectado

---

## Resultados

### Resumo do relatório de auditoria

**Arquivo gerado:** `reports/audit-project.md`

| Severidade | Contagem |
|-----------|----------|
| CRITICAL | 2 |
| HIGH | 5 |
| MEDIUM | 3 |
| LOW | 3 |
| **TOTAL** | **13 achados** |

### Comparação antes/depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Arquivos | 3 arquivos flat (180 LOC) | `src/` com 18 arquivos em 7 camadas |
| Estrutura | Monolith (AppManager) | MVC com Controllers, Models, Routes |
| Credenciais | Hardcoded em utils.js | `.env` com fallbacks seguros |
| Acesso a dados | Direto em routes | Repository pattern com 5 modelos |
| Validação | if/checks básicos | Middleware dedicado |
| Erros | Inline, sem logging | Handler centralizado |
| Queries SQL | N+1 aninhadas (111 queries) | Single LEFT JOIN (1 query) |
| Conexão DB | Instanciada em classe | Injetada como dependência |
| Async | Callback hell | Promise-based abstraction |
| Nomes | u, e, p, cid, cc | userName, email, password, courseId, cardNumber |
| Constants | Magic numbers | Named constants (HASH_ITERATIONS, VISA_CARD_PREFIX) |
| Dead code | totalRevenue não usado | Removido |

### Checklist de validação

- ✓ Aplicação boot sem erros
- ✓ `POST /api/checkout` com cartão válido (começa com 4) — enrollment criado
- ✓ `POST /api/checkout` com cartão inválido — 400 "Payment denied"
- ✓ `POST /api/checkout` sem email válido — 400 "Invalid email"
- ✓ `POST /api/checkout` sem courseId — 400 "Course ID must be a number"
- ✓ `POST /api/checkout` com curso inexistente — 404 "Course not found"
- ✓ `GET /api/admin/financial-report` — relatório com cursos e receita
- ✓ `GET /api/admin/financial-report` — dados consolidados (sem N+1 queries)
- ✓ `DELETE /api/users/:id` — usuário deletado com sucesso
- ✓ `DELETE /api/users/invalid` — 400 "Invalid user ID"
- ✓ Nenhuma credencial hardcoded no `src/` ativo
- ✓ Nenhum estado global mutável
- ✓ Todos os handlers de erro retornam estrutura JSON consistente
- ✓ Arquivo `reports/audit-project.md` gerado com 13 achados
