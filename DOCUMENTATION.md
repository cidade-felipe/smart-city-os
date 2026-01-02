# SmartCityOS

Um sistema operacional inteligente para cidades que gerencia usuários, veículos, sensores, incidentes de trânsito e multas de forma automatizada.

## 📋 Visão Geral

O SmartCityOS é um sistema de gestão urbana inteligente desenvolvido em Python com PostgreSQL, projetado para automatizar o controle de trânsito, gerenciamento de multas e monitoramento de sensores em ambientes urbanos. O sistema utiliza triggers de banco de dados para aplicar automaticamente penalidades e gerenciar carteiras digitais de cidadãos.

## 🏗️ Arquitetura do Sistema

### Tecnologias Utilizadas

- **Backend**: Python 3.12+
- **Banco de Dados**: PostgreSQL 18.0
- **Bibliotecas Principais**:
  - `psycopg` - Conexão com PostgreSQL
  - `pandas` - Manipulação de dados
  - `python-dotenv` - Gestão de variáveis de ambiente
  - `tabulate` - Formatação de tabelas

### Estrutura do Projeto

```text
SmartCityOS/
├── smart_city_os.ipynb    # Notebook principal com funções do sistema
├── sql/                   # Scripts SQL do banco de dados
│   ├── create_tables.sql  # Criação das tabelas
│   ├── trigger_functions.sql  # Funções de trigger
│   ├── triggers.sql       # Definição dos triggers
│   └── index.sql          # Índices de performance
├── csv/                   # Exportação de dados
├── backup/                # Backups do banco
├── venv/                  # Ambiente virtual
├── DOCUMENTATION.md       # Este documento
└── README.md              # Documentação principal
```

## 🗄️ Modelo de Dados

### Diagrama Entidade-Relacionamento (ER)

```mermaid
erDiagram
    app_user {
        int id PK
        varchar first_name
        varchar last_name
        varchar cpf UK
        date birth_date
        varchar email UK
        varchar phone
        text address
        varchar username UK
        varchar password_hash
        timestamp created_at
        timestamp updated_at
    }

    citizen {
        int id PK
        int app_user_id FK
        jsonb biometric_reference
        numeric wallet_balance
        numeric debt
        boolean allowed
        timestamp created_at
        timestamp updated_at
    }

    vehicle {
        int id PK
        int app_user_id FK
        varchar license_plate UK
        varchar model
        int year
        int citizen_id FK
        boolean allowed
        timestamp created_at
        timestamp updated_at
    }

    vehicle_citizen {
        int id PK
        int vehicle_id FK
        int citizen_id FK
    }

    sensor {
        int id PK
        int app_user_id FK
        varchar model
        varchar type
        text location
        boolean active
        jsonb last_reading
        timestamp created_at
        timestamp updated_at
    }

    reading {
        int id PK
        int sensor_id FK
        jsonb value
        timestamp timestamp
        timestamp created_at
        timestamp updated_at
    }

    traffic_incident {
        int id PK
        int vehicle_id FK
        int sensor_id FK
        timestamp occurred_at
        text location
        text description
        timestamp created_at
        timestamp updated_at
    }

    fine {
        int id PK
        int traffic_incident_id FK
        numeric amount
        varchar status
        date due_date
        timestamp created_at
        timestamp updated_at
    }

    fine_payment {
        int id PK
        int fine_id FK
        numeric amount_paid
        timestamp paid_at
        varchar payment_method
        timestamp created_at
        timestamp updated_at
    }

    payment_method {
        int id PK
        varchar name UK
        timestamp created_at
    }

    notification {
        int id PK
        varchar type
        text message
        timestamp created_at
        timestamp updated_at
    }

    app_user_notification {
        int id PK
        int notification_id FK
        int app_user_id FK
        timestamp read_at
        timestamp created_at
        timestamp updated_at
    }

    audit_log {
        int id PK
        varchar table_name
        varchar operation
        int row_id
        jsonb old_values
        jsonb new_values
        int app_user_id FK
        timestamp changed_at
    }

    %% Relacionamentos
    app_user ||--o{ citizen : "1:1"
    app_user ||--o{ vehicle : "1:N"
    app_user ||--o{ sensor : "1:N"
    app_user ||--o{ app_user_notification : "1:N"
    app_user ||--o{ audit_log : "1:N"
    
    citizen ||--o{ vehicle : "1:N"
    citizen ||--o{ vehicle_citizen : "1:N"
    
    vehicle ||--o{ vehicle_citizen : "1:N"
    vehicle ||--o{ traffic_incident : "1:N"
    
    sensor ||--o{ reading : "1:N"
    sensor ||--o{ traffic_incident : "1:N"
    
    traffic_incident ||--o{ fine : "1:1"
    fine ||--o{ fine_payment : "1:N"
    
    notification ||--o{ app_user_notification : "1:N"
```

### Tabelas Principais

#### 1. `app_user`

Tabela principal de usuários do sistema.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do usuário
- `first_name` (VARCHAR(100), NOT NULL) - Primeiro nome do usuário
- `last_name` (VARCHAR(150), NOT NULL) - Sobrenome do usuário
- `cpf` (VARCHAR(11), UNIQUE, NOT NULL) - CPF do usuário
- `birth_date` (DATE, NOT NULL) - Data de nascimento
- `email` (VARCHAR(255), UNIQUE, NOT NULL) - Email do usuário
- `phone` (VARCHAR(20)) - Telefone de contato
- `address` (TEXT, NOT NULL) - Endereço completo
- `username` (VARCHAR(255), UNIQUE, NOT NULL) - Nome de usuário para login
- `password_hash` (VARCHAR(255), NOT NULL) - Hash da senha
- `created_at` (TIMESTAMP) - Data de criação do registro
- `updated_at` (TIMESTAMP) - Data da última atualização

#### 2. `citizen`

Extensão do usuário com informações específicas de cidadão.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do cidadão
- `app_user_id` (INTEGER, NOT NULL) - Referência ao usuário (FK)
- `biometric_reference` (JSONB) - Dados biométricos para autenticação
- `wallet_balance` (NUMERIC(10,2), DEFAULT 0.00) - Saldo da carteira digital
- `debt` (NUMERIC(10,2), DEFAULT 0.00) - Dívida acumulada
- `allowed` (BOOLEAN, DEFAULT TRUE) - Status de acesso ao sistema
- `created_at` (TIMESTAMP) - Data de criação
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `chk_wallet_balance` - Garante que o saldo não seja negativo
- `chk_debt` - Garante que a dívida não seja negativa
- `fk_user` - Chave estrangeira para `app_user`

#### 3. `vehicle`

Cadastro de veículos dos cidadãos.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do veículo
- `app_user_id` (INTEGER, NOT NULL) - Proprietário do veículo (FK)
- `license_plate` (VARCHAR(12), UNIQUE, NOT NULL) - Placa do veículo
- `model` (VARCHAR(100), NOT NULL) - Modelo do veículo
- `year` (INTEGER, NOT NULL) - Ano de fabricação
- `citizen_id` (INTEGER) - Cidadão associado (FK)
- `allowed` (BOOLEAN, DEFAULT TRUE) - Status de permissão do veículo
- `created_at` (TIMESTAMP) - Data de cadastro
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `fk_citizen` - Chave estrangeira para `citizen`
- `fk_user` - Chave estrangeira para `app_user`

#### 4. `sensor`

Sensores de monitoramento urbano.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do sensor
- `app_user_id` (INTEGER, NOT NULL) - Usuário responsável (FK)
- `model` (VARCHAR(255), NOT NULL) - Modelo do sensor
- `type` (VARCHAR(100), NOT NULL) - Tipo de sensor (ex: câmera, radar)
- `location` (TEXT, NOT NULL) - Localização física do sensor
- `active` (BOOLEAN, DEFAULT TRUE) - Status de atividade
- `last_reading` (JSONB) - Última leitura capturada
- `created_at` (TIMESTAMP) - Data de instalação
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `fk_user` - Chave estrangeira para `app_user`

#### 5. `reading`

Leituras capturadas pelos sensores.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único da leitura
- `sensor_id` (INTEGER, NOT NULL) - Sensor que capturou (FK)
- `value` (JSONB, NOT NULL) - Valor da leitura em formato JSON
- `timestamp` (TIMESTAMP) - Momento da captura
- `created_at` (TIMESTAMP) - Data de registro
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `fk_sensor` - Chave estrangeira para `sensor`

#### 6. `vehicle_citizen`

Tabela de relacionamento muitos-para-muitos entre veículos e cidadãos.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do relacionamento
- `vehicle_id` (INTEGER, NOT NULL) - Veículo relacionado (FK)
- `citizen_id` (INTEGER, NOT NULL) - Cidadão relacionado (FK)

**Constraints:**

- Chave única composta (vehicle_id, citizen_id)
- `fk_vehicle` - Chave estrangeira para `vehicle`
- `fk_citizen` - Chave estrangeira para `citizen`

#### 7. `traffic_incident`

Incidentes de trânsito detectados pelo sistema.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do incidente
- `vehicle_id` (INTEGER, NOT NULL) - Veículo envolvido (FK)
- `sensor_id` (INTEGER, NOT NULL) - Sensor que detectou (FK)
- `occurred_at` (TIMESTAMP) - Data/hora do incidente
- `location` (TEXT) - Localização do incidente
- `description` (TEXT) - Descrição detalhada
- `created_at` (TIMESTAMP) - Data de registro
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `fk_vehicle` - Chave estrangeira para `vehicle`
- `fk_sensor` - Chave estrangeira para `sensor`

#### 8. `fine`

Multas aplicadas aos incidentes.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único da multa
- `traffic_incident_id` (INTEGER, NOT NULL) - Incidente relacionado (FK)
- `amount` (NUMERIC(10,2), NOT NULL) - Valor da multa
- `status` (VARCHAR(20), DEFAULT 'pending') - Status (pending/paid/cancelled)
- `due_date` (DATE) - Data de vencimento
- `created_at` (TIMESTAMP) - Data de emissão
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `chk_fine_amount` - Garante que o valor não seja negativo
- `chk_fine_status` - Limita os valores de status
- `fk_traffic_incident` - Chave estrangeira para `traffic_incident`

#### 9. `fine_payment`

Pagamentos de multas realizados.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do pagamento
- `fine_id` (INTEGER, NOT NULL) - Multa paga (FK)
- `amount_paid` (NUMERIC(10,2), NOT NULL) - Valor pago
- `paid_at` (TIMESTAMP) - Data/hora do pagamento
- `payment_method` (VARCHAR(50), NOT NULL) - Método de pagamento
- `created_at` (TIMESTAMP) - Data de registro
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `chk_amount_paid` - Garante que o valor pago não seja negativo
- `fk_fine` - Chave estrangeira para `fine`

#### 10. `notification`

Sistema de notificações do sistema.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único
- `type` (VARCHAR(50), NOT NULL) - Tipo da notificação
- `message` (TEXT, NOT NULL) - Conteúdo da mensagem
- `created_at` (TIMESTAMP) - Data de criação
- `updated_at` (TIMESTAMP) - Data da última atualização

#### 11. `payment_method`

Métodos de pagamento disponíveis.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único
- `name` (VARCHAR(50), UNIQUE, NOT NULL) - Nome do método
- `created_at` (TIMESTAMP) - Data de cadastro

#### 12. `app_user_notification`

Relacionamento entre usuários e notificações.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único
- `notification_id` (INTEGER, NOT NULL) - Notificação (FK)
- `app_user_id` (INTEGER, NOT NULL) - Usuário destinatário (FK)
- `read_at` (TIMESTAMP) - Data de leitura (NULL se não lida)
- `created_at` (TIMESTAMP) - Data de criação
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- Chave única composta (notification_id, app_user_id)
- `fk_notification` - Chave estrangeira para `notification`
- `fk_app_user` - Chave estrangeira para `app_user`

#### 13. `audit_log`

Registro de auditoria do sistema.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único
- `table_name` (VARCHAR(100), NOT NULL) - Tabela afetada
- `operation` (VARCHAR(10), NOT NULL) - Operação (INSERT/UPDATE/DELETE)
- `row_id` (INTEGER) - ID da linha afetada
- `old_values` (JSONB) - Valores anteriores
- `new_values` (JSONB) - Novos valores
- `app_user_id` (INTEGER) - Usuário que realizou a operação (FK)
- `changed_at` (TIMESTAMP) - Data/hora da alteração

**Constraints:**

- `chk_operation` - Limita os tipos de operação
- `fk_changed_by` - Chave estrangeira para `app_user`

## ⚡ Triggers e Funções

### 1. `trigger_apply_fine`

**Função:** `apply_fine_to_wallet()`
**Evento:** AFTER INSERT ON `traffic_incident`
**Descrição:** Aplica automaticamente multas à carteira do cidadão quando um incidente é criado.

**Lógica:**

- Identifica o cidadão proprietário do veículo
- Verifica se há valor de multa definido
- Se o saldo for suficiente, deduz da carteira
- Se insuficiente, zera o saldo, acumula como dívida e bloqueia acesso

### 2. `trigger_apply_fine_payment`

**Função:** `apply_fine_payment()`
**Evento:** AFTER INSERT ON `fine_payment`
**Descrição:** Processa pagamentos de multas e atualiza o status do cidadão.

**Lógica:**

- Reduz a dívida do cidadão pelo valor pago
- Reativa o acesso quando a dívida for completamente paga
- Atualiza timestamps automaticamente

### 3. `audit_trigger_citizen`

**Função:** `audit_log_function()`
**Evento:** AFTER INSERT OR UPDATE OR DELETE ON `citizen`
**Descrição:** Registra todas as alterações na tabela `citizen` para auditoria.

**Lógica:**

- Captura dados antigos e novos
- Registra tipo de operação
- Armazena informações em `audit_log`

## 🚀 Índices de Performance

### Índices de Trânsito e Incidentes

- `idx_traffic_incident_vehicle` - Busca por veículo em incidentes
- `idx_traffic_incident_sensor` - Busca por sensor em incidentes  
- `idx_traffic_incident_occurred_at` - Consultas por período

### Índices de Multas

- `idx_fine_traffic_incident` - Relacionamento multa-incidente
- `idx_fine_pending` - Multas pendentes (índice parcial)
- `idx_fine_due_date` - Ordenação por vencimento

### Índices de Pagamentos

- `idx_fine_payment_fine` - Busca por multa
- `idx_fine_payment_paid_at` - Consultas por data de pagamento

### Índices de Veículos e Cidadãos

- `idx_vehicle_app_user` - Veículos por proprietário
- `idx_vehicle_allowed_true` - Veículos ativos (índice parcial)
- `idx_citizen_app_user` - Cidadãos por usuário

### Índices de Sensores

- `idx_sensor_app_user_active` - Sensores ativos por usuário

### Índices de Notificações

- `idx_app_user_notification_app_user` - Notificações por usuário
- `idx_app_user_notification_unread` - Notificações não lidas (índice parcial)

### Índices de Auditoria

- `idx_audit_log_app_user` - Logs por usuário
- `idx_audit_log_changed_at` - Ordenação por data
- `idx_audit_log_table_operation` - Busca por tabela e operação
- `idx_audit_log_row_id` - Busca por registro específico

## 🔧 Configuração e Instalação

### Pré-requisitos

- Python 3.12+
- PostgreSQL 18.0
- Ambiente virtual (venv)

### Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis:

```env
DB_NAME=smart_city_os
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_POOL_URL=postgresql+psycopg2://postgres:sua_senha@localhost:5432/smart_city_os
```

### Instalação

```bash
# Clonar repositório
git clone <repositório>
cd SmartCityOS

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install psycopg python-dotenv pandas tabulate
```

### Configuração do Banco de Dados

1. Criar banco de dados PostgreSQL
2. Executar os scripts SQL em ordem:
   - `sql/create_tables.sql`
   - `sql/trigger_functions.sql`
   - `sql/triggers.sql`
   - `sql/index.sql`

## 📊 Funcionalidades Principais

### 1. Gestão de Usuários e Cidadãos

- Cadastro de usuários com autenticação
- Extensão para cidadãos com carteira digital
- Controle biométrico opcional

### 2. Gestão de Veículos

- Cadastro de veículos com validação de placa
- Associação automática com cidadãos
- Controle de permissão de acesso

### 3. Monitoramento por Sensores

- Cadastro de sensores urbanos
- Captura automática de leituras
- Detecção de incidentes em tempo real

### 4. Sistema de Multas Automático

- Geração automática de multas
- Dedução automática da carteira digital
- Acumulação de dívida quando necessário
- Bloqueio automático de acesso

### 5. Sistema de Pagamentos

- Múltiplos métodos de pagamento
- Processamento automático de quitação
- Reativação automática de acesso

### 6. Sistema de Notificações

- Notificações personalizadas
- Controle de leitura
- Envio por usuário

### 7. Auditoria Completa

- Registro de todas as operações
- Rastreabilidade completa
- Dados anteriores e posteriores

## 🔄 Fluxo de Trabalho

### Fluxo de Incidente de Trânsito

1. Sensor detecta infração
2. Sistema cria `traffic_incident`
3. Trigger `apply_fine_to_wallet` é acionado
4. Multa é aplicada à carteira do cidadão
5. Se saldo insuficiente, vira dívida e acesso é bloqueado
6. Notificação é gerada automaticamente

### Fluxo de Pagamento

1. Cidadão realiza pagamento
2. Registro em `fine_payment`
3. Trigger `apply_fine_payment` é acionado
4. Dívida é reduzida
5. Se dívida zerada, acesso é reativado
6. Auditoria registra operação

## 🧪 Testes e Exemplos

O notebook `smart_city_os.ipynb` contém funções para:

- Conexão com o banco de dados
- Criação de tabelas
- Inserção de dados de teste
- Consultas e visualizações
- Exportação de dados para CSV

## 📈 Performance e Otimização

### Índices Estratégicos

- Índices parciais para consultas frequentes
- Índices compostos para buscas complexas
- Otimização para queries de tempo real

### Triggers Eficientes

- Processamento automático no banco
- Redução de round trips
- Consistência garantida

## 🔒 Segurança

### Controle de Acesso

- Bloqueio automático por dívida
- Validação de CPF único
- Hash de senhas seguro

### Auditoria

- Registro completo de operações
- Rastreabilidade de alterações
- Logs de acesso

## 🚀 Extensões Futuras

### Possíveis Melhorias

- Integração com APIs de pagamento externas
- Sistema de notificações por email/SMS
- Dashboard em tempo real
- Machine learning para previsão de incidentes
- Integração com sistemas de trânsito municipais

## 📝 Licença

Este projeto está licenciado sob os termos da licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.

## 👥 Contribuição

Contribuições são bem-vindas! Por favor:

1. Fork do projeto
2. Criar branch para feature
3. Submeter pull request
4. Manter padrão de código e documentação

## Suporte

Para dúvidas e suporte:

- Analisar o notebook de exemplos
- Verificar logs de auditoria
- Consultar documentação do PostgreSQL
- Revisar estrutura de tabelas e triggers

## Autor

Este projeto foi desenvolvido por **Felipe Cidade Soares**.

**LinkedIn:** [https://www.linkedin.com/in/cidadefelipe/](https://www.linkedin.com/in/cidadefelipe/)
