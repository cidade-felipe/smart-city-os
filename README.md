# SmartCityOS

Um sistema operacional inteligente para cidades que gerencia usuários, veículos, sensores, incidentes de trânsito e multas de forma automatizada.

## 📋 Visão Geral

O SmartCityOS é um sistema de gestão urbana inteligente desenvolvido em Python com PostgreSQL, projetado para automatizar o controle de trânsito, gerenciamento de multas e monitoramento de sensores em ambientes urbanos. O sistema utiliza triggers de banco de dados para aplicar automaticamente penalidades e gerenciar carteiras digitais de cidadãos.

## 🏗️ Arquitetura

- **Backend**: Python 3.12+ com PostgreSQL 18.0
- **Bibliotecas**: psycopg, pandas, python-dotenv, tabulate
- **Estrutura**: Notebook Jupyter para desenvolvimento e scripts SQL para banco de dados

## 🗄️ Modelo de Dados

### Tabelas Principais (13)

- **app_user**: Usuários do sistema com autenticação
- **citizen**: Extensão com carteira digital e controle biométrico
- **vehicle**: Cadastro de veículos com permissões
- **sensor**: Sensores urbanos para monitoramento
- **reading**: Leituras capturadas pelos sensores
- **traffic_incident**: Incidentes de trânsito detectados
- **fine**: Multas aplicadas aos incidentes
- **fine_payment**: Pagamentos de multas realizados
- **notification**: Sistema de notificações
- **payment_method**: Métodos de pagamento disponíveis
- **app_user_notification**: Relacionamento usuários-notificações
- **vehicle_citizen**: Relacionamento veículos-cidadãos
- **audit_log**: Registro completo de auditoria

## ⚡ Automação

### Triggers Principais (15 ativos)

1. **Auditoria (8)**: Registro completo de todas as operações DML
2. **Soft Delete (4)**: Exclusão lógica automática para usuários, cidadãos, veículos, sensores
3. **Proteção de Dados (2)**: Bloqueio de atualização em registros deletados
4. **Processamento de Multas (4)**: Aplicação automática, pagamentos, cancelamentos e validações

### Fluxo Automatizado

- Sensor detecta infração → Incidente criado → Multa aplicada → Saldo deduzido/Dívida acumulada → Acesso bloqueado se necessário
- Pagamento realizado → Dívida reduzida → Acesso reativado automaticamente
- Soft delete automático com proteção de dados
- Auditoria completa de todas as operações

## 🚀 Performance

- **21 índices estratégicos** para otimização de consultas
- Índices únicos condicionais para soft delete
- Índices filtrados para queries frequentes (ativos, pendentes, não lidas)
- Otimização direta: `citizen_id` em `fine` elimina JOINs
- 15 triggers ativos com processamento automático

## 🔧 Instalação

### Pré-requisitos

- Python 3.12+
- PostgreSQL 18.0
- Ambiente virtual

### Setup

```bash
# Clonar e configurar
git clone <repositório>
cd smart-city-os
python -m venv venv
source venv/bin/activate  # Linux/Mac ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados
# Executar scripts SQL em ordem: create_tables.sql → trigger_functions.sql → triggers.sql → index.sql
```

## 📊 Funcionalidades

- ✅ Gestão completa de usuários e cidadãos com soft delete
- ✅ Cadastro e controle de veículos com reutilização de placas
- ✅ Monitoramento por sensores urbanos com desativação automática
- ✅ Sistema de multas 100% automatizado
- ✅ Pagamentos e reativação automática de acesso
- ✅ Sistema de notificações com controle de leitura
- ✅ Auditoria completa e rastreabilidade de operações
- ✅ Interface gráfica profissional com dashboard
- ✅ Relatórios Excel com múltiplas abas e gráficos
- ✅ Proteção de dados com bloqueio de atualização em registros deletados

## 🔒 Segurança

- Bloqueio automático por dívida com reativação automática
- Validação de CPF/email únicos apenas para registros ativos
- Hash de senhas seguro com gerenciamento de sessão
- Soft delete protege dados sensíveis mantendo integridade
- Auditoria completa de operações com usuário e timestamp
- Proteção contra atualização de registros deletados
- Logs de acesso para conformidade e forense

## 📝 Documentação Completa

Para detalhes técnicos completos, consulte o arquivo `DOCUMENTATION.md` que contém:

- Descrição detalhada de todas as tabelas e colunas
- Explicação completa de triggers e funções
- Lista completa de índices de performance
- Fluxos de trabalho detalhados
- Exemplos e guias de configuração

## Contribuição

Contribuições são bem-vindas! Por favor:

1. Fork do projeto
2. Criar branch para feature
3. Submeter pull request
4. Manter padrão de código e documentação

## 👨‍💻 Autor

Desenvolvido por **Felipe Cidade Soares**

**LinkedIn:** [https://www.linkedin.com/in/cidadefelipe/](https://www.linkedin.com/in/cidadefelipe/)

## 📄 Licença

MIT License - Consulte arquivo LICENSE para detalhes.