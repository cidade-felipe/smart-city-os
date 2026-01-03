import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
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
import pandas as pd



# Carregar variáveis de ambiente
load_dotenv()

class SmartCityOSGUI:
    def __init__(self, root):
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
        self.check_connection()

        self.conection_string = connection_string()
        
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
        
        # Frame esquerdo - Logo e título
        left_frame = tk.Frame(header_content, bg=self.styles.colors['primary'])
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Logo (simulado com texto estilizado)
        logo_label = tk.Label(left_frame, text="🏙️", bg=self.styles.colors['primary'], 
                              fg=self.styles.colors['white'], font=('Segoe UI', 32))
        logo_label.pack(side=tk.TOP, anchor='w')
        
        # Título principal
        title_label = tk.Label(left_frame, text="SmartCityOS", bg=self.styles.colors['primary'],
                              fg=self.styles.colors['white'], font=self.styles.fonts['title'])
        title_label.pack(side=tk.TOP, anchor='w', pady=(5, 0))
        
        # Subtítulo
        subtitle_label = tk.Label(left_frame, text="Sistema Operacional Inteligente para Cidades",
                                 bg=self.styles.colors['primary'], fg=self.styles.colors['light'],
                                 font=self.styles.fonts['normal'])
        subtitle_label.pack(side=tk.TOP, anchor='w')
        
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
            ("📊 Dashboard", self.show_dashboard, "primary"),
            ("👤 Usuários", self.show_users, "normal"),
            ("👥 Cidadãos", self.show_citizens, "normal"),
            ("🚗 Veículos", self.show_vehicles, "normal"),
            ("📹 Sensores", self.show_sensors, "normal"),
            ("⚠️ Incidentes", self.show_incidents, "normal"),
            ("💰 Multas", self.show_fines, "normal"),
            ("📈 Estatísticas", self.show_statistics, "normal"),
            ("🔍 Consultas SQL", self.show_sql_console, "secondary"),
        ]
        
        for text, command, style_type in buttons_data:
            btn_frame = tk.Frame(sidebar_frame, bg=self.styles.colors['card'])
            btn_frame.pack(fill=tk.X, padx=20, pady=2)
            
            # Definir cores baseado no estilo
            if style_type == "primary":
                bg_color = self.styles.colors['secondary']
                fg_color = self.styles.colors['white']
            elif style_type == "secondary":
                bg_color = self.styles.colors['light']
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
        
        # Mostrar dashboard inicial
        self.show_dashboard()
        
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
            
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
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
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as this_month FROM app_user")
                    user_stats = cur.fetchone()
                    stats['users'] = user_stats
                    
                    # Cidadãos
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN debt > 0 THEN 1 END) as with_debt, COALESCE(SUM(debt), 0) as total_debt FROM citizen")
                    citizen_stats = cur.fetchone()
                    stats['citizens'] = citizen_stats
                    
                    # Veículos
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN allowed = TRUE THEN 1 END) as active FROM vehicle")
                    vehicle_stats = cur.fetchone()
                    stats['vehicles'] = vehicle_stats
                    
                    # Incidentes
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN occurred_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as this_week FROM traffic_incident")
                    incident_stats = cur.fetchone()
                    stats['incidents'] = incident_stats
                    
                    # Multas
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending, COALESCE(SUM(amount), 0) as total_amount FROM fine")
                    fine_stats = cur.fetchone()
                    stats['fines'] = fine_stats
                    
                    # Sensores
                    cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN active = TRUE THEN 1 END) as active FROM sensor")
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
             f"R$ {stats['citizens']['total_debt']:.2f}", self.styles.colors['success']),
            ("🚗 Veículos", stats['vehicles']['total'], stats['vehicles']['active'], 
             f"{stats['vehicles']['total'] - stats['vehicles']['active']} bloqueados", self.styles.colors['warning']),
            ("⚠️ Incidentes", stats['incidents']['total'], stats['incidents']['this_week'], 
             f"Média: {stats['incidents']['total']/30:.1f}/dia", self.styles.colors['accent']),
            ("💰 Multas", stats['fines']['total'], stats['fines']['pending'], 
             f"R$ {stats['fines']['total_amount']:.2f}", self.styles.colors['secondary']),
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
                        FROM app_user
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
        
        # Título
        title_label = tk.Label(card, text=title, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        title_label.pack(pady=(10, 5))
        
        # Valor principal
        value_label = tk.Label(card, text=str(value), 
                               bg=self.styles.colors['card'], fg=color,
                               font=self.styles.fonts['title'])
        value_label.pack()
        
        # Extra
        extra_label = tk.Label(card, text=extra, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        extra_label.pack(pady=(0, 10))
        
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
                        FROM citizen c
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
                    title_label.pack(side=tk.LEFT, padx=20, pady=15)
                    
                    # Frame de filtros para cidadãos
                    filter_frame = tk.Frame(header_frame, bg=self.styles.colors['card'])
                    filter_frame.pack(side=tk.RIGHT, padx=20, pady=15)
                    
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
            filtered_citizens = [c for c in filtered_citizens if c['debt'] and c['debt'] > 0]
        elif debt_filter == "Sem Dívida":
            filtered_citizens = [c for c in filtered_citizens if not c['debt'] or c['debt'] == 0]
        
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
                f"R$ {citizen['wallet_balance']:,.2f}" if citizen['wallet_balance'] else 'R$ 0,00',
                f"R$ {citizen['debt']:,.2f}" if citizen['debt'] else 'R$ 0,00',
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
                ("👥 Total Cidadãos", total_citizens, f"R$ {total_balance:,.2f}", self.styles.colors['primary']),
                ("✅ Ativos", active_citizens, f"{(active_citizens/total_citizens*100):.1f}%" if total_citizens > 0 else "0%", self.styles.colors['success']),
                ("🔴 Inativos", inactive_citizens, f"R$ {total_debt:,.2f}", self.styles.colors['warning'])
            ]
            
            for i, (title, value, extra, color) in enumerate(cards_data):
                card = self.create_citizens_stat_card(stats_frame, title, value, extra, color)
                card.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        except Exception as e:
            print(f"Erro ao criar estatísticas de cidadãos: {e}")
            # Não mostrar erro ao usuário, apenas não criar os stats
            
    def create_citizens_stat_card(self, parent, title, value, extra, color):
        card = tk.Frame(parent, bg=self.styles.colors['card'], relief='solid', bd=1)
        
        # Título
        title_label = tk.Label(card, text=title, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        title_label.pack(pady=(10, 5))
        
        # Valor principal
        value_label = tk.Label(card, text=str(value), 
                               bg=self.styles.colors['card'], fg=color,
                               font=self.styles.fonts['title'])
        value_label.pack()
        
        # Extra
        extra_label = tk.Label(card, text=extra, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        extra_label.pack(pady=(0, 10))
        
        return card
        
    def create_citizens_table(self, citizens):
        # Frame da tabela
        table_frame = tk.Frame(self.content_frame, bg=self.styles.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview para cidadãos
        columns = ('ID', 'Nome', 'Email', 'CPF', 'Telefone', 'Saldo', 'Dívida', 'Status', 'Username')
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
                f"R$ {citizen['wallet_balance']:,.2f}" if citizen['wallet_balance'] else 'R$ 0,00',
                f"R$ {citizen['debt']:,.2f}" if citizen['debt'] else 'R$ 0,00',
                status,
                citizen['username'] or 'N/A'
            ))
            
        # Frame de informações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"👥 {len(citizens)} cidadãos registrados",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT)
                
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
                        FROM vehicle v
                        JOIN app_user u ON v.app_user_id = u.id
                        LEFT JOIN citizen c ON v.citizen_id = c.id
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
        
        # Título
        title_label = tk.Label(card, text=title, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        title_label.pack(pady=(10, 5))
        
        # Valor principal
        value_label = tk.Label(card, text=str(value), 
                               bg=self.styles.colors['card'], fg=color,
                               font=self.styles.fonts['title'])
        value_label.pack()
        
        # Extra
        extra_label = tk.Label(card, text=extra, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        extra_label.pack(pady=(0, 10))
        
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
            
        # Frame de informações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"🚗 {len(vehicles)} veículos registrados",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT)
        
        
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
                        FROM sensor s
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
        
        # Título
        title_label = tk.Label(card, text=title, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        title_label.pack(pady=(10, 5))
        
        # Valor principal
        value_label = tk.Label(card, text=str(value), 
                               bg=self.styles.colors['card'], fg=color,
                               font=self.styles.fonts['title'])
        value_label.pack()
        
        # Extra
        extra_label = tk.Label(card, text=extra, 
                              bg=self.styles.colors['card'], fg=self.styles.colors['text_secondary'],
                              font=self.styles.fonts['small'])
        extra_label.pack(pady=(0, 10))
        
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
            
        # Informações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"📊 {len(sensors)} sensores cadastrados",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT)
       
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
                    f"R$ {incident['total_fines']:.2f}" if incident['total_fines'] and incident['total_fines'] > 0 else "R$ 0,00"
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
                    f"R$ {incident['total_fines']:.2f}" if incident['total_fines'] and incident['total_fines'] > 0 else "R$ 0,00"
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
                               v.license_plate
                        FROM fine f
                        LEFT JOIN traffic_incident ti ON f.traffic_incident_id = ti.id
                        LEFT JOIN vehicle v ON ti.vehicle_id = v.id
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
        paid_fines = len([f for f in fines if f['status'] == 'paid'])
        total_amount = sum(f['amount'] for f in fines if f['amount'])
        pending_amount = sum(f['amount'] for f in fines if f['status'] == 'pending' and f['amount'])
        
        # Frame de estatísticas
        stats_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Cards
        cards_data = [
            ("💰 Total Multas", total_fines, f"R$ {total_amount:,.2f}", self.styles.colors['primary']),
            ("🔴 Pendentes", pending_fines, f"R$ {pending_amount:,.2f}", self.styles.colors['warning']),
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
        columns = ('ID', 'Valor', 'Status', 'Data', 'Vencimento', 'Local', 'Descrição', 'Placa')
        self.fines_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Fines.Treeview')
        
        # Configurar colunas
        col_widths = {
            'ID': 50, 'Valor': 80, 'Status': 80, 'Data': 80, 'Vencimento': 80,
            'Local': 100, 'Descrição': 120, 'Placa': 80
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
                    'overdue': '⚠️ Vencida'
                }
                status = status_map.get(fine['status'], fine['status'])
                
                # Formatar valores
                amount = f"R$ {fine['amount']:,.2f}" if fine['amount'] and fine['amount'] > 0 else "R$ 0,00"
                created_at = fine['created_at'].strftime('%d/%m/%Y') if fine['created_at'] else "N/A"
                due_date = fine['due_date'].strftime('%d/%m/%Y') if fine['due_date'] else "N/A"
                incident_location = fine.get('incident_location', 'N/A')
                incident_description = fine.get('incident_description', 'N/A')
                if incident_description and len(incident_description) > 30:
                    incident_description = incident_description[:27] + "..."
                license_plate = fine.get('license_plate', 'N/A')
                
                tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                self.fines_tree.insert('', tk.END, values=(
                    fine['id'],
                    amount,
                    status,
                    created_at,
                    due_date,
                    incident_location,
                    incident_description,
                    license_plate
                ), tags=(tag,))
            except Exception as e:
                print(f"Erro ao processar multa {i}: {e}")
                continue
            
        # Informações
        info_frame = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text=f"💰 {len(fines)} multas cadastradas",
                            bg=self.styles.colors['background'], fg=self.styles.colors['text_secondary'],
                            font=self.styles.fonts['small'])
        info_label.pack(side=tk.LEFT)
        
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
            now = datetime.now()
            filtered_fines = [
                f for f in filtered_fines 
                if f['due_date'] and f['due_date'] < now and f['status'] != 'paid'
            ]
        
        # Filtro por valor mínimo
        amount_filter = self.fine_amount_var.get().strip()
        if amount_filter:
            try:
                min_amount = float(amount_filter)
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
                filtered_fines = [
                    f for f in filtered_fines 
                    if f['due_date'] and f['due_date'] < now and f['status'] != 'paid'
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
            status = status_map.get(fine['status'], fine['status'])
            
            # Formatar valores
            amount = f"R$ {fine['amount']:,.2f}" if fine['amount'] else "R$ 0,00"
            due_date = fine['due_date'].strftime('%d/%m/%Y') if fine['due_date'] else "N/A"
            
            self.fines_tree.insert('', tk.END, values=(
                fine['id'],
                amount,
                status,
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
                                          bg=self.styles.colors['primary'], fg=self.styles.colors['white'],
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
                FROM app_user
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
                FROM citizen
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
                FROM vehicle
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
                FROM sensor
                GROUP BY type
                ORDER BY count DESC
            """)
            stats['sensors_by_type'] = cur.fetchall()
            
            cur.execute("""
                SELECT COUNT(*) as total_sensors,
                       COUNT(CASE WHEN active = TRUE THEN 1 END) as active_sensors,
                       COUNT(DISTINCT type) as sensor_types
                FROM sensor
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
                SELECT status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                FROM fine
                GROUP BY status
            """)
            stats['fines_by_status'] = cur.fetchall()
            
            cur.execute("""
                SELECT COUNT(*) as total_fines,
                       COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_fines,
                       COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_fines,
                       COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_fines,
                       COALESCE(SUM(amount), 0) as total_amount,
                       COALESCE(SUM(CASE WHEN status = 'pending' THEN amount END), 0) as pending_amount,
                       COALESCE(SUM(CASE WHEN status = 'paid' THEN amount END), 0) as paid_amount,
                       COALESCE(AVG(amount), 0) as avg_amount
                FROM fine
            """)
            stats['fines'] = cur.fetchone()
        except Exception as e:
            print(f"Erro ao carregar estatísticas de multas: {e}")
            stats['fines_by_status'] = []
            stats['fines'] = {'total_fines': 0, 'pending_fines': 0, 'paid_fines': 0, 'cancelled_fines': 0, 'total_amount': 0, 'pending_amount': 0, 'paid_amount': 0, 'avg_amount': 0}
        
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
             f"R$ {stats['citizens']['total_debt']:,.2f}", self.styles.colors['success']),
            ("🚗 Veículos", stats['vehicles']['total'],
             f"{stats['vehicles']['active']} ativos", self.styles.colors['warning']),
            ("⚠️ Incidentes", stats['incidents']['total_incidents'],
             f"{stats['incidents']['last_7_days']} esta semana", self.styles.colors['accent']),
            ("💰 Multas", stats['fines']['total_fines'],
             f"R$ {stats['fines']['total_amount']:,.2f}", self.styles.colors['secondary'])
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
            f"R$ {stats['fines']['pending_amount']:,.2f}", 
            self.styles.colors['accent']
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
                        f"R$ {avg_fine:.2f}"
                    ]
                elif title == "💰 Multas por Status":
                    total_amount = row['total_amount'] if row['total_amount'] and row['total_amount'] > 0 else 0
                    values = [
                        row['status'] or "N/A", 
                        row['count'] or 0, 
                        f"R$ {total_amount:.2f}"
                    ]
                
                tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                tree.insert('', tk.END, values=values, tags=(tag,))
            except Exception as e:
                print(f"Erro ao processar linha {i} na tabela {title}: {e}")
                continue
            
        # Pack
        table_frame.pack(fill=tk.X, padx=10, pady=5)
        
    def export_statistics(self):
        """Exporta estatísticas para CSV"""
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de exportação em desenvolvimento!")
        
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
        
        example_btn = tk.Button(button_frame, text="📋 Exemplo", command=self.load_sql_example,
                              bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                              font=self.styles.fonts['button'], relief='flat',
                              padx=12, pady=6, cursor='hand2')
        example_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame principal com duas colunas
        main_container = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
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
        self.sql_text.insert(tk.END, "SELECT * FROM app_user LIMIT 10;")
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
        
        # Botão de exportação
        self.export_btn = tk.Button(info_frame, text="📥 Exportar Relatório", command=self.export_results,
                                   bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                   font=self.styles.fonts['button'], relief='flat',
                                   padx=12, pady=6, cursor='hand2', state='disabled')
        self.export_btn.pack(side=tk.RIGHT)
        
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
            
        try:
            # Garantir que a conexão está válida
            if self.conn.closed:
                messagebox.showerror("Erro", "Conexão com banco de dados foi fechada. Conecte-se novamente.")
                return
                
            # Criar cursor com psycopg2.extras.DictCursor
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(sql)
            results = cur.fetchall()
            
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
                self.export_btn.config(state='normal')
                
            else:
                # Sem resultados
                self.results_info.config(text="📭 Nenhum registro encontrado")
                self.export_btn.config(state='disabled')
                
        except psycopg2.Error as e:
            # Limpar treeview em caso de erro
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.results_info.config(text=f"❌ Erro SQL: {str(e)}")
            self.export_btn.config(state='disabled')
            messagebox.showerror("Erro SQL", f"Erro ao executar consulta: {str(e)}")
        except Exception as e:
            # Limpar treeview em caso de erro
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.results_info.config(text=f"❌ Erro: {str(e)}")
            self.export_btn.config(state='disabled')
            messagebox.showerror("Erro", f"Erro ao executar consulta: {str(e)}")
            
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
            "SELECT COUNT(*) as total_citizens FROM citizen;",
            "SELECT * FROM vehicle WHERE allowed = TRUE;",
            "SELECT v.license_plate, c.wallet_balance FROM vehicle v JOIN citizen c ON v.citizen_id = c.id;",
            "SELECT status, COUNT(*) FROM fine GROUP BY status;",
            "SELECT type, COUNT(*) FROM sensor GROUP BY type ORDER BY COUNT DESC;"
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
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de adicionar cidadão em desenvolvimento!")
        
    def search_citizen_by_cpf(self):
        messagebox.showinfo("Em desenvolvimento", "Busca por CPF em desenvolvimento!")
        
    def add_vehicle_dialog(self):
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de adicionar veículo em desenvolvimento!")
        
    def search_vehicle_by_plate(self):
        messagebox.showinfo("Em desenvolvimento", "Busca por placa em desenvolvimento!")
        
    def add_sensor_dialog(self):
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de adicionar sensor em desenvolvimento!")
        
    def add_incident_dialog(self):
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de registrar incidente em desenvolvimento!")
        
    def pay_fine_dialog(self):
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de pagar multa em desenvolvimento!")
        
    def generate_fine_dialog(self):
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de gerar multa em desenvolvimento!")
        
def main():
    root = tk.Tk()
    app = SmartCityOSGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
