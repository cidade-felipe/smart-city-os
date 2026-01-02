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

### Triggers Principais

1. **apply_fine_to_wallet()**: Aplica multas automaticamente à carteira do cidadão
2. **apply_fine_payment()**: Processa pagamentos e reativa acesso
3. **audit_log_function()**: Registra todas as alterações para auditoria

### Fluxo Automatizado

- Sensor detecta infração → Incidente criado → Multa aplicada → Saldo deduzido/Dívida acumulada → Acesso bloqueado se necessário
- Pagamento realizado → Dívida reduzida → Acesso reativado automaticamente

## 🚀 Performance

- **17 índices estratégicos** para otimização de consultas
- Índices parciais para queries frequentes
- Processamento automático no banco de dados
- Consistência garantida via triggers

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

- ✅ Gestão completa de usuários e cidadãos
- ✅ Cadastro e controle de veículos
- ✅ Monitoramento por sensores urbanos
- ✅ Sistema de multas automatizado
- ✅ Pagamentos e reativação automática
- ✅ Sistema de notificações
- ✅ Auditoria completa e rastreabilidade

## 🔒 Segurança

- Bloqueio automático por dívida
- Validação de CPF único
- Hash de senhas seguro
- Auditoria completa de operações

## 📝 Documentação Completa

Para detalhes técnicos completos, consulte o arquivo `DOCUMENTATION.md` que contém:

- Descrição detalhada de todas as tabelas e colunas
- Explicação completa de triggers e funções
- Lista completa de índices de performance
- Fluxos de trabalho detalhados
- Exemplos e guias de configuração

## 👨‍💻 Autor

Desenvolvido por **Felipe Cidade Soares**

**LinkedIn:** [https://www.linkedin.com/in/cidadefelipe/](https://www.linkedin.com/in/cidadefelipe/)

## 📄 Licença

MIT License - Consulte arquivo LICENSE para detalhes