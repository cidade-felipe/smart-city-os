import sys
import os

sys.path.append(os.path.abspath(".."))
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg as psy
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

class DatabaseManager:
    """Gerenciador de conexões e operações com o banco de dados"""
    
    @staticmethod
    def get_connection_string():
        """Retorna string de conexão com o banco"""
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT', '5432')
        
        return f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=True):
        """Executa uma query no banco de dados"""
        try:
            with psy.connect(DatabaseManager.get_connection_string()) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, params or ())
                    
                    if fetch_one:
                        return cur.fetchone()
                    elif fetch_all:
                        return cur.fetchall()
                    else:
                        conn.commit()
                        return {"affected_rows": cur.rowcount}
                        
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

class FormDialog(tk.Toplevel):
    """Classe base para diálogos de formulário"""
    
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Variável para resultado
        self.result = None
        
        # Frame principal
        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de botões
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        # Botões padrão
        ttk.Button(self.button_frame, text="Salvar", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def save(self):
        """Método a ser implementado nas subclasses"""
        raise NotImplementedError("Subclasses must implement save method")

class CitizenFormDialog(FormDialog):
    """Formulário para cadastro/edição de cidadãos"""
    
    def __init__(self, parent, citizen_data=None):
        super().__init__(parent, "Cadastrar Cidadão" if not citizen_data else "Editar Cidadão")
        self.citizen_data = citizen_data
        self.create_widgets()
        
    def create_widgets(self):
        # Frame de dados pessoais
        personal_frame = ttk.LabelFrame(self.main_frame, text="Dados Pessoais", padding="10")
        personal_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Nome
        ttk.Label(personal_frame, text="Nome:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.first_name_var = tk.StringVar(value=self.citizen_data.get('first_name', '') if self.citizen_data else '')
        ttk.Entry(personal_frame, textvariable=self.first_name_var, width=40).grid(row=0, column=1, pady=2)
        
        # Sobrenome
        ttk.Label(personal_frame, text="Sobrenome:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.last_name_var = tk.StringVar(value=self.citizen_data.get('last_name', '') if self.citizen_data else '')
        ttk.Entry(personal_frame, textvariable=self.last_name_var, width=40).grid(row=1, column=1, pady=2)
        
        # CPF
        ttk.Label(personal_frame, text="CPF:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.cpf_var = tk.StringVar(value=self.citizen_data.get('cpf', '') if self.citizen_data else '')
        cpf_entry = ttk.Entry(personal_frame, textvariable=self.cpf_var, width=40)
        cpf_entry.grid(row=2, column=1, pady=2)
        
        # Data de nascimento
        ttk.Label(personal_frame, text="Data Nasc:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.birth_date_var = tk.StringVar(value=self.citizen_data.get('birth_date', '') if self.citizen_data else '')
        ttk.Entry(personal_frame, textvariable=self.birth_date_var, width=40).grid(row=3, column=1, pady=2)
        
        # Frame de contato
        contact_frame = ttk.LabelFrame(self.main_frame, text="Contato", padding="10")
        contact_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Email
        ttk.Label(contact_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.email_var = tk.StringVar(value=self.citizen_data.get('email', '') if self.citizen_data else '')
        ttk.Entry(contact_frame, textvariable=self.email_var, width=40).grid(row=0, column=1, pady=2)
        
        # Telefone
        ttk.Label(contact_frame, text="Telefone:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.phone_var = tk.StringVar(value=self.citizen_data.get('phone', '') if self.citizen_data else '')
        ttk.Entry(contact_frame, textvariable=self.phone_var, width=40).grid(row=1, column=1, pady=2)
        
        # Endereço
        ttk.Label(contact_frame, text="Endereço:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.address_var = tk.StringVar(value=self.citizen_data.get('address', '') if self.citizen_data else '')
        ttk.Entry(contact_frame, textvariable=self.address_var, width=40).grid(row=2, column=1, pady=2)
        
        # Frame de acesso
        access_frame = ttk.LabelFrame(self.main_frame, text="Acesso", padding="10")
        access_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Usuário
        ttk.Label(access_frame, text="Usuário:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar(value=self.citizen_data.get('username', '') if self.citizen_data else '')
        ttk.Entry(access_frame, textvariable=self.username_var, width=40).grid(row=0, column=1, pady=2)
        
        # Senha
        ttk.Label(access_frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar()
        ttk.Entry(access_frame, textvariable=self.password_var, show="*", width=40).grid(row=1, column=1, pady=2)
        
        # Frame financeiro
        financial_frame = ttk.LabelFrame(self.main_frame, text="Dados Financeiros", padding="10")
        financial_frame.pack(fill=tk.X)
        
        # Saldo da carteira
        ttk.Label(financial_frame, text="Saldo Carteira:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.wallet_balance_var = tk.StringVar(value=str(self.citizen_data.get('wallet_balance', 0)) if self.citizen_data else '0.00')
        ttk.Entry(financial_frame, textvariable=self.wallet_balance_var, width=40).grid(row=0, column=1, pady=2)
        
        # Dívida
        ttk.Label(financial_frame, text="Dívida:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.debt_var = tk.StringVar(value=str(self.citizen_data.get('debt', 0)) if self.citizen_data else '0.00')
        ttk.Entry(financial_frame, textvariable=self.debt_var, width=40).grid(row=1, column=1, pady=2)
        
        # Status
        ttk.Label(financial_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.allowed_var = tk.BooleanVar(value=self.citizen_data.get('allowed', True) if self.citizen_data else True)
        ttk.Checkbutton(financial_frame, text="Permitido", variable=self.allowed_var).grid(row=2, column=1, sticky=tk.W, pady=2)
        
    def save(self):
        """Salva os dados do cidadão"""
        try:
            # Validação básica
            if not all([self.first_name_var.get(), self.last_name_var.get(), 
                       self.cpf_var.get(), self.email_var.get(), self.username_var.get()]):
                messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                return
                
            # Validar CPF
            cpf = self.cpf_var.get().replace('.', '').replace('-', '')
            if len(cpf) != 11 or not cpf.isdigit():
                messagebox.showerror("Erro", "CPF inválido!")
                return
                
            # Validar email
            if '@' not in self.email_var.get():
                messagebox.showerror("Erro", "Email inválido!")
                return
                
            # Preparar dados
            citizen_data = {
                'first_name': self.first_name_var.get(),
                'last_name': self.last_name_var.get(),
                'cpf': cpf,
                'birth_date': self.birth_date_var.get(),
                'email': self.email_var.get(),
                'phone': self.phone_var.get(),
                'address': self.address_var.get(),
                'username': self.username_var.get(),
                'password': self.password_var.get() if self.password_var.get() else None,
                'wallet_balance': float(self.wallet_balance_var.get() or 0),
                'debt': float(self.debt_var.get() or 0),
                'allowed': self.allowed_var.get()
            }
            
            self.result = citizen_data
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

class VehicleFormDialog(FormDialog):
    """Formulário para cadastro/edição de veículos"""
    
    def __init__(self, parent, vehicle_data=None):
        super().__init__(parent, "Cadastrar Veículo" if not vehicle_data else "Editar Veículo")
        self.vehicle_data = vehicle_data
        self.create_widgets()
        
    def create_widgets(self):
        # Placa
        ttk.Label(self.main_frame, text="Placa:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.license_plate_var = tk.StringVar(value=self.vehicle_data.get('license_plate', '') if self.vehicle_data else '')
        ttk.Entry(self.main_frame, textvariable=self.license_plate_var, width=40).grid(row=0, column=1, pady=5)
        
        # Modelo
        ttk.Label(self.main_frame, text="Modelo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=self.vehicle_data.get('model', '') if self.vehicle_data else '')
        ttk.Entry(self.main_frame, textvariable=self.model_var, width=40).grid(row=1, column=1, pady=5)
        
        # Ano
        ttk.Label(self.main_frame, text="Ano:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.year_var = tk.StringVar(value=str(self.vehicle_data.get('year', '')) if self.vehicle_data else '')
        ttk.Entry(self.main_frame, textvariable=self.year_var, width=40).grid(row=2, column=1, pady=5)
        
        # Status
        ttk.Label(self.main_frame, text="Status:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.allowed_var = tk.BooleanVar(value=self.vehicle_data.get('allowed', True) if self.vehicle_data else True)
        ttk.Checkbutton(self.main_frame, text="Permitido", variable=self.allowed_var).grid(row=3, column=1, sticky=tk.W, pady=5)
        
    def save(self):
        """Salva os dados do veículo"""
        try:
            # Validação básica
            if not all([self.license_plate_var.get(), self.model_var.get(), self.year_var.get()]):
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
                
            # Validar ano
            try:
                year = int(self.year_var.get())
                if year < 1900 or year > 2100:
                    raise ValueError("Ano inválido")
            except ValueError:
                messagebox.showerror("Erro", "Ano inválido!")
                return
                
            # Preparar dados
            vehicle_data = {
                'license_plate': self.license_plate_var.get().upper().replace('-', '').replace(' ', ''),
                'model': self.model_var.get(),
                'year': year,
                'allowed': self.allowed_var.get()
            }
            
            self.result = vehicle_data
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

class SearchDialog(tk.Toplevel):
    """Diálogo de busca genérico"""
    
    def __init__(self, parent, title, search_label):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        # Frame principal
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label e campo de busca
        ttk.Label(main_frame, text=search_label).pack(pady=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        # Frame de botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        ttk.Button(button_frame, text="Buscar", command=self.search).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter key
        search_entry.bind('<Return>', lambda e: self.search())
        
    def search(self):
        """Executa a busca"""
        search_value = self.search_var.get().strip()
        if search_value:
            self.result = search_value
            self.destroy()
        else:
            messagebox.showwarning("Aviso", "Digite um termo para buscar!")

class ReportDialog(tk.Toplevel):
    """Diálogo para exibir relatórios"""
    
    def __init__(self, parent, title, data, columns):
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")
        self.transient(parent)
        
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview para dados
        tree = ttk.Treeview(main_frame, columns=columns, show='headings')
        
        # Configurar colunas
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
            
        # Inserir dados
        for row in data:
            values = [str(row.get(col, '')) for col in columns]
            tree.insert('', tk.END, values=values)
            
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Frame de botões
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Fechar", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Exportar relatório", command=self.export_csv).pack(side=tk.RIGHT, padx=5)
        
        # Armazenar referências
        self.tree = tree
        self.data = data
        self.columns = columns
        
    def export_csv(self):
        """Exporta dados para CSV"""
        try:
            import csv
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Escrever cabeçalho
                    writer.writerow(self.columns)
                    
                    # Escrever dados
                    for row in self.data:
                        values = [str(row.get(col, '')) for col in self.columns]
                        writer.writerow(values)
                        
                messagebox.showinfo("Sucesso", f"Dados exportados para {filename}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
