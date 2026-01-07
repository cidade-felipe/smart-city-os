import tkinter as tk
from tkinter import ttk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.conect_db import connect_to_db, connection_string
import psycopg as psy
import psycopg2
import psycopg2.extras
from psycopg.rows import dict_row
from datetime import datetime
import pandas as pd
from tabulate import tabulate
from dotenv import load_dotenv
from gui.styles import SmartCityStyles
import io
from PIL import Image, ImageTk

# Carregar variáveis de ambiente
load_dotenv()

def format_currency_brl(value):
    """Formata valor monetário para o padrão brasileiro (R$ 1.234,56)"""
    if value is None or value == 0:
        return "R$ 0,00"
    
    # Arredondar para 2 casas decimais
    value = round(float(value), 2)
    
    # Separar parte inteira e decimal
    integer_part = int(value)
    decimal_part = int(round((value - integer_part) * 100))
    
    # Formatar parte inteira com separador de milhar
    if integer_part >= 1000:
        integer_formatted = f"{integer_part:,}".replace(',', '.')
    else:
        integer_formatted = str(integer_part)
    
    return f"R$ {integer_formatted},{decimal_part:02d}"

class SmartCityOSGUI:
    """Interface principal do SmartCityOS com design moderno e responsivo"""

    def converter_valor_monetario(self, valor):
        """Converte valor monetário brasileiro para float de forma robusta"""
        if not valor:
            return 0.0
        
        try:
            # Remover símbolos e limpar
            valor_limpo = str(valor).replace('R$', '').strip()
            
            # Substituir vírgula por ponto para decimais brasileiros
            if ',' in valor_limpo and '.' in valor_limpo:
                # Formato "1.234,56" → "1234.56"
                partes = valor_limpo.split('.')
                if len(partes) == 2:
                    decimal = partes[1].replace(',', '')
                    valor_limpo = f"{partes[0]}.{decimal}"
                else:
                    valor_limpo = valor_limpo.replace(',', '')
            else:
                # Formato "100,00" → "100.00" ou "1.234,56" → "1234.56"
                valor_limpo = valor_limpo.replace(',', '.')
            
            return float(valor_limpo)
        except (ValueError, AttributeError, TypeError):
            return 0.0

    def format_currency_brl(self, amount):
        """Formata valor como moeda brasileira"""
        if amount is None or amount == 0:
            return "R$ 0,00"
        return f"R$ {amount:,.2f}".replace('.', ',')
    
    def __init__(self, root):
        """Inicializar interface principal"""
        self.root = root
        self.root.title("SmartCityOS - Sistema Operacional Inteligente para Cidades")
        self.root.geometry("1400x900")
        self.root.configure(bg='#F0F0F0')
        self.root.state('zoomed')
        
        # Configurar tema para clam
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Inicializar estilos
        self.styles = SmartCityStyles()
        self.styles.configure_styles(self.root)
        
        # Variáveis de conexão
        self.conn = None
        self.connected = False
        
        # Criar interface
        self.create_widgets()
        
        self.conection_string = connection_string()
        
        # Verificar conexão após criar todos os widgets
        self.check_connection()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Menu lateral
        self.create_sidebar(main_frame)
        
        # Área de conteúdo
        self.create_content_area(main_frame)
        
        # Barra de status
        self.create_status_bar(main_frame)
        
    def create_header(self, parent):
        # Header com gradiente
        header_frame = tk.Frame(parent, height=120, bg=self.styles.colors['primary'])
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.grid_propagate(False)
        
        # Container para conteúdo do header
        header_content = tk.Frame(header_frame, bg=self.styles.colors['primary'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        logo_img = Image.open(r'gui\img\logo.png')
        logo_img.thumbnail((100,100), Image.LANCZOS)
        self.logo = ImageTk.PhotoImage(logo_img)

        # Frame esquerdo - Logo e título
        left_frame = tk.Frame(header_content, bg=self.styles.colors['primary'])
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
                
        # Logo (simulado com texto estilizado)
        logo_label = tk.Label(left_frame, image=self.logo,bg=self.styles.colors['primary'])
        logo_label.pack(side=tk.TOP, anchor='w')
        
        # Frame direito - Status e conexão
        right_frame = tk.Frame(header_content, bg=self.styles.colors['primary'])
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame de status de conexão
        conn_status_frame = tk.Frame(right_frame, bg=self.styles.colors['primary'])
        conn_status_frame.pack(side=tk.TOP, pady=(10, 0))
        
        # Status de conexão
        self.connection_status = tk.Label(conn_status_frame, text="🔴 Desconectado",
                                         bg=self.styles.colors['primary'], fg=self.styles.colors['light'],
                                         font=self.styles.fonts['normal'])
        self.connection_status.pack(side=tk.RIGHT, padx=(0, 15))
        
        # Botão de conexão estilizado
        self.connect_btn = tk.Button(conn_status_frame, text="🔌 Conectar", 
                                    command=self.toggle_connection,
                                    bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                    font=self.styles.fonts['button'], relief='flat',
                                    padx=15, pady=8, cursor='hand2')
        self.connect_btn.pack(side=tk.RIGHT)
        
        # Frame de informações do sistema
        info_frame = tk.Frame(right_frame, bg=self.styles.colors['primary'])
        info_frame.pack(side=tk.TOP, pady=(15, 0))
        
        # Versão e status
        version_label = tk.Label(info_frame, text="v1.0.0", bg=self.styles.colors['primary'],
                                 fg=self.styles.colors['light'], font=self.styles.fonts['small'])
        version_label.pack(side=tk.RIGHT)
        
    def create_sidebar(self, parent):
        # Sidebar estilizado
        sidebar_frame = tk.Frame(parent, bg=self.styles.colors['card'], width=250)
        sidebar_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        sidebar_frame.grid_propagate(False)
        
        # Título do menu
        menu_title = tk.Label(sidebar_frame, text="📋 Menu Principal", 
                             bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                             font=self.styles.fonts['heading'])
        menu_title.pack(pady=(20, 15), padx=20, anchor='w')
        
        # Separador
        separator = tk.Frame(sidebar_frame, height=2, bg=self.styles.colors['border'])
        separator.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # Botões de navegação com estilos melhorados
        buttons_data = [
            ("📊 Dashboard", self.show_dashboard, "accent"),
            ("👥 Cidadãos", self.show_citizens, "normal"),
            ("🚗 Veículos", self.show_vehicles, "normal"),
            ("📹 Sensores", self.show_sensors, "normal"),
            ("⚠️ Incidentes", self.show_incidents, "normal"),
            ("💰 Multas", self.show_fines, "normal"),
            ("📈 Estatísticas", self.show_statistics, "normal"),
            ("🔍 Consultas SQL", self.show_sql_console, "secondary"),
            ("⚙️ Configurações", self.show_settings, "secondary"),
        ]
        
        for text, command, style_type in buttons_data:
            btn_frame = tk.Frame(sidebar_frame, bg=self.styles.colors['card'])
            btn_frame.pack(fill=tk.X, padx=20, pady=2)
            
            # Definir cores baseado no estilo
            if style_type == "primary":
                bg_color = self.styles.colors['secondary']
                fg_color = self.styles.colors['white']
            elif style_type == "secondary":
                bg_color = self.styles.colors['white']
                fg_color = self.styles.colors['text_primary']
            else:
                bg_color = self.styles.colors['white']
                fg_color = self.styles.colors['text_primary']
            
            btn = tk.Button(btn_frame, text=text, command=command,
                           bg=bg_color, fg=fg_color, font=self.styles.fonts['normal'],
                           relief='flat', cursor='hand2', 
                           activebackground=self.styles.colors['primary'],
                           activeforeground=self.styles.colors['white'])
            btn.pack(fill=tk.X, pady=1)
            
            # Efeito hover
            btn.bind('<Enter>', lambda e, b=btn, c=bg_color: b.config(bg=self.styles.colors['primary']))
            btn.bind('<Leave>', lambda e, b=btn, c=bg_color: b.config(bg=c))
        
        # Espaçador no final
        spacer = tk.Frame(sidebar_frame, bg=self.styles.colors['card'], height=50)
        spacer.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
            
    def create_content_area(self, parent):
        # Notebook para abas
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Aba principal
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Principal")
        
        # Área de conteúdo dinâmico
        self.content_frame = ttk.Frame(self.main_frame, padding="10")
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mostrar mensagem inicial
        self.show_welcome_message()
        
    def create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Pronto", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Data e hora
        self.datetime_label = ttk.Label(status_frame, text="", relief=tk.SUNKEN)
        self.datetime_label.pack(side=tk.RIGHT)
        self.update_datetime()
        
    def update_datetime(self):
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.config(text=now)
        self.root.after(1000, self.update_datetime)
        
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def is_username_available(self, username):
        """Verifica se username está disponível (apenas em usuários ativos)"""
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM app_user_active WHERE username = %s", (username,))
                    return cur.fetchone() is None
        except:
            return False
    
    def show_welcome_message(self):
        """Mostra mensagem de boas-vindas na tela inicial"""
        self.clear_content()
        
        # Frame de boas-vindas
        welcome_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        welcome_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Container centralizado
        center_frame = tk.Frame(welcome_frame, bg=self.styles.colors['card'], relief='solid', bd=1)
        center_frame.pack(expand=True, fill=tk.BOTH, pady=50)
        
        
        # Logo e título
        logo_label = tk.Label(center_frame, image=self.logo, bg=self.styles.colors['card'],
                              fg=self.styles.colors['primary'], font=('Segoe UI', 48))
        logo_label.pack(pady=(30, 10))
        
        title_label = tk.Label(center_frame, text="Bem-vindo ao SmartCityOS",
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                              font=self.styles.fonts['title'])
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(center_frame, text="Sistema Operacional Inteligente para Cidades",
                                bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                                font=self.styles.fonts['normal'])
        subtitle_label.pack(pady=(0, 30))
        
        # Instruções
        instructions_frame = tk.Frame(center_frame, bg=self.styles.colors['card'])
        instructions_frame.pack(pady=20, padx=40)
        
        instructions = [
            "🔌 Primeiro, conecte-se ao banco de dados usando o botão no header",
            "📊 Explore o Dashboard interativo com gráficos Plotly",
            "👥 Gerencie cidadãos, veículos, sensores e incidentes",
            "💰 Controle multas e finanças da cidade",
            "🔍 Use o Console SQL para consultas personalizadas"
        ]
        
        for instruction in instructions:
            instruction_label = tk.Label(instructions_frame, text=instruction,
                                       bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                       font=self.styles.fonts['normal'], justify='left')
            instruction_label.pack(anchor='w', pady=2)
        
        # Status de conexão
        status_text = "🟢 Conectado ao banco de dados" if self.connected else "🔴 Desconectado do banco de dados"
        status_label = tk.Label(center_frame, text=status_text,
                               bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                               font=self.styles.fonts['small'])
        status_label.pack(pady=(20, 30))
            
    def show_dashboard(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Estatísticas gerais
                    stats = {}
                    
                    # Usuários
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as this_month FROM app_user_active")
                    user_stats = cur.fetchone()
                    stats['users'] = user_stats
                    
                    # Cidadãos
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN debt > 0 THEN 1 END) as with_debt, COALESCE(SUM(debt), 0) as total_debt FROM citizen_active")
                    citizen_stats = cur.fetchone()
                    stats['citizens'] = citizen_stats
                    
                    # Veículos
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN allowed = TRUE THEN 1 END) as active FROM vehicle_active")
                    vehicle_stats = cur.fetchone()
                    stats['vehicles'] = vehicle_stats
                    
                    # Incidentes
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN occurred_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as this_week FROM traffic_incident")
                    incident_stats = cur.fetchone()
                    stats['incidents'] = incident_stats
                    
                    # Multas
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending, COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue, COALESCE(SUM(amount), 0) as total_amount FROM fine")
                    fine_stats = cur.fetchone()
                    stats['fines'] = fine_stats
                    
                    # Sensores
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN active = TRUE THEN 1 END) as active FROM sensor_active")
                    sensor_stats = cur.fetchone()
                    stats['sensors'] = sensor_stats
                    
                    # Exibir dashboard
                    self.display_dashboard_stats(stats)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dashboard: {str(e)}")
            
    def display_dashboard_stats(self, stats):
        # Header do dashboard
        header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        title_label = tk.Label(header_frame, text="📊 Dashboard - Visão Geral", 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                              font=self.styles.fonts['title'])
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Botão de atualização
        refresh_btn = tk.Button(header_frame, text="🔄 Atualizar", command=self.show_dashboard,
                               bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                               font=self.styles.fonts['button'], relief='flat',
                               padx=20, pady=10, cursor='hand2')
        refresh_btn.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Grid de estatísticas com cards
        stats_container = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        stats_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Cards de estatísticas com design moderno
        cards_data = [
            ("👤 Usuários", stats['users']['total'], stats['users']['this_month'], 
             f"Novos este mês", self.styles.colors['primary']),
            ("👥 Cidadãos", stats['citizens']['total'], stats['citizens']['with_debt'], 
             format_currency_brl(stats['citizens']['total_debt']), self.styles.colors['success']),
            ("🚗 Veículos", stats['vehicles']['total'], stats['vehicles']['active'], 
             f"{stats['vehicles']['total'] - stats['vehicles']['active']} bloqueados", self.styles.colors['warning']),
            ("⚠️ Incidentes", stats['incidents']['total'], stats['incidents']['this_week'], 
             f"Média: {stats['incidents']['total']/30:.1f}/dia", self.styles.colors['accent']),
            ("💰 Multas", stats['fines']['total'], stats['fines']['pending'], 
             format_currency_brl(stats['fines']['total_amount']), self.styles.colors['secondary']),
            ("📹 Sensores", stats['sensors']['total'], stats['sensors']['active'], 
             f"{stats['sensors']['total'] - stats['sensors']['active']} inativos", self.styles.colors['dark']),
        ]
        
        # Criar cards em grid
        for i, (title, total, active, extra, color) in enumerate(cards_data):
            row = i // 3
            col = i % 3
            
            # Card container
            card = self.create_dashboard_card(stats_container, title, total, active, extra, color)
            card.grid(row=row, column=col, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        for i in range(3):
            stats_container.columnconfigure(i, weight=1)
        stats_container.rowconfigure(0, weight=1)
        stats_container.rowconfigure(1, weight=1)
        
    def create_dashboard_card(self, parent, title, total, active, extra, color):
        """Cria um card estilizado para o dashboard"""
        # Card principal
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header do card com cor
        header = tk.Frame(card, bg=color, height=60)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        # Título do card
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                             font=self.styles.fonts['heading'])
        title_label.pack(pady=15)
        
        # Conteúdo do card
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Número principal grande
        main_number = tk.Label(content, text=str(total), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', 36, 'bold'))
        main_number.pack(anchor='w')
        
        # Label secundário
        if title == "👤 Usuários":
            secondary_text = f"Novos este mês: {active}"
        elif title == "👥 Cidadãos":
            secondary_text = f"Com dívida: {active}"
        elif title == "🚗 Veículos":
            secondary_text = f"Ativos: {active}"
        elif title == "⚠️ Incidentes":
            secondary_text = f"Esta semana: {active}"
        elif title == "💰 Multas":
            secondary_text = f"Pendentes: {active}"
        elif title == "📹 Sensores":
            secondary_text = f"Ativos: {active}"
        else:
            secondary_text = f"Ativos: {active}"
            
        secondary_label = tk.Label(content, text=secondary_text, bg=self.styles.colors['card'],
                                 fg=self.styles.colors['text_secondary'], font=self.styles.fonts['normal'])
        secondary_label.pack(anchor='w', pady=(5, 10))
        
        # Informação extra
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_primary'], font=self.styles.fonts['small'])
        extra_label.pack(anchor='w')
        
        return card
        
    def show_users(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Query para usuários (apenas credenciais)
                    cur.execute("""
                        SELECT id, username, created_at, updated_at
                        FROM app_user_active
                        ORDER BY username
                    """)
                    users = cur.fetchall()
                    
                    # Header estilizado
                    header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
                    header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
                    
                    # Título
                    title_label = tk.Label(header_frame, text="👤 Gestão de Usuários", 
                                          bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                          font=self.styles.fonts['title'])
                    title_label.pack(side=tk.LEFT, padx=20, pady=15)
                    
                    # Botão de atualizar
                    refresh_btn = tk.Button(header_frame, text="🔄 Atualizar", command=self.show_users,
                                          bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=15, pady=8, cursor='hand2')
                    refresh_btn.pack(side=tk.RIGHT, padx=20, pady=15)
                    
                    # Cards de estatísticas
                    self.create_users_stats(users)
                    
                    # Tabela de usuários
                    self.create_users_table(users)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar usuários: {str(e)}")
            
    def create_users_stats(self, users):
        try:
            # Calcular estatísticas
            total_users = len(users)
            
            # Contar usuários por período de criação
            if users:
                recent_users = len([u for u in users if u['created_at'] and 
                                  (datetime.now() - u['created_at']).days <= 30])
            else:
                recent_users = 0
            
            # Frame de estatísticas
            stats_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
            stats_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
            
            # Cards
            cards_data = [
                ("👤 Total Usuários", total_users, f"100%", self.styles.colors['primary']),
                ("🆕 Novos (30 dias)", recent_users, f"{(recent_users/total_users*100):.1f}%" if total_users > 0 else "0%", self.styles.colors['success']),
                ("🔐 Credenciais", total_users, "Apenas login/senha", self.styles.colors['warning'])
            ]
            
            for i, (title, value, extra, color) in enumerate(cards_data):
                card = self.create_users_stat_card(stats_frame, title, value, extra, color)
                card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        except Exception as e:
            print(f"Erro ao criar estatísticas de usuários: {e}")
            # Não mostrar erro ao usuário, apenas não criar os stats
            
    def create_users_stat_card(self, parent, title, value, extra, color):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header
        header = tk.Frame(card, bg=color, height=40)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                              font=self.styles.fonts['normal'])
        title_label.pack(pady=8)
        
        # Content
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        value_label = tk.Label(content, text=str(value), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', 24, 'bold'))
        value_label.pack(anchor='w')
        
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small'])
        extra_label.pack(anchor='w', pady=(2, 0))
        
        return card
        
    def create_users_table(self, users):
        # Frame da tabela
        table_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview para usuários
        columns = ('ID', 'Username', 'Criado em', 'Atualizado em')
        self.users_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Users.Treeview')
        
        # Configurar colunas
        for col in columns:
            self.users_tree.heading(col, text=col)
            if col == 'ID':
                self.users_tree.column(col, width=50)
            elif col == 'Username':
                self.users_tree.column(col, width=200)
            else:
                self.users_tree.column(col, width=150)
                
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.users_tree.xview)
        self.users_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.users_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Inserir dados
        for user in users:
            # Tratar datas de forma segura
            if user['created_at'] and hasattr(user['created_at'], 'strftime'):
                created_date = user['created_at'].strftime('%d/%m/%Y %H:%M')
            else:
                created_date = 'N/A'
                
            if user['updated_at'] and hasattr(user['updated_at'], 'strftime'):
                updated_date = user['updated_at'].strftime('%d/%m/%Y %H:%M')
            else:
                updated_date = 'N/A'
            
            self.users_tree.insert('', tk.END, values=(
                user['id'],
                user['username'],
                created_date,
                updated_date
            ))
            
        # Frame de informações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"👤 {len(users)} usuários registrados (apenas credenciais)",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT)
                
    def show_citizens(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Query para cidadãos (dados pessoais estão na tabela citizen)
                    cur.execute("""
                        SELECT c.id, c.first_name, c.last_name, c.email, c.cpf, c.phone,
                               c.address, c.birth_date, c.wallet_balance, c.debt, c.allowed,
                               u.username, c.created_at
                        FROM citizen_active c
                        JOIN app_user u ON c.app_user_id = u.id
                        ORDER BY c.first_name, c.last_name
                    """)
                    citizens = cur.fetchall()
                    
                    # Header estilizado
                    header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
                    header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
                    
                    title_label = tk.Label(header_frame, text="👥 Gestão de Cidadãos", 
                                          bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                          font=self.styles.fonts['title'])
                    title_label.pack(side=tk.LEFT, padx=1, pady=15)
                    
                    # Frame de filtros para cidadãos
                    filter_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
                    filter_frame.pack(side=tk.LEFT, padx=20, pady=15)
                    
                    # Filtro por nome
                    tk.Label(filter_frame, text="🔍 Nome:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(0, 5))
                    
                    self.citizen_name_var = tk.StringVar()
                    self.citizen_name_var.trace('w', lambda *args: self.filter_citizens())
                    name_entry = tk.Entry(filter_frame, textvariable=self.citizen_name_var, 
                                      font=self.styles.fonts['normal'], width=20)
                    name_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por CPF
                    tk.Label(filter_frame, text="📋 CPF:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.citizen_cpf_var = tk.StringVar()
                    self.citizen_cpf_var.trace('w', lambda *args: self.filter_citizens())
                    cpf_entry = tk.Entry(filter_frame, textvariable=self.citizen_cpf_var, 
                                     font=self.styles.fonts['normal'], width=15)
                    cpf_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por status
                    tk.Label(filter_frame, text="Status:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.citizen_status_var = tk.StringVar(value="Todos")
                    status_combo = ttk.Combobox(filter_frame, textvariable=self.citizen_status_var, 
                                            values=["Todos", "Ativos", "Inativos"], width=10, state="readonly")
                    status_combo.pack(side=tk.LEFT, padx=5)
                    status_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_citizens())
                    
                    # Filtro por dívida
                    tk.Label(filter_frame, text="💳 Dívida:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.citizen_debt_var = tk.StringVar(value="Todos")
                    debt_combo = ttk.Combobox(filter_frame, textvariable=self.citizen_debt_var, 
                                           values=["Todos", "Com Dívida", "Sem Dívida"], width=12, state="readonly")
                    debt_combo.pack(side=tk.LEFT, padx=5)
                    debt_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_citizens())
                    
                    # Botões de ação
                    add_btn = tk.Button(filter_frame, text="➕ Adicionar", command=self.add_citizen_dialog,
                                      bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                      font=self.styles.fonts['button'], relief='flat',
                                      padx=10, pady=8, cursor='hand2')
                    add_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Botão de atualizar
                    refresh_btn = tk.Button(filter_frame, text="🔄 Atualizar", command=self.show_citizens,
                                          bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    refresh_btn.pack(side=tk.LEFT, padx=5)

                    delete_btn = tk.Button(filter_frame, text='❌ Excluir', command=self.delete_selected_citizen,
                                          bg=self.styles.colors['danger'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    delete_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Armazenar dados originais para filtros
                    self.all_citizens = citizens
                    
                    self.create_citizens_stats(citizens)
                    # Tabela de cidadãos
                    self.create_citizens_table(citizens)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar cidadãos: {str(e)}")
            
    def filter_citizens(self):
        """Filtra cidadãos baseado nos critérios selecionados"""
        if not hasattr(self, 'all_citizens'):
            return
            
        filtered_citizens = self.all_citizens.copy()
        
        # Filtro por nome
        name_filter = self.citizen_name_var.get().lower().strip()
        if name_filter:
            filtered_citizens = [
                c for c in filtered_citizens 
                if (c['first_name'] and name_filter in c['first_name'].lower()) or
                   (c['last_name'] and name_filter in c['last_name'].lower())
            ]
        
        # Filtro por CPF
        cpf_filter = self.citizen_cpf_var.get().strip()
        if cpf_filter:
            filtered_citizens = [
                c for c in filtered_citizens 
                if c['cpf'] and cpf_filter in c['cpf']
            ]
        
        # Filtro por status
        status_filter = self.citizen_status_var.get()
        if status_filter == "Ativos":
            filtered_citizens = [c for c in filtered_citizens if c['allowed']]
        elif status_filter == "Inativos":
            filtered_citizens = [c for c in filtered_citizens if not c['allowed']]
        
        # Filtro por dívida
        debt_filter = self.citizen_debt_var.get()
        if debt_filter == "Com Dívida":
            # Cidadão tem dívida se o campo debt for maior que zero (mantido pelo trigger)
            filtered_citizens = [c for c in filtered_citizens if c.get('debt', 0) > 0]
        elif debt_filter == "Sem Dívida":
            # Cidadão não tem dívida se o campo debt for zero ou não existir
            filtered_citizens = [c for c in filtered_citizens if c.get('debt', 0) == 0]
        else:  # "Todos"
            filtered_citizens = filtered_citizens
        
        # Atualizar tabela com dados filtrados
        self.update_citizens_table(filtered_citizens)
        
    def update_citizens_table(self, citizens):
        """Atualiza apenas a tabela de cidadãos sem recarregar tudo"""
        # Limpar tabela atual
        for item in self.citizens_tree.get_children():
            self.citizens_tree.delete(item)
        
        # Inserir dados filtrados
        for citizen in citizens:
            full_name = f"{citizen['first_name']} {citizen['last_name']}"
            status = "✅ Ativo" if citizen['allowed'] else "🔴 Inativo"
            
            self.citizens_tree.insert('', tk.END, values=(
                citizen['id'],
                full_name,
                citizen['email'] or 'N/A',
                citizen['cpf'] or 'N/A',
                citizen['phone'] or 'N/A',
                citizen['address'] or 'N/A',
                format_currency_brl(citizen['wallet_balance']) if citizen['wallet_balance'] else 'R$ 0,00',
                format_currency_brl(citizen['debt']) if citizen['debt'] else 'R$ 0,00',
                status,
                citizen['username'] or 'N/A'
            ))
        
        # Atualizar contador
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "cidadãos registrados" in child.cget("text"):
                        child.config(text=f"👥 {len(citizens)} cidadãos registrados ({len(self.all_citizens)} total)")
                        break
                        
    def create_citizens_stats(self, citizens):
        try:
            # Calcular estatísticas
            total_citizens = len(citizens)
            active_citizens = len([c for c in citizens if c['allowed']]) if citizens else 0
            inactive_citizens = len([c for c in citizens if not c['allowed']]) if citizens else 0
            total_balance = sum(c['wallet_balance'] for c in citizens if c['wallet_balance']) if citizens else 0
            total_debt = sum(c['debt'] for c in citizens if c['debt']) if citizens else 0
            
            # Frame de estatísticas
            stats_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
            stats_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
            
            # Cards
            cards_data = [
                ("👥 Total Cidadãos", total_citizens, format_currency_brl(total_balance), self.styles.colors['primary']),
                ("✅ Ativos", active_citizens, f"{(active_citizens/total_citizens*100):.1f}%" if total_citizens > 0 else "0%", self.styles.colors['success']),
                ("🔴 Inativos", inactive_citizens, format_currency_brl(total_debt), self.styles.colors['warning'])
            ]
            
            for i, (title, value, extra, color) in enumerate(cards_data):
                card = self.create_citizens_stat_card(stats_frame, title, value, extra, color)
                card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        except Exception as e:
            print(f"Erro ao criar estatísticas de cidadãos: {e}")
            # Não mostrar erro ao usuário, apenas não criar os stats
            
    def create_citizens_stat_card(self, parent, title, value, extra, color):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header
        header = tk.Frame(card, bg=color, height=40)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                              font=self.styles.fonts['normal'])
        title_label.pack(pady=8)
        
        # Content
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        value_label = tk.Label(content, text=str(value), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', 24, 'bold'))
        value_label.pack(anchor='w')
        
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small'])
        extra_label.pack(anchor='w', pady=(2, 0))
        
        return card
        
    def create_citizens_table(self, citizens):
        # Frame da tabela
        table_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview para cidadãos
        columns = ('ID', 'Nome', 'Email', 'CPF', 'Telefone', 'Endereço', 'Saldo', 'Dívida', 'Status', 'Username')
        self.citizens_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Citizens.Treeview')
        
        # Configurar colunas
        for col in columns:
            self.citizens_tree.heading(col, text=col)
            if col == 'ID':
                self.citizens_tree.column(col, width=50)
            elif col in ['Saldo', 'Dívida']:
                self.citizens_tree.column(col, width=100)
            elif col == 'Username':
                self.citizens_tree.column(col, width=120)
            elif col == 'CPF':
                self.citizens_tree.column(col, width=120)
            elif col == 'Telefone':
                self.citizens_tree.column(col, width=120)
            else:
                self.citizens_tree.column(col, width=150)
                
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.citizens_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.citizens_tree.xview)
        self.citizens_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.citizens_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Inserir dados
        for citizen in citizens:
            full_name = f"{citizen['first_name']} {citizen['last_name']}"
            status = "✅ Ativo" if citizen['allowed'] else "🔴 Inativo"
            
            self.citizens_tree.insert('', tk.END, values=(
                citizen['id'],
                full_name,
                citizen['email'] or 'N/A',
                citizen['cpf'] or 'N/A',
                citizen['phone'] or 'N/A',
                citizen['address'] or 'N/A',
                format_currency_brl(citizen['wallet_balance']) if citizen['wallet_balance'] else 'R$ 0,00',
                format_currency_brl(citizen['debt']) if citizen['debt'] else 'R$ 0,00',
                status,
                citizen['username'] or 'N/A'
            ))
            
        # Frame de informações e ações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"👥 {len(citizens)} cidadãos registrados",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botão de excluir cidadão selecionado
        delete_btn = tk.Button(info_frame, text="🗑️ Excluir Selecionado", command=self.delete_selected_citizen,
                              bg=self.styles.colors['danger'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=10, pady=8, cursor='hand2')
        delete_btn.pack(side=tk.RIGHT, padx=(0, 10))
                
    def delete_selected_citizen(self):
        """Exclui o cidadão selecionado na tabela"""
        if not hasattr(self, 'citizens_tree'):
            messagebox.showwarning("Aviso", "Nenhuma tabela de cidadãos disponível!")
            return
            
        selection = self.citizens_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um cidadão para excluir!")
            return
            
        # Obter dados do cidadão selecionado
        item = self.citizens_tree.item(selection[0])
        values = item['values']
        citizen_id = values[0]
        citizen_name = values[1]
        
        # Confirmar exclusão
        result = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir o cidadão:\n\n{citizen_name} (ID: {citizen_id})\n\n"
            "Esta ação não poderá ser desfeita!",
            icon='warning'
        )
        
        if result:
            try:
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Verificar se há multas pendentes
                        cur.execute("SELECT COUNT(*) FROM fine WHERE citizen_id = %s AND status = 'pending'", (citizen_id,))
                        pending_fines = cur.fetchone()[0]
                        
                        if pending_fines > 0:
                            messagebox.showerror("Erro", f"Não é possível excluir cidadão com {pending_fines} multa(s) pendente(s)!")
                            return
                        
                        # Excluir cidadão (cascade deve excluir app_user)
                        cur.execute("DELETE FROM citizen WHERE id = %s", (citizen_id,))
                        conn.commit()
                        
                        messagebox.showinfo("Sucesso", f"Cidadão {citizen_name} excluído com sucesso!")
                        self.show_citizens()  # Atualizar lista
                        
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir cidadão: {str(e)}")
                
    def show_vehicles(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Query para veículos com JOIN em app_user e citizen
                    cur.execute("""
                        SELECT v.id, v.license_plate, v.model, v.year, v.allowed,
                               u.username, c.first_name, c.last_name
                        FROM vehicle_active v
                        JOIN app_user u ON v.app_user_id = u.id
                        LEFT JOIN citizen_active c ON v.citizen_id = c.id
                        ORDER BY v.license_plate
                    """)
                    vehicles = cur.fetchall()
                                       
                    # Header estilizado
                    header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
                    header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
                    
                    title_label = tk.Label(header_frame, text="🚗 Gestão de Veículos", 
                                          bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                          font=self.styles.fonts['title'])
                    title_label.pack(side=tk.LEFT, padx=20, pady=15)
                    
                    # Frame de filtros para veículos
                    filter_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
                    filter_frame.pack(side=tk.RIGHT, padx=20, pady=15)
                    
                    # Filtro por placa
                    tk.Label(filter_frame, text="🔍 Placa:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(0, 5))
                    
                    self.vehicle_plate_var = tk.StringVar()
                    self.vehicle_plate_var.trace('w', lambda *args: self.filter_vehicles())
                    plate_entry = tk.Entry(filter_frame, textvariable=self.vehicle_plate_var, 
                                       font=self.styles.fonts['normal'], width=15)
                    plate_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por modelo
                    tk.Label(filter_frame, text="🚗 Modelo:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.vehicle_model_var = tk.StringVar()
                    self.vehicle_model_var.trace('w', lambda *args: self.filter_vehicles())
                    model_entry = tk.Entry(filter_frame, textvariable=self.vehicle_model_var, 
                                       font=self.styles.fonts['normal'], width=15)
                    model_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por status
                    tk.Label(filter_frame, text="Status:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.vehicle_status_var = tk.StringVar(value="Todos")
                    status_combo = ttk.Combobox(filter_frame, textvariable=self.vehicle_status_var, 
                                            values=["Todos", "Ativos", "Inativos"], width=10, state="readonly")
                    status_combo.pack(side=tk.LEFT, padx=5)
                    status_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_vehicles())
                    
                    # Filtro por ano
                    tk.Label(filter_frame, text="📅 Ano:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.vehicle_year_var = tk.StringVar()
                    self.vehicle_year_var.trace('w', lambda *args: self.filter_vehicles())
                    year_entry = tk.Entry(filter_frame, textvariable=self.vehicle_year_var, 
                                      font=self.styles.fonts['normal'], width=8)
                    year_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Botões de ação
                    add_btn = tk.Button(filter_frame, text="➕ Adicionar", command=self.add_vehicle_dialog,
                                      bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                      font=self.styles.fonts['button'], relief='flat',
                                      padx=10, pady=8, cursor='hand2')
                    add_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Botão de atualizar
                    refresh_btn = tk.Button(filter_frame, text="🔄 Atualizar", command=self.show_vehicles,
                                          bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    refresh_btn.pack(side=tk.LEFT, padx=5)

                    delete_btn = tk.Button(filter_frame, text='❌ Excluir', command=self.delete_selected_vehicle,
                                          bg=self.styles.colors['danger'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    delete_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Armazenar dados originais para filtros
                    self.all_vehicles = vehicles
                    
               
                    self.create_vehicles_stats(vehicles)
                    # Tabela de veículos
                    self.create_vehicles_table(vehicles)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar veículos: {str(e)}")
            
    def filter_vehicles(self):
        """Filtra veículos baseado nos critérios selecionados"""
        if not hasattr(self, 'all_vehicles'):
            return
            
        filtered_vehicles = self.all_vehicles.copy()
        
        # Filtro por placa
        plate_filter = self.vehicle_plate_var.get().upper().strip()
        if plate_filter:
            filtered_vehicles = [
                v for v in filtered_vehicles 
                if v['license_plate'] and plate_filter in v['license_plate'].upper()
            ]
        
        # Filtro por modelo
        model_filter = self.vehicle_model_var.get().lower().strip()
        if model_filter:
            filtered_vehicles = [
                v for v in filtered_vehicles 
                if v['model'] and model_filter in v['model'].lower()
            ]
        
        # Filtro por ano
        year_filter = self.vehicle_year_var.get().strip()
        if year_filter:
            filtered_vehicles = [
                v for v in filtered_vehicles 
                if v['year'] and year_filter in str(v['year'])
            ]
        
        # Filtro por status
        status_filter = self.vehicle_status_var.get()
        if status_filter == "Ativos":
            filtered_vehicles = [v for v in filtered_vehicles if v['allowed']]
        elif status_filter == "Inativos":
            filtered_vehicles = [v for v in filtered_vehicles if not v['allowed']]
        
        # Atualizar tabela com dados filtrados
        self.update_vehicles_table(filtered_vehicles)
        
    def update_vehicles_table(self, vehicles):
        """Atualiza apenas a tabela de veículos sem recarregar tudo"""
        # Limpar tabela atual
        for item in self.vehicles_tree.get_children():
            self.vehicles_tree.delete(item)
        
        # Inserir dados filtrados
        for vehicle in vehicles:
            # Tenta pegar nome do cidadão primeiro, senão usa username
            if vehicle['first_name'] and vehicle['last_name']:
                owner_name = f"{vehicle['first_name']} {vehicle['last_name']}"
            else:
                owner_name = vehicle['username'] or 'N/A'
            status = "✅ Ativo" if vehicle['allowed'] else "🔴 Inativo"
            
            self.vehicles_tree.insert('', tk.END, values=(
                vehicle['id'],
                vehicle['license_plate'],
                vehicle['model'],
                vehicle['year'],
                owner_name,
                status
            ))
        
        # Atualizar contador
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "veículos registrados" in child.cget("text"):
                        child.config(text=f"🚗 {len(vehicles)} veículos registrados ({len(self.all_vehicles)} total)")
                        break
                        
    def create_vehicles_stats(self, vehicles):
        try:
            # Calcular estatísticas
            total_vehicles = len(vehicles)
            active_vehicles = len([v for v in vehicles if v['allowed']]) if vehicles else 0
            inactive_vehicles = len([v for v in vehicles if not v['allowed']]) if vehicles else 0
            
            # Frame de estatísticas
            stats_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
            stats_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
            
            # Cards
            cards_data = [
                ("🚗 Total Veículos", total_vehicles, f"100%", self.styles.colors['primary']),
                ("✅ Ativos", active_vehicles, f"{(active_vehicles/total_vehicles*100):.1f}%" if total_vehicles > 0 else "0%", self.styles.colors['success']),
                ("🔴 Inativos", inactive_vehicles, f"{(inactive_vehicles/total_vehicles*100):.1f}%" if total_vehicles > 0 else "0%", self.styles.colors['warning'])
            ]
            
            for i, (title, value, extra, color) in enumerate(cards_data):
                card = self.create_vehicles_stat_card(stats_frame, title, value, extra, color)
                card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        except Exception as e:
            print(f"Erro ao criar estatísticas de veículos: {e}")
            # Não mostrar erro ao usuário, apenas não criar os stats
            
    def create_vehicles_stat_card(self, parent, title, value, extra, color):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header
        header = tk.Frame(card, bg=color, height=40)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                              font=self.styles.fonts['normal'])
        title_label.pack(pady=8)
        
        # Content
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        value_label = tk.Label(content, text=str(value), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', 24, 'bold'))
        value_label.pack(anchor='w')
        
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small'])
        extra_label.pack(anchor='w', pady=(2, 0))
        
        return card
        
    def create_vehicles_table(self, vehicles):
        # Frame da tabela
        table_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview para veículos
        columns = ('ID', 'Placa', 'Modelo', 'Ano', 'Proprietário', 'Status')
        self.vehicles_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Vehicles.Treeview')
        
        # Configurar colunas
        for col in columns:
            self.vehicles_tree.heading(col, text=col)
            if col == 'ID':
                self.vehicles_tree.column(col, width=50)
            elif col == 'Ano':
                self.vehicles_tree.column(col, width=80)
            else:
                self.vehicles_tree.column(col, width=150)
                
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.vehicles_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.vehicles_tree.xview)
        self.vehicles_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.vehicles_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Inserir dados
        for vehicle in vehicles:
            # Tenta pegar nome do cidadão primeiro, senão usa username
            if vehicle['first_name'] and vehicle['last_name']:
                owner_name = f"{vehicle['first_name']} {vehicle['last_name']}"
            else:
                owner_name = vehicle['username'] or 'N/A'
            status = "✅ Ativo" if vehicle['allowed'] else "🔴 Inativo"
            
            self.vehicles_tree.insert('', tk.END, values=(
                vehicle['id'],
                vehicle['license_plate'],
                vehicle['model'],
                vehicle['year'],
                owner_name,
                status
            ))
            
        # Frame de informações e ações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"🚗 {len(vehicles)} veículos registrados",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botão de excluir veículo selecionado
        delete_btn = tk.Button(info_frame, text="🗑️ Excluir Selecionado", command=self.delete_selected_vehicle,
                              bg=self.styles.colors['danger'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=10, pady=8, cursor='hand2')
        delete_btn.pack(side=tk.RIGHT, padx=(0, 10))        
                
    def delete_selected_vehicle(self):
        """Exclui o veículo selecionado na tabela"""
        if not hasattr(self, 'vehicles_tree'):
            messagebox.showwarning("Aviso", "Nenhuma tabela de veículos disponível!")
            return
            
        selection = self.vehicles_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um veículo para excluir!")
            return
            
        # Obter dados do veículo selecionado
        item = self.vehicles_tree.item(selection[0])
        values = item['values']
        vehicle_id = values[0]
        license_plate = values[1]
        model = values[2]
        
        # Confirmar exclusão
        result = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir o veículo:\n\n{model} - Placa: {license_plate} (ID: {vehicle_id})\n\n"
            "Esta ação não poderá ser desfeita!",
            icon='warning'
        )
        
        if result:
            try:
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Verificar se há multas ou incidentes
                        cur.execute("SELECT COUNT(*) FROM traffic_incident WHERE vehicle_id = %s", (vehicle_id,))
                                               
                        # Excluir veículo
                        cur.execute("DELETE FROM vehicle WHERE id = %s", (vehicle_id,))
                        conn.commit()
                        
                        messagebox.showinfo("Sucesso", f"Veículo {license_plate} excluído com sucesso!")
                        self.show_vehicles()  # Atualizar lista
                        
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir veículo: {str(e)}")
        
    def show_sensors(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT s.id, s.type, s.location, s.active, 
                               COUNT(r.id) as reading_count,
                               MAX(r.timestamp) as last_reading
                        FROM sensor_active s
                        LEFT JOIN reading r ON s.id = r.sensor_id
                        GROUP BY s.id, s.type, s.location, s.active
                        ORDER BY s.type, s.location
                    """)
                    sensors = cur.fetchall()
                    
                    # Header estilizado
                    header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
                    header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
                    
                    title_label = tk.Label(header_frame, text="📹 Gestão de Sensores", 
                                          bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                          font=self.styles.fonts['title'])
                    title_label.pack(side=tk.LEFT, padx=20, pady=15)
                    
                    # Frame de filtros para sensores
                    filter_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
                    filter_frame.pack(side=tk.RIGHT, padx=20, pady=15)
                    
                    # Filtro por tipo
                    tk.Label(filter_frame, text="🔍 Tipo:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(0, 5))
                    
                    self.sensor_type_var = tk.StringVar()
                    self.sensor_type_var.trace('w', lambda *args: self.filter_sensors())
                    type_entry = tk.Entry(filter_frame, textvariable=self.sensor_type_var, 
                                      font=self.styles.fonts['normal'], width=15)
                    type_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por localização
                    tk.Label(filter_frame, text="📍 Local:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.sensor_location_var = tk.StringVar()
                    self.sensor_location_var.trace('w', lambda *args: self.filter_sensors())
                    location_entry = tk.Entry(filter_frame, textvariable=self.sensor_location_var, 
                                         font=self.styles.fonts['normal'], width=15)
                    location_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por status
                    tk.Label(filter_frame, text="Status:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.sensor_status_var = tk.StringVar(value="Todos")
                    status_combo = ttk.Combobox(filter_frame, textvariable=self.sensor_status_var, 
                                            values=["Todos", "Ativos", "Inativos"], width=10, state="readonly")
                    status_combo.pack(side=tk.LEFT, padx=5)
                    status_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_sensors())
                    
                    # Filtro por leituras
                    tk.Label(filter_frame, text="📊 Leituras:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.sensor_readings_var = tk.StringVar(value="Todos")
                    readings_combo = ttk.Combobox(filter_frame, textvariable=self.sensor_readings_var, 
                                             values=["Todos", "Com Leituras", "Sem Leituras"], width=12, state="readonly")
                    readings_combo.pack(side=tk.LEFT, padx=5)
                    readings_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_sensors())
                    
                    # Botões de ação
                    add_btn = tk.Button(filter_frame, text="➕ Adicionar", command=self.add_sensor_dialog,
                                      bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                      font=self.styles.fonts['button'], relief='flat',
                                      padx=10, pady=8, cursor='hand2')
                    add_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Botão de atualizar
                    refresh_btn = tk.Button(filter_frame, text="🔄 Atualizar", command=self.show_sensors,
                                          bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    refresh_btn.pack(side=tk.LEFT, padx=5)
                    
                    delete_btn = tk.Button(filter_frame, text='❌ Excluir', command=self.delete_selected_sensor,
                                          bg=self.styles.colors['danger'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    delete_btn.pack(side=tk.LEFT, padx=5)

                    # Armazenar dados originais para filtros
                    self.all_sensors = sensors
                    
                    self.create_sensors_stats(sensors)
                    # Tabela de sensores
                    self.create_sensors_table(sensors)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar sensores: {str(e)}")
            
    def create_sensors_stats(self, sensors):
        """Cria cards de estatísticas para sensores"""
        try:
            # Calcular estatísticas
            total_sensors = len(sensors)
            active_sensors = len([s for s in sensors if s['active']]) if sensors else 0
            inactive_sensors = len([s for s in sensors if not s['active']]) if sensors else 0
            total_readings = sum(s['reading_count'] for s in sensors if s['reading_count']) if sensors else 0
            
            # Frame de estatísticas
            stats_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
            stats_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
            
            # Cards
            cards_data = [
                ("📹 Total Sensores", total_sensors, f"{total_readings} leituras", self.styles.colors['primary']),
                ("✅ Ativos", active_sensors, f"{(active_sensors/total_sensors*100):.1f}%" if total_sensors > 0 else "0%", self.styles.colors['success']),
                ("🔴 Inativos", inactive_sensors, f"{(inactive_sensors/total_sensors*100):.1f}%" if total_sensors > 0 else "0%", self.styles.colors['warning'])
            ]
            
            for i, (title, value, extra, color) in enumerate(cards_data):
                card = self.create_sensors_stat_card(stats_frame, title, value, extra, color)
                card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        except Exception as e:
            print(f"Erro ao criar estatísticas de sensores: {e}")
            # Não mostrar erro ao usuário, apenas não criar os stats
            
    def create_sensors_stat_card(self, parent, title, value, extra, color):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header
        header = tk.Frame(card, bg=color, height=40)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                              font=self.styles.fonts['normal'])
        title_label.pack(pady=8)
        
        # Content
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        value_label = tk.Label(content, text=str(value), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', 24, 'bold'))
        value_label.pack(anchor='w')
        
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small'])
        extra_label.pack(anchor='w', pady=(2, 0))
        
        return card
        
    def create_sensors_table(self, sensors):
        # Frame da tabela
        table_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview para sensores
        columns = ('ID', 'Tipo', 'Localização', 'Status', 'Leituras', 'Última Leitura')
        self.sensors_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Sensors.Treeview')
        
        # Configurar colunas
        for col in columns:
            self.sensors_tree.heading(col, text=col)
            if col == 'ID':
                self.sensors_tree.column(col, width=60, minwidth=50)
            elif col == 'Status':
                self.sensors_tree.column(col, width=80, minwidth=70)
            elif col == 'Leituras':
                self.sensors_tree.column(col, width=80, minwidth=70)
            else:
                self.sensors_tree.column(col, width=150, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.sensors_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.sensors_tree.xview)
        self.sensors_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.sensors_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Inserir dados
        for i, sensor in enumerate(sensors):
            status = "🟢 Ativo" if sensor['active'] else "🔴 Inativo"
            last_reading = sensor['last_reading'].strftime('%d/%m %H:%M') if sensor['last_reading'] else "N/A"
            
            tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
            self.sensors_tree.insert('', tk.END, values=(
                sensor['id'],
                sensor['type'],
                sensor['location'],
                status,
                sensor['reading_count'],
                last_reading
            ), tags=(tag,))
            
        # Frame de informações e ações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"📊 {len(sensors)} sensores cadastrados",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botão de excluir sensor selecionado
        delete_btn = tk.Button(info_frame, text="🗑️ Excluir Selecionado", command=self.delete_selected_sensor,
                              bg=self.styles.colors['danger'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=10, pady=8, cursor='hand2')
        delete_btn.pack(side=tk.RIGHT, padx=(0, 10))
                
    def delete_selected_sensor(self):
        """Exclui o sensor selecionado na tabela"""
        if not hasattr(self, 'sensors_tree'):
            messagebox.showwarning("Aviso", "Nenhuma tabela de sensores disponível!")
            return
            
        selection = self.sensors_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um sensor para excluir!")
            return
            
        # Obter dados do sensor selecionado
        item = self.sensors_tree.item(selection[0])
        values = item['values']
        sensor_id = values[0]
        sensor_type = values[1]
        location = values[2]
        
        # Confirmar exclusão
        result = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir o sensor:\n\n{sensor_type} - {location} (ID: {sensor_id})\n\n"
            "Esta ação não poderá ser desfeita!",
            icon='warning'
        )
        
        if result:
            try:
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Verificar se há leituras ou incidentes
                        cur.execute("SELECT COUNT(*) FROM reading WHERE sensor_id = %s", (sensor_id,))
                        readings = cur.fetchone()[0]
                        
                        cur.execute("SELECT COUNT(*) FROM traffic_incident WHERE sensor_id = %s", (sensor_id,))
                        incidents = cur.fetchone()[0]
                        
                                          
                        # Excluir sensor
                        cur.execute("DELETE FROM sensor WHERE id = %s", (sensor_id,))
                        conn.commit()
                        
                        messagebox.showinfo("Sucesso", f"Sensor {sensor_type} excluído com sucesso!")
                        self.show_sensors()  # Atualizar lista
                        
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir sensor: {str(e)}")
       
    def filter_sensors(self):
        """Filtra sensores baseado nos critérios selecionados"""
        if not hasattr(self, 'all_sensors'):
            return
            
        filtered_sensors = self.all_sensors.copy()
        
        # Filtro por tipo
        type_filter = self.sensor_type_var.get().lower().strip()
        if type_filter:
            filtered_sensors = [
                s for s in filtered_sensors 
                if s['type'] and type_filter in s['type'].lower()
            ]
        
        # Filtro por localização
        location_filter = self.sensor_location_var.get().lower().strip()
        if location_filter:
            filtered_sensors = [
                s for s in filtered_sensors 
                if s['location'] and location_filter in s['location'].lower()
            ]
        
        # Filtro por status
        status_filter = self.sensor_status_var.get()
        if status_filter == "Ativos":
            filtered_sensors = [s for s in filtered_sensors if s['active']]
        elif status_filter == "Inativos":
            filtered_sensors = [s for s in filtered_sensors if not s['active']]
        
        # Filtro por leituras
        readings_filter = self.sensor_readings_var.get()
        if readings_filter == "Com Leituras":
            filtered_sensors = [s for s in filtered_sensors if s['reading_count'] and s['reading_count'] > 0]
        elif readings_filter == "Sem Leituras":
            filtered_sensors = [s for s in filtered_sensors if not s['reading_count'] or s['reading_count'] == 0]
        
        # Atualizar tabela com dados filtrados
        self.update_sensors_table(filtered_sensors)
        
    def update_sensors_table(self, sensors):
        """Atualiza apenas a tabela de sensores sem recarregar tudo"""
        # Limpar tabela atual
        for item in self.sensors_tree.get_children():
            self.sensors_tree.delete(item)
        
        # Inserir dados filtrados
        for sensor in sensors:
            status = "✅ Ativo" if sensor['active'] else "🔴 Inativo"
            tag = 'active' if sensor['active'] else 'inactive'
            
            # Formatar data da última leitura
            if sensor['last_reading'] and hasattr(sensor['last_reading'], 'strftime'):
                last_reading = sensor['last_reading'].strftime('%d/%m/%Y %H:%M')
            else:
                last_reading = 'N/A'
            
            self.sensors_tree.insert('', tk.END, values=(
                sensor['id'],
                sensor['type'],
                sensor['location'],
                status,
                sensor['reading_count'],
                last_reading
            ), tags=(tag,))
        
        # Atualizar contador
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "sensores cadastrados" in child.cget("text"):
                        child.config(text=f"📹 {len(sensors)} sensores cadastrados ({len(self.all_sensors)} total)")
                        break
                        
    def show_incidents(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT ti.id, ti.location, ti.occurred_at, ti.description,
                               COUNT(f.id) as fine_count,
                               COALESCE(SUM(f.amount), 0) as total_fines
                        FROM traffic_incident ti
                        LEFT JOIN fine f ON ti.id = f.traffic_incident_id
                        GROUP BY ti.id, ti.location, ti.occurred_at, ti.description
                        ORDER BY ti.occurred_at DESC
                    """)
                    incidents = cur.fetchall()
                    
                    # Header estilizado
                    header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
                    header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
                    
                    title_label = tk.Label(header_frame, text="⚠️ Gestão de Incidentes", 
                                          bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                          font=self.styles.fonts['title'])
                    title_label.pack(side=tk.LEFT, padx=1, pady=15)
                    
                    # Frame de filtros para incidentes
                    filter_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
                    filter_frame.pack(side=tk.RIGHT, padx=1, pady=15)
                    
                    # Filtro por localização
                    tk.Label(filter_frame, text="🔍 Local:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(0, 5))
                    
                    self.incident_location_var = tk.StringVar()
                    self.incident_location_var.trace('w', lambda *args: self.filter_incidents())
                    location_entry = tk.Entry(filter_frame, textvariable=self.incident_location_var, 
                                         font=self.styles.fonts['normal'], width=20)
                    location_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por período
                    tk.Label(filter_frame, text="📅 Período:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.incident_period_var = tk.StringVar(value="Todos")
                    period_combo = ttk.Combobox(filter_frame, textvariable=self.incident_period_var, 
                                            values=["Todos", "Hoje", "Esta Semana", "Este Mês"], width=12, state="readonly")
                    period_combo.pack(side=tk.LEFT, padx=5)
                    period_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_incidents())
                    
                    # Filtro por multas
                    tk.Label(filter_frame, text="💰 Multas:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.incident_fines_var = tk.StringVar(value="Todos")
                    fines_combo = ttk.Combobox(filter_frame, textvariable=self.incident_fines_var, 
                                           values=["Todos", "Com Multas", "Sem Multas"], width=12, state="readonly")
                    fines_combo.pack(side=tk.LEFT, padx=5)
                    fines_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_incidents())
                    
                    # Filtro por descrição
                    tk.Label(filter_frame, text="📝 Descrição:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.incident_description_var = tk.StringVar()
                    self.incident_description_var.trace('w', lambda *args: self.filter_incidents())
                    description_entry = tk.Entry(filter_frame, textvariable=self.incident_description_var, 
                                           font=self.styles.fonts['normal'], width=20)
                    description_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Botões de ação
                    add_btn = tk.Button(filter_frame, text="➕ Registrar", command=self.add_incident_dialog,
                                      bg=self.styles.colors['warning'], fg=self.styles.colors['white'],
                                      font=self.styles.fonts['button'], relief='flat',
                                      padx=10, pady=8, cursor='hand2')
                    add_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Botão de atualizar
                    refresh_btn = tk.Button(filter_frame, text="🔄 Atualizar", command=self.show_incidents,
                                          bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    refresh_btn.pack(side=tk.LEFT, padx=10)
                    
                    # Armazenar dados originais para filtros
                    self.all_incidents = incidents
                    
                    # Cards de estatísticas
                    self.create_incidents_stats(incidents)
                    
                    # Tabela de incidentes
                    self.create_incidents_table(incidents)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar incidentes: {str(e)}")
            
    def create_incidents_table(self, incidents):
        # Frame da tabela
        table_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview para incidentes
        columns = ('ID', 'Local', 'Data/Hora', 'Descrição', 'Multas', 'Valor Total')
        self.incidents_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Incidents.Treeview')
        
        # Configurar colunas
        for col in columns:
            self.incidents_tree.heading(col, text=col)
            if col == 'ID':
                self.incidents_tree.column(col, width=60, minwidth=50)
            elif col == 'Multas':
                self.incidents_tree.column(col, width=60, minwidth=50)
            elif col == 'Valor Total':
                self.incidents_tree.column(col, width=100, minwidth=80)
            else:
                self.incidents_tree.column(col, width=150, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.incidents_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.incidents_tree.xview)
        self.incidents_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.incidents_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Inserir dados
        for i, incident in enumerate(incidents):
            try:
                occurred_at = incident['occurred_at'].strftime('%d/%m %H:%M') if incident['occurred_at'] else "N/A"
                description = incident['description'] or "Sem descrição"
                if len(description) > 50:
                    description = description[:47] + "..."
                
                tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                self.incidents_tree.insert('', tk.END, values=(
                    incident['id'],
                    incident['location'] or "N/A",
                    occurred_at,
                    description,
                    incident['fine_count'] or 0,
                    format_currency_brl(incident['total_fines']) if incident['total_fines'] and incident['total_fines'] > 0 else "R$ 0,00"
                ), tags=(tag,))
            except Exception as e:
                print(f"Erro ao processar incidente {i}: {e}")
                continue
            
        # Informações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"⚠️ {len(incidents)} incidentes registrados",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT)
        
    def create_incidents_stats(self, incidents):
        """Cria cards de estatísticas para incidentes"""
        try:
            # Calcular estatísticas
            total_incidents = len(incidents)
            
            # Incidentes esta semana
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            this_week_incidents = len([i for i in incidents if i['occurred_at'] and i['occurred_at'] >= week_ago])
            
            # Total de multas geradas
            total_fines = sum(i['fine_count'] or 0 for i in incidents)
            total_fines_amount = sum(i['total_fines'] or 0 for i in incidents)
            
            # Frame de estatísticas
            stats_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
            stats_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
            
            # Cards
            cards_data = [
                ("⚠️ Total Incidentes", total_incidents, f"{this_week_incidents} esta semana", self.styles.colors['accent']),
                ("💰 Multas Geradas", total_fines, f"R$ {total_fines_amount:,.2f}", self.styles.colors['secondary']),
                ("📊 Média/Dia", f"{total_incidents/30:.1f}" if total_incidents > 0 else "0", "Últimos 30 dias", self.styles.colors['primary'])
            ]
            
            for i, (title, value, extra, color) in enumerate(cards_data):
                card = self.create_incidents_stat_card(stats_frame, title, value, extra, color)
                card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        except Exception as e:
            print(f"Erro ao criar estatísticas de incidentes: {e}")
            # Não mostrar erro ao usuário, apenas não criar os stats
            
    def create_incidents_stat_card(self, parent, title, value, extra, color):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header
        header = tk.Frame(card, bg=color, height=40)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                              font=self.styles.fonts['normal'])
        title_label.pack(pady=8)
        
        # Content
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        value_label = tk.Label(content, text=str(value), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', 24, 'bold'))
        value_label.pack(anchor='w')
        
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small'])
        extra_label.pack(anchor='w', pady=(2, 0))
        
        return card
        
    def filter_incidents(self):
        """Filtra incidentes baseado nos critérios selecionados"""
        if not hasattr(self, 'all_incidents'):
            return
            
        filtered_incidents = self.all_incidents.copy()
        
        # Filtro por localização
        location_filter = self.incident_location_var.get().lower().strip()
        if location_filter:
            filtered_incidents = [
                i for i in filtered_incidents 
                if i['location'] and location_filter in i['location'].lower()
            ]
        
        # Filtro por período
        period_filter = self.incident_period_var.get()
        if period_filter != "Todos":
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if period_filter == "Hoje":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered_incidents = [
                    i for i in filtered_incidents 
                    if i['occurred_at'] and i['occurred_at'].date() >= start_date.date()
                ]
            elif period_filter == "Esta Semana":
                start_date = now - timedelta(days=7)
                filtered_incidents = [
                    i for i in filtered_incidents 
                    if i['occurred_at'] and i['occurred_at'] >= start_date
                ]
            elif period_filter == "Este Mês":
                start_date = now - timedelta(days=30)
                filtered_incidents = [
                    i for i in filtered_incidents 
                    if i['occurred_at'] and i['occurred_at'] >= start_date
                ]
        
        # Filtro por multas
        fines_filter = self.incident_fines_var.get()
        if fines_filter == "Com Multas":
            filtered_incidents = [i for i in filtered_incidents if i['fine_count'] and i['fine_count'] > 0]
        elif fines_filter == "Sem Multas":
            filtered_incidents = [i for i in filtered_incidents if not i['fine_count'] or i['fine_count'] == 0]
        
        # Filtro por descrição
        description_filter = self.incident_description_var.get().lower().strip()
        if description_filter:
            filtered_incidents = [
                i for i in filtered_incidents 
                if i['description'] and description_filter in i['description'].lower()
            ]
        
        # Atualizar tabela com dados filtrados
        self.update_incidents_table(filtered_incidents)
        
    def update_incidents_table(self, incidents):
        """Atualiza apenas a tabela de incidentes sem recarregar tudo"""
        # Limpar tabela atual
        for item in self.incidents_tree.get_children():
            self.incidents_tree.delete(item)
        
        # Inserir dados filtrados
        for i, incident in enumerate(incidents):
            try:
                occurred_at = incident['occurred_at'].strftime('%d/%m %H:%M') if incident['occurred_at'] else "N/A"
                description = incident['description'] or "Sem descrição"
                if len(description) > 50:
                    description = description[:47] + "..."
                
                tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                self.incidents_tree.insert('', tk.END, values=(
                    incident['id'],
                    incident['location'] or "N/A",
                    occurred_at,
                    description,
                    incident['fine_count'] or 0,
                    format_currency_brl(incident['total_fines']) if incident['total_fines'] and incident['total_fines'] > 0 else "R$ 0,00"
                ), tags=(tag,))
            except Exception as e:
                print(f"Erro ao processar incidente {i}: {e}")
                continue
        
        # Atualizar contador
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "incidentes registrados" in child.cget("text"):
                        child.config(text=f"⚠️ {len(incidents)} incidentes registrados ({len(self.all_incidents)} total)")
                        break
        
    def show_fines(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    # Query simplificada para testar
                    cur.execute("""
                        SELECT f.id, f.amount, f.status, f.created_at, f.due_date,
                               ti.location as incident_location, ti.description as incident_description,
                               v.license_plate,
                               c.first_name, c.last_name
                        FROM fine f
                        LEFT JOIN traffic_incident ti ON f.traffic_incident_id = ti.id
                        LEFT JOIN vehicle v ON ti.vehicle_id = v.id
                        LEFT JOIN citizen c ON f.citizen_id = c.id
                        ORDER BY f.created_at DESC
                    """)
                    fines = cur.fetchall()
                    
                    # Header estilizado
                    header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
                    header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
                    
                    title_label = tk.Label(header_frame, text="💰 Gestão de Multas", 
                                          bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                          font=self.styles.fonts['title'])
                    title_label.pack(side=tk.LEFT, padx=20, pady=15)
                    
                    # Botões de ação
                    button_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
                    button_frame.pack(side=tk.RIGHT, padx=20, pady=15)
                    
                    # Filtro por status
                    tk.Label(button_frame, text="Status:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(0, 5))
                    
                    # Filtro de status com ttk.Combobox (padrão)
                    self.fine_status_var = tk.StringVar(value="Todos")
                    status_combo = ttk.Combobox(button_frame, textvariable=self.fine_status_var, 
                                               values=["Todos", "Pendentes", "Pagas", "Vencidas"], width=10, state="readonly")
                    status_combo.pack(side=tk.LEFT, padx=5)
                    status_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_fines())
                    
                    # Filtro por valor
                    tk.Label(button_frame, text="💰 Valor Mínimo:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.fine_amount_var = tk.StringVar()
                    self.fine_amount_var.trace('w', lambda *args: self.filter_fines())
                    amount_entry = tk.Entry(button_frame, textvariable=self.fine_amount_var, 
                                        font=self.styles.fonts['normal'], width=12)
                    amount_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por placa
                    tk.Label(button_frame, text="🚗 Placa:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.fine_plate_var = tk.StringVar()
                    self.fine_plate_var.trace('w', lambda *args: self.filter_fines())
                    plate_entry = tk.Entry(button_frame, textvariable=self.fine_plate_var, 
                                      font=self.styles.fonts['normal'], width=12)
                    plate_entry.pack(side=tk.LEFT, padx=5)
                    
                    # Filtro por período
                    tk.Label(button_frame, text="📅 Período:", bg=self.styles.colors['card'], 
                            fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small']).pack(side=tk.LEFT, padx=(10, 5))
                    
                    self.fine_period_var = tk.StringVar(value="Todos")
                    period_combo = ttk.Combobox(button_frame, textvariable=self.fine_period_var, 
                                           values=["Todos", "Hoje", "Esta Semana", "Este Mês", "Vencidas"], width=12, state="readonly")
                    period_combo.pack(side=tk.LEFT, padx=5)
                    period_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_fines())
                    
                    # Botões de ação
                    pay_btn = tk.Button(button_frame, text="💳 Pagar", command=self.pay_fine_dialog,
                                      bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                      font=self.styles.fonts['button'], relief='flat',
                                      padx=10, pady=8, cursor='hand2')
                    pay_btn.pack(side=tk.LEFT, padx=5)
                    
                    add_btn = tk.Button(button_frame, text="➕ Gerar", command=self.generate_fine_dialog,
                                      bg=self.styles.colors['warning'], fg=self.styles.colors['white'],
                                      font=self.styles.fonts['button'], relief='flat',
                                      padx=10, pady=8, cursor='hand2')
                    add_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Botão de atualizar
                    refresh_btn = tk.Button(button_frame, text="🔄 Atualizar", command=self.show_fines,
                                          bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    refresh_btn.pack(side=tk.LEFT, padx=5)
                    
                    # Armazenar dados originais para filtros
                    self.all_fines = fines
                    
                    # Cards de estatísticas
                    self.create_fines_stats(fines)
                    
                    # Tabela de multas
                    self.create_fines_table(fines)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar multas: {str(e)}")
            
    def create_fines_stats(self, fines):
        # Calcular estatísticas
        total_fines = len(fines)
        pending_fines = len([f for f in fines if f['status'] == 'pending'])
        overdue_fines = len([f for f in fines if f['status'] == 'overdue'])
        paid_fines = len([f for f in fines if f['status'] == 'paid'])
        total_amount = sum(f['amount'] for f in fines if f['amount'])
        pending_amount = sum(f['amount'] for f in fines if f['status'] == 'pending' and f['amount'])
        overdue_amount = sum(f['amount'] for f in fines if f['status'] == 'overdue' and f['amount'])
        
        # Frame de estatísticas
        stats_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Cards
        cards_data = [
            ("💰 Total Multas", total_fines, format_currency_brl(total_amount), self.styles.colors['primary']),
            ("🔴 Pendentes", pending_fines, format_currency_brl(pending_amount), self.styles.colors['warning']),
            ("⚠️ Vencidas", overdue_fines, format_currency_brl(overdue_amount), self.styles.colors['accent']),
            ("✅ Pagas", paid_fines, f"{(paid_fines/total_fines*100):.1f}%" if total_fines > 0 else "0%", self.styles.colors['success'])
        ]
        
        for i, (title, value, extra, color) in enumerate(cards_data):
            card = self.create_fines_stat_card(stats_frame, title, value, extra, color)
            card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
            
    def create_fines_stat_card(self, parent, title, value, extra, color):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header
        header = tk.Frame(card, bg=color, height=40)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                              font=self.styles.fonts['normal'])
        title_label.pack(pady=8)
        
        # Content
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        value_label = tk.Label(content, text=str(value), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', 24, 'bold'))
        value_label.pack(anchor='w')
        
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small'])
        extra_label.pack(anchor='w', pady=(2, 0))
        
        return card
        
    def create_fines_table(self, fines):
        # Frame da tabela
        table_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview para multas
        columns = ('ID', 'Valor', 'Status', 'Data', 'Vencimento', 'Local', 'Descrição', 'Placa', 'Cidadão')
        self.fines_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Fines.Treeview')
        
        # Configurar colunas
        col_widths = {
            'ID': 50, 'Valor': 80, 'Status': 80, 'Data': 80, 'Vencimento': 80,
            'Local': 100, 'Descrição': 120, 'Placa': 80, 'Cidadão': 120
        }
        
        for col in columns:
            self.fines_tree.heading(col, text=col)
            self.fines_tree.column(col, width=col_widths.get(col, 100), minwidth=60)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.fines_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.fines_tree.xview)
        self.fines_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.fines_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Inserir dados
        for i, fine in enumerate(fines):
            try:
                status_map = {
                    'pending': '🔴 Pendente',
                    'paid': '✅ Paga',
                    'overdue': '⚠️ Vencida',
                    'cancelled': '❌ Cancelada'
                }
                
                display_status = status_map.get(fine['status'], fine['status'])
                
                # Formatar valores
                amount = format_currency_brl(fine['amount']) if fine['amount'] and fine['amount'] > 0 else "R$ 0,00"
                created_at = fine['created_at'].strftime('%d/%m/%Y') if fine['created_at'] else "N/A"
                due_date = fine['due_date'].strftime('%d/%m/%Y') if fine['due_date'] else "N/A"
                incident_location = fine.get('incident_location', 'N/A')
                incident_description = fine.get('incident_description', 'N/A')
                if incident_description and len(incident_description) > 30:
                    incident_description = incident_description[:27] + "..."
                license_plate = fine.get('license_plate', 'N/A')
                
                # Formatar nome do cidadão
                citizen_name = "N/A"
                if fine.get('first_name') and fine.get('last_name'):
                    citizen_name = f"{fine['first_name']} {fine['last_name']}"
                
                tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                self.fines_tree.insert('', tk.END, values=(
                    fine['id'],
                    amount,
                    display_status,
                    created_at,
                    due_date,
                    incident_location,
                    incident_description[:30] + '...' if incident_description else 'N/A',
                    license_plate,
                    citizen_name
                ), tags=(tag,))
            except Exception as e:
                print(f"Erro ao processar multa {i}: {e}")
                continue
            
        # Frame de informações e ações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"💰 {len(fines)} multas cadastradas",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botão de excluir multa selecionada
        delete_btn = tk.Button(info_frame, text="🗑️ Excluir Selecionado", command=self.delete_selected_fine,
                              bg=self.styles.colors['danger'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=10, pady=8, cursor='hand2')
        delete_btn.pack(side=tk.RIGHT, padx=(0, 10))
                
    def delete_selected_fine(self):
        """Exclui a multa selecionada na tabela"""
        if not hasattr(self, 'fines_tree'):
            messagebox.showwarning("Aviso", "Nenhuma tabela de multas disponível!")
            return
            
        selection = self.fines_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma multa para excluir!")
            return
            
        # Obter dados da multa selecionada
        item = self.fines_tree.item(selection[0])
        values = item['values']
        fine_id = values[0]
        amount = values[1]
        status = values[2]
        
        # Confirmar exclusão
        result = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir a multa:\n\nID: {fine_id} - Valor: {amount} - Status: {status}\n\n"
            "Esta ação não poderá ser desfeita!",
            icon='warning'
        )
        
        if result:
            try:
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Verificar se há pagamentos registrados
                        cur.execute("SELECT COUNT(*) FROM fine_payment WHERE fine_id = %s", (fine_id,))
                        payments = cur.fetchone()[0]
                        
                        if payments > 0:
                            messagebox.showerror("Erro", f"Não é possível excluir multa com {payments} pagamento(s) registrado(s)!")
                            return
                        
                        # Excluir multa (cascade deve excluir registros relacionados)
                        cur.execute("DELETE FROM fine WHERE id = %s", (fine_id,))
                        conn.commit()
                        
                        messagebox.showinfo("Sucesso", f"Multa ID: {fine_id} excluída com sucesso!")
                        self.show_fines()  # Atualizar lista
                        
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir multa: {str(e)}")
        
    def filter_fines(self):
        """Filtra multas baseado nos critérios selecionados"""
        if not hasattr(self, 'all_fines'):
            return
            
        filtered_fines = self.all_fines.copy()
        
        # Filtro por status
        status_filter = self.fine_status_var.get()
        if status_filter == "Pendentes":
            filtered_fines = [f for f in filtered_fines if f['status'] == 'pending']
        elif status_filter == "Pagas":
            filtered_fines = [f for f in filtered_fines if f['status'] == 'paid']
        elif status_filter == "Vencidas":
            from datetime import datetime
            now = datetime.now().date()  # Converter para date
            filtered_fines = [
                f for f in filtered_fines 
                if f['due_date'] and f['due_date'] < now and f['status'] != 'paid'
            ]
        
        # Filtro por valor mínimo
        amount_filter = self.fine_amount_var.get().strip()
        if amount_filter:
            try:
                # Converter valor monetário brasileiro (ex: "100,00") para float
                amount_clean = amount_filter.replace('R$', '').replace('.', '').replace(',', '.')
                min_amount = float(amount_clean)
                filtered_fines = [f for f in filtered_fines if f['amount'] and f['amount'] >= min_amount]
            except ValueError:
                pass
        
        # Filtro por placa
        plate_filter = self.fine_plate_var.get().upper().strip()
        if plate_filter:
            filtered_fines = [
                f for f in filtered_fines 
                if f['license_plate'] and plate_filter in f['license_plate'].upper()
            ]
        
        # Filtro por período
        period_filter = self.fine_period_var.get()
        if period_filter != "Todos":
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if period_filter == "Hoje":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered_fines = [
                    f for f in filtered_fines 
                    if f['created_at'] and f['created_at'].date() >= start_date.date()
                ]
            elif period_filter == "Esta Semana":
                start_date = now - timedelta(days=7)
                filtered_fines = [
                    f for f in filtered_fines 
                    if f['created_at'] and f['created_at'] >= start_date
                ]
            elif period_filter == "Este Mês":
                start_date = now - timedelta(days=30)
                filtered_fines = [
                    f for f in filtered_fines 
                    if f['created_at'] and f['created_at'] >= start_date
                ]
            elif period_filter == "Vencidas":
                now_date = now.date()  # Converter para date
                filtered_fines = [
                    f for f in filtered_fines 
                    if f['due_date'] and f['due_date'] < now_date and f['status'] != 'paid'
                ]
        
        # Atualizar tabela com dados filtrados
        self.update_fines_table(filtered_fines)
        
    def update_fines_table(self, fines):
        """Atualiza apenas a tabela de multas sem recarregar tudo"""
        # Limpar tabela atual
        for item in self.fines_tree.get_children():
            self.fines_tree.delete(item)
        
        # Inserir dados filtrados
        for fine in fines:
            status_map = {
                'pending': '🔴 Pendente',
                'paid': '✅ Paga',
                'overdue': '⚠️ Vencida'
            }
            
            # Verificar se multa pendente está vencida
            display_status = status_map.get(fine['status'], fine['status'])
            if fine['status'] == 'pending' and fine['due_date']:
                from datetime import date
                if fine['due_date'] < date.today():
                    display_status = '⚠️ Vencida'
            
            # Formatar valores
            amount = format_currency_brl(fine['amount']) if fine['amount'] else "R$ 0,00"
            due_date = fine['due_date'].strftime('%d/%m/%Y') if fine['due_date'] else "N/A"
            
            self.fines_tree.insert('', tk.END, values=(
                fine['id'],
                amount,
                display_status,
                fine['created_at'].strftime('%d/%m/%Y') if fine['created_at'] else "N/A",
                due_date,
                fine.get('incident_location', 'N/A'),
                fine.get('incident_description', 'N/A')[:30] + '...' if fine.get('incident_description') else 'N/A',
                fine.get('license_plate', 'N/A')
            ))
        
        # Atualizar contador
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "multas registradas" in child.cget("text"):
                        child.config(text=f"💰 {len(fines)} multas registradas ({len(self.all_fines)} total)")
                        break
        
    def show_dashboard(self):
        """Dashboard interativo com gráficos inline e exportação Excel"""
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
        
        try:
            # Importar bibliotecas para gráficos inline
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.subplots import make_subplots
            import pandas as pd
            import numpy as np
            import tempfile
            import os
            from PIL import Image, ImageTk
            
            # Header estilizado
            header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
            header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
            
            title_label = tk.Label(header_frame, text="📊 Dashboard Interativo", 
                                  bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                  font=self.styles.fonts['title'])
            title_label.pack(side=tk.LEFT, padx=20, pady=15)
            
            # Frame de filtros modernos
            filters_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
            filters_frame.pack(side=tk.RIGHT, padx=20, pady=15)
            
            # Filtros dropdown padrão do Tkinter
            tk.Label(filters_frame, text="Período:", bg=self.styles.colors['card'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(side=tk.LEFT, padx=(0, 5))
            
            # Criar period_var apenas se não existir
            if not hasattr(self, 'period_var'):
                self.period_var = tk.StringVar(value="Últimos 7 dias")
            
            period_combo = ttk.Combobox(filters_frame, textvariable=self.period_var, 
                                      values=["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todo o período"],
                                      state="readonly", width=15)
            period_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            # Botões de ação
            refresh_btn = tk.Button(filters_frame, text="🔄 Atualizar", 
                                  command=lambda: self.update_dashboard(self.period_var.get()),
                                  bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                  font=self.styles.fonts['button'], relief='flat',
                                  padx=15, pady=8, cursor='hand2')
            refresh_btn.pack(side=tk.LEFT)
            
            export_excel_btn = tk.Button(filters_frame, text="📊 Exportar Dados", 
                                       command=lambda: self.export_dashboard_excel(),
                                       bg=self.styles.colors['primary'], fg=self.styles.colors['white'],
                                       font=self.styles.fonts['button'], relief='flat',
                                       padx=15, pady=8, cursor='hand2')
            export_excel_btn.pack(side=tk.LEFT, padx=(5, 0))
            
           # Frame principal para gráficos inline
            charts_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
            charts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Criar gráficos Plotly inline
            self.create_plotly_html_inline(charts_frame, self.period_var.get())
            
            # Marcar que o dashboard foi inicializado
            self._dashboard_initialized = True
            
        except ImportError as e:
            messagebox.showerror("Erro", f"Bibliotecas necessárias não encontradas!\n\nInstale:\npip install plotly Pillow ipywidgets xlsxwriter\n\nErro: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dashboard: {str(e)}")
    
    def get_dashboard_data(self, period):
        """Carrega dados do banco para o dashboard baseado no período"""
        try:
            import psycopg2 as psy
            import psycopg2.extras
            
            # Converter período em dias para o SQL
            period_days = {
                "Últimos 7 dias": 7,
                "Últimos 30 dias": 30,
                "Últimos 90 dias": 90,
                "Todo o período": 365  # Aproximadamente 1 ano
            }
            
            days = period_days.get(period, 30)
            
            # Carregar dados do banco com filtro de período
            with psy.connect(self.get_connection_string()) as conn:
                # Configurar row_factory para retornar dicionários
                conn.cursor_factory = psycopg2.extras.RealDictCursor
                
                with conn.cursor() as cur:
                    
                    # Dados para gráficos
                    data = {}
                    
                    # 1. Evolução de incidentes (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            WHERE occurred_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY DATE(occurred_at)
                            ORDER BY date
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            WHERE occurred_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY DATE(occurred_at)
                            ORDER BY date
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            WHERE occurred_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY DATE(occurred_at)
                            ORDER BY date
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT DATE_TRUNC('month', occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            GROUP BY DATE_TRUNC('month', occurred_at)
                            ORDER BY date
                        """)
                    incident_timeline = cur.fetchall()
                    data['incident_timeline'] = incident_timeline
                    
                    # 2. Multas por status (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY status
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY status
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY status
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            GROUP BY status
                        """)
                    fines_by_status = cur.fetchall()
                    data['fines_by_status'] = fines_by_status
                    
                    # 3. Veículos por status (sem filtro de período - dados atuais)
                    cur.execute("""
                        SELECT CASE WHEN allowed = TRUE THEN 'Ativos' ELSE 'Bloqueados' END as status, 
                               COUNT(*) as count
                        FROM vehicle_active 
                        GROUP BY allowed
                    """)
                    vehicles_by_status = cur.fetchall()
                    data['vehicles_by_status'] = vehicles_by_status
                    
                    # 4. Sensores por tipo (dados atuais)
                    cur.execute("""
                        SELECT type, COUNT(*) as count, 
                               COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                        FROM sensor_active 
                        GROUP BY type
                        ORDER BY count DESC
                    """)
                    sensors_by_type = cur.fetchall()
                    data['sensors_by_type'] = sensors_by_type
                    
                    # 5. Crescimento de usuários (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT DATE(created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY DATE(created_at)
                            ORDER BY date
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT DATE_TRUNC('week', created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY DATE_TRUNC('week', created_at)
                            ORDER BY date
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT DATE_TRUNC('week', created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY DATE_TRUNC('week', created_at)
                            ORDER BY date
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT DATE_TRUNC('month', created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            GROUP BY DATE_TRUNC('month', created_at)
                            ORDER BY date
                        """)
                    user_growth = cur.fetchall()
                    data['user_growth'] = user_growth
            
            return data
            
        except Exception as e:
            print(f"Erro ao carregar dados do dashboard: {e}")
            # Retornar dados vazios em caso de erro
            return {
                'incident_timeline': [],
                'fines_by_status': [],
                'vehicles_by_status': [],
                'sensors_by_type': [],
                'user_growth': []
            }

    def create_plotly_html_inline(self, parent, period):
        """Cria gráficos Plotly inline usando HTML embutido no Tkinter"""
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.subplots import make_subplots
            import pandas as pd
            import numpy as np
            import tempfile
            import os
            from PIL import Image, ImageTk
            import webbrowser
            import threading
            import json
            
            # Carregar dados do banco
            data = self.get_dashboard_data(period)
            
            # Criar dashboard completo
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(f'Incidentes ({period})', f'Multas por Status ({period})', 
                                f'Veículos por Status ({period})', f'Sensores por Tipo ({period})',
                                f'Crescimento de Usuários ({period})', f'Resumo Financeiro ({period})'),
                specs=[[{"secondary_y": False}, {"type": "pie"}],
                       [{"secondary_y": False}, {"type": "bar"}],
                       [{"secondary_y": False}, {"type": "indicator"}]],
                vertical_spacing=0.08,
                horizontal_spacing=0.05
            )
            
            # Adicionar traces
            if data['incident_timeline']:
                df_incidents = pd.DataFrame(data['incident_timeline'])
                df_incidents['incidents'] = df_incidents['incidents'].astype(int)
                df_incidents['date'] = pd.to_datetime(df_incidents['date']).dt.strftime('%Y-%m-%d')
                
                fig.add_trace(
                    go.Scatter(x=df_incidents['date'], y=df_incidents['incidents'],
                              mode='lines+markers', name='Incidentes',
                              line=dict(color='#FF6B6B', width=3),
                              marker=dict(size=8)),
                    row=1, col=1
                )
            
            if data['fines_by_status']:
                df_fines = pd.DataFrame(data['fines_by_status'])
                status_map = {'pending': 'Pendentes', 'paid': 'Pagas', 'overdue': 'Vencidas', 'cancelled': 'Canceladas'}
                df_fines['status_display'] = df_fines['status'].map(status_map)
                df_fines['count'] = df_fines['count'].astype(int)
                
                fig.add_trace(
                    go.Pie(labels=df_fines['status_display'], values=df_fines['count'],
                           name="Multas", hole=0.4,
                           marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']),
                    row=1, col=2
                )
            
            if data['vehicles_by_status']:
                df_vehicles = pd.DataFrame(data['vehicles_by_status'])
                df_vehicles['count'] = df_vehicles['count'].astype(int)
                
                fig.add_trace(
                    go.Bar(x=df_vehicles['status'], y=df_vehicles['count'],
                           name='Veículos', marker_color='#4ECDC4'),
                    row=2, col=1
                )
            
            if data['sensors_by_type']:
                df_sensors = pd.DataFrame(data['sensors_by_type'])
                df_sensors['count'] = df_sensors['count'].astype(int)
                
                fig.add_trace(
                    go.Bar(y=df_sensors['type'], x=df_sensors['count'],
                           name='Sensores', orientation='h',
                           marker_color='#45B7D1'),
                    row=2, col=2
                )
            
            if data['user_growth']:
                df_users = pd.DataFrame(data['user_growth'])
                df_users['new_users'] = df_users['new_users'].astype(int)
                df_users['date'] = pd.to_datetime(df_users['date']).dt.strftime('%Y-%m-%d')
                
                fig.add_trace(
                    go.Scatter(x=df_users['date'], y=df_users['new_users'],
                              mode='lines+markers', name='Novos Usuários',
                              line=dict(color='#96CEB4', width=3),
                              marker=dict(size=8)),
                    row=3, col=1
                )
            
            if data['fines_by_status']:
                df_fines = pd.DataFrame(data['fines_by_status'])
                df_fines['total_amount'] = pd.to_numeric(df_fines['total_amount'], errors='coerce').fillna(0).astype(float)
                
                total_amount = float(df_fines['total_amount'].sum())
                pending_amount = float(df_fines[df_fines['status'] == 'pending']['total_amount'].sum() if len(df_fines[df_fines['status'] == 'pending']) > 0 else 0)
                
                fig.add_trace(
                    go.Indicator(
                        mode="number+gauge+delta",
                        value=total_amount,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Valor Total de Multas"},
                        delta={'reference': pending_amount},
                        gauge={
                            'axis': {'range': [None, total_amount * 1.2] if total_amount > 0 else [0, 100]},
                            'bar': {'color': "#FF6B6B"},
                            'steps': [
                                {'range': [0, total_amount * 0.5] if total_amount > 0 else [0, 50], 'color': "lightgray"},
                                {'range': [total_amount * 0.5, total_amount] if total_amount > 0 else [50, 100], 'color': "gray"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': (total_amount * 0.9) if total_amount > 0 else 90
                            }
                        }
                    ),
                    row=3, col=2
                )
            
            # Configurar layout
            fig.update_layout(
                title_text=f"📊 SmartCityOS Dashboard<br>Período: {period}",
                title_x=0.5,
                title_y=0.98,
                title_font_size=18,
                height=800,
                showlegend=True,
                template="plotly_white",
                font=dict(size=10),
                margin=dict(l=50, r=50, t=100, b=50),
                hovermode='closest'
            )
            
            # Criar HTML inline
            def create_inline_html():
                try:
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>SmartCityOS Dashboard</title>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <style>
                            body {{
                                margin: 0;
                                padding: 5px;
                                font-family: Arial, sans-serif;
                                background-color: {self.styles.colors.get('background', '#f5f5f5')};
                                overflow: auto;
                            }}
                            #plotly-div {{
                                width: 100%;
                                height: 750px;
                                border-radius: 8px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            }}
                        </style>
                    </head>
                    <body>
                        <div id="plotly-div"></div>
                        <script>
                            var plotlyData = {fig.to_json()};
                            Plotly.newPlot('plotly-div', plotlyData.data, plotlyData.layout, {{
                                responsive: true,
                                displayModeBar: true,
                                displaylogo: false,
                                modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                                toImageButtonOptions: {{
                                    format: 'png',
                                    filename: 'smartcityos_dashboard',
                                    height: 800,
                                    width: 1200,
                                    scale: 2
                                }}
                            }});
                            
                            window.addEventListener('resize', function() {{
                                Plotly.Plots.resize('plotly-div');
                            }});
                        </script>
                    </body>
                    </html>
                    """
                    
                    temp_path = tempfile.mktemp(suffix='.html')
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    return temp_path
                    
                except Exception as e:
                    print(f"Erro ao criar HTML: {e}")
                    return None
            
            # Tentar usar tkinterweb para HTML inline
            try:
                from tkinterweb import HtmlFrame
                
                # Criar frame HTML
                html_frame = HtmlFrame(parent, messages_enabled=False)
                html_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Carregar HTML
                temp_path = create_inline_html()
                if temp_path:
                    html_frame.load_file(temp_path)
                    
            except ImportError:
                # Fallback: criar frame com botão para abrir no navegador
                control_frame = tk.Frame(parent, bg=self.styles.colors.get('card', '#ffffff'))
                control_frame.pack(fill=tk.X, padx=15, pady=10)
                
                def open_interactive():
                    temp_path = create_inline_html()
                    if temp_path:
                        webbrowser.open(f'file://{temp_path}')
                
                tk.Button(control_frame, 
                        text="🌐 Abrir Dashboard Interativo",
                        command=open_interactive,
                        bg=self.styles.colors.get('primary', '#007bff'), 
                        fg='white',
                        font=('Arial', 10, 'bold'), 
                        relief='flat',
                        padx=20, pady=10, cursor='hand2').pack(pady=5)
                
                # Criar preview estático
                img_bytes = fig.to_image(format="png", width=1000, height=800, scale=1.5)
                img = Image.open(io.BytesIO(img_bytes))
                img = img.resize((850, 680), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(img)
                
                preview_frame = tk.Frame(parent, bg=self.styles.colors.get('card', '#ffffff'))
                preview_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
                
                tk.Label(preview_frame, text="📊 Preview do Dashboard", 
                        bg=self.styles.colors.get('card', '#ffffff'), 
                        fg=self.styles.colors.get('text_secondary', '#666666'),
                        font=('Arial', 10)).pack(pady=(5, 0))
                
                img_label = tk.Label(preview_frame, image=photo, bg=self.styles.colors.get('card', '#ffffff'))
                img_label.image = photo
                img_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Armazenar figura e dados
            self.current_figure = fig
            self.current_data = data
                
        except Exception as e:
            print(f"Erro ao criar gráficos: {e}")
            error_frame = tk.Frame(parent, bg=self.styles.colors.get('card', '#ffffff'))
            error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            tk.Label(error_frame, 
                    text="❌ Erro ao carregar gráficos\n\nVerifique os dados e tente novamente.",
                    bg=self.styles.colors.get('card', '#ffffff'), 
                    fg=self.styles.colors.get('text_primary', '#333333'),
                    font=('Arial', 12), justify=tk.CENTER).pack(expand=True)

    def create_plotly_charts(self, parent, period):
        """Cria gráficos inline com Plotly no Tkinter"""
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.subplots import make_subplots
            import pandas as pd
            import numpy as np
            import tempfile
            import os
            from PIL import Image, ImageTk
            
            # Converter período em dias para o SQL
            period_days = {
                "Últimos 7 dias": 7,
                "Últimos 30 dias": 30,
                "Últimos 90 dias": 90,
                "Todo o período": 365  # Aproximadamente 1 ano
            }
            
            days = period_days.get(period, 30)
            
            # Carregar dados do banco com filtro de período
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    
                    # Dados para gráficos
                    data = {}
                    
                    # 1. Evolução de incidentes (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            WHERE occurred_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY DATE(occurred_at)
                            ORDER BY date
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            WHERE occurred_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY DATE(occurred_at)
                            ORDER BY date
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            WHERE occurred_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY DATE(occurred_at)
                            ORDER BY date
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT DATE_TRUNC('month', occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            GROUP BY DATE_TRUNC('month', occurred_at)
                            ORDER BY date
                        """)
                    incident_timeline = cur.fetchall()
                    data['incident_timeline'] = incident_timeline
                    
                    # 2. Multas por status (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY status
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY status
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY status
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            GROUP BY status
                        """)
                    fines_by_status = cur.fetchall()
                    data['fines_by_status'] = fines_by_status
                    
                    # 3. Veículos por status (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT CASE WHEN allowed = TRUE THEN 'Ativos' ELSE 'Bloqueados' END as status, 
                                   COUNT(*) as count
                            FROM vehicle_active 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY allowed
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT CASE WHEN allowed = TRUE THEN 'Ativos' ELSE 'Bloqueados' END as status, 
                                   COUNT(*) as count
                            FROM vehicle_active 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY allowed
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT CASE WHEN allowed = TRUE THEN 'Ativos' ELSE 'Bloqueados' END as status, 
                                   COUNT(*) as count
                            FROM vehicle_active 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY allowed
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT CASE WHEN allowed = TRUE THEN 'Ativos' ELSE 'Bloqueados' END as status, 
                                   COUNT(*) as count
                            FROM vehicle_active 
                            GROUP BY allowed
                        """)
                    vehicles_by_status = cur.fetchall()
                    data['vehicles_by_status'] = vehicles_by_status
                    
                    # 4. Sensores por tipo (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT type, COUNT(*) as count, 
                                   COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                            FROM sensor_active 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY type
                            ORDER BY count DESC
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT type, COUNT(*) as count, 
                                   COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                            FROM sensor_active 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY type
                            ORDER BY count DESC
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT type, COUNT(*) as count, 
                                   COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                            FROM sensor_active 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY type
                            ORDER BY count DESC
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT type, COUNT(*) as count, 
                                   COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                            FROM sensor_active 
                            GROUP BY type
                            ORDER BY count DESC
                        """)
                    sensors_by_type = cur.fetchall()
                    data['sensors_by_type'] = sensors_by_type
                    
                    # 5. Crescimento de usuários (com filtro de período específico)
                    if days == 7:
                        cur.execute("""
                            SELECT DATE_TRUNC('day', created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY DATE_TRUNC('day', created_at)
                            ORDER BY date
                        """)
                    elif days == 30:
                        cur.execute("""
                            SELECT DATE_TRUNC('day', created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY DATE_TRUNC('day', created_at)
                            ORDER BY date
                        """)
                    elif days == 90:
                        cur.execute("""
                            SELECT DATE_TRUNC('day', created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
                            GROUP BY DATE_TRUNC('day', created_at)
                            ORDER BY date
                        """)
                    else:  # Todo o período
                        cur.execute("""
                            SELECT DATE_TRUNC('month', created_at) as date, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '1 year'
                            GROUP BY DATE_TRUNC('month', created_at)
                            ORDER BY date
                        """)
                    user_growth = cur.fetchall()
                    data['user_growth'] = user_growth
            
            # Criar subplots Plotly
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(f'Incidentes ({period})', f'Multas por Status ({period})', 
                                f'Veículos por Status ({period})', f'Sensores por Tipo ({period})',
                                f'Crescimento de Usuários ({period})', f'Resumo Financeiro ({period})'),
                specs=[[{"secondary_y": False}, {"type": "pie"}],
                       [{"secondary_y": False}, {"type": "bar"}],
                       [{"secondary_y": False}, {"type": "indicator"}]],
                vertical_spacing=0.08,
                horizontal_spacing=0.05
            )
            
            # 1. Gráfico de linha - Incidentes
            if data['incident_timeline']:
                df_incidents = pd.DataFrame(data['incident_timeline'])
                df_incidents['incidents'] = df_incidents['incidents'].astype(int)
                df_incidents['date'] = pd.to_datetime(df_incidents['date']).dt.strftime('%Y-%m-%d')
                
                fig.add_trace(
                    go.Scatter(x=df_incidents['date'], y=df_incidents['incidents'],
                              mode='lines+markers', name='Incidentes',
                              line=dict(color='#FF6B6B', width=3),
                              marker=dict(size=8)),
                    row=1, col=1
                )
            
            # 2. Gráfico de pizza - Multas por status
            if data['fines_by_status']:
                df_fines = pd.DataFrame(data['fines_by_status'])
                status_map = {'pending': 'Pendentes', 'paid': 'Pagas', 'overdue': 'Vencidas', 'cancelled': 'Canceladas'}
                df_fines['status_display'] = df_fines['status'].map(status_map)
                df_fines['count'] = df_fines['count'].astype(int)
                
                fig.add_trace(
                    go.Pie(labels=df_fines['status_display'], values=df_fines['count'],
                           name="Multas", hole=0.4,
                           marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']),
                    row=1, col=2
                )
            
            # 3. Gráfico de barras - Veículos
            if data['vehicles_by_status']:
                df_vehicles = pd.DataFrame(data['vehicles_by_status'])
                df_vehicles['count'] = df_vehicles['count'].astype(int)
                
                fig.add_trace(
                    go.Bar(x=df_vehicles['status'], y=df_vehicles['count'],
                           name='Veículos', marker_color='#4ECDC4'),
                    row=2, col=1
                )
            
            # 4. Gráfico de barras horizontais - Sensores
            if data['sensors_by_type']:
                df_sensors = pd.DataFrame(data['sensors_by_type'])
                df_sensors['count'] = df_sensors['count'].astype(int)
                
                fig.add_trace(
                    go.Bar(y=df_sensors['type'], x=df_sensors['count'],
                           name='Sensores', orientation='h',
                           marker_color='#45B7D1'),
                    row=2, col=2
                )
            
            # 5. Gráfico de linha - Crescimento de usuários
            if data['user_growth']:
                df_users = pd.DataFrame(data['user_growth'])
                df_users['new_users'] = df_users['new_users'].astype(int)
                df_users['date'] = pd.to_datetime(df_users['date']).dt.strftime('%Y-%m-%d')
                
                fig.add_trace(
                    go.Scatter(x=df_users['date'], y=df_users['new_users'],
                              mode='lines+markers', name='Usuários',
                              line=dict(color='#FFA07A', width=3),
                              marker=dict(size=8)),
                    row=3, col=1
                )
            
            # 6. Indicador financeiro
            if data['fines_by_status']:
                df_fines = pd.DataFrame(data['fines_by_status'])
                df_fines['total_amount'] = pd.to_numeric(df_fines['total_amount'], errors='coerce').fillna(0).astype(float)
                
                total_amount = float(df_fines['total_amount'].sum())
                pending_amount = float(df_fines[df_fines['status'] == 'pending']['total_amount'].sum() if len(df_fines[df_fines['status'] == 'pending']) > 0 else 0)
                
                fig.add_trace(
                    go.Indicator(
                        mode="number+gauge+delta",
                        value=total_amount,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Valor Total de Multas"},
                        delta={'reference': pending_amount},
                        gauge={
                            'axis': {'range': [None, total_amount * 1.2] if total_amount > 0 else [0, 100]},
                            'bar': {'color': "#FF6B6B"},
                            'steps': [
                                {'range': [0, total_amount * 0.5] if total_amount > 0 else [0, 50], 'color': "lightgray"},
                                {'range': [total_amount * 0.5, total_amount] if total_amount > 0 else [50, 100], 'color': "gray"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': (total_amount * 0.9) if total_amount > 0 else 90
                            }
                        }
                    ),
                    row=3, col=2
                )
            
            # Layout do gráfico
            fig.update_layout(
                title_text=f"📊 SmartCityOS - Dashboard Interativo<br>Período: {period}",
                title_x=0.5,
                title_font_size=20,
                height=1200,
                showlegend=True,
                template="plotly_white",
                font=dict(size=10)
            )
            
            # Converter para imagem e exibir no Tkinter
            try:
                # Salvar como imagem temporária com nome único
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                temp_filename = f"dashboard_{unique_id}.png"
                temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
                
                # Salvar imagem
                fig.write_image(temp_path, width=1200, height=800, scale=2)
                
                # Carregar imagem
                img = Image.open(temp_path)
                img = img.resize((500, 333), Image.Resampling.LANCZOS)
                
                # Converter para PhotoImage
                photo = ImageTk.PhotoImage(img)
                
                # Exibir no Tkinter
                img_label = tk.Label(parent, image=photo, bg=self.styles.colors['background'])
                img_label.image = photo  # Manter referência para não ser coletado pelo GC
                img_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Adicionar botão para abrir versão interativa
                interactive_frame = tk.Frame(parent, bg=self.styles.colors['background'])
                interactive_frame.pack(fill=tk.X, pady=(0, 10))
                
                # interactive_btn = tk.Button(interactive_frame, 
                #                          text="🌐 Abrir Versão Interativa (Navegador)",
                #                          command=lambda: self.open_interactive_dashboard(),
                #                          bg=self.styles.colors['primary'], 
                #                          fg=self.styles.colors['white'],
                #                          font=self.styles.fonts['button'], 
                #                          relief='flat',
                #                          padx=20, pady=10, cursor='hand2')
                # interactive_btn.pack()
                
                # Armazenar caminho para limpeza posterior
                if not hasattr(self, 'temp_files'):
                    self.temp_files = []
                self.temp_files.append(temp_path)
                
                # Limpar arquivos antigos periodicamente
                self.cleanup_temp_files()
                
            except Exception as img_error:
                print(f"Erro ao converter imagem: {img_error}")
                # Fallback: mostrar botão para abrir no navegador
                fallback_frame = tk.Frame(parent, bg=self.styles.colors['card'])
                fallback_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                tk.Label(fallback_frame, 
                        text="📊 Dashboard Plotly Criado!\n\n" +
                             "Clique abaixo para abrir a versão interativa no navegador.\n" +
                             "Você poderá usar zoom, hover e filtros interativos.",
                        bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                        font=self.styles.fonts['normal'], justify='center').pack(expand=True)
                
                interactive_btn = tk.Button(fallback_frame, 
                                         text="🌐 Abrir Dashboard Interativo",
                                         command=lambda: self.open_interactive_dashboard(),
                                         bg=self.styles.colors['primary'], 
                                         fg=self.styles.colors['white'],
                                         font=self.styles.fonts['button'], 
                                         relief='flat',
                                         padx=20, pady=10, cursor='hand2')
                interactive_btn.pack(pady=20)
            
            # Armazenar figura e dados para exportação
            self.current_figure = fig
            self.current_data = data
            
        except Exception as e:
            print(f"Erro no display_dashboard: {e}")
            import traceback
            print(f"Traceback completo: {traceback.format_exc()}")


    def cleanup_temp_files(self):
        """Limpa arquivos temporários antigos"""
        try:
            import os
            import glob
            import tempfile
            
            # Manter apenas os arquivos mais recentes
            temp_pattern = os.path.join(tempfile.gettempdir(), "dashboard_*.png")
            existing_files = glob.glob(temp_pattern)
            
            # Se tiver mais de 5 arquivos, remover os mais antigos
            if len(existing_files) > 5:
                existing_files.sort(key=os.path.getctime)
                for old_file in existing_files[:-5]:  # Manter os 5 mais recentes
                    try:
                        os.unlink(old_file)
                    except:
                        pass  # Ignorar erros ao remover
                        
        except Exception as e:
            print(f"Erro ao limpar arquivos temporários: {e}")
    
    def open_interactive_dashboard(self):
        """Abre o dashboard interativo no navegador"""
        try:
            import tempfile
            import webbrowser
            
            if not hasattr(self, 'current_figure'):
                messagebox.showwarning("Aviso", "Nenhum dashboard para exibir!")
                return
            
            # Salvar como HTML temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
                self.current_figure.write_html(tmp_file.name, include_plotlyjs='cdn')
                
                # Abrir no navegador
                webbrowser.open(f'file://{tmp_file.name}')
                
                messagebox.showinfo("Sucesso", "Dashboard interativo aberto no navegador!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir dashboard interativo: {str(e)}")
    
    def export_dashboard_excel(self):
        """Exporta dashboard para Excel com formatação profissional e múltiplas abas"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import xlsxwriter
            from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
            
            if not hasattr(self, 'current_data'):
                messagebox.showwarning("Aviso", "Nenhum dado para exportar. Gere o dashboard primeiro!")
                return
            
            # File dialog para salvar
            file_path = filedialog.asksaveasfilename(
                title="Exportar Relatório SmartCityOS",
                defaultextension=".xlsx",
                filetypes=[("Arquivo Excel (*.xlsx)", "*.xlsx"), ("Todos os Arquivos", "*.*")],
                initialfile=f"relatorio_smartcity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            # Criar Excel writer com formatação avançada
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # Definir estilos profissionais
                header_format = workbook.add_format({
                    'bold': True,
                    'font_size': 12,
                    'bg_color': '#2E86AB',
                    'font_color': 'white',
                    'border': 1,
                    'border_color': '#000000',
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                title_format = workbook.add_format({
                    'bold': True,
                    'font_size': 16,
                    'bg_color': '#1E5F74',
                    'font_color': 'white',
                    'border': 1,
                    'border_color': '#000000',
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                subtitle_format = workbook.add_format({
                    'bold': True,
                    'font_size': 11,
                    'bg_color': '#F4F4F4',
                    'font_color': '#333333',
                    'border': 1,
                    'border_color': '#000000',
                    'align': 'left',
                    'valign': 'vcenter'
                })
                
                data_format = workbook.add_format({
                    'font_size': 10,
                    'bg_color': 'white',
                    'font_color': '#333333',
                    'border': 1,
                    'border_color': '#D0D0D0',
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                currency_format = workbook.add_format({
                    'font_size': 10,
                    'bg_color': 'white',
                    'font_color': '#2E7D32',
                    'border': 1,
                    'border_color': '#D0D0D0',
                    'align': 'right',
                    'valign': 'vcenter',
                    'num_format': 'R$ #,##0.00'
                })
                
                number_format = workbook.add_format({
                    'font_size': 10,
                    'bg_color': 'white',
                    'font_color': '#333333',
                    'border': 1,
                    'border_color': '#D0D0D0',
                    'align': 'right',
                    'valign': 'vcenter',
                    'num_format': '#,##0'
                })
                
                # 1. ABA: CAPA DO RELATÓRIO
                cover_worksheet = workbook.add_worksheet('📊 Capa')
                cover_worksheet.set_column('A:A', 50)
                cover_worksheet.set_column('B:B', 30)
                
                # Título principal
                cover_worksheet.merge_range('A1:B1', '🏙️ SmartCityOS - Relatório Completo', title_format)
                cover_worksheet.merge_range('A2:B2', f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', subtitle_format)
                cover_worksheet.merge_range('A3:B3', f'Período: {self.period_var.get() if hasattr(self, "period_var") else "Todos"}', subtitle_format)
                
                # Estatísticas principais
                row = 5
                cover_worksheet.write(row, 0, '📈 ESTATÍSTICAS GERAIS', title_format)
                row += 1
                
                stats = [
                    ('Total de Incidentes', len(self.current_data.get('incident_timeline', [])), '#FF6B6B'),
                    ('Total de Multas', len(self.current_data.get('fines_by_status', [])), '#4ECDC4'),
                    ('Total de Veículos', len(self.current_data.get('vehicles_by_status', [])), '#45B7D1'),
                    ('Total de Sensores', len(self.current_data.get('sensors_by_type', [])), '#96CEB4'),
                    ('Total de Usuários', len(self.current_data.get('user_growth', [])), '#FFA07A'),
                ]
                
                for stat_name, stat_value, color in stats:
                    stat_format = workbook.add_format({
                        'bold': True,
                        'font_size': 11,
                        'bg_color': color,
                        'font_color': 'white',
                        'border': 1,
                        'border_color': '#000000',
                        'align': 'center',
                        'valign': 'vcenter'
                    })
                    cover_worksheet.write(row, 0, stat_name, stat_format)
                    cover_worksheet.write(row, 1, stat_value, number_format)
                    row += 1
                
                # 2. ABA: INCIDENTES DETALHADOS
                if self.current_data.get('incident_timeline'):
                    incidents_worksheet = workbook.add_worksheet('🚨 Incidentes')
                    
                    # Configurar colunas
                    incidents_worksheet.set_column('A:A', 15)
                    incidents_worksheet.set_column('B:B', 20)
                    
                    # Título
                    incidents_worksheet.merge_range('A1:B1', '🚨 INCIDENTES - ANÁLISE TEMPORAL', title_format)
                    incidents_worksheet.merge_range('A2:B2', f'Período: {self.period_var.get() if hasattr(self, "period_var") else "Todos"}', subtitle_format)
                    
                    # Dados
                    df_incidents = pd.DataFrame(self.current_data['incident_timeline'])
                    if not df_incidents.empty:
                        # Renomear colunas para português
                        df_incidents.columns = ['Data', 'Quantidade']
                        
                        # Adicionar colunas de análise
                        df_incidents['Dia da Semana'] = pd.to_datetime(df_incidents['Data']).dt.day_name()
                        df_incidents['Mês'] = pd.to_datetime(df_incidents['Data']).dt.month_name()
                        
                        # Escrever dados com formatação
                        for col_num, value in enumerate(df_incidents.columns):
                            incidents_worksheet.write(3, col_num, value, header_format)
                        
                        for row_num, (_, row) in enumerate(df_incidents.iterrows(), start=4):
                            for col_num, value in enumerate(row):
                                if col_num == 1:  # Quantidade
                                    incidents_worksheet.write(row_num, col_num, value, number_format)
                                else:
                                    incidents_worksheet.write(row_num, col_num, value, data_format)
                    
                    # Gráfico de incidentes
                    if not df_incidents.empty:
                        chart = workbook.add_chart({'type': 'line'})
                        chart.add_series({
                            'categories': f'=Incidentes!$A$4:$A${len(df_incidents)+3}',
                            'values': f'=Incidentes!$B$4:$B${len(df_incidents)+3}',
                            'name': 'Incidentes',
                            'line': {'color': '#FF6B6B', 'width': 3},
                            'marker': {'type': 'circle', 'size': 6, 'fill': {'color': '#FF6B6B'}}
                        })
                        chart.set_title({'name': 'Evolução de Incidentes'})
                        chart.set_x_axis({'name': 'Data'})
                        chart.set_y_axis({'name': 'Quantidade'})
                        chart.set_legend({'none': True})
                        incidents_worksheet.insert_chart('F2', chart)
                
                # 3. ABA: MULTAS COMPLETAS
                if self.current_data.get('fines_by_status'):
                    fines_worksheet = workbook.add_worksheet('💰 Multas')
                    
                    # Configurar colunas
                    fines_worksheet.set_column('A:A', 15)
                    fines_worksheet.set_column('B:B', 15)
                    fines_worksheet.set_column('C:C', 20)
                    
                    # Título
                    fines_worksheet.merge_range('A1:C1', '💰 MULTAS - ANÁLISE FINANCEIRA', title_format)
                    fines_worksheet.merge_range('A2:C2', f'Período: {self.period_var.get() if hasattr(self, "period_var") else "Todos"}', subtitle_format)
                    
                    # Dados
                    df_fines = pd.DataFrame(self.current_data['fines_by_status'])
                    if not df_fines.empty:
                        # Renomear e traduzir
                        df_fines.columns = ['Status', 'Quantidade', 'Valor Total']
                        
                        # Mapear status
                        status_map = {'pending': 'Pendentes', 'paid': 'Pagas', 'overdue': 'Vencidas', 'cancelled': 'Canceladas'}
                        df_fines['Status'] = df_fines['Status'].map(status_map).fillna(df_fines['Status'])
                        
                        # Adicionar análise
                        total_multas = df_fines['Valor Total'].sum()
                        df_fines['% do Total'] = (df_fines['Valor Total'] / total_multas * 100).round(2)
                        
                        # Escrever cabeçalho
                        for col_num, value in enumerate(df_fines.columns):
                            fines_worksheet.write(3, col_num, value, header_format)
                        
                        # Escrever dados
                        for row_num, (_, row) in enumerate(df_fines.iterrows(), start=4):
                            for col_num, value in enumerate(row):
                                if col_num == 2:  # Valor Total
                                    fines_worksheet.write(row_num, col_num, value, currency_format)
                                elif col_num == 3:  # Percentual
                                    percent_format = workbook.add_format({
                                        'font_size': 10,
                                        'bg_color': 'white',
                                        'font_color': '#333333',
                                        'border': 1,
                                        'border_color': '#D0D0D0',
                                        'align': 'right',
                                        'valign': 'vcenter',
                                        'num_format': '0.00%'
                                    })
                                    fines_worksheet.write(row_num, col_num, value, percent_format)
                                elif col_num == 1:  # Quantidade
                                    fines_worksheet.write(row_num, col_num, value, number_format)
                                else:
                                    fines_worksheet.write(row_num, col_num, value, data_format)
                        
                        # Total geral
                        fines_worksheet.write(len(df_fines)+4, 1, 'TOTAL GERAL', title_format)
                        fines_worksheet.write(len(df_fines)+4, 2, total_multas, currency_format)
                        
                        # Gráfico de pizza
                        chart = workbook.add_chart({'type': 'pie'})
                        for i, (_, row) in enumerate(df_fines.iterrows()):
                            chart.add_series({
                                'name': f"={row['Status']}",
                                'categories': f'=Multas!$A$4:$A${len(df_fines)+3}',
                                'values': f'=Multas!$C$4:$C${len(df_fines)+3}',
                                'data_labels': {'percentage': True, 'position': 'out_end'}
                            })
                        chart.set_title({'name': 'Distribuição de Multas por Status'})
                        fines_worksheet.insert_chart('F2', chart)
                
                # 4. ABA: VEÍCULOS
                if self.current_data.get('vehicles_by_status'):
                    vehicles_worksheet = workbook.add_worksheet('🚗 Veículos')
                    
                    # Configurar colunas
                    vehicles_worksheet.set_column('A:A', 20)
                    vehicles_worksheet.set_column('B:B', 15)
                    
                    # Título
                    vehicles_worksheet.merge_range('A1:B1', '🚗 FROTA DE VEÍCULOS', title_format)
                    
                    # Dados
                    df_vehicles = pd.DataFrame(self.current_data['vehicles_by_status'])
                    if not df_vehicles.empty:
                        df_vehicles.columns = ['Status', 'Quantidade']
                        
                        # Escrever dados
                        for col_num, value in enumerate(df_vehicles.columns):
                            vehicles_worksheet.write(3, col_num, value, header_format)
                        
                        for row_num, (_, row) in enumerate(df_vehicles.iterrows(), start=4):
                            for col_num, value in enumerate(row):
                                vehicles_worksheet.write(row_num, col_num, value, number_format)
                        
                        # Gráfico de barras
                        chart = workbook.add_chart({'type': 'column'})
                        chart.add_series({
                            'categories': f'=Veículos!$A$4:$A${len(df_vehicles)+3}',
                            'values': f'=Veículos!$B$4:$B${len(df_vehicles)+3}',
                            'name': 'Veículos',
                            'fill': {'color': '#45B7D1'}
                        })
                        chart.set_title({'name': 'Frota por Status'})
                        chart.set_x_axis({'name': 'Status'})
                        chart.set_y_axis({'name': 'Quantidade'})
                        chart.set_legend({'none': True})
                        vehicles_worksheet.insert_chart('D2', chart)
                
                # 5. ABA: SENSORES
                if self.current_data.get('sensors_by_type'):
                    sensors_worksheet = workbook.add_worksheet('📡 Sensores')
                    
                    # Configurar colunas
                    sensors_worksheet.set_column('A:A', 20)
                    sensors_worksheet.set_column('B:B', 15)
                    sensors_worksheet.set_column('C:C', 15)
                    
                    # Título
                    sensors_worksheet.merge_range('A1:C1', '📡 REDE DE SENSORES', title_format)
                    
                    # Dados
                    df_sensors = pd.DataFrame(self.current_data['sensors_by_type'])
                    if not df_sensors.empty:
                        df_sensors.columns = ['Tipo', 'Total', 'Ativos']
                        
                        # Calcular percentual de ativos
                        df_sensors['% Ativos'] = (df_sensors['Ativos'] / df_sensors['Total'] * 100).round(2)
                        
                        # Escrever dados
                        for col_num, value in enumerate(df_sensors.columns):
                            sensors_worksheet.write(3, col_num, value, header_format)
                        
                        for row_num, (_, row) in enumerate(df_sensors.iterrows(), start=4):
                            for col_num, value in enumerate(row):
                                if col_num == 3:  # Percentual
                                    percent_format = workbook.add_format({
                                        'font_size': 10,
                                        'bg_color': 'white',
                                        'font_color': '#333333',
                                        'border': 1,
                                        'border_color': '#D0D0D0',
                                        'align': 'right',
                                        'valign': 'vcenter',
                                        'num_format': '0.00%'
                                    })
                                    sensors_worksheet.write(row_num, col_num, value, percent_format)
                                else:
                                    sensors_worksheet.write(row_num, col_num, value, number_format)
                        
                        # Gráfico horizontal
                        chart = workbook.add_chart({'type': 'bar'})
                        chart.add_series({
                            'categories': f'=Sensores!$A$4:$A${len(df_sensors)+3}',
                            'values': f'=Sensores!$B$4:$B${len(df_sensors)+3}',
                            'name': 'Total de Sensores',
                            'fill': {'color': '#96CEB4'}
                        })
                        chart.set_title({'name': 'Sensores por Tipo'})
                        chart.set_x_axis({'name': 'Quantidade'})
                        chart.set_y_axis({'name': 'Tipo'})
                        chart.set_legend({'none': True})
                        sensors_worksheet.insert_chart('F2', chart)
                
                # 6. ABA: USUÁRIOS
                if self.current_data.get('user_growth'):
                    users_worksheet = workbook.add_worksheet('👥 Usuários')
                    
                    # Configurar colunas
                    users_worksheet.set_column('A:A', 15)
                    users_worksheet.set_column('B:B', 15)
                    
                    # Título
                    users_worksheet.merge_range('A1:B1', '👥 CRESCIMENTO DE USUÁRIOS', title_format)
                    users_worksheet.merge_range('A2:B2', f'Período: {self.period_var.get() if hasattr(self, "period_var") else "Todos"}', subtitle_format)
                    
                    # Dados
                    df_users = pd.DataFrame(self.current_data['user_growth'])
                    if not df_users.empty:
                        df_users.columns = ['Data', 'Novos Usuários']
                        
                        # Escrever dados
                        for col_num, value in enumerate(df_users.columns):
                            users_worksheet.write(3, col_num, value, header_format)
                        
                        for row_num, (_, row) in enumerate(df_users.iterrows(), start=4):
                            for col_num, value in enumerate(row):
                                if col_num == 1:
                                    users_worksheet.write(row_num, col_num, value, number_format)
                                else:
                                    users_worksheet.write(row_num, col_num, value, data_format)
                        
                        # Gráfico de área
                        chart = workbook.add_chart({'type': 'area'})
                        chart.add_series({
                            'categories': f'=Usuários!$A$4:$A${len(df_users)+3}',
                            'values': f'=Usuários!$B$4:$B${len(df_users)+3}',
                            'name': 'Novos Usuários',
                            'fill': {'color': '#FFA07A', 'transparency': 30}
                        })
                        chart.set_title({'name': 'Crescimento de Usuários'})
                        chart.set_x_axis({'name': 'Data'})
                        chart.set_y_axis({'name': 'Novos Usuários'})
                        chart.set_legend({'none': True})
                        users_worksheet.insert_chart('D2', chart)
                
                # 7. ABA: RESUMO EXECUTIVO
                summary_worksheet = workbook.add_worksheet('📋 Resumo Executivo')
                summary_worksheet.set_column('A:A', 30)
                summary_worksheet.set_column('B:B', 20)
                summary_worksheet.set_column('C:C', 25)
                
                # Título
                summary_worksheet.merge_range('A1:C1', '📋 RESUMO EXECUTIVO - SMARTCITYOS', title_format)
                summary_worksheet.merge_range('A2:C2', f'Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', subtitle_format)
                
                # Métricas principais
                row = 4
                summary_worksheet.write(row, 0, 'MÉTRICA PRINCIPAL', title_format)
                summary_worksheet.write(row, 1, 'VALOR ATUAL', title_format)
                summary_worksheet.write(row, 2, 'OBSERVAÇÕES', title_format)
                row += 1
                
                # Dados do resumo
                summary_data = [
                    ('🚨 Total de Incidentes', len(self.current_data.get('incident_timeline', [])), 'Eventos registrados no período'),
                    ('💰 Total de Multas Emitidas', len(self.current_data.get('fines_by_status', [])), 'Documentos fiscais gerados'),
                    ('💵 Valor Total em Multas', f"R$ {sum([item.get('total_amount', 0) for item in self.current_data.get('fines_by_status', [])]):,.2f}", 'Receita potencial do sistema'),
                    ('🚗 Veículos Cadastrados', len(self.current_data.get('vehicles_by_status', [])), 'Frota total monitorada'),
                    ('📡 Sensores Ativos', sum([item.get('active', 0) for item in self.current_data.get('sensors_by_type', [])]), 'Dispositivos funcionando'),
                    ('👥 Novos Usuários', len(self.current_data.get('user_growth', [])), 'Crescimento da base de usuários'),
                ]
                
                for metric, value, observation in summary_data:
                    summary_worksheet.write(row, 0, metric, subtitle_format)
                    if 'R$' in str(value):
                        summary_worksheet.write(row, 1, value, currency_format)
                    else:
                        summary_worksheet.write(row, 1, value, number_format)
                    summary_worksheet.write(row, 2, observation, data_format)
                    row += 1
                
                # Insights
                row += 2
                summary_worksheet.merge_range(f'A{row}:C{row}', '🎯 INSIGHTS E RECOMENDAÇÕES', title_format)
                row += 1
                
                insights = [
                    '📊 Análise de Tendências: Monitore o crescimento de usuários para planejar capacidade',
                    '💰 Otimização Financeira: Verifique o índice de multas pagas vs pendentes',
                    '🚗 Gestão da Frota: Analise o balanceamento entre veículos ativos e bloqueados',
                    '📡 Manutenção: Sensores inativos podem precisar de manutenção preventiva',
                    '🚨 Segurança: Incidentes em alta podem indicar necessidade de intervenção',
                ]
                
                for insight in insights:
                    summary_worksheet.merge_range(f'A{row}:C{row}', insight, data_format)
                    row += 1
            
            messagebox.showinfo("✅ Sucesso", f"📊 Relatório profissional exportado com sucesso!\n\n📁 Arquivo: {file_path}\n\n✨ Formato: Excel com múltiplas abas, gráficos e formatação avançada")
            
        except ImportError:
            messagebox.showerror("❌ Erro", "Bibliotecas necessárias não encontradas!\n\nInstale:\npip install xlsxwriter openpyxl")
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao exportar relatório: {str(e)}")
            import traceback
            print(f"Erro completo: {traceback.format_exc()}")
    
    def create_interactive_charts(self, parent, period, chart_type):
        """Cria gráficos interativos com Plotly"""
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.subplots import make_subplots
            import pandas as pd
            import webbrowser
            import tempfile
            import os
            
            # Carregar dados do banco
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    
                    # Dados para gráficos
                    data = {}
                    
                    # 1. Evolução de incidentes (linha temporal)
                    cur.execute("""
                        SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                        FROM traffic_incident 
                        WHERE occurred_at >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY DATE(occurred_at)
                        ORDER BY date
                    """)
                    incident_timeline = cur.fetchall()
                    data['incident_timeline'] = incident_timeline
                    
                    # 2. Multas por status (pizza)
                    cur.execute("""
                        SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                        FROM fine 
                        GROUP BY status
                    """)
                    fines_by_status = cur.fetchall()
                    data['fines_by_status'] = fines_by_status
                    
                    # 3. Veículos por status (barras)
                    cur.execute("""
                        SELECT CASE WHEN allowed = TRUE THEN 'Ativos' ELSE 'Bloqueados' END as status, 
                               COUNT(*) as count
                        FROM vehicle_active 
                        GROUP BY allowed
                    """)
                    vehicles_by_status = cur.fetchall()
                    data['vehicles_by_status'] = vehicles_by_status
                    
                    # 4. Sensores por tipo (barras horizontais)
                    cur.execute("""
                        SELECT type, COUNT(*) as count, 
                               COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                        FROM sensor_active 
                        GROUP BY type
                        ORDER BY count DESC
                    """)
                    sensors_by_type = cur.fetchall()
                    data['sensors_by_type'] = sensors_by_type
                    
                    # 5. Crescimento de usuários (linha)
                    cur.execute("""
                        SELECT DATE_TRUNC('month', created_at) as month, COUNT(*) as new_users
                        FROM app_user 
                        WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
                        GROUP BY DATE_TRUNC('month', created_at)
                        ORDER BY month
                    """)
                    user_growth = cur.fetchall()
                    data['user_growth'] = user_growth
            
            # Criar subplots
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=('Incidentes (Últimos 30 dias)', 'Multas por Status', 
                                'Veículos por Status', 'Sensores por Tipo',
                                'Crescimento de Usuários', 'Resumo Financeiro'),
                specs=[[{"secondary_y": False}, {"type": "pie"}],
                       [{"secondary_y": False}, {"type": "bar"}],
                       [{"secondary_y": False}, {"type": "indicator"}]],
                vertical_spacing=0.08,
                horizontal_spacing=0.05
            )
            
            # 1. Gráfico de linha - Incidentes
            if data['incident_timeline']:
                df_incidents = pd.DataFrame(data['incident_timeline'])
                # Converter para tipos compatíveis com Plotly
                df_incidents['incidents'] = df_incidents['incidents'].astype(int)
                df_incidents['date'] = pd.to_datetime(df_incidents['date']).dt.strftime('%Y-%m-%d')
                
                fig.add_trace(
                    go.Scatter(x=df_incidents['date'], y=df_incidents['incidents'],
                              mode='lines+markers', name='Incidentes',
                              line=dict(color='#FF6B6B', width=3),
                              marker=dict(size=8)),
                    row=1, col=1
                )
            
            # 2. Gráfico de pizza - Multas por status
            if data['fines_by_status']:
                df_fines = pd.DataFrame(data['fines_by_status'])
                status_map = {'pending': 'Pendentes', 'paid': 'Pagas', 'overdue': 'Vencidas', 'cancelled': 'Canceladas'}
                df_fines['status_display'] = df_fines['status'].map(status_map)
                # Converter para tipos compatíveis
                df_fines['count'] = df_fines['count'].astype(int)
                df_fines['total_amount'] = pd.to_numeric(df_fines['total_amount'], errors='coerce').fillna(0).astype(float)
                
                fig.add_trace(
                    go.Pie(labels=df_fines['status_display'], values=df_fines['count'],
                           name="Multas", hole=0.4,
                           marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']),
                    row=1, col=2
                )
            
            # 3. Gráfico de barras - Veículos
            if data['vehicles_by_status']:
                df_vehicles = pd.DataFrame(data['vehicles_by_status'])
                # Converter para tipos compatíveis
                df_vehicles['count'] = df_vehicles['count'].astype(int)
                
                fig.add_trace(
                    go.Bar(x=df_vehicles['status'], y=df_vehicles['count'],
                           name='Veículos', marker_color='#4ECDC4'),
                    row=2, col=1
                )
            
            # 4. Gráfico de barras horizontais - Sensores
            if data['sensors_by_type']:
                df_sensors = pd.DataFrame(data['sensors_by_type'])
                # Converter para tipos compatíveis
                df_sensors['count'] = df_sensors['count'].astype(int)
                df_sensors['active'] = df_sensors['active'].astype(int)
                
                fig.add_trace(
                    go.Bar(y=df_sensors['type'], x=df_sensors['count'],
                           name='Sensores', orientation='h',
                           marker_color='#45B7D1'),
                    row=2, col=2
                )
            
            # 5. Gráfico de linha - Crescimento de usuários
            if data['user_growth']:
                df_users = pd.DataFrame(data['user_growth'])
                # Converter para tipos compatíveis
                df_users['new_users'] = df_users['new_users'].astype(int)
                df_users['month'] = pd.to_datetime(df_users['month']).dt.strftime('%Y-%m-%d')
                
                fig.add_trace(
                    go.Scatter(x=df_users['month'], y=df_users['new_users'],
                              mode='lines+markers', name='Novos Usuários',
                              line=dict(color='#96CEB4', width=3),
                              marker=dict(size=8)),
                    row=3, col=1
                )
            
            # 6. Indicador financeiro
            if data['fines_by_status']:
                df_fines = pd.DataFrame(data['fines_by_status'])
                # Converter para tipos compatíveis
                df_fines['total_amount'] = pd.to_numeric(df_fines['total_amount'], errors='coerce').fillna(0).astype(float)
                
                total_amount = float(df_fines['total_amount'].sum())
                pending_amount = float(df_fines[df_fines['status'] == 'pending']['total_amount'].sum() if len(df_fines[df_fines['status'] == 'pending']) > 0 else 0)
                
                fig.add_trace(
                    go.Indicator(
                        mode="number+gauge+delta",
                        value=total_amount,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Valor Total de Multas"},
                        delta={'reference': pending_amount},
                        gauge={
                            'axis': {'range': [None, total_amount * 1.2]},
                            'bar': {'color': "#FF6B6B"},
                            'steps': [
                                {'range': [0, total_amount * 0.5], 'color': "lightgray"},
                                {'range': [total_amount * 0.5, total_amount], 'color': "gray"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': total_amount * 0.9
                            }
                        }
                    ),
                    row=3, col=2
                )
            
            # Layout do gráfico
            fig.update_layout(
                title_text="📊 SmartCityOS - Dashboard Interativo",
                title_x=0.5,
                title_font_size=20,
                height=1200,
                showlegend=True,
                template="plotly_white"
            )
            
            # Salvar gráfico em arquivo HTML temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                fig.write_html(f.name, include_plotlyjs='cdn')
                temp_file = f.name
            
            # Abrir no navegador diretamente
            import webbrowser
            webbrowser.open(f'file://{temp_file}')
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar gráficos: {str(e)}")
    
    def display_plotly_chart(self, html_file, parent):
        """Exibe gráfico Plotly no Tkinter"""
        try:
            import webbrowser
            
            # Frame para o gráfico
            chart_frame = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
            chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Botão para abrir no navegador
            open_btn = tk.Button(chart_frame, text="🌐 Abrir no Navegador (Interativo)",
                               command=lambda: webbrowser.open(f'file://{html_file}'),
                               bg=self.styles.colors['primary'], fg=self.styles.colors['white'],
                               font=self.styles.fonts['button'], relief='flat',
                               padx=20, pady=10, cursor='hand2')
            open_btn.pack(pady=10)
            
            # Label informativo
            info_label = tk.Label(chart_frame, 
                                text="📈 Gráficos interativos criados com Plotly!\n" +
                                     "Clique no botão acima para abrir no navegador com zoom, filtros e animações.",
                                bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                font=self.styles.fonts['normal'], justify='center')
            info_label.pack(pady=10)
            
            # Preview estático (simples)
            preview_label = tk.Label(chart_frame, 
                                    text="📊 Dashboard com 6 gráficos interativos:\n" +
                                    "• Incidentes (linha temporal)\n" +
                                    "• Multas por status (pizza)\n" +
                                    "• Veículos por status (barras)\n" +
                                    "• Sensores por tipo (barras horizontais)\n" +
                                    "• Crescimento de usuários (linha)\n" +
                                    "• Indicador financeiro (gauge)",
                                    bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                                    font=self.styles.fonts['small'], justify='left')
            preview_label.pack(pady=10, padx=20)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar HTML: {str(e)}")
    
    def update_dashboard(self, period):
        """Atualiza dashboard com filtro de período"""
        try:
            # Atualizar o valor do filtro primeiro
            if hasattr(self, 'period_var'):
                self.period_var.set(period)
            
            # Limpar completamente o conteúdo antes de atualizar
            self.clear_content()
            
            # Recriar o dashboard completo com o filtro de período atualizado
            self.show_dashboard()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar dashboard: {str(e)}")
    
    def export_dashboard_charts(self, period, chart_type):
        """Exporta gráficos do dashboard"""
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.subplots import make_subplots
            import pandas as pd
            import tempfile
            import shutil
            from tkinter import filedialog
            
            # Criar gráficos novamente para exportação
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                # Reutilizar a lógica de create_interactive_charts
                # Carregar dados e criar gráficos
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor(row_factory=dict_row) as cur:
                        
                        # Dados para gráficos (mesma lógica de create_interactive_charts)
                        data = {}
                        
                        # 1. Evolução de incidentes
                        cur.execute("""
                            SELECT DATE(occurred_at) as date, COUNT(*) as incidents
                            FROM traffic_incident 
                            WHERE occurred_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY DATE(occurred_at)
                            ORDER BY date
                        """)
                        incident_timeline = cur.fetchall()
                        data['incident_timeline'] = incident_timeline
                        
                        # 2. Multas por status
                        cur.execute("""
                            SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                            FROM fine 
                            GROUP BY status
                        """)
                        fines_by_status = cur.fetchall()
                        data['fines_by_status'] = fines_by_status
                        
                        # 3. Veículos por status
                        cur.execute("""
                            SELECT CASE WHEN allowed = TRUE THEN 'Ativos' ELSE 'Bloqueados' END as status, 
                                   COUNT(*) as count
                            FROM vehicle_active 
                            GROUP BY allowed
                        """)
                        vehicles_by_status = cur.fetchall()
                        data['vehicles_by_status'] = vehicles_by_status
                        
                        # 4. Sensores por tipo
                        cur.execute("""
                            SELECT type, COUNT(*) as count, 
                                   COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                            FROM sensor_active 
                            GROUP BY type
                            ORDER BY count DESC
                        """)
                        sensors_by_type = cur.fetchall()
                        data['sensors_by_type'] = sensors_by_type
                        
                        # 5. Crescimento de usuários
                        cur.execute("""
                            SELECT DATE_TRUNC('month', created_at) as month, COUNT(*) as new_users
                            FROM app_user 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
                            GROUP BY DATE_TRUNC('month', created_at)
                            ORDER BY month
                        """)
                        user_growth = cur.fetchall()
                        data['user_growth'] = user_growth
                
                # Criar gráficos (mesma lógica)
                fig = make_subplots(
                    rows=3, cols=2,
                    subplot_titles=('Incidentes (Últimos 30 dias)', 'Multas por Status', 
                                    'Veículos por Status', 'Sensores por Tipo',
                                    'Crescimento de Usuários', 'Resumo Financeiro'),
                    specs=[[{"secondary_y": False}, {"type": "pie"}],
                           [{"secondary_y": False}, {"type": "bar"}],
                           [{"secondary_y": False}, {"type": "indicator"}]],
                    vertical_spacing=0.08,
                    horizontal_spacing=0.05
                )
                
                # Adicionar traces (todos os gráficos)
                if data['incident_timeline']:
                    df_incidents = pd.DataFrame(data['incident_timeline'])
                    df_incidents['incidents'] = df_incidents['incidents'].astype(int)
                    df_incidents['date'] = pd.to_datetime(df_incidents['date']).dt.strftime('%Y-%m-%d')
                    
                    fig.add_trace(
                        go.Scatter(x=df_incidents['date'], y=df_incidents['incidents'],
                                  mode='lines+markers', name='Incidentes',
                                  line=dict(color='#FF6B6B', width=3),
                                  marker=dict(size=8)),
                        row=1, col=1
                    )
                
                if data['fines_by_status']:
                    df_fines = pd.DataFrame(data['fines_by_status'])
                    status_map = {'pending': 'Pendentes', 'paid': 'Pagas', 'overdue': 'Vencidas', 'cancelled': 'Canceladas'}
                    df_fines['status_display'] = df_fines['status'].map(status_map)
                    df_fines['count'] = df_fines['count'].astype(int)
                    df_fines['total_amount'] = pd.to_numeric(df_fines['total_amount'], errors='coerce').fillna(0).astype(float)
                    
                    fig.add_trace(
                        go.Pie(labels=df_fines['status_display'], values=df_fines['count'],
                               name="Multas", hole=0.4,
                               marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']),
                        row=1, col=2
                    )
                
                if data['vehicles_by_status']:
                    df_vehicles = pd.DataFrame(data['vehicles_by_status'])
                    df_vehicles['count'] = df_vehicles['count'].astype(int)
                    
                    fig.add_trace(
                        go.Bar(x=df_vehicles['status'], y=df_vehicles['count'],
                               name='Veículos', marker_color='#4ECDC4'),
                        row=2, col=1
                    )
                
                if data['sensors_by_type']:
                    df_sensors = pd.DataFrame(data['sensors_by_type'])
                    df_sensors['count'] = df_sensors['count'].astype(int)
                    df_sensors['active'] = df_sensors['active'].astype(int)
                    
                    fig.add_trace(
                        go.Bar(y=df_sensors['type'], x=df_sensors['count'],
                               name='Sensores', orientation='h',
                               marker_color='#45B7D1'),
                        row=2, col=2
                    )
                
                if data['user_growth']:
                    df_users = pd.DataFrame(data['user_growth'])
                    df_users['new_users'] = df_users['new_users'].astype(int)
                    df_users['month'] = pd.to_datetime(df_users['month']).dt.strftime('%Y-%m-%d')
                    
                    fig.add_trace(
                        go.Scatter(x=df_users['month'], y=df_users['new_users'],
                                  mode='lines+markers', name='Novos Usuários',
                                  line=dict(color='#96CEB4', width=3),
                                  marker=dict(size=8)),
                        row=3, col=1
                    )
                
                # Indicador financeiro
                if data['fines_by_status']:
                    df_fines = pd.DataFrame(data['fines_by_status'])
                    df_fines['total_amount'] = pd.to_numeric(df_fines['total_amount'], errors='coerce').fillna(0).astype(float)
                    
                    total_amount = float(df_fines['total_amount'].sum())
                    pending_amount = float(df_fines[df_fines['status'] == 'pending']['total_amount'].sum() if len(df_fines[df_fines['status'] == 'pending']) > 0 else 0)
                    
                    fig.add_trace(
                        go.Indicator(
                            mode="number+gauge+delta",
                            value=total_amount,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Valor Total de Multas"},
                            delta={'reference': pending_amount},
                            gauge={
                                'axis': {'range': [None, total_amount * 1.2] if total_amount > 0 else [0, 100]},
                                'bar': {'color': "#FF6B6B"},
                                'steps': [
                                    {'range': [0, total_amount * 0.5] if total_amount > 0 else [0, 50], 'color': "lightgray"},
                                    {'range': [total_amount * 0.5, total_amount] if total_amount > 0 else [50, 100], 'color': "gray"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': (total_amount * 0.9) if total_amount > 0 else 90
                                }
                            }
                        ),
                        row=3, col=2
                    )
                
                # Layout
                fig.update_layout(
                    title_text=f"📊 SmartCityOS - Dashboard Exportado<br>Período: {period} | Tipo: {chart_type}",
                    title_x=0.5,
                    title_font_size=20,
                    height=1200,
                    showlegend=True,
                    template="plotly_white"
                )
                
                # Salvar gráfico
                fig.write_html(f.name, include_plotlyjs='cdn')
                
                # File dialog para salvar
                file_path = filedialog.asksaveasfilename(
                    title="Exportar Dashboard",
                    defaultextension=".html",
                    filetypes=[("Arquivo HTML (*.html)", "*.html"), ("Todos os Arquivos", "*.*")],
                    initialfile=f"dashboard_smartcity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                )
                
                if file_path:
                    # Copiar arquivo temporário para o local escolhido
                    shutil.copy2(f.name, file_path)
                    messagebox.showinfo("Sucesso", f"Dashboard exportado para:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar dashboard: {str(e)}")
        
    def show_statistics(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    
                    # Header estilizado
                    header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
                    header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
                    
                    title_label = tk.Label(header_frame, text="📈 Estatísticas do Sistema", 
                                          bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                          font=self.styles.fonts['title'])
                    title_label.pack(side=tk.LEFT, padx=20, pady=15)
                    
                    # Botões de ação
                    button_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
                    button_frame.pack(side=tk.RIGHT, padx=20, pady=15)
                    
                    export_btn = tk.Button(button_frame, text="📥 Exportar Relatório", command=self.export_statistics,
                                         bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                         font=self.styles.fonts['button'], relief='flat',
                                         padx=10, pady=8, cursor='hand2')
                    export_btn.pack(side=tk.RIGHT, padx=5)
                    
                    refresh_btn = tk.Button(button_frame, text="🔄 Atualizar", command=self.show_statistics,
                                          bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                          font=self.styles.fonts['button'], relief='flat',
                                          padx=10, pady=8, cursor='hand2')
                    refresh_btn.pack(side=tk.RIGHT, padx=20, pady=15)
                    
                    # Carregar estatísticas
                    stats = self.load_comprehensive_statistics(cur)
                    
                    # Exibir estatísticas
                    self.display_comprehensive_statistics(stats)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar estatísticas: {str(e)}")
            
    def load_comprehensive_statistics(self, cur):
        stats = {}
        
        try:
            # Estatísticas de Usuários
            cur.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as this_month,
                       COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as this_week
                FROM app_user_active
            """)
            stats['users'] = cur.fetchone()
        except Exception as e:
            print(f"Erro ao carregar estatísticas de usuários: {e}")
            stats['users'] = {'total': 0, 'this_month': 0, 'this_week': 0}
        
        try:
            # Estatísticas de Cidadãos
            cur.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(CASE WHEN debt > 0 THEN 1 END) as with_debt,
                       COUNT(CASE WHEN allowed = TRUE THEN 1 END) as with_access,
                       COALESCE(SUM(debt), 0) as total_debt,
                       COALESCE(AVG(debt), 0) as avg_debt
                FROM citizen_active
            """)
            stats['citizens'] = cur.fetchone()
        except Exception as e:
            print(f"Erro ao carregar estatísticas de cidadãos: {e}")
            stats['citizens'] = {'total': 0, 'with_debt': 0, 'with_access': 0, 'total_debt': 0, 'avg_debt': 0}
        
        try:
            # Estatísticas de Veículos
            cur.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN allowed = TRUE THEN 1 END) as active,
                       COUNT(CASE WHEN allowed = FALSE THEN 1 END) as blocked,
                       COUNT(DISTINCT citizen_id) as unique_owners
                FROM vehicle_active
            """)
            stats['vehicles'] = cur.fetchone()
        except Exception as e:
            print(f"Erro ao carregar estatísticas de veículos: {e}")
            stats['vehicles'] = {'total': 0, 'active': 0, 'blocked': 0, 'unique_owners': 0}
        
        try:
            # Estatísticas de Sensores
            cur.execute("""
                SELECT type, COUNT(*) as count, 
                       COUNT(CASE WHEN active = TRUE THEN 1 END) as active
                FROM sensor_active
                GROUP BY type
                ORDER BY count DESC
            """)
            stats['sensors_by_type'] = cur.fetchall()
            
            cur.execute("""
                SELECT COUNT(*) as total_sensors,
                       COUNT(CASE WHEN active = TRUE THEN 1 END) as active_sensors,
                       COUNT(DISTINCT type) as sensor_types
                FROM sensor_active
            """)
            stats['sensors'] = cur.fetchone()
        except Exception as e:
            print(f"Erro ao carregar estatísticas de sensores: {e}")
            stats['sensors_by_type'] = []
            stats['sensors'] = {'total_sensors': 0, 'active_sensors': 0, 'sensor_types': 0}
        
        try:
            # Estatísticas de Incidentes
            cur.execute("""
                SELECT COUNT(*) as count,
                       COUNT(CASE WHEN ti.occurred_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days,
                       COUNT(CASE WHEN ti.occurred_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_7_days,
                       COALESCE(SUM(f.amount), 0) as total_fines
                FROM traffic_incident ti
                LEFT JOIN fine f ON ti.id = f.traffic_incident_id
            """)
            incident_summary = cur.fetchone()
            
            # Incidentes por localização
            cur.execute("""
                SELECT ti.location, COUNT(*) as count,
                       COUNT(f.id) as fine_count,
                       COALESCE(AVG(f.amount), 0) as avg_fine
                FROM traffic_incident ti
                LEFT JOIN fine f ON ti.id = f.traffic_incident_id
                GROUP BY ti.location
                ORDER BY count DESC
            """)
            stats['incidents_by_type'] = cur.fetchall()
            
            stats['incidents'] = {
                'total_incidents': incident_summary['count'],
                'resolved': 0,  # Não temos campo resolved
                'pending': incident_summary['count'],  # Todos são pendentes por padrão
                'last_30_days': incident_summary['last_30_days'],
                'last_7_days': incident_summary['last_7_days'],
                'total_fines': incident_summary['total_fines']
            }
        except Exception as e:
            print(f"Erro ao carregar estatísticas de incidentes: {e}")
            stats['incidents_by_type'] = []
            stats['incidents'] = {'total_incidents': 0, 'resolved': 0, 'pending': 0, 'last_30_days': 0, 'last_7_days': 0, 'total_fines': 0}
        
        try:
            # Estatísticas de Multas
            cur.execute("""
                SELECT COUNT(*) as total_fines,
                       COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_fines,
                       COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_fines,
                       COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_fines,
                       COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_fines,
                       COALESCE(SUM(amount), 0) as total_amount,
                       COALESCE(SUM(CASE WHEN status = 'pending' THEN amount END), 0) as pending_amount,
                       COALESCE(SUM(CASE WHEN status = 'overdue' THEN amount END), 0) as overdue_amount,
                       COALESCE(SUM(CASE WHEN status = 'paid' THEN amount END), 0) as paid_amount,
                       COALESCE(AVG(amount), 0) as avg_amount
                FROM fine
            """)
            stats['fines'] = cur.fetchone()
            
            # Multas por status
            cur.execute("""
                SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                FROM fine
                GROUP BY status
                ORDER BY count DESC
            """)
            stats['fines_by_status'] = cur.fetchall()
        except Exception as e:
            print(f"Erro ao carregar estatísticas de multas: {e}")
            stats['fines_by_status'] = []
            stats['fines'] = {'total_fines': 0, 'pending_fines': 0, 'overdue_fines': 0, 'paid_fines': 0, 'cancelled_fines': 0, 'total_amount': 0, 'pending_amount': 0, 'overdue_amount': 0, 'paid_amount': 0, 'avg_amount': 0}
        
        try:
            # Estatísticas de Leituras (últimos 7 dias)
            cur.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as readings_count
                FROM reading
                WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            stats['readings_last_7_days'] = cur.fetchall()
        except Exception as e:
            print(f"Erro ao carregar estatísticas de leituras: {e}")
            stats['readings_last_7_days'] = []
        
        return stats
        
    def display_comprehensive_statistics(self, stats):
        # Container principal
        main_container = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Seção 1: Cards Principais
        self.create_main_stats_cards(main_container, stats)
        
        # Seção 2: Gráficos e Tabelas
        stats_frame = tk.Frame(main_container, bg=self.styles.colors['background'])
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Coluna esquerda - Tabelas detalhadas
        left_frame = tk.Frame(stats_frame, bg=self.styles.colors['background'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Coluna direita - Cards secundários
        right_frame = tk.Frame(stats_frame, bg=self.styles.colors['background'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Tabelas detalhadas
        self.create_detailed_tables(left_frame, stats)
        
        # Cards secundários
        self.create_secondary_stats_cards(right_frame, stats)
        
    def create_main_stats_cards(self, parent, stats):
        # Frame para cards principais
        cards_frame = tk.Frame(parent, bg=self.styles.colors['background'])
        cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Cards principais
        main_cards = [
            ("👤 Usuários", stats['users']['total'], 
             f"{stats['users']['this_month']} novos este mês", self.styles.colors['primary']),
            ("👥 Cidadãos", stats['citizens']['total'], 
             format_currency_brl(stats['citizens']['total_debt']), self.styles.colors['success']),
            ("🚗 Veículos", stats['vehicles']['total'],
             f"{stats['vehicles']['active']} ativos", self.styles.colors['warning']),
            ("⚠️ Incidentes", stats['incidents']['total_incidents'],
             f"{stats['incidents']['last_7_days']} esta semana", self.styles.colors['accent']),
            ("💰 Multas", stats['fines']['total_fines'],
             format_currency_brl(stats['fines']['total_amount']), self.styles.colors['secondary'])
        ]
        
        for i, (title, value, extra, color) in enumerate(main_cards):
            card = self.create_stats_card(cards_frame, title, value, extra, color, large=True)
            card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
            
    def create_secondary_stats_cards(self, parent, stats):
        # Cards secundários com tratamento de divisão por zero
        secondary_cards = []
        
        # Usuários Totais
        users_total = stats['users']['total']
        users_this_month = stats['users']['this_month']
        month_percent = (users_this_month / users_total * 100) if users_total > 0 else 0
        secondary_cards.append((
            "👤 Usuários Totais", 
            users_total,
            f"{month_percent:.1f}% novos este mês", 
            self.styles.colors['primary']
        ))
        
        # Cidadãos com Dívida
        citizens_with_debt = stats['citizens']['with_debt']
        citizens_total = stats['citizens']['total']
        debt_percent = (citizens_with_debt / citizens_total * 100) if citizens_total > 0 else 0
        secondary_cards.append((
            "💳 Cidadãos c/ Dívida", 
            citizens_with_debt,
            f"{debt_percent:.1f}% do total", 
            self.styles.colors['warning']
        ))
        
        # Sensores
        secondary_cards.append((
            "📹 Sensores", 
            stats['sensors']['total_sensors'],
            f"{stats['sensors']['active_sensors']} ativos", 
            self.styles.colors['secondary']
        ))
        
        # Veículos Bloqueados
        vehicles_total = stats['vehicles']['total']
        vehicles_blocked = stats['vehicles']['blocked']
        blocked_percent = (vehicles_blocked / vehicles_total * 100) if vehicles_total > 0 else 0
        secondary_cards.append((
            "🔒 Veículos Bloqueados", 
            vehicles_blocked,
            f"{blocked_percent:.1f}%", 
            self.styles.colors['warning']
        ))
        
        # Multas Pendentes
        secondary_cards.append((
            "💳 Multas Pendentes", 
            stats['fines']['pending_fines'],
            format_currency_brl(stats['fines']['pending_amount']), 
            self.styles.colors['accent']
        ))
        
        # Multas Vencidas
        secondary_cards.append((
            "⚠️ Multas Vencidas", 
            stats['fines']['overdue_fines'],
            format_currency_brl(stats['fines']['overdue_amount']), 
            self.styles.colors['warning']
        ))
        
        # Incidentes Resolvidos
        incidents_total = stats['incidents']['total_incidents']
        incidents_resolved = stats['incidents']['resolved']
        resolved_percent = (incidents_resolved / incidents_total * 100) if incidents_total > 0 else 0
        secondary_cards.append((
            "✅ Incidentes Resolvidos", 
            incidents_resolved,
            f"{resolved_percent:.1f}%", 
            self.styles.colors['success']
        ))
        
        for title, value, extra, color in secondary_cards:
            card = self.create_stats_card(parent, title, value, extra, color, large=False)
            card.pack(fill=tk.X, pady=5)
            
    def create_stats_card(self, parent, title, value, extra, color, large=True):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Header
        header_height = 60 if large else 40
        header = tk.Frame(card, bg=color, height=header_height)
        header.pack(fill=tk.X)
        header.grid_propagate(False)
        
        font_size = 14 if large else 11
        title_label = tk.Label(header, text=title, bg=color, fg=self.styles.colors['white'],
                              font=('Segoe UI', font_size))
        title_label.pack(pady=15 if large else 10)
        
        # Content
        content = tk.Frame(card, bg=self.styles.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        font_size_value = 32 if large else 20
        value_label = tk.Label(content, text=str(value), bg=self.styles.colors['card'],
                              fg=color, font=('Segoe UI', font_size_value, 'bold'))
        value_label.pack(anchor='w')
        
        extra_label = tk.Label(content, text=extra, bg=self.styles.colors['card'],
                               fg=self.styles.colors['text_secondary'], font=self.styles.fonts['normal'])
        extra_label.pack(anchor='w', pady=(5, 0))
        
        return card
        
    def create_detailed_tables(self, parent, stats):
        # Tabela de Sensores por Tipo
        self.create_type_table(parent, "📹 Sensores por Tipo", stats['sensors_by_type'], 
                              ['Tipo', 'Total', 'Ativos'])
        
        # Tabela de Incidentes por Tipo
        self.create_type_table(parent, "⚠️ Incidentes por Localização", stats['incidents_by_type'],
                              ['Localização', 'Total', 'Multas', 'Multa Média'])
        
        # Tabela de Multas por Status
        self.create_type_table(parent, "💰 Multas por Status", stats['fines_by_status'],
                              ['Status', 'Quantidade', 'Valor Total'])
                              
    def create_type_table(self, parent, title, data, columns):
        # Frame da tabela
        table_frame = tk.LabelFrame(parent, text=title, bg=self.styles.colors['card'],
                                  fg=self.styles.colors['text_primary'], font=self.styles.fonts['heading'],
                                  relief='solid', bd=1)
        table_frame.pack(fill=tk.X, pady=10)
        
        # Treeview
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=4, style='Results.Treeview')
        
        # Configurar colunas
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, minwidth=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Inserir dados
        for i, row in enumerate(data):
            try:
                values = []
                if title == "📹 Sensores por Tipo":
                    values = [row['type'] or "N/A", row['count'] or 0, row['active'] or 0]
                elif title == "⚠️ Incidentes por Localização":
                    avg_fine = row['avg_fine'] if row['avg_fine'] and row['avg_fine'] > 0 else 0
                    values = [
                        row['location'] or "N/A", 
                        row['count'] or 0, 
                        row['fine_count'] or 0, 
                        format_currency_brl(avg_fine)
                    ]
                elif title == "💰 Multas por Status":
                    total_amount = row['total_amount'] if row['total_amount'] and row['total_amount'] > 0 else 0
                    values = [
                        row['status'] or "N/A", 
                        row['count'] or 0, 
                        format_currency_brl(total_amount)
                    ]
                
                tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                tree.insert('', tk.END, values=values, tags=(tag,))
            except Exception as e:
                print(f"Erro ao processar linha {i} na tabela {title}: {e}")
                continue
            
        # Pack
        table_frame.pack(fill=tk.X, padx=10, pady=5)
        
    def export_sql_results(self):
        """Exporta resultados de consulta SQL para CSV ou XLSX"""
        if not self.connected:
            messagebox.showerror("Erro", "Conecte-se ao banco de dados para exportar resultados!")
            return
        
        try:
            # Dialog para selecionar arquivo e formato
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="Exportar Resultados SQL",
                filetypes=[
                    ("Arquivo Excel (*.xlsx)", "*.xlsx"),
                    ("Arquivo CSV (*.csv)", "*.csv"),
                    ("Todos os Arquivos", "*.*")
                ],
                defaultextension=".xlsx",
                initialfile=f"resultados_sql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            # Garantir que o arquivo tenha extensão
            if not file_path.lower().endswith(('.xlsx', '.csv')):
                file_path += '.xlsx'  # Padrão Excel
            
            # Determinar formato pelo arquivo selecionado
            is_excel = file_path.lower().endswith('.xlsx')
            
            # Obter SQL do text widget
            sql_query = self.sql_text.get("1.0", tk.END).strip()
            
            if not sql_query:
                messagebox.showerror("Erro", "Digite uma consulta SQL para exportar os resultados!")
                return
            
            # Executar consulta SQL
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    try:
                        cur.execute(sql_query)
                        results = cur.fetchall()
                        
                        if not results:
                            messagebox.showwarning("Sem Resultados", "A consulta não retornou nenhum resultado!")
                            return
                        
                        # Importar pandas
                        import pandas as pd
                        
                        # Criar DataFrame
                        df = pd.DataFrame(results)
                        
                        # Exportar baseado no formato
                        if is_excel:
                            # Exportar para Excel
                            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                                # Resultados da consulta
                                df.to_excel(writer, sheet_name='Resultados', index=False)
                                
                                # Adicionar informações da consulta
                                query_info = pd.DataFrame([
                                    ['SmartCityOS - Resultados de Consulta SQL'],
                                    [f'Data da Exportação: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'],
                                    [f'Formato: Excel (.xlsx)'],
                                    [f'Consulta SQL:'],
                                    [sql_query],
                                    [f'Total de Registros: {len(results)}']
                                ], columns=['Informação'])
                                query_info.to_excel(writer, sheet_name='Informações', index=False)
                            
                            messagebox.showinfo("Sucesso", f"Resultados exportados com sucesso!\n\nArquivo Excel salvo em:\n{file_path}\n\nRegistros exportados: {len(results)}")
                        else:
                            # Exportar para CSV
                            df.to_csv(file_path, index=False, encoding='utf-8-sig')
                            messagebox.showinfo("Sucesso", f"Resultados exportados com sucesso!\n\nArquivo CSV salvo em:\n{file_path}\n\nRegistros exportados: {len(results)}")
                        
                    except Exception as sql_error:
                        messagebox.showerror("Erro SQL", f"Erro na consulta SQL:\n{str(sql_error)}")
                        return
            
        except ImportError:
            messagebox.showerror("Erro", "Bibliotecas necessárias não encontradas!\n\nInstale:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar resultados: {str(e)}")
        
    def export_statistics(self):
        """Exporta estatísticas para CSV ou XLSX usando pandas"""
        if not self.connected:
            messagebox.showerror("Erro", "Conecte-se ao banco de dados para exportar estatísticas!")
            return
        
        try:
            # Dialog para selecionar arquivo e formato
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="Exportar Estatísticas",
                filetypes=[
                    ("Arquivo Excel (*.xlsx)", "*.xlsx"),
                    ("Arquivo CSV (*.csv)", "*.csv"),
                    ("Todos os Arquivos", "*.*")
                ],
                defaultextension=".xlsx",
                initialfile=f"estatisticas_smartcity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            # Garantir que o arquivo tenha extensão
            if not file_path.lower().endswith(('.xlsx', '.csv')):
                file_path += '.xlsx'  # Padrão Excel
            
            # Determinar formato pelo arquivo selecionado
            is_excel = file_path.lower().endswith('.xlsx')
            
            # Carregar estatísticas completas
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    stats = self.load_comprehensive_statistics(cur)
            
            # Importar pandas
            import pandas as pd
            
            # Criar dados para exportação
            export_data = []
            
            # Estatísticas Gerais
            export_data.extend([
                ['ESTATÍSTICAS GERAIS', '', ''],
                ['Métrica', 'Total', 'Descrição'],
                ['Total de Usuários', stats['users']['total'], 'Número total de usuários cadastrados'],
                ['Total de Cidadãos', stats['citizens']['total'], 'Número total de cidadãos cadastrados'],
                ['Total de Veículos', stats['vehicles']['total'], 'Número total de veículos cadastrados'],
                ['Total de Sensores', stats['sensors']['total_sensors'], 'Número total de sensores cadastrados'],
                ['Total de Incidentes', stats['incidents']['total_incidents'], 'Número total de incidentes registrados'],
                ['Total de Multas', stats['fines']['total_fines'], 'Número total de multas geradas'],
                ['', '', ''],
                
                # Estatísticas de Usuários
                ['ESTATÍSTICAS DE USUÁRIOS', '', ''],
                ['Métrica', 'Total', 'Descrição'],
                ['Usuários Ativos', stats['users']['total'], 'Usuários com acesso ao sistema'],
                ['Usuários Inativos', 0, 'Usuários sem acesso (calculado)'],
                ['Novos Usuários (30 dias)', stats['users']['this_month'], 'Usuários cadastrados nos últimos 30 dias'],
                ['', '', ''],
                
                # Estatísticas de Cidadãos
                ['ESTATÍSTICAS DE CIDADÃOS', '', ''],
                ['Métrica', 'Total', 'Descrição'],
                ['Cidadãos Ativos', stats['citizens']['with_access'], 'Cidadãos com permissão de acesso'],
                ['Cidadãos Inativos', stats['citizens']['total'] - stats['citizens']['with_access'], 'Cidadãos sem permissão de acesso'],
                ['Saldo Total (R$)', 0.00, 'Saldo total disponível dos cidadãos'],
                ['Dívida Total (R$)', f"{stats['citizens']['total_debt']:.2f}", 'Dívida total acumulada dos cidadãos'],
                ['Novos Cidadãos (30 dias)', 0, 'Cidadãos cadastrados nos últimos 30 dias'],
                ['', '', ''],
                
                # Estatísticas de Veículos
                ['ESTATÍSTICAS DE VEÍCULOS', '', ''],
                ['Métrica', 'Total', 'Descrição'],
                ['Veículos Ativos', stats['vehicles']['active'], 'Veículos com permissão de circulação'],
                ['Veículos Inativos', stats['vehicles']['blocked'], 'Veículos sem permissão de circulação'],
                ['Novos Veículos (30 dias)', 0, 'Veículos cadastrados nos últimos 30 dias'],
                ['', '', ''],
                
                # Estatísticas de Sensores
                ['ESTATÍSTICAS DE SENSORES', '', ''],
                ['Métrica', 'Total', 'Descrição'],
                ['Sensores Ativos', stats['sensors']['active_sensors'], 'Sensores atualmente em operação'],
                ['Sensores Inativos', stats['sensors']['total_sensors'] - stats['sensors']['active_sensors'], 'Sensores desativados'],
                ['Sensores com Leituras', 0, 'Sensores que já registraram leituras'],
                ['Novos Sensores (30 dias)', 0, 'Sensores cadastrados nos últimos 30 dias'],
                ['', '', ''],
                
                # Estatísticas de Incidentes
                ['ESTATÍSTICAS DE INCIDENTES', '', ''],
                ['Métrica', 'Total', 'Descrição'],
                ['Incidentes (7 dias)', stats['incidents']['last_7_days'], 'Incidentes registrados nos últimos 7 dias'],
                ['Incidentes (30 dias)', stats['incidents']['last_30_days'], 'Incidentes registrados nos últimos 30 dias'],
                ['', '', ''],
                
                # Estatísticas de Multas
                ['ESTATÍSTICAS DE MULTAS', '', ''],
                ['Métrica', 'Total', 'Descrição'],
                ['Multas Pendentes', stats['fines']['pending_fines'], 'Multas aguardando pagamento'],
                ['Multas Pagas', stats['fines']['paid_fines'], 'Multas já quitadas'],
                ['Multas Canceladas', stats['fines']['cancelled_fines'], 'Multas canceladas'],
                ['Multas Vencidas', stats['fines']['overdue_fines'], 'Multas com vencimento ultrapassado'],
                ['Valor Total Pendente (R$)', f"{stats['fines']['pending_amount']:.2f}", 'Valor total das multas pendentes'],
                ['Valor Total Pago (R$)', f"{stats['fines']['paid_amount']:.2f}", 'Valor total das multas já pagas'],
                ['Valor Total Vencido (R$)', f"{stats['fines']['overdue_amount']:.2f}", 'Valor total das multas vencidas'],
                ['', '', ''],
                
                # Resumo Financeiro
                ['RESUMO FINANCEIRO', '', ''],
                ['Métrica', 'Valor (R$)', 'Descrição'],
                ['Saldo Total dos Cidadãos', 0.00, 'Saldo total disponível dos cidadãos'],
                ['Dívida Total dos Cidadãos', f"{stats['citizens']['total_debt']:.2f}", 'Dívida total acumulada dos cidadãos'],
                ['Valor Total de Multas Pendentes', f"{stats['fines']['pending_amount']:.2f}", 'Valor total das multas pendentes'],
                ['Valor Total de Multas Pagas', f"{stats['fines']['paid_amount']:.2f}", 'Valor total das multas já pagas'],
                ['Valor Total de Multas Vencidas', f"{stats['fines']['overdue_amount']:.2f}", 'Valor total das multas vencidas'],
            ])
            
            # Criar DataFrame
            df = pd.DataFrame(export_data, columns=['Categoria', 'Valor', 'Descrição'])
            
            # Exportar baseado no formato
            if is_excel:
                # Exportar para Excel
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # Estatísticas Gerais
                    df.to_excel(writer, sheet_name='Estatísticas', index=False)
                    
                    # Adicionar metadados
                    metadata_df = pd.DataFrame([
                        ['SmartCityOS - Sistema Operacional Inteligente para Cidades'],
                        [f'Data da Exportação: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'],
                        [f'Formato: Excel (.xlsx)'],
                        [f'Ve rsão: 1.0']
                    ], columns=['Informação'])
                    metadata_df.to_excel(writer, sheet_name='Metadados', index=False)
                
                messagebox.showinfo("Sucesso", f"Estatísticas exportadas com sucesso!\n\nArquivo Excel salvo em:\n{file_path}")
            else:
                # Exportar para CSV
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Sucesso", f"Estatísticas exportadas com sucesso!\n\nArquivo CSV salvo em:\n{file_path}")
            
        except ImportError:
            messagebox.showerror("Erro", "Bibliotecas necessárias não encontradas!\n\nInstale:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar estatísticas: {str(e)}")
        
    def show_sql_console(self):
        self.clear_content()
        
        # Header estilizado
        header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        title_label = tk.Label(header_frame, text="🔍 Console SQL", 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                              font=self.styles.fonts['title'])
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Botões de ação
        button_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
        button_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        clear_btn = tk.Button(button_frame, text="🗑️ Limpar", command=self.clear_sql,
                            bg=self.styles.colors['light'], fg=self.styles.colors['text_primary'],
                            font=self.styles.fonts['button'], relief='flat',
                            padx=12, pady=6, cursor='hand2')
        clear_btn.pack(side=tk.RIGHT, padx=5)
        
        export_btn = tk.Button(button_frame, text="📊 Exportar", command=self.export_sql_results,
                              bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=12, pady=6, cursor='hand2')
        export_btn.pack(side=tk.RIGHT, padx=5)
        
        example_btn = tk.Button(button_frame, text="📋 Exemplo", command=self.load_sql_example,
                              bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=12, pady=6, cursor='hand2')
        example_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame principal com duas colunas
        main_container = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ... (restante do código permanece igual)
        # Coluna esquerda - Editor SQL
        left_frame = tk.Frame(main_container, bg=self.styles.colors['background'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Frame do editor SQL
        sql_frame = tk.LabelFrame(left_frame, text="Editor SQL", bg=self.styles.colors['card'],
                                  fg=self.styles.colors['text_primary'], font=self.styles.fonts['heading'],
                                  relief='solid', bd=1)
        sql_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área de texto para SQL - CONFIGURAÇÃO MÍNIMA
        self.sql_text = scrolledtext.ScrolledText(
            sql_frame, 
            height=12, 
            width=60,
            bg='#2E3440',
            fg='#D8DEE9',
            font=('Consolas', 11),
            insertbackground='#88C0D0',
            selectbackground='#4C566A',
            relief='flat',
            bd=0,
            wrap='word',
            padx=8,
            pady=8
        )
        self.sql_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Inserir texto inicial
        self.sql_text.insert(tk.END, "-- Digite sua consulta SQL aqui\n")
        self.sql_text.insert(tk.END, "SELECT * FROM app_user_active LIMIT 10;")
        self.sql_text.tag_add("comment", "1.0", "1.end")
        self.sql_text.tag_config("comment", foreground='#616E88')
        
        # FORÇAR FOCO IMEDIATO APÓS CRIAR O WIDGET
        self.sql_text.focus_set()
        self.sql_text.mark_set('insert', 'end')
        
        # EVENTOS SIMPLES
        self.sql_text.bind('<FocusIn>', lambda e: None)
        self.sql_text.bind('<Button-1>', lambda e: self.sql_text.focus_set())
        
        # SIMULAR CLIQUE AUTOMÁTICO AO ABRIR ABA
        def simulate_click():
            # Simular um clique no editor SQL para forçar foco
            try:
                self.sql_text.event_generate('<Button-1>', x=1, y=1)
                self.sql_text.focus_set()
                self.sql_text.mark_set('insert', 'end')
            except:
                pass
        
        # CRIAR BOTÃO INVISÍVEL PARA "ATIVAR" A DIGITAÇÃO
        self.focus_activator = tk.Button(self.root, text="", command=lambda: None, width=0, height=0)
        
        def activate_focus():
            # Simular clique no botão invisível e depois no editor
            try:
                self.focus_activator.invoke()
                self.root.after(10, simulate_click)
            except: 
                pass
        
        # FORÇAR FOCO QUANDO A ABA FOR SELECIONADA
        def on_tab_selected(event):
            # Verificar se estamos na aba de SQL
            try:
                current_tab = self.notebook.select()
                tab_text = self.notebook.tab(current_tab, "text")
                if "SQL" in tab_text:
                    # Ativar foco com simulação de botão
                    self.root.after(10, activate_focus)
            except:
                pass
        
        self.notebook.bind('<<NotebookTabChanged>>', on_tab_selected)
        
        # Simular clique inicial ao criar a aba
        self.root.after(200, activate_focus)
        
        # Frame de botões do editor
        editor_buttons = tk.Frame(sql_frame, bg=self.styles.colors['card'])
        editor_buttons.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        execute_btn = tk.Button(editor_buttons, text="▶️ Executar Query", command=self.execute_sql,
                               bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                               font=self.styles.fonts['button'], relief='flat',
                               padx=20, pady=10, cursor='hand2')
        execute_btn.pack(side=tk.LEFT)
        
        # Coluna direita - Resultados
        right_frame = tk.Frame(main_container, bg=self.styles.colors['background'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Frame dos resultados
        results_frame = tk.LabelFrame(right_frame, text="Resultados da Consulta", 
                                     bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                     font=self.styles.fonts['heading'], relief='solid', bd=1)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Container para resultados
        results_container = tk.Frame(results_frame, bg=self.styles.colors['card'])
        results_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Frame para a tabela de resultados
        table_frame = tk.Frame(results_container, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview estilizado para resultados
        self.results_tree = ttk.Treeview(table_frame, show='headings', style='Results.Treeview')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Frame de informações e exportação
        info_frame = tk.Frame(results_container, bg=self.styles.colors['card'])
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Label de informações
        self.results_info = tk.Label(info_frame, text="Execute uma query para ver os resultados",
                                    bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                                    font=self.styles.fonts['small'])
        self.results_info.pack(side=tk.LEFT)
        
        # Configurar weights do container principal
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
    def execute_sql(self):
        if not self.connected or self.conn is None:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        sql = self.sql_text.get(1.0, tk.END).strip()
        
        if not sql:
            messagebox.showwarning("Aviso", "Digite uma consulta SQL!")
            return
        
        # Remover comentários e espaços em branco do início para validação
        sql_clean = sql
        lines = sql.split('\n')
        first_non_comment_line = None
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('--'):
                first_non_comment_line = stripped
                break
        
        if not first_non_comment_line:
            messagebox.showwarning("Aviso", "Digite uma consulta SQL válida!")
            return
        
        # Verificar se contém apenas comandos de consulta permitidos
        sql_upper = sql_clean.upper()
        forbidden_commands = ['ALTER', 'DROP', 'UPDATE', 'DELETE', 'INSERT', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
        
        # Verificar se algum comando proibido está no SQL (em qualquer posição)
        for cmd in forbidden_commands:
            # Usar regex para detectar comando como palavra completa
            pattern = r'\b' + cmd + r'\b'
            if re.search(pattern, sql_upper):
                messagebox.showerror("Erro", f"Comando '{cmd}' não é permitido no console SQL!\n\nApenas consultas SELECT são permitidas.")
                return
        
        # Verificar se a primeira linha não-comentário começa com SELECT ou WITH (para CTEs)
        first_line_upper = first_non_comment_line.upper()
        if not (first_line_upper.startswith('SELECT') or first_line_upper.startswith('WITH')):
            messagebox.showerror("Erro", "Apenas consultas SELECT são permitidas no console SQL!\n\nUse SELECT para consultar dados.")
            return
        
        # VALIDAÇÃO: Verificar se está usando views para tabelas principais
        # Tabelas que devem ser acessadas apenas via views
        restricted_tables = {
            'citizen': 'citizen_active',
            'vehicle': 'vehicle_active', 
            'sensor': 'sensor_active',
            'app_user': 'app_user_active'
        }
        
        # Padrões para detectar uso de tabelas restritas
        for table, view in restricted_tables.items():
            # Detectar FROM table ou JOIN table (mas não FROM view ou JOIN view)
            patterns = [
                rf'\bFROM\s+{table}\b(?!\s*\()',  # FROM table (não seguido de parentese)
                rf'\bJOIN\s+{table}\b(?!\s*\()',   # JOIN table (não seguido de parentese)
                rf'\b{table}\s+AS\b',              # table AS
                rf'\b{table}\s+\w+\s*,',           # table alias com vírgula
            ]
            
            for pattern in patterns:
                if re.search(pattern, sql_clean, re.IGNORECASE):
                    messagebox.showerror(
                        "Erro de Acesso Restrito", 
                        f"❌ Tabela '{table}' não pode ser consultada diretamente!\n\n"
                        f"📋 Use a view '{view}' em vez da tabela base.\n\n"
                        f"🔒 Esta restrição garante que dados soft-deletados não sejam exibidos.\n\n"
                        f"✅ Exemplo correto: SELECT * FROM {view};"
                    )
                    return
            
        try:
            # Garantir que a conexão está válida
            if self.conn.closed:
                messagebox.showerror("Erro", "Conexão com banco de dados foi fechada. Conecte-se novamente.")
                return
                
            # Iniciar transação
            self.conn.autocommit = False
            
            # Criar cursor com psycopg2.extras.DictCursor
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(sql)
            results = cur.fetchall()
            
            # Commit da transação
            self.conn.commit()
            
            # Voltar ao modo autocommit para outras operações
            self.conn.autocommit = True
            
            # Limpar treeview
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            if results:
                # Configurar colunas
                columns = list(results[0].keys())
                self.results_tree['columns'] = columns
                
                # Configurar headings
                for col in columns:
                    self.results_tree.heading(col, text=col.replace('_', ' ').title())
                    self.results_tree.column(col, width=120, minwidth=80)
                
                # Inserir dados
                for i, row in enumerate(results):
                    values = [str(row.get(col, '')) if row.get(col, '') is not None else 'NULL' for col in columns]
                    tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                    self.results_tree.insert('', tk.END, values=values, tags=(tag,))
                
                # Atualizar informações
                self.results_info.config(text=f"✅ {len(results)} registros encontrados")
                
            else:
                # Sem resultados
                self.results_info.config(text="📭 Nenhum registro encontrado")
                
        except psycopg2.Error as e:
            # Rollback automático em caso de erro
            try:
                self.conn.rollback()
                self.conn.autocommit = True
            except:
                pass
            
            # Limpar treeview em caso de erro
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
        except Exception as e:
            # Rollback automático em caso de erro
            try:
                self.conn.rollback()
                self.conn.autocommit = True
            except:
                pass
            
            # Limpar treeview em caso de erro
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.results_info.config(text=f"❌ Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao executar consulta: {str(e)}\n\n🔄 Rollback automático realizado!")
            
    def show_settings(self):
        """Exibe a aba de configurações do sistema"""
        self.clear_content()
        
        # Header estilizado
        header_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        header_frame.pack(fill=tk.X, padx=0, pady=(20, 10))
        
        title_label = tk.Label(header_frame, text="⚙️ Configurações do Sistema", 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                              font=self.styles.fonts['title'])
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Botão de salvar
        save_btn = tk.Button(header_frame, text="💾 Salvar Configurações", command=self.save_settings,
                            bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                            font=self.styles.fonts['button'], relief='flat',
                            padx=15, pady=8, cursor='hand2')
        save_btn.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Container principal com scrollbar
        main_container = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Canvas e Scrollbar
        canvas = tk.Canvas(main_container, bg=self.styles.colors['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.styles.colors['background'])
        
        # Configurar scrollbar
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Criar window no canvas que ocupa toda largura
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=10000)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empacotar canvas e scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Atualizar largura do scrollable_frame para ocupar canvas inteiro
        def update_canvas_width(event=None):
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:  # Só atualiza se canvas tiver largura válida
                canvas.itemconfig(canvas.find_all()[0], width=canvas_width)
                # Forçar atualização dos LabelFrames
                scrollable_frame.update_idletasks()
        
        # Agendar atualização após a janela ser exibida
        main_container.after(100, update_canvas_width)
        main_container.bind('<Configure>', lambda e: main_container.after(50, update_canvas_width))
        
        # Carregar configurações salvas
        self.load_settings()
        
        # Funções para mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Seção de Preferências da Interface
        ui_frame = tk.LabelFrame(scrollable_frame, text="🎨 Preferências da Interface", 
                                 bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                 font=self.styles.fonts['heading'], relief='solid', bd=1)
        ui_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Preferências em grid
        ui_grid = tk.Frame(ui_frame, bg=self.styles.colors['card'])
        ui_grid.pack(fill=tk.X, padx=10, pady=8)
        
        # Tema da Interface
        tk.Label(ui_grid, text="Tema:", bg=self.styles.colors['card'], 
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(row=0, column=0, sticky='w', pady=2)
        
        self.theme_var = tk.StringVar(value="Escuro")
        theme_options = ["Escuro", "Claro", "Azul"]
        self.theme_combo = ttk.Combobox(ui_grid, textvariable=self.theme_var, 
                                        values=theme_options, state="readonly", width=15)
        self.theme_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Idioma
        tk.Label(ui_grid, text="Idioma:", bg=self.styles.colors['card'], 
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(row=1, column=0, sticky='w', pady=2)
        
        self.lang_var = tk.StringVar(value="Português")
        lang_options = ["Português", "English", "Español"]
        self.lang_combo = ttk.Combobox(ui_grid, textvariable=self.lang_var, 
                                       values=lang_options, state="readonly", width=15)
        self.lang_combo.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Seção de Sistema
        system_frame = tk.LabelFrame(scrollable_frame, text="🔧 Configurações do Sistema", 
                                    bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                    font=self.styles.fonts['heading'], relief='solid', bd=1)
        system_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Sistema em grid
        system_grid = tk.Frame(system_frame, bg=self.styles.colors['card'])
        system_grid.pack(fill=tk.X, padx=10, pady=8)
        
        # Auto-save
        self.autosave_var = tk.BooleanVar(value=True)
        autosave_check = tk.Checkbutton(system_grid, text="Auto-save automático", 
                                       variable=self.autosave_var, bg=self.styles.colors['card'],
                                       fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal'],
                                       selectcolor=self.styles.colors['primary'])
        autosave_check.grid(row=0, column=0, sticky='w', pady=2)
        
        # Notificações
        self.notifications_var = tk.BooleanVar(value=True)
        notifications_check = tk.Checkbutton(system_grid, text="Habilitar notificações", 
                                           variable=self.notifications_var, bg=self.styles.colors['card'],
                                           fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal'],
                                           selectcolor=self.styles.colors['primary'])
        notifications_check.grid(row=1, column=0, sticky='w', pady=2)
        
        # Seção de Backup
        backup_frame = tk.LabelFrame(scrollable_frame, text="💾 Backup e Restauração", 
                                     bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                     font=self.styles.fonts['heading'], relief='solid', bd=1)
        backup_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Botões de backup
        backup_buttons_frame = tk.Frame(backup_frame, bg=self.styles.colors['card'])
        backup_buttons_frame.pack(fill=tk.X, padx=10, pady=8)
        
        backup_btn = tk.Button(backup_buttons_frame, text="📦 Fazer Backup", command=self.backup_database,
                              bg=self.styles.colors['primary'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=12, pady=6, cursor='hand2')
        backup_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        restore_btn = tk.Button(backup_buttons_frame, text="📂 Restaurar Backup", command=self.restore_database,
                               bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                               font=self.styles.fonts['button'], relief='flat',
                               padx=12, pady=6, cursor='hand2')
        restore_btn.pack(side=tk.LEFT)
        
        # Informações do Sistema
        info_frame = tk.LabelFrame(scrollable_frame, text="ℹ️ Informações do Sistema", 
                                   bg=self.styles.colors['card'], fg=self.styles.colors['text_primary'],
                                   font=self.styles.fonts['heading'], relief='solid', bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = f"""
Versão: SmartCityOS v1.0.0
Python: {sys.version.split()[0]}
PostgreSQL: 18.0
Último acesso: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        
        info_label = tk.Label(info_frame, text=info_text, bg=self.styles.colors['card'], 
                             fg=self.styles.colors['text_secondary'], font=self.styles.fonts['small'],
                             justify=tk.LEFT, height=5)
        info_label.pack(padx=10, pady=(0, 10))
    
    def check_connection(self):
        try:
            # Usar a mesma lógica da função connect_to_db
            conn_info = self.get_connection_string()
            
            # Testar conexão e armazenar
            self.conn = psycopg2.connect(conn_info)
            
            # Testar se funciona
            with self.conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()
                    
            self.connected = True
            self.connection_status.config(text="🟢 Conectado")
            self.connect_btn.config(text="Desconectar")
            self.status_label.config(text=f"Conectado ao PostgreSQL - {version[0].split(',')[0]}")
            
        except psycopg2.Error as e:
            self.connected = False
            self.conn = None
            self.connection_status.config(text="🔴 Desconectado")
            self.connect_btn.config(text="Conectar")
            self.status_label.config(text=f"Erro de conexão PostgreSQL: {str(e)}")
        except Exception as e:
            self.connected = False
            self.conn = None
            self.connection_status.config(text="🔴 Desconectado")
            self.connect_btn.config(text="Conectar")
            self.status_label.config(text=f"Erro de conexão: {str(e)}")
            
    def get_connection_string(self):
        """Retorna string de conexão com o banco usando a mesma lógica do connect_to_db"""
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST')
        
        if not all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST]):
            raise Exception("Variáveis de ambiente do banco não configuradas")
        
        return f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST}"
            
    def toggle_connection(self):
        if self.connected:
            # Fechar conexão
            if self.conn:
                try:
                    self.conn.close()
                except:
                    pass
            self.connected = False
            self.conn = None
            self.connection_status.config(text="🔴 Desconectado")
            self.connect_btn.config(text="Conectar")
            self.status_label.config(text="Desconectado do banco de dados")
        else:
            self.check_connection()

    def load_settings(self):
        """Carrega as configurações salvas do arquivo settings.json"""
        try:
            import json
            import os
            
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                
                # Carregar configurações do banco
                if 'database' in settings:
                    db_config = settings['database']
                    if hasattr(self, 'host_entry'):
                        self.host_entry.delete(0, tk.END)
                        self.host_entry.insert(0, db_config.get('host', 'localhost'))
                    
                    if hasattr(self, 'port_entry'):
                        self.port_entry.delete(0, tk.END)
                        self.port_entry.insert(0, db_config.get('port', '5432'))
                    
                    if hasattr(self, 'dbname_entry'):
                        self.dbname_entry.delete(0, tk.END)
                        self.dbname_entry.insert(0, db_config.get('dbname', 'smart_city_os'))
                
                # Carregar configurações da interface
                if 'ui' in settings:
                    ui_config = settings['ui']
                    if hasattr(self, 'theme_var'):
                        self.theme_var.set(ui_config.get('theme', 'Escuro'))
                    
                    if hasattr(self, 'lang_var'):
                        self.lang_var.set(ui_config.get('language', 'Português'))
                
                # Carregar configurações do sistema
                if 'system' in settings:
                    system_config = settings['system']
                    if hasattr(self, 'autosave_var'):
                        self.autosave_var.set(system_config.get('autosave', True))
                    
                    if hasattr(self, 'notifications_var'):
                        self.notifications_var.set(system_config.get('notifications', True))
                
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            # Continuar com valores padrão
        
    def save_settings(self):
        """Salva as configurações do sistema"""
        try:
            # Coletar configurações
            settings = {
                'database': {
                    'host': self.host_entry.get(),
                    'port': self.port_entry.get(),
                    'dbname': self.dbname_entry.get()
                },
                'ui': {
                    'theme': self.theme_var.get(),
                    'language': self.lang_var.get()
                },
                'system': {
                    'autosave': self.autosave_var.get(),
                    'notifications': self.notifications_var.get()
                }
            }
            
            # Salvar em arquivo JSON
            import json
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Sucesso", "✅ Configurações salvas com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"❌ Erro ao salvar configurações: {str(e)}")
    
    def backup_database(self):
        """Faz backup do banco de dados usando SQL nativo"""
        try:
            if not self.connected or self.conn is None:
                messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
                return
            
            # Pedir local para salvar backup
            from tkinter import filedialog
            backup_file = filedialog.asksaveasfilename(
                title="Salvar Backup",
                defaultextension=".sql",
                filetypes=[("Arquivos SQL", "*.sql"), ("Todos os Arquivos", "*.*")]
            )
            
            if not backup_file:
                return
            
            messagebox.showinfo("Backup", "🔄 Iniciando backup do banco de dados...")
            
            try:
                # Garantir que a conexão está válida
                if self.conn.closed:
                    messagebox.showerror("Erro", "Conexão com banco de dados foi fechada. Conecte-se novamente.")
                    return
                
                # Criar cursor
                cur = self.conn.cursor()
                
                # Obter lista de todas as tabelas
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cur.fetchall()]
                
                # Escrever backup em arquivo SQL
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(f"-- SmartCityOS Database Backup\n")
                    f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"-- Database: {self.dbname_entry.get() if hasattr(self, 'dbname_entry') else 'smart_city_os'}\n")
                    f.write(f"-- Total tables: {len(tables)}\n\n")
                    
                    # Para cada tabela, fazer dump dos dados
                    for table in tables:
                        f.write(f"--\n-- Data for table: {table}\n--\n\n")
                        
                        try:
                            # Obter estrutura da tabela
                            cur.execute(f"""
                                SELECT column_name, data_type 
                                FROM information_schema.columns 
                                WHERE table_name = '{table}' 
                                AND table_schema = 'public'
                                ORDER BY ordinal_position
                            """)
                            columns = [row[0] for row in cur.fetchall()]
                            
                            if not columns:
                                f.write(f"-- Table {table} has no columns or doesn't exist\n\n")
                                continue
                            
                            # Obter dados da tabela
                            cur.execute(f"SELECT * FROM {table}")
                            rows = cur.fetchall()
                            
                            if rows:
                                # Gerar INSERT statements
                                for row in rows:
                                    # Escapar valores para SQL
                                    values = []
                                    for value in row:
                                        if value is None:
                                            values.append('NULL')
                                        elif isinstance(value, str):
                                            # Escapar aspas simples
                                            escaped_value = value.replace("'", "''")
                                            values.append(f"'{escaped_value}'")
                                        elif isinstance(value, bool):
                                            values.append('TRUE' if value else 'FALSE')
                                        elif isinstance(value, (int, float)):
                                            values.append(str(value))
                                        else:
                                            # Para outros tipos (JSON, etc.)
                                            if isinstance(value, dict):
                                                import json
                                                escaped_json = json.dumps(value).replace("'", "''")
                                                values.append(f"'{escaped_json}'")
                                            else:
                                                values.append(f"'{str(value)}'")
                                    
                                    insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                                    f.write(insert_sql + "\n")
                                
                                f.write(f"\n-- {len(rows)} rows backed up for table {table}\n\n")
                            else:
                                f.write(f"-- Table {table} is empty\n\n")
                                
                        except Exception as table_error:
                            f.write(f"-- Error backing up table {table}: {str(table_error)}\n\n")
                            continue
                
                # Commit da transação
                self.conn.commit()
                
                messagebox.showinfo("Backup", f"✅ Backup concluído com sucesso!\n\nArquivo: {backup_file}\n\nTabelas backup: {len(tables)}")
                
            except Exception as db_error:
                # Rollback em caso de erro
                try:
                    self.conn.rollback()
                except:
                    pass
                messagebox.showerror("Erro", f"❌ Erro ao acessar banco de dados: {str(db_error)}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"❌ Erro ao fazer backup: {str(e)}")
    
    def restore_database(self):
        """Restaura o banco de dados usando SQL nativo"""
        try:
            if not self.connected or self.conn is None:
                messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
                return
            
            # Pedir arquivo de backup
            from tkinter import filedialog
            backup_file = filedialog.askopenfilename(
                title="Selecionar Arquivo de Backup",
                filetypes=[("Arquivos SQL", "*.sql"), ("Todos os Arquivos", "*.*")]
            )
            
            if not backup_file:
                return
            
            # Confirmar restauração
            if not messagebox.askyesno(
                "Confirmar Restauração", 
                "⚠️ ATENÇÃO: Esta operação irá substituir todos os dados atuais!\n\nDeseja continuar?"
            ):
                return
            
            messagebox.showinfo("Restauração", "🔄 Iniciando restauração do banco de dados...")
            
            try:
                # Garantir que a conexão está válida
                if self.conn.closed:
                    messagebox.showerror("Erro", "Conexão com banco de dados foi fechada. Conecte-se novamente.")
                    return
                
                # Ler arquivo de backup
                with open(backup_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Criar cursor
                cur = self.conn.cursor()
                
                # Dividir o conteúdo em comandos SQL individuais
                sql_commands = []
                current_command = ""
                
                for line in sql_content.split('\n'):
                    line = line.strip()
                    
                    # Ignorar comentários e linhas vazias
                    if line.startswith('--') or not line:
                        continue
                    
                    # Adicionar linha ao comando atual
                    current_command += line + " "
                    
                    # Se a linha termina com ;, comando está completo
                    if line.endswith(';'):
                        sql_commands.append(current_command.strip())
                        current_command = ""
                
                # Executar cada comando SQL
                success_count = 0
                error_count = 0
                errors = []
                
                for i, command in enumerate(sql_commands):
                    if not command.strip():
                        continue
                    
                    try:
                        cur.execute(command)
                        success_count += 1
                    except Exception as cmd_error:
                        error_count += 1
                        errors.append(f"Comando {i+1}: {str(cmd_error)}")
                        # Continuar com outros comandos mesmo se um falhar
                        continue
                
                # Commit da transação
                self.conn.commit()
                
                # Mostrar resultado
                result_msg = f"✅ Restauração concluída!\n\n"
                result_msg += f"Comandos executados com sucesso: {success_count}\n"
                result_msg += f"Comandos com erro: {error_count}\n"
                result_msg += f"Arquivo: {backup_file}"
                
                if errors and len(errors) <= 5:  # Mostrar até 5 erros
                    result_msg += f"\n\nErros encontrados:\n" + "\n".join(errors[:5])
                elif errors:
                    result_msg += f"\n\nErros encontrados: {len(errors)} (primeiros 5 mostrados)"
                    result_msg += "\n" + "\n".join(errors[:5])
                
                if error_count == 0:
                    messagebox.showinfo("Restauração", result_msg + "\n\n🎉 Todos os dados foram restaurados com sucesso!")
                else:
                    messagebox.showwarning("Restauração", result_msg + "\n\n⚠️ Alguns comandos falharam, mas a restauração foi concluída.")
                
            except Exception as db_error:
                # Rollback em caso de erro
                try:
                    self.conn.rollback()
                except:
                    pass
                messagebox.showerror("Erro", f"❌ Erro ao acessar banco de dados: {str(db_error)}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"❌ Erro ao restaurar: {str(e)}")

    def clear_sql(self):
        """Limpa o editor SQL completamente"""
        try:
            # Limpar completamente
            self.sql_text.delete(1.0, tk.END)
            
            # Inserir texto inicial
            self.sql_text.insert(tk.END, "-- Digite sua consulta SQL aqui\n")
           
            # Configurar tag de comentário
            self.sql_text.tag_add("comment", "1.0", "1.end")
            self.sql_text.tag_config("comment", foreground='#616E88')
            
            # FORÇAR FOCO
            self.sql_text.focus_set()
            self.sql_text.mark_set('insert', 'end')
            
            # Limpar resultados
            if hasattr(self, 'results_tree'):
                for item in self.results_tree.get_children():
                    self.results_tree.delete(item)
            
            if hasattr(self, 'results_info'):
                self.results_info.config(text="Execute uma query para ver os resultados")
            
            if hasattr(self, 'export_btn'):
                self.export_btn.config(state='disabled')
                
        except Exception as e:
            print(f"Erro ao limpar SQL: {e}")
            messagebox.showerror("Erro", f"Erro ao limpar editor SQL: {str(e)}")
        
    def load_sql_example(self):
        """Carrega um exemplo de query SQL no editor"""
        examples = [
            "SELECT COUNT(*) as total_citizens FROM citizen_active;",
            "SELECT * FROM vehicle_active WHERE allowed = TRUE;",
            "SELECT v.license_plate, c.first_name FROM vehicle_active v JOIN citizen_active c ON v.citizen_id = c.id;",
            "SELECT status, COUNT(*) FROM fine GROUP BY status;",
            "SELECT type, COUNT(*) FROM sensor_active GROUP BY type ORDER BY COUNT DESC;",
            "SELECT username, created_at FROM app_user_active ORDER BY created_at DESC LIMIT 5;",
            "SELECT * FROM citizen_active WHERE debt > 0 ORDER BY debt DESC;",
            "SELECT s.type, s.location, COUNT(r.id) as readings FROM sensor_active s LEFT JOIN reading r ON s.id = r.sensor_id GROUP BY s.id;"
        ]
        
        try:
            # Limpar e inserir exemplo
            self.sql_text.delete(1.0, tk.END)
            example = examples[0]  # Pode ser randomizado depois
            self.sql_text.insert(tk.END, example)
            
            # FORÇAR FOCO
            self.sql_text.focus_set()
            self.sql_text.mark_set('insert', 'end')
            
        except Exception as e:
            print(f"Erro ao carregar exemplo: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar exemplo SQL: {str(e)}")

    def export_results(self):
        """Exporta resultados para xlsx ou csv"""
        query = self.sql_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Aviso", "Digite uma consulta SQL!")
            return
           
        try:
            # import csv
            from tkinter import filedialog
            
            df_query = pd.read_sql(query, self.conection_string)
            # Dialog para salvar arquivo
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Exportar Resultados"
            )
            
            if filename:
                
                if filename.endswith(".xlsx"):
                    df_query.to_excel(filename, index=False)
                elif filename.endswith(".csv"):
                    df_query.to_csv(filename, index=False)
                messagebox.showinfo("Sucesso", f"Dados exportados para {filename}")
                self.status_label.config(text=f"Dados exportados para {filename}")
                
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
            print('Erro ao exportar: ', e)
        
    def add_citizen_dialog(self):
        """Abre diálogo para adicionar novo cidadão"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Adicionar Cidadão")
        dialog.geometry("650x700")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['primary'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="👤 Novo Cidadão", 
                        bg=self.styles.colors['primary'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame principal
        main_form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        main_form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variáveis
        vars = {
            'username': tk.StringVar(),
            'password': tk.StringVar(),
            'first_name': tk.StringVar(),
            'last_name': tk.StringVar(),
            'cpf': tk.StringVar(),
            'birth_date': tk.StringVar(),
            'email': tk.StringVar(),
            'phone': tk.StringVar(),
            'state': tk.StringVar(),
            'city': tk.StringVar(),
            'neighborhood': tk.StringVar(),
            'street': tk.StringVar(),
            'number': tk.StringVar(),
            'complement': tk.StringVar(),
            'wallet_balance': tk.StringVar(value="0.00")
        }
        
        # Seção 1: Dados Pessoais
        personal_frame = tk.LabelFrame(main_form_frame, text="👤 Dados Pessoais", 
                                      bg=self.styles.colors['background'], fg=self.styles.colors['text_primary'],
                                      font=self.styles.fonts['heading'], relief='solid', bd=1)
        personal_frame.pack(fill=tk.X, pady=(0, 15))
        
        personal_fields = [
            ("🔐 Nome de Usuário", "username", "Digite o nome de usuário"),
            ("🔒 Senha", "password", "Digite a senha"),
            ("👤 Nome", "first_name", "Digite o nome"),
            ("👥 Sobrenome", "last_name", "Digite o sobrenome"),
            ("📋 CPF", "cpf", "Digite o CPF (11 dígitos)"),
            ("🎂 Data de Nascimento", "birth_date", "DD/MM/AAAA")
        ]
        
        for i, (label, key, placeholder) in enumerate(personal_fields):
            tk.Label(personal_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', padx=10, pady=(10 if i == 0 else 5))
            
            entry = tk.Entry(personal_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
            entry.grid(row=i, column=1, pady=5, padx=(10, 10), sticky='ew')
            if key in ['password']:
                entry.config(show='*')
        
        personal_frame.columnconfigure(1, weight=1)
        
        # Seção 2: Contato
        contact_frame = tk.LabelFrame(main_form_frame, text="📞 Contato", 
                                    bg=self.styles.colors['background'], fg=self.styles.colors['text_primary'],
                                    font=self.styles.fonts['heading'], relief='solid', bd=1)
        contact_frame.pack(fill=tk.X, pady=(0, 15))
        
        contact_fields = [
            ("📧 Email", "email", "Digite o email"),
            ("📱 Telefone", "phone", "Digite o telefone")
        ]
        
        for i, (label, key, placeholder) in enumerate(contact_fields):
            tk.Label(contact_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', padx=10, pady=(10 if i == 0 else 5))
            
            entry = tk.Entry(contact_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
            entry.grid(row=i, column=1, pady=5, padx=(10, 10), sticky='ew')
        
        contact_frame.columnconfigure(1, weight=1)
        
        # Seção 3: Endereço
        address_frame = tk.LabelFrame(main_form_frame, text="🏠 Endereço", 
                                     bg=self.styles.colors['background'], fg=self.styles.colors['text_primary'],
                                     font=self.styles.fonts['heading'], relief='solid', bd=1)
        address_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Primeira linha do endereço
        address_row1 = tk.Frame(address_frame, bg=self.styles.colors['background'])
        address_row1.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(address_row1, text="🏠 Estado:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(side=tk.LEFT, padx=(0, 5))
        state_entry = tk.Entry(address_row1, textvariable=vars['state'], font=self.styles.fonts['normal'], width=5)
        state_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(address_row1, text="🏙️ Cidade:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(side=tk.LEFT, padx=(0, 5))
        city_entry = tk.Entry(address_row1, textvariable=vars['city'], font=self.styles.fonts['normal'], width=20)
        city_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(address_row1, text="🏘️ Bairro:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(side=tk.LEFT, padx=(0, 5))
        neighborhood_entry = tk.Entry(address_row1, textvariable=vars['neighborhood'], font=self.styles.fonts['normal'], width=15)
        neighborhood_entry.pack(side=tk.LEFT)
        
        # Segunda linha do endereço
        address_row2 = tk.Frame(address_frame, bg=self.styles.colors['background'])
        address_row2.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(address_row2, text="🛣️ Rua:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(side=tk.LEFT, padx=(0, 5))
        street_entry = tk.Entry(address_row2, textvariable=vars['street'], font=self.styles.fonts['normal'], width=25)
        street_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(address_row2, text="🔢 Número:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(side=tk.LEFT, padx=(0, 5))
        number_entry = tk.Entry(address_row2, textvariable=vars['number'], font=self.styles.fonts['normal'], width=8)
        number_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(address_row2, text="📝 Complemento:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(side=tk.LEFT, padx=(0, 5))
        complement_entry = tk.Entry(address_row2, textvariable=vars['complement'], font=self.styles.fonts['normal'], width=18)
        complement_entry.pack(side=tk.LEFT)
        
        # Seção 4: Financeiro
        financial_frame = tk.LabelFrame(main_form_frame, text="💰 Financeiro", 
                                       bg=self.styles.colors['background'], fg=self.styles.colors['text_primary'],
                                       font=self.styles.fonts['heading'], relief='solid', bd=1)
        financial_frame.pack(fill=tk.X, pady=(0, 15))
        
        financial_fields = [
            ("💰 Saldo Inicial (R$)", "wallet_balance", "0.00")
        ]
        
        for i, (label, key, placeholder) in enumerate(financial_fields):
            tk.Label(financial_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', padx=10, pady=(10 if i == 0 else 5))
            
            entry = tk.Entry(financial_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
            entry.grid(row=i, column=1, pady=5, padx=(10, 10), sticky='ew')
        
        financial_frame.columnconfigure(1, weight=1)
        
        # Botões
        button_frame = tk.Frame(main_form_frame, bg=self.styles.colors['background'])
        button_frame.pack(fill=tk.X, pady=20)
        
        def save_citizen():
            try:
                # Validar campos
                username = vars['username'].get().strip()
                password = vars['password'].get().strip()
                first_name = vars['first_name'].get().strip()
                last_name = vars['last_name'].get().strip()
                cpf = vars['cpf'].get().strip()
                birth_date = vars['birth_date'].get().strip()
                email = vars['email'].get().strip()
                phone = vars['phone'].get().strip()
                state = vars['state'].get().strip()
                city = vars['city'].get().strip()
                neighborhood = vars['neighborhood'].get().strip()
                street = vars['street'].get().strip()
                number = vars['number'].get().strip()
                complement = vars['complement'].get().strip()
                
                # Montar endereço completo
                address_parts = [street, number, neighborhood, city, state]
                if complement:
                    address_parts.append(complement)
                address = ', '.join(address_parts)
                
                if not all([username, password, first_name, last_name, cpf, email, state, city, street]):
                    messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                    return
                
                # Validar CPF
                cpf_clean = cpf.replace('.', '').replace('-', '')
                if len(cpf_clean) != 11 or not cpf_clean.isdigit():
                    messagebox.showerror("Erro", "CPF inválido! Deve ter 11 dígitos.")
                    return
                
                # Validar data
                try:
                    from datetime import datetime
                    birth_date_obj = datetime.strptime(birth_date, '%d/%m/%Y').date()
                except:
                    messagebox.showerror("Erro", "Data de nascimento inválida! Use DD/MM/AAAA")
                    return
                
                # Verificar se username já existe (apenas em usuários ativos)
                if not self.is_username_available(username):
                    messagebox.showerror("Erro", f"Username '{username}' já está em uso! Escolha outro.")
                    return
                
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Inserir em app_user primeiro (sem hash temporariamente)
                        password_hash = password.encode().decode()  # Temporário sem bcrypt
                        
                        cur.execute("""
                            INSERT INTO app_user (username, password_hash) 
                            VALUES (%s, %s) RETURNING id
                        """, (username, password_hash))
                        app_user_id = cur.fetchone()[0]
                        
                        # Inserir em citizen
                        cur.execute("""
                            INSERT INTO citizen (
                                app_user_id, first_name, last_name, cpf, birth_date, 
                                email, phone, address, wallet_balance
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            app_user_id,
                            first_name,
                            last_name,
                            cpf_clean,
                            birth_date_obj,
                            email,
                            phone,
                            address,  # Endereço completo concatenado
                            float(vars['wallet_balance'].get())
                        ))
                        
                        conn.commit()
                
                messagebox.showinfo("Sucesso", "Cidadão adicionado com sucesso!")
                dialog.destroy()
                self.show_citizens()  # Atualizar a lista
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao adicionar cidadão: {str(e)}")
        
        tk.Button(button_frame, text="💾 Salvar", command=save_citizen,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
    def search_citizen_by_cpf(self):
        """Busca cidadão por CPF"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔍 Buscar Cidadão por CPF")
        dialog.geometry("400x200")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['primary'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🔍 Buscar Cidadão", 
                        bg=self.styles.colors['primary'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # CPF input
        tk.Label(form_frame, text="📋 CPF:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(anchor='w', pady=(0, 5))
        
        cpf_var = tk.StringVar()
        cpf_entry = tk.Entry(form_frame, textvariable=cpf_var, font=self.styles.fonts['normal'])
        cpf_entry.pack(fill=tk.X, pady=(0, 20))
        cpf_entry.focus_set()
        
        def search():
            cpf = cpf_var.get().strip()
            if not cpf:
                messagebox.showerror("Erro", "Digite o CPF para buscar!")
                return
            
            # Remover caracteres não numéricos
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            if len(cpf_clean) != 11:
                messagebox.showerror("Erro", "CPF deve ter 11 dígitos!")
                return
            
            try:
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute("""
                            SELECT c.id, c.first_name, c.last_name, c.email, c.cpf, c.phone,
                                   c.address, c.birth_date, c.wallet_balance, c.debt, c.allowed,
                                   u.username, c.created_at
                            FROM citizen_active c
                            JOIN app_user u ON c.app_user_id = u.id
                            WHERE c.cpf = %s
                        """, (cpf_clean,))
                        citizen = cur.fetchone()
                        
                        if citizen:
                            # Mostrar resultados
                            result_dialog = tk.Toplevel(self.root)
                            result_dialog.title("👤 Cidadão Encontrado")
                            result_dialog.geometry("500x400")
                            result_dialog.configure(bg=self.styles.colors['background'])
                            result_dialog.transient(self.root)
                            result_dialog.grab_set()
                            
                            # Header
                            result_header = tk.Frame(result_dialog, bg=self.styles.colors['success'], height=60)
                            result_header.pack(fill=tk.X)
                            result_header.pack_propagate(False)
                            
                            result_title = tk.Label(result_header, text="✅ Cidadão Encontrado", 
                                                bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                                font=self.styles.fonts['title'])
                            result_title.pack(expand=True)
                            
                            # Info frame
                            info_frame = tk.Frame(result_dialog, bg=self.styles.colors['background'])
                            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                            
                            # Dados do cidadão
                            full_name = f"{citizen['first_name']} {citizen['last_name']}"
                            status = "✅ Ativo" if citizen['allowed'] else "🔴 Inativo"
                            
                            info_text = f"""
👤 **Nome Completo:** {full_name}
📋 **CPF:** {citizen['cpf']}
📧 **Email:** {citizen['email']}
📱 **Telefone:** {citizen['phone'] or 'Não informado'}
🏠 **Endereço:** {citizen['address']}
🎂 **Data Nascimento:** {citizen['birth_date'].strftime('%d/%m/%Y') if citizen['birth_date'] else 'N/A'}
💰 **Saldo:** {format_currency_brl(citizen['wallet_balance']) if citizen['wallet_balance'] else 'R$ 0,00'}
💳 **Dívida:** {format_currency_brl(citizen['debt']) if citizen['debt'] else 'R$ 0,00'}
📊 **Status:** {status}
👤 **Username:** {citizen['username']}
📅 **Cadastro:** {citizen['created_at'].strftime('%d/%m/%Y %H:%M') if citizen['created_at'] else 'N/A'}
                            """
                            
                            info_label = tk.Label(info_frame, text=info_text, bg=self.styles.colors['background'],
                                             fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal'],
                                             justify='left')
                            info_label.pack(anchor='w')
                            
                            # Botão fechar
                            tk.Button(result_dialog, text="✅ Fechar", command=result_dialog.destroy,
                                   bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                   font=self.styles.fonts['button'], padx=20, pady=8).pack(pady=20)
                            
                            dialog.destroy()
                        else:
                            messagebox.showwarning("Não Encontrado", f"Nenhum cidadão encontrado com o CPF {cpf}")
                            
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao buscar cidadão: {str(e)}")
        
        # Botões
        button_frame = tk.Frame(form_frame, bg=self.styles.colors['background'])
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="🔍 Buscar", command=search,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT)
        
        # Enter para buscar
        cpf_entry.bind('<Return>', lambda e: search())
        
    def add_vehicle_dialog(self):
        """Abre diálogo para adicionar novo veículo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Adicionar Veículo")
        dialog.geometry("450x400")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['warning'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🚗 Novo Veículo", 
                        bg=self.styles.colors['warning'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variáveis
        vars = {
            'username': tk.StringVar(),
            'password': tk.StringVar(),
            'license_plate': tk.StringVar(),
            'model': tk.StringVar(),
            'year': tk.StringVar(),
            'citizen_cpf': tk.StringVar()
        }
        
        # Campos do formulário
        fields = [
            ("🔐 Nome de Usuário", "username", "Digite o nome de usuário para o veículo"),
            ("🔒 Senha", "password", "Digite a senha"),
            ("🚗 Placa", "license_plate", "ABC-1234"),
            ("📋 Modelo", "model", "Ex: Fiat Palio"),
            ("📅 Ano", "year", "2024"),
            ("👤 CPF do Proprietário (opcional)", "citizen_cpf", "CPF do cidadão proprietário")
        ]
        
        for i, (label, key, placeholder) in enumerate(fields):
            tk.Label(form_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', pady=5)
            
            entry = tk.Entry(form_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
            entry.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
            if key in ['password']:
                entry.config(show='*')
        
        form_frame.columnconfigure(1, weight=1)
        
        # Botões
        button_frame = tk.Frame(form_frame, bg=self.styles.colors['background'])
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def save_vehicle():
            try:
                # Validar campos obrigatórios
                if not all(vars[k].get().strip() for k in ['username', 'password', 'license_plate', 'model', 'year']):
                    messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                    return
                
                # Validar ano
                try:
                    year = int(vars['year'].get())
                    current_year = 2024
                    if year < 1900 or year > current_year + 1:
                        messagebox.showerror("Erro", f"Ano inválido! Deve estar entre 1900 e {current_year + 1}")
                        return
                except ValueError:
                    messagebox.showerror("Erro", "Ano deve ser um número válido!")
                    return
                
                # Validar placa
                license_plate = vars['license_plate'].get().upper()
                if len(license_plate) < 7:
                    messagebox.showerror("Erro", "Placa muito curta! Mínimo 7 caracteres.")
                    return
                
                citizen_id = None
                # Se CPF foi informado, buscar o cidadão
                if vars['citizen_cpf'].get().strip():
                    cpf_clean = vars['citizen_cpf'].get().replace('.', '').replace('-', '')
                    if len(cpf_clean) != 11 or not cpf_clean.isdigit():
                        messagebox.showerror("Erro", "CPF inválido! Deve ter 11 dígitos.")
                        return
                    
                    with psy.connect(self.get_connection_string()) as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT id FROM citizen_active WHERE cpf = %s", (cpf_clean,))
                            citizen_result = cur.fetchone()
                            if citizen_result:
                                citizen_id = citizen_result[0]
                            else:
                                messagebox.showerror("Erro", "CPF não encontrado no sistema! Cadastre o cidadão primeiro.")
                                return
                
                # Verificar se username já existe (apenas em usuários ativos)
                if not self.is_username_available(vars['username'].get()):
                    messagebox.showerror("Erro", f"Username '{vars['username'].get()}' já está em uso! Escolha outro.")
                    return
                
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Inserir em app_user primeiro (sem hash temporariamente)
                        password_hash = vars['password'].get().encode().decode()  # Temporário sem bcrypt
                        
                        cur.execute("""
                            INSERT INTO app_user (username, password_hash) 
                            VALUES (%s, %s) RETURNING id
                        """, (vars['username'].get(), password_hash))
                        app_user_id = cur.fetchone()[0]
                        
                        # Inserir em vehicle
                        cur.execute("""
                            INSERT INTO vehicle (
                                app_user_id, license_plate, model, year, citizen_id
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, (
                            app_user_id,
                            license_plate,
                            vars['model'].get(),
                            year,
                            citizen_id
                        ))
                        
                        # Se tem proprietário, adicionar relação na vehicle_citizen
                        if citizen_id:
                            cur.execute("""
                                INSERT INTO vehicle_citizen (vehicle_id, citizen_id) 
                                VALUES (currval('vehicle_id_seq'), %s)
                            """, (citizen_id,))
                        
                        conn.commit()
                
                messagebox.showinfo("Sucesso", "Veículo adicionado com sucesso!")
                dialog.destroy()
                self.show_vehicles()  # Atualizar a lista
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao adicionar veículo: {str(e)}")
        
        tk.Button(button_frame, text="💾 Salvar", command=save_vehicle,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
    def search_vehicle_by_plate(self):
        """Busca veículo por placa"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔍 Buscar Veículo por Placa")
        dialog.geometry("400x200")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['primary'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🔍 Buscar Veículo", 
                        bg=self.styles.colors['primary'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Placa input
        tk.Label(form_frame, text="🚗 Placa:", bg=self.styles.colors['background'],
                fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).pack(anchor='w', pady=(0, 5))
        
        plate_var = tk.StringVar()
        plate_entry = tk.Entry(form_frame, textvariable=plate_var, font=self.styles.fonts['normal'])
        plate_entry.pack(fill=tk.X, pady=(0, 20))
        plate_entry.focus_set()
        
        def search():
            plate = plate_var.get().strip().upper()
            if not plate:
                messagebox.showerror("Erro", "Digite a placa para buscar!")
                return
            
            # Validar formato básico da placa (XXX-XXXX ou XXXXXXX)
            import re
            if not re.match(r'^[A-Z]{3}-?[A-Z0-9]{4}$', plate):
                messagebox.showerror("Erro", "Formato de placa inválido! Use XXX-XXXX ou XXXXXXX")
                return
            
            # Padronizar formato
            if len(plate) == 7:
                plate = plate[:3] + '-' + plate[3:]
            
            try:
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute("""
                            SELECT v.id, v.license_plate, v.model, v.year, v.allowed,
                                   u.username, c.first_name, c.last_name, c.cpf,
                                   v.created_at
                            FROM vehicle_active v
                            JOIN app_user u ON v.app_user_id = u.id
                            LEFT JOIN citizen_active c ON v.citizen_id = c.id
                            WHERE v.license_plate = %s
                        """, (plate,))
                        vehicle = cur.fetchone()
                        
                        if vehicle:
                            # Mostrar resultados
                            result_dialog = tk.Toplevel(self.root)
                            result_dialog.title("🚗 Veículo Encontrado")
                            result_dialog.geometry("500x350")
                            result_dialog.configure(bg=self.styles.colors['background'])
                            result_dialog.transient(self.root)
                            result_dialog.grab_set()
                            
                            # Header
                            result_header = tk.Frame(result_dialog, bg=self.styles.colors['success'], height=60)
                            result_header.pack(fill=tk.X)
                            result_header.pack_propagate(False)
                            
                            result_title = tk.Label(result_header, text="✅ Veículo Encontrado", 
                                                bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                                font=self.styles.fonts['title'])
                            result_title.pack(expand=True)
                            
                            # Info frame
                            info_frame = tk.Frame(result_dialog, bg=self.styles.colors['background'])
                            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                            
                            # Dados do veículo
                            status = "✅ Ativo" if vehicle['allowed'] else "🔴 Inativo"
                            owner_name = f"{vehicle['first_name'] or ''} {vehicle['last_name'] or ''}".strip() or 'Não vinculado'
                            
                            info_text = f"""
🚗 **Placa:** {vehicle['license_plate']}
📋 **Modelo:** {vehicle['model']}
📅 **Ano:** {vehicle['year']}
👤 **Proprietário:** {owner_name}
📋 **CPF Proprietário:** {vehicle['cpf'] or 'Não vinculado'}
👤 **Username:** {vehicle['username']}
📊 **Status:** {status}
📅 **Cadastro:** {vehicle['created_at'].strftime('%d/%m/%Y %H:%M') if vehicle['created_at'] else 'N/A'}
                            """
                            
                            info_label = tk.Label(info_frame, text=info_text, bg=self.styles.colors['background'],
                                             fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal'],
                                             justify='left')
                            info_label.pack(anchor='w')
                            
                            # Botão fechar
                            tk.Button(result_dialog, text="✅ Fechar", command=result_dialog.destroy,
                                   bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                                   font=self.styles.fonts['button'], padx=20, pady=8).pack(pady=20)
                            
                            dialog.destroy()
                        else:
                            messagebox.showwarning("Não Encontrado", f"Nenhum veículo encontrado com a placa {plate}")
                            
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao buscar veículo: {str(e)}")
        
        # Botões
        button_frame = tk.Frame(form_frame, bg=self.styles.colors['background'])
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="🔍 Buscar", command=search,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT)
        
        # Enter para buscar
        plate_entry.bind('<Return>', lambda e: search())
        
    def add_sensor_dialog(self):
        """Abre diálogo para adicionar novo sensor"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Adicionar Sensor")
        dialog.geometry("450x350")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['dark'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="📹 Novo Sensor", 
                        bg=self.styles.colors['dark'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variáveis
        vars = {
            'username': tk.StringVar(),
            'password': tk.StringVar(),
            'model': tk.StringVar(),
            'type': tk.StringVar(),
            'location': tk.StringVar()
        }
        
        # Tipos de sensores disponíveis
        sensor_types = ['Câmera', 'Radar', 'LIDAR', 'Sensor de Tráfego', 'Sensor de Velocidade', 'Outro']
        
        # Campos do formulário
        fields = [
            ("🔐 Nome de Usuário", "username", "Digite o nome de usuário para o sensor"),
            ("🔒 Senha", "password", "Digite a senha"),
            ("📋 Modelo", "model", "Ex: IP Camera X100"),
            ("📹 Tipo", "type", sensor_types),
            ("📍 Localização", "location", "Ex: Av. Principal, 1000")
        ]
        
        for i, (label, key, placeholder) in enumerate(fields):
            tk.Label(form_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', pady=5)
            
            if key == 'type':
                # Combobox para tipo
                combo = ttk.Combobox(form_frame, textvariable=vars[key], values=placeholder, 
                                   state="readonly", font=self.styles.fonts['normal'])
                combo.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                combo.current(0)
            else:
                entry = tk.Entry(form_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
                entry.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                if key in ['password']:
                    entry.config(show='*')
        
        form_frame.columnconfigure(1, weight=1)
        
        # Botões
        button_frame = tk.Frame(form_frame, bg=self.styles.colors['background'])
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def save_sensor():
            try:
                # Validar campos obrigatórios
                if not all(vars[k].get().strip() for k in ['username', 'password', 'model', 'type', 'location']):
                    messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                    return
                
                # Verificar se username já existe (apenas em usuários ativos)
                if not self.is_username_available(vars['username'].get()):
                    messagebox.showerror("Erro", f"Username '{vars['username'].get()}' já está em uso! Escolha outro.")
                    return
                
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Inserir em app_user primeiro (sem hash temporariamente)
                        password_hash = vars['password'].get().encode().decode()  # Temporário sem bcrypt
                        
                        cur.execute("""
                            INSERT INTO app_user (username, password_hash) 
                            VALUES (%s, %s) RETURNING id
                        """, (vars['username'].get(), password_hash))
                        app_user_id = cur.fetchone()[0]
                        
                        # Inserir em sensor
                        cur.execute("""
                            INSERT INTO sensor (
                                app_user_id, model, type, location
                            ) VALUES (%s, %s, %s, %s)
                        """, (
                            app_user_id,
                            vars['model'].get(),
                            vars['type'].get(),
                            vars['location'].get()
                        ))
                        
                        conn.commit()
                
                messagebox.showinfo("Sucesso", "Sensor adicionado com sucesso!")
                dialog.destroy()
                self.show_sensors()  # Atualizar a lista
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao adicionar sensor: {str(e)}")
        
        tk.Button(button_frame, text="💾 Salvar", command=save_sensor,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
    def add_incident_dialog(self):
        """Abre diálogo para registrar novo incidente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Registrar Incidente")
        dialog.geometry("500x400")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['accent'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="⚠️ Novo Incidente", 
                        bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variáveis
        vars = {
            'vehicle_plate': tk.StringVar(),
            'sensor_location': tk.StringVar(),
            'location': tk.StringVar(),
            'description': tk.StringVar()
        }
        
        # Carregar dados para dropdowns
        vehicles_list = []
        sensors_list = []
        
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor() as cur:
                    # Buscar veículos
                    cur.execute("SELECT license_plate, model FROM vehicle_active WHERE allowed = true ORDER BY license_plate")
                    vehicles_list = [f"{row[0]} - {row[1]}" for row in cur.fetchall()]
                    
                    # Buscar sensores
                    cur.execute("SELECT id, location, type FROM sensor_active WHERE active = true ORDER BY location")
                    sensors_list = [f"{row[0]} - {row[2]} - {row[1]}" for row in cur.fetchall()]
        except:
            pass
        
        # Campos do formulário
        fields = [
            ("🚗 Veículo", "vehicle_plate", vehicles_list),
            ("📹 Sensor", "sensor_location", sensors_list),
            ("📍 Localização", "location", "Ex: Av. Principal, esquina com Rua Secundária"),
            ("📝 Descrição", "description", "Descreva o incidente em detalhes")
        ]
        
        for i, (label, key, placeholder) in enumerate(fields):
            tk.Label(form_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', pady=5)
            
            if key in ['vehicle_plate', 'sensor_location']:
                # Combobox para veículos e sensores
                combo = ttk.Combobox(form_frame, textvariable=vars[key], values=placeholder, 
                                   state="readonly", font=self.styles.fonts['normal'])
                combo.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                if placeholder and len(placeholder) > 0:
                    combo.current(0)
            elif key == 'description':
                # Text area para descrição
                text_area = tk.Text(form_frame, height=4, width=40, font=self.styles.fonts['normal'])
                text_area.insert('1.0', placeholder)
                text_area.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                vars[key] = text_area
            else:
                entry = tk.Entry(form_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
                entry.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        form_frame.columnconfigure(1, weight=1)
        
        # Botões
        button_frame = tk.Frame(form_frame, bg=self.styles.colors['background'])
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def save_incident():
            try:
                # Validar campos obrigatórios
                if not vars['vehicle_plate'].get().strip() or not vars['sensor_location'].get().strip():
                    messagebox.showerror("Erro", "Selecione o veículo e o sensor!")
                    return
                
                if not vars['location'].get().strip():
                    messagebox.showerror("Erro", "Preencha a localização!")
                    return
                
                description = vars['description'].get('1.0', 'end').strip()
                if not description:
                    messagebox.showerror("Erro", "Preencha a descrição do incidente!")
                    return
                
                # Extrair IDs
                vehicle_plate = vars['vehicle_plate'].get().split(' - ')[0]
                sensor_info = vars['sensor_location'].get().split(' - ')
                sensor_id = int(sensor_info[0])
                
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Buscar ID do veículo
                        cur.execute("SELECT id FROM vehicle_active WHERE license_plate = %s", (vehicle_plate,))
                        vehicle_result = cur.fetchone()
                        if not vehicle_result:
                            messagebox.showerror("Erro", "Veículo não encontrado!")
                            return
                        vehicle_id = vehicle_result[0]
                        
                        # Inserir incidente
                        cur.execute("""
                            INSERT INTO traffic_incident (
                                vehicle_id, sensor_id, location, description
                            ) VALUES (%s, %s, %s, %s)
                        """, (
                            vehicle_id,
                            sensor_id,
                            vars['location'].get(),
                            description
                        ))
                        
                        conn.commit()
                
                messagebox.showinfo("Sucesso", "Incidente registrado com sucesso!")
                dialog.destroy()
                self.show_incidents()  # Atualizar a lista
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao registrar incidente: {str(e)}")
        
        tk.Button(button_frame, text="💾 Salvar", command=save_incident,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
    def pay_fine_dialog(self):
        """Abre diálogo para pagar multa existente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("💳 Pagar Multa")
        dialog.geometry("500x400")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['success'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="💳 Pagar Multa", 
                        bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variáveis
        vars = {
            'fine': tk.StringVar(),
            'amount': tk.StringVar(),
            'payment_method': tk.StringVar()
        }
        
        # Carregar multas pendentes
        fines_list = []
        
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT f.id, f.amount, f.due_date, f.created_at,
                               ti.location, ti.occurred_at,
                               v.license_plate, c.first_name, c.last_name
                        FROM fine f
                        JOIN traffic_incident ti ON f.traffic_incident_id = ti.id
                        LEFT JOIN vehicle v ON ti.vehicle_id = v.id
                        LEFT JOIN citizen c ON v.citizen_id = c.id
                        WHERE f.status = 'pending'
                        ORDER BY f.due_date ASC
                    """)
                    fines = cur.fetchall()
                    fines_list = [
                        f"#{fine['id']} - {format_currency_brl(fine['amount'])} - Venc: {fine['due_date'].strftime('%d/%m/%Y')} - {fine['license_plate'] or 'Veículo não identificado'}"
                        for fine in fines
                    ]
        except:
            pass
        
        # Métodos de pagamento
        payment_methods = ['Carteira Digital','Cartão de Crédito', 'Cartão de Débito', 'Dinheiro', 'PIX', 'Boleto', 'Transferência Bancária']
        
        def update_amount():
            """Atualiza o valor quando uma multa é selecionada"""
            try:
                fine_info = vars['fine'].get()
                if fine_info and '#' in fine_info:
                    # Extrair valor da string da multa
                    parts = fine_info.split(' - ')
                    if len(parts) >= 2 and 'R$' in parts[1]:
                        amount_str = parts[1].replace('R$ ', '').strip()
                        vars['amount'].set(amount_str)
            except:
                pass
        
        # Campos do formulário
        fields = [
            ("💰 Multa Pendente", "fine", fines_list),
            ("💳 Valor a Pagar (R$)", "amount", "0.00"),
            ("🏦 Método de Pagamento", "payment_method", payment_methods)
        ]
        
        for i, (label, key, placeholder) in enumerate(fields):
            tk.Label(form_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', pady=5)
            
            if key == 'fine':
                # Combobox para multas
                combo = ttk.Combobox(form_frame, textvariable=vars[key], values=placeholder, 
                                   state="readonly", font=self.styles.fonts['normal'])
                combo.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                combo.bind('<<ComboboxSelected>>', lambda e: update_amount())
                if placeholder and len(placeholder) > 0:
                    combo.current(0)
                    update_amount()  # Atualizar valor inicial
            elif key == 'payment_method':
                # Combobox para métodos de pagamento
                combo = ttk.Combobox(form_frame, textvariable=vars[key], values=placeholder, 
                                   state="readonly", font=self.styles.fonts['normal'])
                combo.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                combo.current(0)
            else:
                entry = tk.Entry(form_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
                entry.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                entry.config(state='readonly')  # Valor readonly
        
        form_frame.columnconfigure(1, weight=1)
        
        def update_amount():
            """Atualiza o valor quando uma multa é selecionada"""
            try:
                fine_info = vars['fine'].get()
                if fine_info:
                    # Extrair valor da string: "#1 - R$ 150.00 - Venc: 15/01/2024 - ABC-1234"
                    parts = fine_info.split(' - ')
                    if len(parts) >= 2:
                        amount_str = parts[1].replace('R$ ', '').strip()
                        vars['amount'].set(amount_str)
            except:
                pass
        
        # Botões
        button_frame = tk.Frame(form_frame, bg=self.styles.colors['background'])
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def pay_fine():
            try:
                # Validar campos obrigatórios
                if not vars['fine'].get().strip():
                    messagebox.showerror("Erro", "Selecione uma multa!")
                    return
                
                if not vars['payment_method'].get().strip():
                    messagebox.showerror("Erro", "Selecione o método de pagamento!")
                    return
                
                # Extrair ID da multa
                fine_id = int(vars['fine'].get().split('#')[1].split(' -')[0])
                amount = self.converter_valor_monetario(vars['amount'].get())
                payment_method = vars['payment_method'].get()
                
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Verificar se multa ainda está pendente
                        cur.execute("SELECT status, amount FROM fine WHERE id = %s", (fine_id,))
                        fine_result = cur.fetchone()
                        if not fine_result:
                            messagebox.showerror("Erro", "Multa não encontrada!")
                            return
                        
                        status, db_amount = fine_result
                        if status != 'pending':
                            messagebox.showerror("Erro", f"Esta multa já está {status}!")
                            return
                        
                        # Validar valor digitado
                        amount_digitado = self.converter_valor_monetario(vars['amount'].get())
                        amount_banco = self.converter_valor_monetario(db_amount)
                        
                        if abs(amount_digitado - amount_banco) > 0.01:
                            messagebox.showerror("Erro", "Valor da multa não confere!")
                            return
                        
                        # Inserir registro de pagamento - o trigger apply_fine_payment cuida do resto
                        cur.execute("""
                            INSERT INTO fine_payment (
                                fine_id, amount_paid, payment_method
                            ) VALUES (%s, %s, %s)
                        """, (
                            fine_id,
                            amount,
                            payment_method
                        ))
                        
                        conn.commit()
                
                messagebox.showinfo("Sucesso", "Multa paga com sucesso!")
                dialog.destroy()
                self.show_fines()  # Atualizar a lista
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao pagar multa: {str(e)}")
        
        tk.Button(button_frame, text="💳 Pagar", command=pay_fine,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
    def generate_fine_dialog(self):
        """Abre diálogo para gerar multa para um incidente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("💰 Gerar Multa")
        dialog.geometry("500x450")
        dialog.configure(bg=self.styles.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=self.styles.colors['secondary'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="💰 Gerar Nova Multa", 
                        bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                        font=self.styles.fonts['title'])
        title.pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.styles.colors['background'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variáveis
        vars = {
            'incident': tk.StringVar(),
            'amount': tk.StringVar(),
            'due_date': tk.StringVar()
        }
        
        # Dicionário para guardar dados dos incidentes
        incidents_data = {}
        
        # Carregar incidentes sem multas
        incidents_list = []
        
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT ti.id, ti.location, ti.occurred_at, ti.description,
                               v.license_plate, c.first_name, c.last_name
                        FROM traffic_incident ti
                        LEFT JOIN vehicle v ON ti.vehicle_id = v.id
                        LEFT JOIN citizen c ON v.citizen_id = c.id
                        LEFT JOIN fine f ON ti.id = f.traffic_incident_id
                        WHERE f.id IS NULL
                        ORDER BY ti.occurred_at DESC
                    """)
                    incidents = cur.fetchall()
                    for inc in incidents:
                        display_text = f"#{inc['id']} - {inc['license_plate'] or 'Veículo não identificado'} - {inc['location'] or 'Local não informado'} - {inc['occurred_at'].strftime('%d/%m %H:%M')}"
                        incidents_list.append(display_text)
                        incidents_data[display_text] = inc
        except:
            pass
        
        # Campos do formulário
        fields = [
            ("⚠️ Incidente", "incident", incidents_list),
            ("💰 Valor (R$)", "amount", "150.00"),
            ("📅 Data Vencimento", "due_date", "DD/MM/AAAA")
        ]
        
        for i, (label, key, placeholder) in enumerate(fields):
            tk.Label(form_frame, text=label, bg=self.styles.colors['background'],
                    fg=self.styles.colors['text_primary'], font=self.styles.fonts['normal']).grid(
                row=i, column=0, sticky='w', pady=5)
            
            if key == 'incident':
                # Combobox para incidentes
                combo = ttk.Combobox(form_frame, textvariable=vars[key], values=incidents_list, 
                                   state="readonly", font=self.styles.fonts['normal'])
                combo.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                if incidents_list and len(incidents_list) > 0:
                    combo.current(0)
            else:
                entry = tk.Entry(form_frame, textvariable=vars[key], font=self.styles.fonts['normal'])
                entry.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        form_frame.columnconfigure(1, weight=1)
        
        # Botões
        button_frame = tk.Frame(form_frame, bg=self.styles.colors['background'])
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def save_fine():
            try:
                # Validar campos obrigatórios
                if not vars['incident'].get().strip():
                    messagebox.showerror("Erro", "Selecione um incidente!")
                    return
                
                if not vars['amount'].get().strip():
                    messagebox.showerror("Erro", "Preencha o valor da multa!")
                    return
                
                # Validar valor
                try:
                    # Converter valor monetário brasileiro (ex: "100,00") para float
                    amount = self.converter_valor_monetario(vars['amount'].get())
                    if amount <= 0:
                        messagebox.showerror("Erro", "Valor deve ser maior que zero!")
                        return
                except ValueError:
                    messagebox.showerror("Erro", "Valor inválido!")
                    return
                
                # Validar data de vencimento
                try:
                    from datetime import datetime, timedelta
                    due_date = datetime.strptime(vars['due_date'].get(), '%d/%m/%Y').date()
                    today = datetime.now().date()
                    
                    # Buscar data do incidente
                    incident_id = int(vars['incident'].get().split('#')[1].split(' -')[0])
                    with psy.connect(self.get_connection_string()) as conn:
                        with conn.cursor(row_factory=dict_row) as cur:
                            cur.execute("SELECT occurred_at FROM traffic_incident WHERE id = %s", (incident_id,))
                            incident_result = cur.fetchone()
                            if incident_result:
                                incident_date = incident_result['occurred_at'].date()
                                
                                # Validar se vencimento é anterior à data do incidente
                                if due_date < incident_date:
                                    messagebox.showerror("Erro", "A data de vencimento não pode ser anterior à data do incidente!")
                                    return
                                
                                # Validar se vencimento é muito anterior à data atual
                                if due_date < today - timedelta(days=365):
                                    messagebox.showerror("Erro", "A data de vencimento não pode ser mais de 1 ano no passado!")
                                    return
                except ValueError:
                    messagebox.showerror("Erro", "Data de vencimento inválida! Use o formato DD/MM/AAAA")
                    return
                
                # Extrair ID do incidente
                incident_id = int(vars['incident'].get().split('#')[1].split(' -')[0])
                
                with psy.connect(self.get_connection_string()) as conn:
                    with conn.cursor() as cur:
                        # Verificar se incidente já tem multa
                        cur.execute("SELECT id FROM fine WHERE traffic_incident_id = %s", (incident_id,))
                        if cur.fetchone():
                            messagebox.showerror("Erro", "Este incidente já possui uma multa!")
                            return
                        
                        # Buscar citizen_id do incidente
                        cur.execute("""
                            SELECT c.id as citizen_id
                            FROM traffic_incident ti
                            JOIN vehicle v ON v.id = ti.vehicle_id
                            JOIN citizen c ON c.id = v.citizen_id
                            WHERE ti.id = %s
                        """, (incident_id,))
                        citizen_result = cur.fetchone()
                        if not citizen_result:
                            messagebox.showerror("Erro", "Não foi possível encontrar o cidadão associado ao incidente!")
                            return
                        citizen_id = citizen_result[0]
                        
                        # Inserir multa
                        cur.execute("""
                            INSERT INTO fine (
                                traffic_incident_id, citizen_id, amount, due_date
                            ) VALUES (%s, %s, %s, %s)
                        """, (
                            incident_id,
                            citizen_id,
                            amount,
                            due_date
                        ))
                        
                        conn.commit()
                
                messagebox.showinfo("Sucesso", "Multa gerada com sucesso!")
                dialog.destroy()
                self.show_fines()  # Atualizar a lista
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar multa: {str(e)}")
        
        tk.Button(button_frame, text="💾 Gerar Multa", command=save_fine,
                 bg=self.styles.colors['success'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg=self.styles.colors['accent'], fg=self.styles.colors['white'],
                 font=self.styles.fonts['button'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
def main():
    root = tk.Tk()
    app = SmartCityOSGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
