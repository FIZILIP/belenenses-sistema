# Sistema Belenenses - Documentacao Funcional e de Dados

## 1) Visao geral

Sistema web em Flask + SQLAlchemy + SQLite para gestao operacional do clube, com modulos de:

- autenticacao e usuarios
- atletas
- comissao tecnica
- compras
- gastos mensais
- contas fixas
- inventario
- reunioes
- calendario de eventos
- departamento medico
- scouting
- dashboard com KPIs

Banco atual: `instance/belenenses.db`  
ORM: SQLAlchemy (modelos em `models.py`)  
Rotas e regras: `app.py`

---

## 2) Arquitetura e hierarquia de acesso

### Camadas

1. **Apresentacao**: templates Jinja2 em `templates/`
2. **Aplicacao**: regras de negocio e rotas em `app.py`
3. **Dados**: modelos SQLAlchemy em `models.py` e SQLite em `instance/belenenses.db`

### Hierarquia de usuarios e poderes

- **Usuario autenticado (padrao)**:
  - acessa todos os modulos funcionais (atletas, compras, inventario, etc.)
- **Administrador (`is_admin=True`)**:
  - acesso ao modulo `/usuarios`
  - pode criar/remover usuarios
  - usuario admin nao pode remover a propria conta

### Controle de permissao implementado

- `@login_required` em praticamente todas as rotas (exceto `/login`)
- validacao explicita de admin apenas em:
  - `/usuarios`
  - `/criar-usuario`
  - `/deletar-usuario/<id>`

### Controle de permissao previsto, mas **nao implementado**

Existe tela `templates/permissoes.html` com campos como:

- `can_manage_atletas`
- `can_manage_comissao`
- `can_manage_financeiro`
- `can_manage_inventario`
- `can_manage_reunioes`

Porem:

- esses campos nao existem na tabela `user`
- nao existe rota `atualizar_permissoes`

---

## 3) Base de dados: tabelas, chaves e relacionamentos

## 3.1 Tabelas e chaves primarias

Todas as tabelas usam PK `id INTEGER`.

1. `user`
2. `atleta`
3. `comissao_tecnica`
4. `compra`
5. `gasto_mensal`
6. `conta_fixa`
7. `inventario`
8. `reuniao`
9. `evento`
10. `ficha_medica`
11. `scouting`

## 3.2 Chaves unicas

Em `user`:

- `username` UNIQUE
- `email` UNIQUE

## 3.3 Chaves estrangeiras e relacionamentos

### Relacionamento principal

- `ficha_medica.atleta_id -> atleta.id` (FK obrigatoria)
- cardinalidade: **1 atleta : N fichas_medicas**
- no ORM: `FichaMedica.atleta` e `Atleta.fichas_medicas` (backref)

### Observacao importante de integridade

- nao ha `ON DELETE CASCADE` no schema SQLite
- delecao de atleta remove fichas medicas via codigo:
  - `FichaMedica.query.filter_by(atleta_id=id).delete()`

## 3.4 Objetos de banco existentes

- **Tabelas**: 11
- **Views**: nenhuma
- **Triggers**: nenhum
- **Procedures/Stored Procedures**: nenhuma (SQLite nao possui procedure nativa neste projeto)
- **Functions de banco customizadas**: nenhuma
- **Indexes explicitos**: somente autoindexes de `user` (por UNIQUE)

## 3.5 Mapa direto de tabelas, PK e relacionamentos

| Tabela | Chave primaria | Relacionamento |
|---|---|---|
| `user` | `id` | sem FK para outras tabelas |
| `atleta` | `id` | 1:N com `ficha_medica` |
| `comissao_tecnica` | `id` | sem FK |
| `compra` | `id` | sem FK |
| `gasto_mensal` | `id` | sem FK |
| `conta_fixa` | `id` | sem FK |
| `inventario` | `id` | sem FK |
| `reuniao` | `id` | sem FK |
| `evento` | `id` | sem FK |
| `ficha_medica` | `id` | FK `atleta_id -> atleta.id` |
| `scouting` | `id` | sem FK |

### Detalhe do relacionamento ativo

- **Pai**: `atleta(id)`
- **Filha**: `ficha_medica(atleta_id)`
- **Cardinalidade**: um atleta pode ter varias fichas medicas
- **Regra atual de exclusao**: sem cascade no banco; a aplicacao remove fichas antes de remover atleta

### SQL de referencia do relacionamento

```sql
CREATE TABLE ficha_medica (
  id INTEGER PRIMARY KEY,
  atleta_id INTEGER NOT NULL,
  ...,
  FOREIGN KEY(atleta_id) REFERENCES atleta(id)
);
```

---

## 4) Dicionario de dados resumido (por modulo)

## 4.1 Usuarios (`user`)

- autenticacao: `username`, `password` (hash)
- perfil: `email`, `is_admin`, `is_active`
- auditoria basica: `created_at`, `last_login` (campo existe, mas nao atualizado no login atual)

## 4.2 Atletas (`atleta`)

- cadastro pessoal: nome, nascimento, telefone, email, endereco
- esporte: posicao, numero, categoria
- biometria: altura, peso
- operacional: status, foto, created_at

## 4.3 Departamento medico (`ficha_medica`)

- vinculo com atleta: `atleta_id`
- clinico: tipo_lesao, gravidade, diagnostico, tratamento
- temporal: data_lesao, retorno_previsto, retorno_efetivo
- controle: status (`em_tratamento`/`recuperado`), medico_responsavel, observacoes

## 4.4 Comissao tecnica (`comissao_tecnica`)

- identificacao: nome, cargo, especialidade
- contato: telefone, email
- contrato/status: data_contratacao, status
- imagem: foto

## 4.5 Compras (`compra`)

- item, quantidade, valor_unitario, total
- data_compra, fornecedor, categoria

## 4.6 Gastos mensais (`gasto_mensal`)

- mes (`YYYY-MM`)
- categoria, valor, descricao
- data_pagamento
- comprovante (campo existe, uso parcial na UI)

## 4.7 Contas fixas (`conta_fixa`)

- descricao, valor
- dia vencimento (`data_vencimento` int)
- categoria
- status (`ativa`/`inativa`)

## 4.8 Inventario (`inventario`)

- nome, categoria, quantidade
- localizacao
- data_aquisicao, valor_aquisicao
- status

## 4.9 Reunioes (`reuniao`)

- titulo, data, hora, local
- pauta, participantes, ata
- status (`agendada`/`concluida`)

## 4.10 Calendario (`evento`)

- titulo, data, tipo, descricao

## 4.11 Scouting (`scouting`)

- jogador: nome, clube, posicao, nacionalidade, pe_dominante
- fisico: altura, peso
- contrato/mercado: valor_estimado, contrato_ate
- avaliacao: nota_tecnica, nota_fisica, nota_tatica, nota_mental
- observacao: partida_observada, data_observacao, campeonato, observador
- analise: pontos_fortes, pontos_fracos, resumo
- decisao: indicacao, status
- midia: video_url

---

## 5) Funcionalidades por tela e rotas

## 5.1 Login

- `GET/POST /login`
- valida `username + password` via hash
- redireciona para dashboard

## 5.2 Dashboard (`/`)

KPIs principais:

- total de gastos do mes (busca 1 registro por `mes` atual)
- numero total de atletas
- numero de reunioes futuras
- total de atletas lesionados (`ficha_medica.status = em_tratamento`)

Outros componentes:

- lista dos 5 atletas mais recentes
- graficos (Chart.js) com dados parcialmente estaticos
- atalhos para modulos principais

## 5.3 Usuarios (`/usuarios`)

- somente admin
- listar usuarios
- criar usuario (`POST /criar-usuario`)
- remover usuario (`GET /deletar-usuario/<id>`)
- validacoes:
  - username unico
  - email unico
  - nao remover o proprio usuario

## 5.4 Atletas (`/atletas`)

- listar atletas
- cadastrar atleta com upload de foto
- editar (`/atletas/editar/<id>`)
- deletar (`/atletas/deletar/<id>`)
- ao deletar: remove fichas medicas vinculadas e foto fisica

## 5.5 Comissao tecnica (`/comissao`)

- listar membros
- cadastrar membro com foto
- editar (`/comissao/editar/<id>`)
- deletar (`/comissao/deletar/<id>`)

## 5.6 Compras (`/compras`)

- listar compras
- cadastrar compra
- calcula `total = quantidade * valor_unitario`
- mostra total agregado da pagina
- deletar compra (`/compras/deletar/<id>`)

## 5.7 Gastos (`/gastos`)

- listar gastos
- cadastrar gasto mensal
- deletar gasto (`/gastos/deletar/<id>`)

## 5.8 Contas fixas (`/contas_fixas`)

- listar contas
- cadastrar conta
- alternar status ativa/inativa (`/contas_fixas/toggle/<id>`)
- deletar conta (`/contas_fixas/deletar/<id>`)
- KPI local: total mensal de contas ativas

## 5.9 Inventario (`/inventario`)

- listar itens
- cadastrar item
- deletar item (`/inventario/deletar/<id>`)

## 5.10 Reunioes (`/reunioes`)

- listar reunioes
- agendar reuniao (POST na propria rota)
- concluir reuniao (`/reunioes/concluir/<id>`)
- deletar reuniao (`/reunioes/deletar/<id>`)
- rota adicional duplicada: `POST /adicionar_reuniao`

## 5.11 Calendario (`/calendario`)

- listar eventos em visual de calendario (FullCalendar)
- adicionar evento (`POST /calendario/adicionar`)

## 5.12 Departamento medico (`/departamento_medico`)

- listar fichas medicas
- listar atletas ativos para vinculo
- criar ficha (`POST /departamento_medico/adicionar`)
- atualizar status/observacoes (`POST /departamento_medico/atualizar/<id>`)
- regra: ao marcar `recuperado`, grava `data_retorno_efetivo`

## 5.13 Scouting (`/scouting`)

- listar jogadores observados
- adicionar scouting completo (`POST /scouting/adicionar`)
- atualizar status e indicacao (`POST /scouting/atualizar/<id>`)

---

## 6) KPIs existentes e calculos atuais

### Dashboard

1. **Atletas no elenco**  
   `COUNT(atleta.id)`

2. **Lesionados**  
   `COUNT(ficha_medica.id WHERE status='em_tratamento')`

3. **Reunioes agendadas**  
   `COUNT(reuniao.id WHERE data >= hoje)`

4. **Gastos do mes**  
   Usa apenas o primeiro registro de `gasto_mensal` do mes atual (`.first()`), nao soma todos.

### Modulos

- **Compras**: soma local de `compra.total` exibida na pagina
- **Contas fixas**: soma local de contas com `status='ativa'`

---

## 7) Funcoes e componentes de aplicacao

## 7.1 Funcoes utilitarias

- `allowed_file(filename)`: valida extensao de upload
- `load_user(user_id)`: carrega usuario para sessao Flask-Login
- `create_admin()`: cria admin padrao se inexistente

## 7.2 Objetos tecnicos relevantes

- `app` (Flask)
- `db` (SQLAlchemy)
- `login_manager` (Flask-Login)
- `current_user` (contexto de usuario autenticado)

## 7.3 Rotas e handlers

Rotas CRUD para os modulos citados na secao 5, com commit/rollback em blocos `try/except`.

---

## 8) Relacionamento entre campos e regras de negocio

1. `compra.total` depende de `quantidade * valor_unitario` (calculado na aplicacao).
2. `ficha_medica.data_retorno_efetivo` depende de mudanca de status para `recuperado`.
3. `conta_fixa.status` altera soma mensal do modulo de contas fixas.
4. `atleta.status='ativo'` filtra atletas disponiveis para nova ficha medica.
5. `user.is_admin` controla acesso ao modulo de usuarios.

---

## 9) Lacunas tecnicas atuais

1. Tela `permissoes.html` sem suporte no backend/modelo.
2. `historico_medico.html` existe, mas sem rota dedicada ativa.
3. `templates/deletar_compra` existe sem extensao e sem uso claro.
4. Campo `last_login` nao e atualizado no login.
5. KPI de gastos do dashboard nao soma o mes inteiro (pega somente um registro).
6. Ausencia de delete/edicao para alguns modulos (ex.: evento de calendario, registros scouting).
7. `SECRET_KEY` fixa no codigo (recomendado mover para variavel de ambiente).
8. No `if __name__ == '__main__'` ha dois `app.run()` sequenciais (o segundo fica inatingivel).

---

## 10) Integracoes futuras recomendadas

## 10.1 Prioridade alta

1. **RBAC completo de permissoes**  
   Implementar colunas de permissao no `user`, rota `atualizar_permissoes` e guardas por modulo.

2. **Financeiro consolidado**  
   Integrar compras + gastos + contas fixas em um painel unico com consolidacao mensal real.

3. **Auditoria e trilha de alteracoes**  
   Registrar quem criou/alterou/excluiu registros criticos.

## 10.2 Prioridade media

4. **Integracao de anexos/comprovantes**
   Upload real para `gasto_mensal.comprovante` com armazenamento e visualizacao.

5. **Calendario externo (Google/Outlook)**
   Sincronizar reunioes/eventos com calendarios corporativos.

6. **Comunicacao**
   Disparo de notificacoes por e-mail/WhatsApp para reunioes, vencimentos e status medico.

## 10.3 Prioridade evolutiva

7. **BI/KPIs avancados**
   Indicadores por categoria, tendencia mensal, custo por atleta, taxa de lesao por periodo.

8. **API externa**
   Expor API REST autenticada para integracao com app mobile/painel executivo.

9. **Workflow medico e scouting**
   Estados mais detalhados, aprovacoes, historico de decisoes e anexos de laudos/videos.

---

## 11) Resumo executivo

- O sistema esta funcional para operacao diaria, com CRUDs dos principais modulos.
- O banco e simples, consistente, com 1 relacionamento forte (`atleta` x `ficha_medica`).
- O controle de acesso hoje e binario (admin x autenticado).
- O maior ganho futuro esta em:
  - permissoes granulares,
  - consolidacao financeira real,
  - integracoes (calendario, anexos, notificacoes, API),
  - e melhoria de KPIs/auditoria.
