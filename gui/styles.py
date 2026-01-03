"""
Estilos e temas para a interface SmartCityOS GUI
"""

import tkinter as tk
from tkinter import ttk

class SmartCityStyles:
    """Classe para gerenciar estilos da aplicação"""
    
    def __init__(self):
        self.colors = {
            'primary': '#2E8B57',      # Verde marinho (SeaGreen)
            'secondary': '#4682B4',    # Azul aço (SteelBlue)
            'accent': '#DC143C',       # Vermelho carmesim (Crimson)
            'success': '#228B22',      # Verde floresta (ForestGreen)
            'warning': '#FF8C00',      # Laranja escuro (DarkOrange)
            'light': '#F5F5F5',        # Cinza muito claro (WhiteSmoke)
            'dark': '#2F4F4F',         # Cinza escuro (DarkSlateGray)
            'white': '#FFFFFF',        # Branco puro
            'black': '#000000',        # Preto puro
            'background': '#F0F0F0',  # Cinza claro (LightGray)
            'card': '#FFFFFF',         # Branco para cards
            'border': '#D3D3D3',      # Cinza claro (LightGray)
            'text_primary': '#2F4F4F', # Texto principal
            'text_secondary': '#696969' # Texto secundário
        }
        
        self.fonts = {
            'title': ('Segoe UI', 15, 'bold'),
            'subtitle': ('Segoe UI', 14, 'bold'),
            'heading': ('Segoe UI', 12, 'bold'),
            'normal': ('Segoe UI', 9),
            'small': ('Segoe UI', 8),
            'button': ('Segoe UI', 9, 'bold'),
            'card_title': ('Segoe UI', 11, 'bold')
        }
        
    def configure_styles(self, root):
        """Configura todos os estilos da aplicação"""
        style = ttk.Style()
        
        # Configurar tema
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        else:
            style.theme_use(available_themes[0])
        
        # Estilo para botões principais
        style.configure(
            'Primary.TButton',
            background=self.colors['secondary'],
            foreground=self.colors['white'],
            borderwidth=0,
            focuscolor='none',
            font=self.fonts['button'],
            padding=(20, 10),
        )
        style.map(
            'Primary.TButton',
            background=[('active', '#3A9B5F'), ('pressed', '#2F8B57')]
        )
        
        # Estilo para botões de sucesso
        style.configure(
            'Success.TButton',
            background=self.colors['success'],
            foreground=self.colors['white'],
            borderwidth=0,
            focuscolor='none',
            font=self.fonts['button'],
            padding=(12, 6)
        )
        style.map(
            'Success.TButton',
            background=[('active', '#2E9B32'), ('pressed', '#248B27')]
        )
        
        # Estilo para botões de perigo
        style.configure(
            'Danger.TButton',
            background=self.colors['accent'],
            foreground=self.colors['white'],
            borderwidth=0,
            focuscolor='none',
            font=self.fonts['button'],
            padding=(12, 6)
        )
        style.map(
            'Danger.TButton',
            background=[('active', '#E62844'), ('pressed', '#C91E35')]
        )
        
        # Estilo para botões secundários
        style.configure(
            'Secondary.TButton',
            background=self.colors['light'],
            foreground=self.colors['text_primary'],
            borderwidth=1,
            focuscolor='none',
            font=self.fonts['button'],
            padding=(12, 6)
        )
        style.map(
            'Secondary.TButton',
            background=[('active', '#D5DBDB'), ('pressed', '#AAB7B8')]
        )
        
        # Estilo para frames de cartões
        style.configure(
            'Card.TFrame',
            background=self.colors['card'],
            relief='flat',
            borderwidth=1
        )
        
        # Estilo para labels de títulos
        style.configure(
            'Title.TLabel',
            background=self.colors['card'],
            foreground=self.colors['text_primary'],
            font=self.fonts['title']
        )
        
        # Estilo para labels de subtítulos
        style.configure(
            'Subtitle.TLabel',
            background=self.colors['card'],
            foreground=self.colors['text_secondary'],
            font=self.fonts['subtitle']
        )
        
        # Estilo para labels de cabeçalho
        style.configure(
            'Heading.TLabel',
            background=self.colors['card'],
            foreground=self.colors['text_primary'],
            font=self.fonts['heading']
        )
        
        # Estilo para labels normais
        style.configure(
            'Normal.TLabel',
            background=self.colors['card'],
            foreground=self.colors['text_primary'],
            font=self.fonts['normal']
        )
        
        # Estilo para labels pequenos
        style.configure(
            'Small.TLabel',
            background=self.colors['card'],
            foreground=self.colors['text_secondary'],
            font=self.fonts['small']
        )
        
        # Estilo para Treeview
        style.configure(
            'Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=1,
            font=self.fonts['normal']
        )
        style.configure(
            'Treeview.Heading',
            background=self.colors['primary'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Treeview',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Estilo alternativo para tabelas de resultados
        style.configure(
            'Results.Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=0,
            font=self.fonts['normal']
        )
        style.configure(
            'Results.Treeview.Heading',
            background=self.colors['dark'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Results.Treeview',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Configurar tags para cores alternadas
        style.configure(
            'Results.Treeview.Even',
            background=self.colors['white'],
            foreground=self.colors['text_primary']
        )
        style.configure(
            'Results.Treeview.Odd',
            background='#F8F9FA',
            foreground=self.colors['text_primary']
        )
        
        # Estilos específicos para cada aba
        # Usuários - Verde marinho
        style.configure(
            'Users.Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=0,
            font=self.fonts['normal']
        )
        style.configure(
            'Users.Treeview.Heading',
            background=self.colors['primary'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Users.Treeview',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Cidadãos - Azul aço
        style.configure(
            'Citizens.Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=0,
            font=self.fonts['normal']
        )
        style.configure(
            'Citizens.Treeview.Heading',
            background=self.colors['secondary'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Citizens.Treeview',
            background=[('selected', self.colors['primary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Veículos - Laranja escuro
        style.configure(
            'Vehicles.Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=0,
            font=self.fonts['normal']
        )
        style.configure(
            'Vehicles.Treeview.Heading',
            background=self.colors['warning'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Vehicles.Treeview',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Sensores - Verde floresta
        style.configure(
            'Sensors.Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=0,
            font=self.fonts['normal']
        )
        style.configure(
            'Sensors.Treeview.Heading',
            background=self.colors['success'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Sensors.Treeview',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Incidentes - Vermelho carmesim
        style.configure(
            'Incidents.Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=0,
            font=self.fonts['normal']
        )
        style.configure(
            'Incidents.Treeview.Heading',
            background=self.colors['accent'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Incidents.Treeview',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Multas - Cinza escuro
        style.configure(
            'Fines.Treeview',
            background=self.colors['white'],
            foreground=self.colors['text_primary'],
            fieldbackground=self.colors['white'],
            borderwidth=0,
            font=self.fonts['normal']
        )
        style.configure(
            'Fines.Treeview.Heading',
            background=self.colors['dark'],
            foreground=self.colors['white'],
            font=self.fonts['heading'],
            relief='flat'
        )
        style.map(
            'Fines.Treeview',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Estilo para Notebook (abas)
        style.configure(
            'TNotebook',
            background=self.colors['background'],
            borderwidth=0
        )
        style.configure(
            'TNotebook.Tab',
            background=self.colors['light'],
            foreground=self.colors['text_primary'],
            padding=(15, 8),
            font=self.fonts['normal']
        )
        style.map(
            'TNotebook.Tab',
            background=[('selected', self.colors['secondary'])],
            foreground=[('selected', self.colors['white'])]
        )
        
        # Estilo para Entry
        style.configure(
            'TEntry',
            fieldbackground=self.colors['white'],
            borderwidth=1,
            font=self.fonts['normal']
        )
        style.map(
            'TEntry',
            focuscolor=[('focus', self.colors['secondary'])]
        )
        
        # Estilo para LabelFrame
        style.configure(
            'TLabelframe',
            background=self.colors['card'],
            foreground=self.colors['text_primary'],
            borderwidth=1,
            font=self.fonts['heading']
        )
        style.configure(
            'TLabelframe.Label',
            background=self.colors['card'],
            foreground=self.colors['primary'],
            font=self.fonts['heading']
        )
        
        # Configurar cores do root
        root.configure(bg=self.colors['background'])
        
    def create_gradient_frame(self, parent, height=100, color1=None, color2=None):
        """Cria um frame com gradiente"""
        if color1 is None:
            color1 = self.colors['primary']
        if color2 is None:
            color2 = self.colors['secondary']
            
        frame = tk.Frame(parent, height=height, bg=color1)
        
        # Simular gradiente com linhas
        for i in range(height):
            # Calcular cor intermediária
            ratio = i / height
            r1, g1, b1 = self._hex_to_rgb(color1)
            r2, g2, b2 = self._hex_to_rgb(color2)
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            color = self._rgb_to_hex(r, g, b)
            line = tk.Frame(frame, height=1, bg=color)
            line.place(x=0, y=i, relwidth=1)
            
        return frame
    
    def _hex_to_rgb(self, hex_color):
        """Converte cor hex para RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, r, g, b):
        """Converte RGB para hex"""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def create_card(self, parent, title="", padding=20):
        """Cria um cartão estilizado"""
        card = ttk.Frame(parent, style='Card.TFrame', padding=padding)
        
        if title:
            title_label = ttk.Label(card, text=title, style='Heading.TLabel')
            title_label.pack(anchor='w', pady=(0, 10))
            
        return card
    
    def create_status_badge(self, parent, text, status_type="normal"):
        """Cria um badge de status"""
        colors = {
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'danger': self.colors['accent'],
            'normal': self.colors['secondary']
        }
        
        bg_color = colors.get(status_type, self.colors['secondary'])
        
        badge = tk.Frame(parent, bg=bg_color, relief='flat', padx=8, pady=4)
        label = tk.Label(badge, text=text, bg=bg_color, fg='white', 
                       font=self.fonts['small'])
        label.pack()
        
        return badge
    
    def create_icon_label(self, parent, icon, text, icon_size=20):
        """Cria um label com ícone e texto"""
        frame = tk.Frame(parent, bg=self.colors['card'])
        
        # Ícone (simulado com texto por enquanto)
        icon_label = tk.Label(frame, text=icon, bg=self.colors['card'], 
                           fg=self.colors['secondary'], 
                           font=('Segoe UI', icon_size))
        icon_label.pack(side='left', padx=(0, 8))
        
        # Texto
        text_label = tk.Label(frame, text=text, bg=self.colors['card'],
                           fg=self.colors['text_primary'],
                           font=self.fonts['normal'])
        text_label.pack(side='left')
        
        return frame
