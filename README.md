# Mini-sistema IoT de Cultivo de Morangos
### Atividade T3 — Back-end (API + Persistência em XML + Validação XSD)
### Atividade T4 — Interfaces (Front-end) sobre XML + API T3
#### **Aluna:** Izadora Bernardi
#### **Disciplina:** Engenharia de Software

## 1. Organização do diretório
```bash
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── controller.py
│   │   ├── service_xml.py
│   │   └── model/
│   │       └── schema.xsd
│   │
│   ├── config/
│   │   ├── regras_defaut.json
│   │   ├── regras_atuais.json (.gitignore)
│   │   └── settings.py
│   │
│   ├── data/
│   │
│   ├── docs/
│   │   ├── XML_tree.png
│   │   ├── diagrama_sequencia_GET.png
│   │   └── diagrama_sequencia_POST.png
│   │ 
│   └── tests/
│       └── test_api.py
│     
├── frontend/
│   ├── index.html
│   ├── main.js
│   ├── styles.css   
│   └── favicon.ico
│ 
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 2. Requisitos Funcionais

* **RF1 (Leitura) e RF2 (Armazenamento):**
    * `POST /api/leituras`: Recebe, valida (XSD, Regras) e persiste os dados XML.
    * 409 Conflict: A API rejeita XMLs com IDs de leitura duplicados.

* **RF3 (Alertas):**
    * `GET /api/alertas`: Endpoint que processa todos os dados e retorna apenas as leituras que estão fora das faixas de regras.

* **RF5 (Visualização em Tempo Real):**
    * `GET /api/leituras`: Endpoint que lê e retorna todos os dados persistidos em formato JSON.

* **RF6 (Ajuste de Intervalos):**
    * `GET /api/configuracoes`: Endpoint que lê as regras de negócio atuais (ex: faixas de pH).
    * `PUT /api/configuracoes`: Endpoint que permite ao administrador *atualizar* as regras.
    * **(Extra) `POST /api/configuracoes/reset`:** Endpoint que restaura as regras para o "Padrão de Fábrica", garantindo robustez (uma decisão de design para segurança).

* **RF8 (Exportação de Dados):**
    * `GET /api/exportar?formato=csv`: Endpoint que exporta *todos* os dados do sistema para um ficheiro CSV, pronto para análise externa.

* **Requisitos Abandonados:**
    * Os requisitos **RF4 (Relatórios Estatísticos)** e **RF7 (Gestão de Sensores)** foram abandonados devido à complexidade do sistema.

* **Gestão de Dados (Adicionado posteriormente):**
    * **`DELETE /api/leituras`:** Endpoint que apaga permanentemente *todos* os dados de leitura (`.xml`) do sistema, permitindo "limpar o histórico".
---

## 3. Arquitetura do Software

O projeto utiliza uma arquitetura de 3 camadas para garantir a separação de responsabilidades:

1.  **`routes.py`:**
    * Define os endpoints da API (as URLs) e os métodos HTTP (GET, POST, PUT).
    * Dereciona os pedidos para o `controller` e formata erros.

2.  **`controller.py`:**
    * Orquestra o fluxo do pedido. Não contém lógica de negócio.
    * Ele "gere" o fluxo, pedindo ao `service` para executar o trabalho e formatando a resposta de sucesso (ex: `jsonify`).

3.  **`service_xml.py`:**
    * Contém 100% da lógica de negócio.
    * Sabe como: validar XSD, validar regras, ler/escrever ficheiros (`data/`), ler/escrever JSONs de regras (`config/`) e converter dados para CSV (`pandas`).

---

## 4. Endpoints

#### Leituras
* `POST /api/leituras`
    * **Ação:** Envia um novo conjunto de leituras.
    * **Body:** XML (conforme `schema.xsd`).
    * **Resposta (Sucesso):** `201 Created`
    * **Resposta (Falha):** `400 Bad Request` (XSD, Regras), `409 Conflict` (Duplicado).

* `GET /api/leituras`
    * **Ação:** Lista todos os dados de todas as estufas.
    * **Resposta:** `200 OK` (com um JSON de todos os dados).

* `DELETE /api/leituras`
    * **Ação:** Deleta o histórico de leituras (backend/data/).
    * **Resposta:** `200 OK`

#### Alertas e Exportação
* `GET /api/alertas`
    * **Ação:** Lista apenas as leituras que estão fora das faixas definidas.
    * **Resposta:** `200 OK` (com um JSON dos alertas).

* `GET /api/exportar?formato=csv`
    * **Ação:** Inicia o download de um `.csv` com todos os dados.
    * **Resposta:** `200 OK` (com o ficheiro `leituras.csv`).

#### Configuração
* `GET /api/configuracoes`
    * **Ação:** Mostra as regras de negócio atuais (ex: faixas de pH).
    * **Resposta:** `200 OK` (com o JSON das regras).

* `PUT /api/configuracoes`
    * **Ação:** Atualiza/sobrescreve as regras de negócio.
    * **Body:** JSON com as novas regras.
    * **Resposta:** `200 OK`

* `POST /api/configuracoes/reset`
    * **Ação:** Restaura as regras para os padrões de fábrica (o `regras_default.json`).
    * **Resposta:** `200 OK`

## 5. Arquitetura do Frontend

O frontend utiliza HTML, CSS, JavaScript puros. Por ser algo pequeno, foi desenhado como uma Single-Page Application (SPA):
* `index.html`: Atua como a "casca" principal da aplicação.
* `styles.css`: Define a aparência de todos os componentes.
* `main.js`: Contém todo o "cérebro" do frontend. Ele controla a navegação (escondendo e mostrando as secções `<section>`) e faz todos os pedidos `fetch` para a API do T3.

## 9. Funcionalidades Implementadas

A interface é dividida em quatro "views" principais:

* **`Dashboard` (RF5, RF8)**
    * Consome `GET /api/leituras` assim que a página carrega.
    * Inclui um link **"Exportar Dados para CSV" (RF8)** que aponta para o `GET /api/exportar`.
    * Inclui um botão **"Limpar Histórico de Leituras"** que chama o `DELETE /api/leituras` .

* **`Alertas` (RF3)**
    * Consome `GET /api/alertas` assim que a página carrega.
    * Mostra "cards" (em estilo de alerta) apenas para as leituras que o backend identificou como "fora da faixa".

* **`Editor XML` (T4)**
    * **Botão "Importar XML (Completo)"** e **"Importar XML (Simples)":** Preenche o `<textarea>` com um XML de teste com 7 e 1 sensore(s), respectivamente.
    * **Botão "Enviar XML para API":** Envia o conteúdo do `<textarea>` para o `POST /api/leituras`. O frontend *não* bloqueia o envio; ele confia no backend (T3) para fazer a validação XSD e de regras. Se o envio for bem-sucedido, o Dashboard e os Alertas são atualizados automaticamente.
    
* **`Configuração` (RF6)**
    * Consome `GET /api/configuracoes` ao carregar a aplicação, preenchendo o formulário com as faixas atuais e guardando-as num "cache" global.
    * **"Salvar Regras":** Chama `PUT /api/configuracoes` para enviar os novos valores do formulário e atualiza o cache local.
    * **"Restaurar Padrão de Fábrica":** Chama `POST /api/configuracoes/reset` e recarrega o formulário e o cache com os dados restaurados.