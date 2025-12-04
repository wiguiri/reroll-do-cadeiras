"""
Diálogos e janelas modais.
"""
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import UI_CONFIG, APP_VERSION


class HotkeySettingsDialog:
    """Diálogo para configuração de atalhos."""
    
    def __init__(self, parent, current_hotkeys, on_save):
        """
        Cria o diálogo de configuração de atalhos.
        
        Args:
            parent: Widget pai.
            current_hotkeys: Dicionário com atalhos atuais.
            on_save: Callback para salvar (recebe dict com novos atalhos).
        """
        self.parent = parent
        self.on_save = on_save
        self.hotkey_vars = {}
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("⚙️ Configurar Atalhos")
        self.window.geometry("450x350")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Centraliza
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 225
        y = (self.window.winfo_screenheight() // 2) - 175
        self.window.geometry(f"+{x}+{y}")
        
        # Inicializa variáveis
        for key, value in current_hotkeys.items():
            self.hotkey_vars[key] = tk.StringVar(value=value)
        
        self._build_ui()
        
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_ui(self):
        """Constrói a interface do diálogo."""
        # Título
        ctk.CTkLabel(
            self.window, text="⚙️ Configurar Teclas de Atalho",
            font=(UI_CONFIG['font_family'], 18, "bold")
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            self.window, text="Clique no campo e pressione a nova tecla",
            font=(UI_CONFIG['font_family'], 11), text_color="gray60"
        ).pack(pady=(0, 15))
        
        # Frame para os atalhos
        hotkeys_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        hotkeys_frame.pack(fill="x", padx=30, pady=10)
        
        labels = {
            'region': '🎯 Selecionar Região:',
            'test': '🔍 Testar Captura:',
            'start': '▶ Iniciar Automação:',
            'stop': '⬛ Parar Automação:'
        }
        
        self.entries = {}
        
        for key_name, label_text in labels.items():
            row_frame = ctk.CTkFrame(hotkeys_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=8)
            
            ctk.CTkLabel(
                row_frame, text=label_text,
                font=(UI_CONFIG['font_family'], 12),
                width=180, anchor="w"
            ).pack(side="left")
            
            entry = ctk.CTkEntry(
                row_frame, textvariable=self.hotkey_vars[key_name],
                width=100, height=35, font=(UI_CONFIG['font_family'], 12, "bold"),
                justify="center", border_color="gray50"
            )
            entry.pack(side="left", padx=10)
            entry.bind('<KeyPress>', lambda e, kn=key_name, ent=entry: self._capture_key(e, kn, ent))
            self.entries[key_name] = entry
        
        # Botões
        buttons_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        buttons_frame.pack(pady=25)
        
        ctk.CTkButton(
            buttons_frame, text="✓ Salvar", command=self._save,
            width=120, height=40, font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="#10b981", hover_color="#059669"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttons_frame, text="↺ Padrão", command=self._reset_defaults,
            width=120, height=40, font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="gray40", hover_color="gray30"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttons_frame, text="Cancelar", command=self._on_close,
            width=100, height=40, font=(UI_CONFIG['font_family'], 12),
            fg_color="gray30", hover_color="gray20"
        ).pack(side="left", padx=10)
    
    def _capture_key(self, event, key_name, entry):
        """Captura a tecla pressionada."""
        key = event.keysym
        if key in ['Escape', 'Return', 'Tab']:
            return "break"
        
        # Formata a tecla
        formatted_key = key.upper() if len(key) == 1 else key.capitalize()
        if key.lower().startswith('f') and key[1:].isdigit():
            formatted_key = key.upper()
        
        self.hotkey_vars[key_name].set(formatted_key)
        entry.configure(border_color="#10b981")
        self.window.after(500, lambda: entry.configure(border_color="gray50"))
        return "break"
    
    def _save(self):
        """Salva os atalhos."""
        # Verifica duplicatas
        values = [v.get().upper() for v in self.hotkey_vars.values()]
        if len(values) != len(set(values)):
            messagebox.showwarning("Aviso", "Não pode haver atalhos duplicados!")
            return
        
        # Prepara resultado
        result = {key: var.get().upper() for key, var in self.hotkey_vars.items()}
        
        self.window.destroy()
        self.on_save(result)
        messagebox.showinfo("✓ Sucesso", "Atalhos atualizados com sucesso!")
    
    def _reset_defaults(self):
        """Restaura atalhos padrão."""
        self.hotkey_vars['region'].set('F1')
        self.hotkey_vars['test'].set('F3')
        self.hotkey_vars['start'].set('F5')
        self.hotkey_vars['stop'].set('F6')
    
    def _on_close(self):
        """Fecha o diálogo."""
        result = {key: var.get().upper() for key, var in self.hotkey_vars.items()}
        self.window.destroy()
        self.on_save(result)


class NewPresetDialog:
    """Diálogo para criar novo preset."""
    
    def __init__(self, parent, existing_names, on_create):
        """
        Cria o diálogo de novo preset.
        
        Args:
            parent: Widget pai.
            existing_names: Lista de nomes existentes.
            on_create: Callback para criar (recebe nome).
        """
        self.parent = parent
        self.existing_names = existing_names
        self.on_create = on_create
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Novo Preset")
        self.dialog.geometry("420x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centraliza
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 210
        y = (self.dialog.winfo_screenheight() // 2) - 125
        self.dialog.geometry(f"+{x}+{y}")
        
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface do diálogo."""
        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Título
        ctk.CTkLabel(
            main_frame, text="Criar Novo Preset",
            font=(UI_CONFIG['font_family'], 18, "bold")
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            main_frame, text="Digite um nome para o novo preset:",
            font=(UI_CONFIG['font_family'], 11), text_color="gray60"
        ).pack(pady=(0, 15))
        
        self.name_entry = ctk.CTkEntry(
            main_frame, width=320, height=42,
            placeholder_text="Ex: Build DPS, Tank Setup...",
            font=(UI_CONFIG['font_family'], 12)
        )
        self.name_entry.pack(pady=(0, 20))
        self.name_entry.focus()
        self.name_entry.bind('<Return>', lambda e: self._create())
        
        # Botões
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_inner.pack()
        
        ctk.CTkButton(
            btn_inner, text="Criar", command=self._create,
            width=130, height=42, font=(UI_CONFIG['font_family'], 13, "bold"),
            fg_color="#047857", hover_color="#065f46",
            text_color="white"
        ).pack(side="left", padx=8)
        
        ctk.CTkButton(
            btn_inner, text="Cancelar", command=self.dialog.destroy,
            width=130, height=42, font=(UI_CONFIG['font_family'], 13),
            fg_color="#4b5563", hover_color="#374151",
            text_color="white"
        ).pack(side="left", padx=8)
    
    def _create(self):
        """Cria o preset."""
        name = self.name_entry.get().strip()
        
        if not name or name == "+ Novo Preset":
            messagebox.showwarning("Aviso", "Digite um nome válido para o preset")
            return
        
        if name in self.existing_names:
            messagebox.showwarning("Aviso", f"Já existe um preset com o nome '{name}'")
            return
        
        self.dialog.destroy()
        self.on_create(name)
        messagebox.showinfo("Sucesso", f"Preset '{name}' criado!")


class UpdateDialog:
    """Diálogo de atualização disponível."""
    
    def __init__(self, parent, update_info, on_update):
        """
        Cria o diálogo de atualização.
        
        Args:
            parent: Widget pai.
            update_info: Informações da atualização.
            on_update: Callback para iniciar atualização.
        """
        self.parent = parent
        self.update_info = update_info
        self.on_update = on_update
        
        # Limita o tamanho das notas
        notes = update_info.get('release_notes', 'Sem notas de atualização')
        if len(notes) > 500:
            notes = notes[:500] + "..."
        
        download_url = update_info.get('download_url', '')
        has_exe = download_url and download_url.endswith('.exe')
        
        if has_exe:
            msg = f"""🎉 Nova versão disponível!

📌 Versão atual: {APP_VERSION}
🆕 Nova versão: {update_info['version']}

📝 Notas da atualização:
{notes}

Deseja atualizar agora?"""
            
            if messagebox.askyesno("🔄 Atualização Disponível", msg):
                on_update(download_url)
        else:
            # Não tem .exe, mostra link para download manual
            import webbrowser
            html_url = update_info.get('html_url', f"https://github.com/wiguiri/reroll-do-cadeiras/releases")
            
            msg = f"""🎉 Nova versão disponível!

📌 Versão atual: {APP_VERSION}
🆕 Nova versão: {update_info['version']}

📝 Notas da atualização:
{notes}

⚠️ Atualização automática não disponível.
Deseja abrir a página de download no navegador?"""
            
            if messagebox.askyesno("🔄 Atualização Disponível", msg):
                webbrowser.open(html_url)


class UpdateProgressDialog:
    """Diálogo de progresso de atualização."""
    
    def __init__(self, parent):
        """
        Cria o diálogo de progresso.
        
        Args:
            parent: Widget pai.
        """
        self.window = ctk.CTkToplevel(parent)
        self.window.title("🔄 Atualizando...")
        self.window.geometry("450x180")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Centraliza
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 225
        y = (self.window.winfo_screenheight() // 2) - 90
        self.window.geometry(f"+{x}+{y}")
        
        # Conteúdo
        ctk.CTkLabel(
            self.window, text="📥 Baixando atualização...",
            font=(UI_CONFIG['font_family'], 16, "bold")
        ).pack(pady=(25, 15))
        
        self.progress_bar = ctk.CTkProgressBar(self.window, width=380, height=20)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self.window, text="0%",
            font=(UI_CONFIG['font_family'], 12)
        )
        self.progress_label.pack(pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.window, text="Conectando ao servidor...",
            font=(UI_CONFIG['font_family'], 10), text_color="gray60"
        )
        self.status_label.pack(pady=5)
    
    def update_progress(self, percent):
        """
        Atualiza o progresso.
        
        Args:
            percent: Porcentagem (0-100).
        """
        try:
            self.progress_bar.set(percent / 100)
            self.progress_label.configure(text=f"{percent}%")
            if percent < 100:
                self.status_label.configure(text="Baixando arquivo...")
            else:
                self.status_label.configure(text="Instalando atualização...")
            self.window.update()
        except:
            pass
    
    def destroy(self):
        """Fecha o diálogo."""
        try:
            self.window.destroy()
        except:
            pass
