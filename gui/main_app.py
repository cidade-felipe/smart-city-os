import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.conect_db import connect_to_db
import psycopg as psy
from psycopg.rows import dict_row
from datetime import datetime
import pandas as pd
from tabulate import tabulate
from dotenv import load_dotenv
from gui.styles import SmartCityStyles

# Carregar variáveis de ambiente
load_dotenv()

class SmartCityOSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartCityOS - Sistema Operacional Inteligente para Cidades")
        self.root.geometry("1400x900")
        self.root.configure(bg='#F8F9FA')
        
        # Inicializar estilos
        self.styles = SmartCityStyles()
        self.styles.configure_styles(self.root)
        
        # Variáveis de conexão
        self.conn = None
        self.connected = False
        
        # Configuração de estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Criar interface
        self.create_widgets()
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
            
            # Testar conexão
            with psy.connect(conn_info) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()
                    
            self.connected = True
            self.connection_status.config(text="🟢 Conectado")
            self.connect_btn.config(text="Desconectar")
            self.status_label.config(text=f"Conectado ao PostgreSQL - {version[0].split(',')[0]}")
            
        except Exception as e:
            self.connected = False
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
            self.connected = False
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
                               padx=15, pady=8, cursor='hand2')
        refresh_btn.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Grid de estatísticas com cards
        stats_container = tk.Frame(self.content_frame, bg=self.styles.colors['background'])
        stats_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Cards de estatísticas com design moderno
        cards_data = [
            ("👥 Cidadãos", stats['citizens']['total'], stats['citizens']['with_debt'], 
             f"R$ {stats['citizens']['total_debt']:.2f}", self.styles.colors['primary']),
            ("🚗 Veículos", stats['vehicles']['total'], stats['vehicles']['active'], 
             f"{stats['vehicles']['total'] - stats['vehicles']['active']} bloqueados", self.styles.colors['success']),
            ("⚠️ Incidentes", stats['incidents']['total'], stats['incidents']['this_week'], 
             f"Média: {stats['incidents']['total']/30:.1f}/dia", self.styles.colors['warning']),
            ("💰 Multas", stats['fines']['total'], stats['fines']['pending'], 
             f"R$ {stats['fines']['total_amount']:.2f}", self.styles.colors['accent']),
            ("📹 Sensores", stats['sensors']['total'], stats['sensors']['active'], 
             f"{stats['sensors']['total'] - stats['sensors']['active']} inativos", self.styles.colors['secondary']),
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
        if title == "👥 Cidadãos":
            secondary_text = f"Com dívida: {active}"
        elif title == "🚗 Veículos":
            secondary_text = f"Ativos: {active}"
        elif title == "⚠️ Incidentes":
            secondary_text = f"Esta semana: {active}"
        elif title == "💰 Multas":
            secondary_text = f"Pendentes: {active}"
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
        
    def show_citizens(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        # Título
        title = ttk.Label(self.content_frame, text="👥 Gestão de Cidadãos", font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # Frame de controles
        control_frame = ttk.Frame(self.content_frame)
        control_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Botões
        ttk.Button(control_frame, text="🔄 Atualizar", command=self.load_citizens).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="➕ Adicionar Cidadão", command=self.add_citizen_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔍 Buscar por CPF", command=self.search_citizen_by_cpf).pack(side=tk.LEFT, padx=5)
        
        # Frame da tabela
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview para cidadãos
        columns = ('ID', 'Nome', 'CPF', 'Email', 'Saldo', 'Dívida', 'Status')
        self.citizens_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configurar colunas
        for col in columns:
            self.citizens_tree.heading(col, text=col)
            if col == 'ID':
                self.citizens_tree.column(col, width=50)
            elif col in ['Saldo', 'Dívida']:
                self.citizens_tree.column(col, width=100)
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
        
        # Carregar dados
        self.load_citizens()
        
    def load_citizens(self):
        if not self.connected:
            return
            
        try:
            # Limpar treeview
            for item in self.citizens_tree.get_children():
                self.citizens_tree.delete(item)
                
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT c.id, u.first_name || ' ' || u.last_name as name, u.cpf, u.email,
                               c.wallet_balance, c.debt, c.allowed
                        FROM citizen c
                        JOIN app_user u ON c.app_user_id = u.id
                        ORDER BY c.id
                    """)
                    
                    citizens = cur.fetchall()
                    
                    for citizen in citizens:
                        status = "✅ Ativo" if citizen['allowed'] else "🚫 Bloqueado"
                        values = (
                            citizen['id'],
                            citizen['name'],
                            citizen['cpf'],
                            citizen['email'],
                            f"R$ {citizen['wallet_balance']:.2f}",
                            f"R$ {citizen['debt']:.2f}",
                            status
                        )
                        self.citizens_tree.insert('', tk.END, values=values)
                        
                    self.status_label.config(text=f"Carregados {len(citizens)} cidadãos")
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar cidadãos: {str(e)}")
            
    def show_vehicles(self):
        self.clear_content()
        
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        # Título
        title = ttk.Label(self.content_frame, text="🚗 Gestão de Veículos", font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # Frame de controles
        control_frame = ttk.Frame(self.content_frame)
        control_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Button(control_frame, text="🔄 Atualizar", command=self.load_vehicles).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="➕ Adicionar Veículo", command=self.add_vehicle_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔍 Buscar por Placa", command=self.search_vehicle_by_plate).pack(side=tk.LEFT, padx=5)
        
        # Frame da tabela
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview para veículos
        columns = ('ID', 'Placa', 'Modelo', 'Ano', 'Proprietário', 'Status')
        self.vehicles_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
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
        
        # Carregar dados
        self.load_vehicles()
        
    def load_vehicles(self):
        if not self.connected:
            return
            
        try:
            # Limpar treeview
            for item in self.vehicles_tree.get_children():
                self.vehicles_tree.delete(item)
                
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT v.id, v.license_plate, v.model, v.year,
                               u.first_name || ' ' || u.last_name as owner_name,
                               v.allowed
                        FROM vehicle v
                        JOIN app_user u ON v.app_user_id = u.id
                        ORDER BY v.id
                    """)
                    
                    vehicles = cur.fetchall()
                    
                    for vehicle in vehicles:
                        status = "✅ Ativo" if vehicle['allowed'] else "🚫 Bloqueado"
                        values = (
                            vehicle['id'],
                            vehicle['license_plate'],
                            vehicle['model'],
                            vehicle['year'],
                            vehicle['owner_name'],
                            status
                        )
                        self.vehicles_tree.insert('', tk.END, values=values)
                        
                    self.status_label.config(text=f"Carregados {len(vehicles)} veículos")
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar veículos: {str(e)}")
            
    def show_sensors(self):
        self.clear_content()
        messagebox.showinfo("Em desenvolvimento", "Módulo de Sensores em desenvolvimento!")
        
    def show_incidents(self):
        self.clear_content()
        messagebox.showinfo("Em desenvolvimento", "Módulo de Incidentes em desenvolvimento!")
        
    def show_fines(self):
        self.clear_content()
        messagebox.showinfo("Em desenvolvimento", "Módulo de Multas em desenvolvimento!")
        
    def show_statistics(self):
        self.clear_content()
        messagebox.showinfo("Em desenvolvimento", "Módulo de Estatísticas em desenvolvimento!")
        
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
        
        # Área de texto para SQL com estilo melhorado
        sql_container = tk.Frame(sql_frame, bg=self.styles.colors['card'])
        sql_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.sql_text = scrolledtext.ScrolledText(
            sql_container, 
            height=12, 
            width=60,
            bg='#2E3440',  # Fundo escuro tipo VS Code
            fg='#D8DEE9',  # Texto claro
            font=('Consolas', 11),
            insertbackground='#88C0D0',  # Cursor
            selectbackground='#4C566A',  # Seleção
            relief='flat',
            bd=1,
            state='normal',  # Garantir que está editável
            wrap='word',  # Quebra de linha automática
            undo=True,  # Habilitar desfazer/refazer
            padx=5,
            pady=5
        )
        self.sql_text.pack(fill=tk.BOTH, expand=True)
        
        # Inserir texto inicial
        self.sql_text.insert(tk.END, "-- Digite sua consulta SQL aqui\n")
        self.sql_text.insert(tk.END, "SELECT * FROM app_user LIMIT 10;")
        self.sql_text.tag_add("comment", "1.0", "1.end")
        self.sql_text.tag_config("comment", foreground='#616E88')  # Comentários em cinza
        
        # Garantir que o widget está focado e editável
        self.sql_text.config(state='normal')
        self.sql_text.focus_set()
        
        # Limpar seleção inicial
        self.sql_text.tag_remove('sel', '1.0', 'end')
        self.sql_text.mark_set('insert', 'end')
        
        # Adicionar evento de clique para garantir foco
        self.sql_text.bind('<Button-1>', lambda e: self.sql_text.focus_set())
        
        # Adicionar evento de foco para garantir estado editável
        self.sql_text.bind('<FocusIn>', lambda e: self.sql_text.config(state='normal'))
        
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
        self.results_tree = ttk.Treeview(table_frame, show='tree', style='Results.Treeview')
        
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
        self.export_btn = tk.Button(info_frame, text="📥 Exportar CSV", command=self.export_results,
                                   bg=self.styles.colors['secondary'], fg=self.styles.colors['white'],
                                   font=self.styles.fonts['button'], relief='flat',
                                   padx=12, pady=6, cursor='hand2', state='disabled')
        self.export_btn.pack(side=tk.RIGHT)
        
        # Configurar weights do container principal
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
    def execute_sql(self):
        if not self.connected:
            messagebox.showwarning("Aviso", "Conecte-se ao banco de dados primeiro!")
            return
            
        sql = self.sql_text.get(1.0, tk.END).strip()
        
        if not sql:
            messagebox.showwarning("Aviso", "Digite uma consulta SQL!")
            return
            
        try:
            with psy.connect(self.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    start_time = datetime.now()
                    cur.execute(sql)
                    
                    if sql.strip().upper().startswith('SELECT'):
                        results = cur.fetchall()
                        end_time = datetime.now()
                        execution_time = (end_time - start_time).total_seconds()
                        
                        # Limpar treeview anterior
                        for item in self.results_tree.get_children():
                            self.results_tree.delete(item)
                        
                        if results:
                            # Configurar colunas do treeview
                            columns = list(results[0].keys())
                            self.results_tree['columns'] = columns
                            self.results_tree['show'] = 'headings'
                            
                            # Configurar headers
                            for col in columns:
                                self.results_tree.heading(col, text=col.replace('_', ' ').title())
                                self.results_tree.column(col, width=120, minwidth=80)
                            
                            # Inserir dados com cores alternadas
                            for i, row in enumerate(results):
                                values = [str(row.get(col, '')) for col in columns]
                                
                                # Formatar valores para exibição
                                formatted_values = []
                                for val in values:
                                    if val and val.replace('.', '').replace('-', '').isdigit():
                                        # Números - alinhar à direita e formatar
                                        try:
                                            num_val = float(val)
                                            if num_val.is_integer():
                                                formatted_values.append(f"{int(num_val):,}")
                                            else:
                                                formatted_values.append(f"{num_val:,.2f}")
                                        except:
                                            formatted_values.append(val)
                                    else:
                                        # Texto - truncar se muito longo
                                        if len(str(val)) > 50:
                                            formatted_values.append(str(val)[:47] + "...")
                                        else:
                                            formatted_values.append(val)
                                
                                # Inserir item com tag baseada no índice
                                tag = 'Results.Treeview.Even' if i % 2 == 0 else 'Results.Treeview.Odd'
                                item = self.results_tree.insert('', tk.END, values=formatted_values, tags=(tag,))
                            
                            # Atualizar informações
                            self.results_info.config(
                                text=f"📊 {len(results)} registros retornados em {execution_time:.3f}s"
                            )
                            self.export_btn.config(state='normal')
                            
                        else:
                            self.results_info.config(text="📭 Nenhum registro encontrado")
                            self.export_btn.config(state='disabled')
                            
                    else:
                        conn.commit()
                        end_time = datetime.now()
                        execution_time = (end_time - start_time).total_seconds()
                        
                        # Limpar treeview
                        for item in self.results_tree.get_children():
                            self.results_tree.delete(item)
                        
                        # Mostrar mensagem de sucesso
                        self.results_info.config(
                            text=f"✅ Query executada com sucesso! {cur.rowcount} linhas afetadas em {execution_time:.3f}s"
                        )
                        self.export_btn.config(state='disabled')
                        
                    self.status_label.config(text=f"Query executada em {execution_time:.3f}s")
                    
        except Exception as e:
            # Limpar treeview em caso de erro
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.results_info.config(text=f"❌ Erro: {str(e)}")
            self.export_btn.config(state='disabled')
            messagebox.showerror("Erro SQL", f"Erro ao executar consulta: {str(e)}")
            
    def clear_sql(self):
        self.sql_text.config(state='normal')
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(tk.END, "-- Digite sua consulta SQL aqui\n")
        self.sql_text.insert(tk.END, "SELECT * FROM app_user LIMIT 10;")
        self.sql_text.tag_add("comment", "1.0", "1.end")
        self.sql_text.tag_config("comment", foreground='#616E88')
        self.sql_text.focus_set()
        self.sql_text.mark_set('insert', 'end')
        
        # Limpar resultados
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.results_info.config(text="Execute uma query para ver os resultados")
        self.export_btn.config(state='disabled')
        
    def load_sql_example(self):
        examples = [
            "SELECT COUNT(*) as total_citizens FROM citizen;",
            "SELECT * FROM vehicle WHERE allowed = TRUE;",
            "SELECT v.license_plate, c.wallet_balance FROM vehicle v JOIN citizen c ON v.citizen_id = c.id;",
            "SELECT status, COUNT(*) FROM fine GROUP BY status;",
            "SELECT type, COUNT(*) FROM sensor GROUP BY type ORDER BY COUNT DESC;"
        ]
        
        example = examples[0]  # Pode ser randomizado depois
        self.sql_text.config(state='normal')
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(tk.END, example)
        self.sql_text.focus_set()
        self.sql_text.mark_set('insert', 'end')
        
    def export_results(self):
        """Exporta resultados da tabela para CSV"""
        try:
            import csv
            from tkinter import filedialog
            
            # Obter dados do treeview
            columns = self.results_tree['columns']
            rows = []
            
            for item in self.results_tree.get_children():
                values = self.results_tree.item(item)['values']
                rows.append(values)
            
            if not rows:
                messagebox.showwarning("Aviso", "Não há dados para exportar!")
                return
            
            # Dialog para salvar arquivo
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Exportar Resultados para CSV"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Escrever cabeçalho
                    writer.writerow([col.replace('_', ' ').title() for col in columns])
                    
                    # Escrever dados
                    writer.writerows(rows)
                        
                messagebox.showinfo("Sucesso", f"Dados exportados para {filename}")
                self.status_label.config(text=f"Dados exportados para {filename}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
        
    def add_citizen_dialog(self):
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de adicionar cidadão em desenvolvimento!")
        
    def search_citizen_by_cpf(self):
        messagebox.showinfo("Em desenvolvimento", "Busca por CPF em desenvolvimento!")
        
    def add_vehicle_dialog(self):
        messagebox.showinfo("Em desenvolvimento", "Funcionalidade de adicionar veículo em desenvolvimento!")
        
    def search_vehicle_by_plate(self):
        messagebox.showinfo("Em desenvolvimento", "Busca por placa em desenvolvimento!")

def main():
    root = tk.Tk()
    app = SmartCityOSGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
