"""
Reroll do Cadeiras - Ponto de entrada principal.
por Victor Gomes de Sá

Este arquivo inicia a aplicação com splash screen e carrega a interface principal.
"""
import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

from src.splash import SplashScreen
from src.app import GameAutomation


def main():
    """Função principal que inicia a aplicação."""
    print("🚀 Iniciando Reroll do Cadeiras...")
    
    try:
        # Mostra splash screen
        splash = SplashScreen()
        splash.run_animation()
        splash.destroy()
        
        # Cria janela principal
        print("✓ Carregando interface...")
        root = ctk.CTk()
        app = GameAutomation(root)
        
        print("✓ Pronto!")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
