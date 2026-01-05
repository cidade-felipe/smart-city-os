# SmartCityOS

Um sistema operacional inteligente para cidades que gerencia usuários, veículos, sensores, incidentes de trânsito e multas de forma automatizada.

## Visão Geral

O SmartCityOS é um sistema de gestão urbana inteligente desenvolvido em Python com PostgreSQL, projetado para automatizar o controle de trânsito, gerenciamento de multas e monitoramento de sensores em ambientes urbanos. O sistema utiliza triggers de banco de dados para aplicar automaticamente penalidades e gerenciar carteiras digitais de cidadãos.

### 🚀 Funcionalidades Principais

- **Soft Delete**: Sistema de exclusão suave que mantém dados históricos
- **Reuso de Username**: Permite reutilizar usernames de usuários deletados
- **Gestão de Entidades**: Cidadãos, Veículos, Sensores com soft delete em cascata
- **Views Ativas**: Views automáticas que filtram apenas dados não deletados
- **Validação de Username**: Verificação em tempo real de disponibilidade de usernames

## Arquitetura do Sistema

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
├── notebooks/              # Notebooks Jupyter
│   └── smart_city_os.ipynb # Notebook principal com funções do sistema
├── functions/              # Módulos Python organizados
│   ├── __init__.py         # Inicialização do pacote
│   ├── conect_db.py        # Conexão com banco de dados
│   ├── create_tables.py    # Criação de tabelas
│   ├── create_triggers.py  # Criação de triggers
│   ├── create_indexes.py   # Criação de índices
│   ├── create_views.py     # Criação de views
│   ├── drop_tables.py      # Remoção de tabelas
│   └── inserts.py          # Inserção de dados genéricos
├── sql/                    # Scripts SQL do banco de dados
│   ├── create_tables.sql   # Criação das tabelas
│   ├── trigger_functions.sql # Funções de trigger
│   ├── triggers.sql        # Definição dos triggers
│   ├── index.sql           # Índices de performance
│   └── wiews.sql           # Views de dados ativos
├── csv/                    # Exportação de dados
├── backup/                 # Backups do banco
├── venv/                   # Ambiente virtual
├── requirements.txt        # Dependências Python
├── DOCUMENTATION.md        # Este documento
└── README.md               # Documentação principal
```

## Modelo de Dados

Neste documento, descrevemos o modelo de dados do SmartCityOS, que é composto por 13 tabelas principais.

### Diagrama Entidade-Relacionamento (ER)

Abaixo está o diagrama ER do SmartCityOS.

```mermaid
erDiagram
    %% Relacionamentos principais
    app_user ||--|| citizen : "[[ 1 : 1 ]]"
    app_user ||--o{ vehicle : "[[ 1 : N ]]"
    app_user ||--o{ sensor : "[[ 1 : N ]]"
    app_user ||--o{ app_user_notification : "[[ 1 : N ]]"
    app_user ||--o{ audit_log : "[[ 1 : N ]]"
    
    citizen ||--o{ vehicle : "[[ 1 : N ]]"
    citizen ||--o{ vehicle_citizen : "[[ 1 : N ]]"
    citizen ||--o{ fine : "[[ 1 : N ]]"

    vehicle ||--o{ vehicle_citizen : "[[ 1 : N ]]"
    vehicle ||--o{ traffic_incident : "[[ 1 : N ]]"

    sensor ||--o{ reading : "[[ 1 : N ]]"
    sensor ||--o{ traffic_incident : "[[ 1 : N ]]"

    traffic_incident ||--|| fine : "[[ 1 : 1 ]]"
    fine ||--o{ fine_payment : "[[ 1 : N ]]"

    notification ||--o{ app_user_notification : "[[ 1 : N ]]"

    %% Definição das entidades com campos principais
    app_user {
        int id PK
        varchar username
        varchar password_hash
        timestamp deleted_at
        timestamp created_at
        timestamp updated_at
    }
    
    citizen {
        int id PK
        int app_user_id FK
        varchar first_name
        varchar last_name
        varchar cpf
        date birth_date
        varchar email
        varchar phone
        text address
        jsonb biometric_reference
        numeric wallet_balance
        numeric debt
        boolean allowed
        timestamp deleted_at
        timestamp created_at
        timestamp updated_at
    }
    
    vehicle {
        int id PK
        int app_user_id FK
        varchar license_plate
        varchar model
        int year
        int citizen_id FK
        boolean allowed
        timestamp deleted_at
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
        timestamp deleted_at
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
        int citizen_id FK
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
        int performed_by_app_user_id FK
        timestamp changed_at
    }
    
    payment_method {
        int id PK
        varchar name
        timestamp created_at
    }
```

### Tabelas Principais

#### 1. `app_user`

Usuários do sistema (administradores, operadores).

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do usuário
- `username` (VARCHAR(255), NOT NULL) - Nome de usuário
- `password_hash` (VARCHAR(255), NOT NULL) - Hash da senha
- `deleted_at` (TIMESTAMP) - Data de exclusão lógica (soft delete)
- `created_at` (TIMESTAMP) - Data de criação
- `updated_at` (TIMESTAMP) - Data da última atualização

**Índices:**

- `uniq_app_user_username_active` - Username único apenas para usuários ativos

**Observação:**

- Dados pessoais como nome, CPF, email estão na tabela `citizen`

#### 2. `citizen`

Extensão do usuário com informações pessoais e financeiras do cidadão.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do cidadão
- `app_user_id` (INTEGER, NOT NULL) - Referência ao usuário (FK)
- `first_name` (VARCHAR(100), NOT NULL) - Primeiro nome do cidadão
- `last_name` (VARCHAR(150), NOT NULL) - Sobrenome do cidadão
- `cpf` (VARCHAR(11), NOT NULL) - CPF do cidadão
- `birth_date` (DATE, NOT NULL) - Data de nascimento
- `email` (VARCHAR(255), NOT NULL) - Email do cidadão
- `phone` (VARCHAR(20)) - Telefone de contato
- `address` (TEXT, NOT NULL) - Endereço completo
- `biometric_reference` (JSONB) - Dados biométricos para autenticação
- `wallet_balance` (NUMERIC(10,2), DEFAULT 0.00) - Saldo da carteira digital
- `debt` (NUMERIC(10,2), DEFAULT 0.00) - Dívida acumulada
- `allowed` (BOOLEAN, DEFAULT TRUE) - Status de acesso ao sistema
- `deleted_at` (TIMESTAMP) - Data de exclusão lógica (soft delete)
- `created_at` (TIMESTAMP) - Data de criação
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `cpf` - Garante que o CPF tenha 11 caracteres
- `birth_date` - Garante que a data de nascimento seja anterior à data atual
- `email` - Garante que o email seja válido
- `chk_wallet_balance` - Garante que o saldo não seja negativo
- `chk_debt` - Garante que a dívida não seja negativa
- `fk_user` - Chave estrangeira para `app_user`

**Índices:**

- `ux_citizen_cpf_active` - CPF único apenas para cidadãos ativos
- `ux_citizen_email_active` - Email único apenas para cidadãos ativos

#### 3. `vehicle`

Cadastro de veículos dos cidadãos.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único do veículo
- `app_user_id` (INTEGER, NOT NULL) - Proprietário do veículo (FK)
- `license_plate` (VARCHAR(12), NOT NULL) - Placa do veículo
- `model` (VARCHAR(100), NOT NULL) - Modelo do veículo
- `year` (INTEGER, NOT NULL) - Ano de fabricação
- `citizen_id` (INTEGER) - Cidadão associado (FK)
- `allowed` (BOOLEAN, DEFAULT TRUE) - Status de permissão do veículo
- `deleted_at` (TIMESTAMP) - Data de exclusão lógica (soft delete)
- `created_at` (TIMESTAMP) - Data de cadastro
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `fk_citizen` - Chave estrangeira para `citizen` (ON DELETE SET NULL)
- `fk_user` - Chave estrangeira para `app_user` (ON DELETE CASCADE)

**Índices:**

- `ux_vehicle_license_plate_active` - Placa única apenas para veículos ativos

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
- `deleted_at` (TIMESTAMP) - Data de exclusão lógica (soft delete)
- `created_at` (TIMESTAMP) - Data de instalação
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `fk_user` - Chave estrangeira para `app_user` (ON DELETE CASCADE)

**Funcionalidade:**

- Soft delete automático define `active = FALSE`
- Previne leituras de sensores excluídos

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

**Observação:**

- Valor da multa é definido na tabela `fine` relacionada

#### 8. `fine`

Multas aplicadas aos incidentes.

**Colunas:**

- `id` (INTEGER, PRIMARY KEY) - Identificador único da multa
- `traffic_incident_id` (INTEGER, NOT NULL) - Incidente relacionado (FK)
- `citizen_id` (INTEGER, NOT NULL) - Cidadão responsável pela multa (FK)
- `amount` (NUMERIC(10,2), NOT NULL) - Valor da multa
- `status` (VARCHAR(20), DEFAULT 'pending') - Status (pending/paid/cancelled)
- `due_date` (DATE) - Data de vencimento
- `created_at` (TIMESTAMP) - Data de emissão
- `updated_at` (TIMESTAMP) - Data da última atualização

**Constraints:**

- `chk_fine_amount` - Garante que o valor não seja negativo
- `chk_fine_status` - Limita os valores de status
- `fk_traffic_incident` - Chave estrangeira para `traffic_incident` (ON DELETE CASCADE)
- `fk_citizen` - Chave estrangeira para `citizen` (ON DELETE CASCADE)

**Otimização:**

- `citizen_id` direto na tabela elimina JOINs desnecessários
- Consultas por cidadão são executadas sem joins adicionais

#### 9. `fine_payment`

Pagamentos de multas realizados.
  
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
- `app_user_id` (INTEGER) - Usuário afetado pela operação (FK)
- `performed_by_app_user_id` (INTEGER) - Usuário que realizou a operação (FK)
- `changed_at` (TIMESTAMP) - Data/hora da alteração

**Constraints:**

- `chk_operation` - Limita os tipos de operação
- `fk_affected_user` - Chave estrangeira para usuário afetado
- `fk_performed_by_user` - Chave estrangeira para usuário que realizou

## Soft Delete e Reuso de Username

### Visão Geral

O SmartCityOS implementa um sistema de **Soft Delete** que permite a exclusão lógica de registros mantendo o histórico completo dos dados. Esta funcionalidade é essencial para:

- **Preservação de dados históricos** para auditoria e análise
- **Recuperação de informações** em caso de exclusão acidental
- **Reuso de usernames** de usuários deletados
- **Manutenção da integridade** de relacionamentos

### Funcionalidades Implementadas

#### 1. Soft Delete em Cascata

Quando uma entidade principal é deletada, o sistema automaticamente:

- **Cidadãos**: Soft delete do cidadão + app_user associado
- **Veículos**: Soft delete do veículo + app_user associado  
- **Sensores**: Soft delete do sensor + app_user associado
- **App Users**: Soft delete individual (quando deletado diretamente)

#### 2. Views de Dados Ativos

O sistema mantém views automáticas que filtram apenas registros não deletados:

- `citizen_active` - Apenas cidadãos ativos
- `vehicle_active` - Apenas veículos ativos
- `sensor_active` - Apenas sensores ativos
- `app_user_active` - Apenas usuários ativos

#### 3. Reuso de Username

A validação de username considera apenas usuários ativos:

```python
def is_username_available(self, username):
    """Verifica se username está disponível (apenas em usuários ativos)"""
    cur.execute("SELECT id FROM app_user_active WHERE username = %s", (username,))
    return cur.fetchone() is None
```

### Triggers Específicos

#### Cidadãos
```sql
CREATE TRIGGER trg_soft_delete_citizen
BEFORE DELETE ON citizen
FOR EACH ROW
EXECUTE FUNCTION soft_delete_citizen_with_user();
```

#### Veículos
```sql
CREATE TRIGGER trg_soft_delete_vehicle
BEFORE DELETE ON vehicle
FOR EACH ROW
EXECUTE FUNCTION soft_delete_vehicle_with_user();
```

#### Sensores
```sql
CREATE TRIGGER trg_soft_delete_sensor
BEFORE DELETE ON sensor
FOR EACH ROW
EXECUTE FUNCTION soft_delete_sensor_with_user();
```

### Funções de Soft Delete

#### soft_delete_citizen_with_user()
```sql
-- Soft delete do app_user associado
UPDATE app_user 
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, allowed = FALSE 
WHERE id = OLD.app_user_id;

-- Soft delete do citizen
UPDATE citizen 
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, allowed = FALSE 
WHERE id = OLD.id;
```

#### soft_delete_vehicle_with_user()
```sql
-- Soft delete do app_user associado
UPDATE app_user 
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, allowed = FALSE 
WHERE id = OLD.app_user_id;

-- Soft delete do vehicle
UPDATE vehicle 
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, allowed = FALSE 
WHERE id = OLD.id;
```

#### soft_delete_sensor_with_user()
```sql
-- Soft delete do app_user associado
UPDATE app_user 
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, allowed = FALSE 
WHERE id = OLD.app_user_id;

-- Soft delete do sensor
UPDATE sensor 
SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, active = FALSE 
WHERE id = OLD.id;
```

### Fluxo de Reuso de Username

1. **Criar Entidade**: Cidadão/Veículo/Sensor com username "teste123"
2. **Deletar Entidade**: Soft delete em cascata (entidade + app_user)
3. **Verificar Disponibilidade**: `app_user_active` não contém "teste123"
4. **Recriar Entidade**: Novo cidadão/veículo/sensor pode usar "teste123"

### Validação na GUI

A validação é implementada nas funções de criação:

```python
# Em save_citizen, save_vehicle, save_sensor
if not self.is_username_available(username):
    messagebox.showerror("Erro", f"Username '{username}' já está em uso! Escolha outro.")
    return
```

### Benefícios

- ✅ **Integridade de Dados**: Histórico completo mantido
- ✅ **Performance**: Views otimizadas para dados ativos
- ✅ **Flexibilidade**: Reuso de usernames entre entidades
- ✅ **Auditoria**: Rastro completo de operações
- ✅ **Recuperação**: Possibilidade de restaurar dados deletados

## Triggers e Funções

### 1. Triggers de Auditoria

**Função:** `audit_log_generic()`
**Evento:** AFTER INSERT OR UPDATE OR DELETE em múltiplas tabelas
**Descrição:** Função genérica de auditoria que registra todas as alterações.

**Lógica:**

- Captura usuário da sessão via `current_setting('app.current_user_id')`
- Registra tipo de operação (INSERT/UPDATE/DELETE)
- Armazena valores antigos e novos em JSONB
- Identifica usuário que realizou a operação
- Retorna `COALESCE(NEW, OLD)` para compatibilidade com soft delete

**Tabelas com auditoria:**

- `app_user` → `audit_app_user`
- `citizen` → `audit_citizen`
- `vehicle` → `audit_vehicle`
- `sensor` → `audit_sensor`
- `fine` → `audit_fine`
- `fine_payment` → `audit_fine_payment`
- `app_user_notification` → `audit_app_user_notification`

### 2. Triggers de Soft Delete

#### `soft_delete_generic()`

**Função:** `soft_delete_generic()`
**Evento:** BEFORE DELETE em múltiplas tabelas
**Descrição:** Função genérica de soft delete que funciona para qualquer tabela.

**Lógica:**

- Define configuração temporária `app.soft_delete = true`
- Executa UPDATE dinâmico usando `format()` com nome da tabela
- Define `deleted_at = CURRENT_TIMESTAMP`
- Define `allowed = FALSE` (bloqueia automaticamente)
- Atualiza `updated_at`
- Limpa configuração temporária
- Retorna `NULL` para impedir DELETE físico

#### `block_update_deleted_generic()`

**Função:** `block_update_deleted_generic()`
**Evento:** BEFORE UPDATE em múltiplas tabelas
**Descrição:** Função genérica que impede atualização de registros deletados.

**Lógica:**

- Verifica se está em processo de soft delete (`app.soft_delete = true`)
- Se estiver, permite atualização (para o próprio soft delete)
- Se `deleted_at` não for NULL e não for soft delete:
  - Levanta exceção genérica com nome da tabela e ID
- Protege integridade de dados deletados

**Tabelas com soft delete genérico:**

- `citizen` → `trg_soft_delete_citizen` + `trg_block_update_deleted_citizen`
- `vehicle` → `trg_soft_delete_vehicle` + `trg_block_update_deleted_vehicle`
- `sensor` → `trg_soft_delete_sensor` + `trg_block_update_deleted_sensor`

### 3. Triggers de Proteção de Dados

#### `block_update_deleted_generic()`

**Função:** `block_update_deleted_generic()`
**Evento:** BEFORE UPDATE em múltiplas tabelas
**Descrição:** Função genérica que impede atualização de registros deletados.

**Lógica:**

- Verifica se está em processo de soft delete (`app.soft_delete = true`)
- Se estiver, permite atualização (para o próprio soft delete)
- Se `deleted_at` não for NULL e não for soft delete:
  - Levanta exceção genérica com nome da tabela e ID
- Protege integridade de dados deletados

**Tabelas com proteção genérica:**

- `citizen` → `trg_block_update_deleted_citizen`
- `vehicle` → `trg_block_update_deleted_vehicle`
- `sensor` → `trg_block_update_deleted_sensor`

### 4. Triggers de Processamento de Multas

#### `apply_fine_to_wallet()`

**Função:** `apply_fine_to_wallet()`
**Evento:** AFTER INSERT ON `fine`
**Descrição:** Aplica automaticamente multas à carteira do cidadão.

**Lógica:**

- Ignora multas canceladas ou com valor zero
- Busca saldo do cidadão por `citizen_id` com `FOR UPDATE`
- Se saldo >= valor da multa:
  - Deduz valor do `wallet_balance`
  - Mantém `debt` inalterado
- Se saldo < valor da multa:
  - Zera `wallet_balance`
  - Adiciona diferença à `debt`
  - Define `allowed = FALSE`
- Atualiza `updated_at` do cidadão

#### `apply_fine_payment()`

**Função:** `apply_fine_payment()`
**Evento:** AFTER INSERT ON `fine_payment`
**Descrição:** Processa pagamentos de multas e atualiza status.

**Lógica:**

- Busca `citizen_id` da multa
- Reduz `debt` pelo valor pago (nunca negativo)
- Reativa `allowed = TRUE` quando dívida zerada
- Se método = "Carteira Digital":
  - Também deduz do `wallet_balance`
- Marca multa como "paid" quando totalmente quitada
- Usa `COALESCE(SUM(amount_paid), 0)` para total pago

#### `cancel_fines_when_citizen_deleted()`

**Função:** `cancel_fines_when_citizen_deleted()`
**Evento:** BEFORE DELETE ON `citizen`
**Descrição:** Cancela multas pendentes quando cidadão é excluído.

**Lógica:**

- Atualiza multas diretamente por `citizen_id`
- Define status como "cancelled"
- Atualiza `updated_at`
- Retorna `OLD` para permitir continuação do soft delete

#### `prevent_delete_citizen_with_pending_fines()`

**Função:** `prevent_delete_citizen_with_pending_fines()`
**Evento:** BEFORE DELETE ON `citizen`
**Descrição:** Impede exclusão de cidadão com multas pendentes.

**Lógica:**

- Conta multas pendentes diretamente por `citizen_id`
- Se houver multas pendentes:
  - Levanta exceção com mensagem clara
- Se não houver:
  - Permite exclusão normalmente

### 5. Triggers Implementados

**Total de Triggers:** 10

#### Auditoria (7 triggers)

- `audit_app_user` - Auditoria de usuários
- `audit_citizen` - Auditoria de cidadãos
- `audit_vehicle` - Auditoria de veículos
- `audit_sensor` - Auditoria de sensores
- `audit_fine` - Auditoria de multas
- `audit_fine_payment` - Auditoria de pagamentos
- `audit_app_user_notification` - Auditoria de notificações

#### Soft Delete (3 triggers)

- `trg_soft_delete_citizen` - Soft delete genérico de cidadãos
- `trg_soft_delete_vehicle` - Soft delete genérico de veículos
- `trg_soft_delete_sensor` - Soft delete genérico de sensores

#### Proteção de Dados (3 triggers)

- `trg_block_update_deleted_citizen` - Bloqueio genérico de cidadãos deletados
- `trg_block_update_deleted_vehicle` - Bloqueio genérico de veículos deletados
- `trg_block_update_deleted_sensor` - Bloqueio genérico de sensores deletados

#### Processamento de Multas (2 triggers)

- `trg_apply_fine` - Aplicação automática de multas
- `trg_apply_fine_payment` - Processamento de pagamentos

### 6. Fluxo de Soft Delete

O sistema implementa um fluxo completo de soft delete genérico:

1. **DELETE Inicial** → Trigger `soft_delete_generic()` marca `deleted_at` e `allowed = FALSE`
2. **Proteção** → Trigger `block_update_deleted_generic()` impede alterações posteriores
3. **Auditoria** → Trigger `audit_*()` registra a operação
4. **Configuração Temporária** → Usa `app.soft_delete` para controle do fluxo

### 7. Views de Dados Ativos

O sistema implementa views para facilitar consultas a registros ativos:

#### `citizen_active`

**Descrição:** View com todos os cidadãos não deletados
**SQL:** `SELECT * FROM citizen WHERE deleted_at IS NULL`

#### `vehicle_active`

**Descrição:** View com todos os veículos não deletados
**SQL:** `SELECT * FROM vehicle WHERE deleted_at IS NULL`

#### `sensor_active`

**Descrição:** View com todos os sensores não deletados
**SQL:** `SELECT * FROM sensor WHERE deleted_at IS NULL`

#### `app_user_active`

**Descrição:** View com todos os usuários não deletados
**SQL:** `SELECT * FROM app_user WHERE deleted_at IS NULL`

**Benefícios das Views:**

- Simplifica consultas frequentes
- Centraliza lógica de filtros
- Melhora performance com cache
- Facilita manutenção de queries

### 8. Otimizações de Performance

- **Índices Condicionais**: Funcionam apenas com registros ativos
- **Queries Otimizadas**: Acesso direto por `citizen_id`
- **Locks Eficientes**: `FOR UPDATE` apenas onde necessário
- **JSONB Compacto**: Auditoria com estrutura otimizada

## Índices de Performance

### Índices de Trânsito e Incidentes

- `idx_traffic_incident_vehicle` - Busca por veículo em incidentes
- `idx_traffic_incident_sensor` - Busca por sensor em incidentes  
- `idx_traffic_incident_occurred_at` - Consultas por período

### Índices de Multas

- `idx_fine_traffic_incident` - Relacionamento com incidentes
- `idx_fine_pending` - Multas pendentes (índice filtrado)
- `idx_fine_due_date` - Consultas por data de vencimento
- `idx_fine_citizen` - Busca direta por cidadão (OTIMIZAÇÃO)
- `idx_fine_payment_fine` - Pagamentos por multa
- `idx_fine_payment_paid_at` - Consultas por data de pagamento

### Índices de Veículos e Sensores

- `idx_vehicle_app_user` - Veículos por usuário
- `idx_vehicle_allowed_true` - Veículos ativos (índice filtrado)
- `idx_sensor_app_user_active` - Sensores ativos por usuário (índice filtrado)

### Índices de Notificações

- `idx_app_user_notification_app_user` - Notificações por usuário
- `idx_app_user_notification_unread` - Notificações não lidas (índice filtrado)

### Índices de Auditoria

- `idx_audit_log_app_user` - Auditoria por usuário
- `idx_audit_log_changed_at` - Consultas por período
- `idx_audit_log_table_operation` - Busca por tabela e operação
- `idx_audit_log_row_id` - Busca por registro específico
- `idx_audit_log_table_row` - Busca combinada (tabela + registro)

### Índices Únicos Condicionais (Soft Delete)

- `uniq_app_user_username_active` - Username único apenas para usuários ativos
- `ux_citizen_cpf_active` - CPF único apenas para cidadãos ativos
- `ux_citizen_email_active` - Email único apenas para cidadãos ativos
- `ux_vehicle_license_plate_active` - Placa única apenas para veículos ativos

**Total de Índices:** 21

**Características:**

- **Índices Únicos Condicionais**: Permitem reutilização de CPFs/emails/placas após soft delete
- **Índices Filtrados**: Otimizam consultas comuns (ativos, pendentes, não lidas)
- **Otimização Direta**: `idx_fine_citizen` elimina JOINs desnecessários

## Configuração e Instalação

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
   - `sql/create_tables.sql` - Criação das tabelas com soft delete
   - `sql/trigger_functions.sql` - Funções de trigger (15 funções)
   - `sql/triggers.sql` - Triggers implementados (15 triggers)
   - `sql/index.sql` - Índices de performance (21 índices)

**Características do Sistema:**

- **Soft Delete Implementado**: Todas as tabelas principais têm `deleted_at`
- **Índices Únicos Condicionais**: Permitem reutilização de dados após exclusão
- **15 Triggers Ativos**: Auditoria completa, soft delete, proteção de dados e processamento de multas
- **Otimização de Queries**: `citizen_id` direto em `fine` elimina JOINs

**Triggers Implementados:**

- **Auditoria (8)**: Registro completo de todas as operações DML
- **Soft Delete (4)**: Exclusão lógica automática para usuários, cidadãos, veículos, sensores
- **Proteção de Dados (2)**: Bloqueio de atualização em registros deletados
- **Processamento de Multas (4)**: Aplicação automática, pagamentos, cancelamentos e validações

## Funcionalidades Principais

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

## Interface Gráfica (GUI)

### Tecnologias

- **Framework**: Tkinter com ttk (tema clam)
- **Estilos**: Sistema de cores e fontes customizadas
- **Componentes**: Treeviews, Forms, Dialogs modais

### Funcionalidades da GUI

#### Dashboard

- Cards com estatísticas em tempo real
- Gráficos de visualização
- Indicadores de performance

#### Gestão de Entidades

- **Cidadãos**: CRUD completo com filtros
- **Veículos**: CRUD com validação de placa
- **Sensores**: Gestão com status ativo/inativo
- **Incidentes**: Registro com seleção de veículo/sensor
- **Multas**: Geração e pagamento com integração automática

#### Console SQL Seguro

- Editor com syntax highlighting
- Execução segura (SELECT apenas)
- Rollback automático em erros
- Suporte a comentários SQL
- Validação de comandos perigosos

#### Sistema de Notificações

- Lista de notificações por usuário
- Controle de leitura
- Criação de novas notificações

## Fluxo de Trabalho

### Fluxo de Incidente de Trânsito

1. Sensor detecta infração
2. Sistema cria `traffic_incident`
3. Sistema cria `fine` manualmente ou automaticamente
4. **Trigger `apply_fine_to_wallet()` é acionado automaticamente:**
   - Se saldo suficiente → Deduz da carteira
   - Se saldo insuficiente → Zera saldo + acumula dívida + bloqueia acesso
5. Pagamento realizado → `fine_payment` → **Trigger `apply_fine_payment()` é acionado:**
   - Reduz dívida automaticamente
   - Se "Carteira Digital" → Reduz saldo também
   - Reativa acesso automaticamente
   - Marca multa como "paid"

### Fluxo de Exclusão de Cidadão

1. Tentativa de exclusão de cidadão
2. **Trigger `prevent_delete_citizen_with_pending_fines()` verifica:**
   - Se há multas pendentes → Impede exclusão com erro claro
   - Se não há multas → Permite exclusão
3. Se exclusão permitida → **Trigger `cancel_fines_when_citizen_deleted()` cancela multas pendentes

### Fluxo de Auditoria (Automático)

1. Qualquer operação DML em tabelas auditadas
2. Trigger correspondente é acionado automaticamente
3. Função `audit_log_generic()` registra em `audit_log`
4. Dados anteriores e posteriores são armazenados em JSONB
5. Usuário da sessão é capturado via configuração

## Testes e Exemplos

O notebook `smart_city_os.ipynb` contém funções para:

- Conexão com o banco de dados
- Criação de tabelas
- Inserção de dados de teste
- Consultas e visualizações
- Exportação de dados para CSV

## Performance e Otimização

### Índices Estratégicos Implementados

- Índices parciais para consultas frequentes (veículos ativos, multas pendentes, notificações não lidas)
- Índices compostos para buscas complexas (tabela + operação em auditoria)
- Otimização para queries de tempo real (incidentes por período, pagamentos por data)

### Triggers Implementados

- **Auditoria completa**: 8 triggers implementados para registro automático
- **Processamento de multas**: Funções disponíveis mas triggers não implementados
- **Consistência garantida**: Auditoria captura todas as alterações automaticamente

### Observações de Performance

- **Soft Delete Otimizado**: Índices condicionais permitem reutilização eficiente de dados
- **15 Triggers Ativos**: Processamento automático com mínimo overhead
- **21 Índices Estratégicos**: Otimização para queries críticas do sistema
- **Auditoria Completa**: Rastreabilidade sem penalizar performance significativamente

## Segurança

### Controle de Acesso

- Bloqueio automático por dívida com reativação automática
- Validação de CPF/email únicos apenas para registros ativos
- Hash de senhas seguro com gerenciamento de sessão
- Soft delete protege dados sensíveis mantendo integridade

### Auditoria e Proteção

- Registro completo de todas as operações DML
- Rastreabilidade de alterações com usuário e timestamp
- Proteção contra atualização de registros deletados
- Logs de acesso para conformidade e forense

## Arquitetura do Sistema

Nesta seção, descrevemos a arquitetura do sistema, incluindo as extensões e funcionalidades implementadas.

### Soft Delete Implementado

**Tabelas com Soft Delete:**

- `citizen`: `deleted_at` + índices únicos condicionais (CPF, email)
- `vehicle`: `deleted_at` + índice único condicional (placa)
- `sensor`: `deleted_at` + desativação automática

**Triggers de Soft Delete Genérico:**

- `soft_delete_generic()`: Função única para todas as tabelas
- `block_update_deleted_generic()`: Função única de proteção
- Configuração temporária `app.soft_delete` para controle do fluxo
- Execução dinâmica com `format()` para qualquer tabela

**Views de Dados Ativos:**

- `citizen_active`: Cidadãos não deletados
- `vehicle_active`: Veículos não deletados
- `sensor_active`: Sensores não deletados
- `app_user_active`: Usuários não deletados

### Otimização de Performance

**Índices Únicos Condicionais:**

- Permitem reutilização de CPFs, emails e placas após soft delete
- Mantêm integridade sem bloquear reutilização natural de dados
- Performance superior a triggers complexos de validação

**Otimização de Queries:**

- `citizen_id` direto em `fine` elimina JOINs desnecessários
- Índices filtrados para consultas comuns (ativos, pendentes)
- 21 índices estratégicos para performance otimizada

### Triggers Completos (10 ativos)

**Auditoria (7):** Registro completo em todas as tabelas principais
**Soft Delete (3):** Exclusão lógica genérica e automática
**Proteção (3):** Bloqueio genérico de atualização em registros deletados  
**Multas (2):** Processamento automático completo

## Extensões Futuras

### Possíveis Melhorias

- Integração com APIs de pagamento externas
- Sistema de notificações por email/SMS
- Dashboard em tempo real
- Machine learning para previsão de incidentes
- Integração com sistemas de trânsito municipais

## Soft Delete e Reuso de Username

### Visão Geral

O SmartCityOS implementa um sistema sofisticado de **Soft Delete** que permite a reutilização de usernames enquanto mantém a integridade e histórico dos dados. Esta abordagem garante que os usuários possam criar novas contas com usernames de contas anteriormente excluídas, sem perder dados históricos importantes.

### Funcionalidades Implementadas

#### Soft Delete em Cascata

- **Cidadãos**: Ao deletar um cidadão, automaticamente soft-deleta o app_user associado
- **Veículos**: Ao deletar um veículo, automaticamente soft-deleta o app_user associado  
- **Sensores**: Ao deletar um sensor, automaticamente soft-deleta o app_user associado
- **Cross-Entity**: Username pode ser reutilizado entre diferentes tipos de entidades

#### Views de Dados Ativos

- **`citizen_active`**: Filtra cidadãos não deletados (`deleted_at IS NULL`)
- **`vehicle_active`**: Filtra veículos não deletados (`deleted_at IS NULL`)
- **`sensor_active`**: Filtra sensores não deletados (`deleted_at IS NULL`)
- **`app_user_active`**: Filtra usuários não deletados (`deleted_at IS NULL`)

#### **Validação de Username**

- **Verificação em tempo real**: Sistema verifica disponibilidade na criação de entidades
- **Cross-entity validation**: Username disponível se não existir em `app_user_active`
- **Mensagens educativas**: GUI informa quando username está disponível para reuso

### Implementação Técnica

#### Triggers de Soft Delete

```sql
-- Trigger para cidadãos
CREATE TRIGGER trg_soft_delete_citizen
BEFORE DELETE ON citizen
FOR EACH ROW
EXECUTE FUNCTION soft_delete_citizen_with_user();

-- Trigger para veículos  
CREATE TRIGGER trg_soft_delete_vehicle
BEFORE DELETE ON vehicle
FOR EACH ROW
EXECUTE FUNCTION soft_delete_vehicle_with_user();

-- Trigger para sensores
CREATE TRIGGER trg_soft_delete_sensor
BEFORE DELETE ON sensor
FOR EACH ROW
EXECUTE FUNCTION soft_delete_sensor_with_user();
```

#### **Funções de Soft Delete**

```sql
-- Exemplo: soft_delete_citizen_with_user()
CREATE OR REPLACE FUNCTION soft_delete_citizen_with_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Soft delete do app_user associado
    UPDATE app_user 
    SET deleted_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP,
        allowed = FALSE
    WHERE id = OLD.app_user_id;
    
    -- Soft delete do citizen
    UPDATE citizen 
    SET deleted_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP,
        allowed = FALSE
    WHERE id = OLD.id;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

#### Views de Filtragem

```sql
-- Exemplo: citizen_active
CREATE VIEW citizen_active AS
SELECT *
FROM citizen
WHERE deleted_at IS NULL;
```

### Restrições de Segurança

#### **Validação na Consulta SQL**

- **Bloqueio de tabelas base**: GUI impede consultas diretas a `citizen`, `vehicle`, `sensor`, `app_user`
- **Mensagens educativas**: Sistema informa qual view usar em vez da tabela base
- **Padrões inteligentes**: Detecta `FROM`, `JOIN`, `AS` e aliases
- **Exemplos práticos**: Fornece consultas corretas como referência

#### Exemplo de Bloqueio

```
Bloqueio de tabela 'citizen' não pode ser consultada diretamente!

Use a view 'citizen_active' em vez da tabela base.

Esta restrição garante que dados soft-deletados não sejam exibidos.

Exemplo correto: SELECT * FROM citizen_active;
```

### Benefícios do Sistema

#### **Para Usuários**

- **Reuso imediato**: Username disponível logo após exclusão
- **Experiência fluida**: Sem confusão com usernames "em uso"
- **Dados corretos**: Lista sempre mostra apenas registros ativos

#### **Para Administradores**

- **Integridade preservada**: Histórico completo mantido
- **Auditoria completa**: Todos os dados rastreados
- **Backup seguro**: Dados soft-deletados incluídos
- **Recuperação fácil**: Erros podem ser desfeitos

#### Para o Sistema

- **Performance otimizada**: Views filtram dados eficientemente
- **Consistência garantida**: Regras aplicadas automaticamente
- **Escalabilidade**: Sistema cresce mantendo regras
- **Compliance**: Retenção de dados conforme melhores práticas

### Exemplos de Uso

#### Criar e Deletar Entidade

```python
# Criar cidadão (username disponível para reuso)
citizen_id = create_citizen("joao", "senha123", "João Silva", "12345678901")

# Deletar cidadão (soft delete automático)
delete_citizen(citizen_id)  # Ativa trigger, soft-deleta citizen e app_user

# Criar novo cidadão com mesmo username
new_citizen_id = create_citizen("joao", "novasenha", "João Santos", "98765432100")
# Funciona! Username estava disponível
```

#### Consultas Apenas com Views

```sql
-- CORRETO: Usa view ativa
SELECT COUNT(*) FROM citizen_active;
SELECT * FROM vehicle_active WHERE allowed = TRUE;
SELECT v.license_plate, c.first_name 
FROM vehicle_active v 
JOIN citizen_active c ON v.citizen_id = c.id;

-- INCORRETO: Bloqueado pela GUI
SELECT COUNT(*) FROM citizen;
SELECT * FROM vehicle;
```

### **Melhores Práticas**

#### **Para Desenvolvedores**

- **Sempre usar views** em consultas SQL
- **Validar usernames** contra `app_user_active`
- **Considerar soft delete** em migrações
- **Preservar dados históricos** em backups

#### **Para Administradores**

- **Treinar usuários** sobre soft delete
- **Monitorar views** para dados consistentes
- **Verificar triggers** para funcionamento correto
- **Documentar processos** de recuperação

#### **Para Usuários Finais**

- **Entender que exclusão é lógica** (soft delete)
- **Username reutilizável** após exclusão
- **Dados históricos preservados** para segurança
- **Contatar suporte** para recuperação de dados

## Licença

Este projeto está licenciado sob os termos da licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.

## Suporte

Para dúvidas e suporte:

- **Verificar logs de auditoria** para rastrear problemas
- **Consultar documentação atualizada** do PostgreSQL e triggers
- **Analisar estrutura de tabelas e índices** para otimização
- **Revisar funções de trigger** para entendimento do fluxo automático
- **GUI completa** com dashboard interativo e relatórios profissionais

## Características do Sistema

### Implementações Principais

- **Soft Delete Completo**: 3 tabelas principais com exclusão lógica genérica  
- **10 Triggers Ativos**: Auditoria, proteção e processamento automático  
- **21 Índices Otimizados**: Performance e reutilização de dados  
- **Proteção de Dados**: Bloqueio genérico de atualização em registros deletados  
- **Views de Dados Ativos**: 4 views para consultas simplificadas  
- **Relatórios Profissionais**: Excel com múltiplas abas e gráficos  
- **Dashboard Interativo**: Plotly com visualizações avançadas  

### Benefícios do Sistema

- **Performance**: Queries otimizadas com índices estratégicos  
- **Segurança**: Dados protegidos com soft delete e auditoria  
- **Visualização**: Relatórios executivos e dashboards completos  
- **Automação**: Processamento de multas 100% automático  
- **Confiabilidade**: Sistema robusto com rastreabilidade completa  

**SmartCityOS agora é uma solução completa de gestão urbana inteligente!**

Este projeto foi desenvolvido por **Felipe Cidade Soares**.

**LinkedIn:** [https://www.linkedin.com/in/cidadefelipe/](https://www.linkedin.com/in/cidadefelipe/)
