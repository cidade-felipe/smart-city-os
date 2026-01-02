#!/usr/bin/env python3
"""
SmartCityOS GUI - Interface Gráfica Desktop
Executável principal para iniciar a interface do SmartCityOS
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from gui.main_app import SmartCityOSGUI
    
    def main():
        """Função principal da aplicação GUI"""
        try:
            # Criar janela principal
            root = tk.Tk()
            
            # Configurar ícone (se disponível)
            try:
                # Tenta carregar ícone personalizado
                root.iconbitmap('gui/icon.ico')
            except:
                pass  # Continua sem ícone se não encontrar
            
            # Criar aplicação
            app = SmartCityOSGUI(root)
            
            # Iniciar loop principal
            print("🚀 SmartCityOS GUI iniciado")
            print("📋 Interface Gráfica Desktop")
            print("🔧 Conecte-se ao banco de dados para começar")
            
            root.mainloop()
            
        except KeyboardInterrupt:
            print("\n👋 Aplicação encerrada pelo usuário")
        except Exception as e:
            print(f"❌ Erro ao iniciar aplicação: {str(e)}")
            input("Pressione Enter para sair...")

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Erro de importação: {str(e)}")
    print("💡 Verifique se todas as dependências estão instaladas:")
    print("   pip install psycopg python-dotenv pandas tabulate")
    input("Pressione Enter para sair...")
except Exception as e:
    print(f"❌ Erro inesperado: {str(e)}")
    input("Pressione Enter para sair...")
