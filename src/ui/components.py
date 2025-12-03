"""
Componentes de UI reutilizáveis.
Widgets customizados e helpers para construção da interface.
"""
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import COLORS, UI_CONFIG


class AttributeRow:
    """Linha de entrada para atributo com valor."""
    
    def __init__(self, parent, on_delete, name_val="", value_val="", show_value=True, show_required=False):
        """
        Cria uma linha de atributo.
        
        Args:
            parent: Widget pai.
            on_delete: Callback para exclusão.
            name_val: Valor inicial do nome.
            value_val: Valor inicial do valor.
            show_value: Se deve mostrar campo de valor.
            show_required: Se deve mostrar checkbox de obrigatório.
        """
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(fill="x", pady=5, padx=5)
        
        # Label e entrada do nome
        ctk.CTkLabel(self.frame, text="Nome:", font=(UI_CONFIG['font_family'], 11)).pack(side="left", padx=5)
        self.name_entry = ctk.CTkEntry(self.frame, width=180, height=35, placeholder_text="Ex: Strength")
        self.name_entry.pack(side="left", padx=5)
        if name_val:
            self.name_entry.insert(0, name_val)
        
        # Campo de valor (opcional)
        self.value_entry = None
        if show_value:
            ctk.CTkLabel(self.frame, text="Valor:", font=(UI_CONFIG['font_family'], 11)).pack(side="left", padx=5)
            self.value_entry = ctk.CTkEntry(self.frame, width=100, height=35, placeholder_text="Ex: 15")
            self.value_entry.pack(side="left", padx=5)
            if value_val:
                self.value_entry.insert(0, value_val)
        
        # Checkbox de obrigatório (opcional)
        self.required_var = None
        if show_required:
            self.required_var = tk.BooleanVar(value=False)
            required_check = ctk.CTkCheckBox(self.frame, text="⭐ Obrigatório", variable=self.required_var)
            required_check.pack(side="left", padx=10)
        
        # Botão de excluir
        self.delete_btn = ctk.CTkButton(
            self.frame, text="X", width=36, height=36,
            fg_color="#7f1d1d", hover_color="#991b1b",
            text_color="white", font=(UI_CONFIG['font_family'], 14, "bold"),
            command=lambda: on_delete(self)
        )
        self.delete_btn.pack(side="left", padx=5)
    
    def get_name(self):
        """Retorna o nome do atributo."""
        return self.name_entry.get().strip()
    
    def get_value(self):
        """Retorna o valor do atributo."""
        if self.value_entry:
            return self.value_entry.get().strip()
        return ""
    
    def is_required(self):
        """Retorna se o atributo é obrigatório."""
        if self.required_var:
            return self.required_var.get()
        return False
    
    def set_required(self, value):
        """Define se o atributo é obrigatório."""
        if self.required_var:
            self.required_var.set(value)
    
    def destroy(self):
        """Remove o widget."""
        self.frame.destroy()
    
    def to_dict(self):
        """Converte para dicionário."""
        data = {'name': self.get_name()}
        if self.value_entry:
            data['value'] = self.get_value()
        if self.required_var:
            data['required'] = self.is_required()
        return data


class PresetSelector:
    """Seletor de presets com botões de ação."""
    
    def __init__(self, parent, on_select, on_save, on_delete, initial_values=None):
        """
        Cria um seletor de presets.
        
        Args:
            parent: Widget pai.
            on_select: Callback para seleção.
            on_save: Callback para salvar.
            on_delete: Callback para excluir.
            initial_values: Lista inicial de presets.
        """
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(side="right")
        
        values = initial_values or ["Preset 1", "+ Novo Preset"]
        
        self.combo = ctk.CTkComboBox(
            self.frame, width=160, height=32,
            values=values,
            command=on_select,
            font=(UI_CONFIG['font_family'], 11)
        )
        self.combo.pack(side="left", padx=5)
        self.combo.set("Preset 1")
        
        ctk.CTkButton(
            self.frame, text="Salvar", width=70, height=32,
            command=on_save,
            font=(UI_CONFIG['font_family'], 11, "bold"),
            fg_color="#047857", hover_color="#065f46",
            text_color="white"
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            self.frame, text="Excluir", width=70, height=32,
            command=on_delete,
            font=(UI_CONFIG['font_family'], 11),
            fg_color="#b91c1c", hover_color="#991b1b",
            text_color="white"
        ).pack(side="left", padx=2)
    
    def get_selected(self):
        """Retorna o preset selecionado."""
        return self.combo.get()
    
    def set_selected(self, name):
        """Define o preset selecionado."""
        self.combo.set(name)
    
    def update_values(self, values):
        """Atualiza a lista de presets."""
        self.combo.configure(values=values)


class PositionCapture:
    """Widget para captura de posição do mouse."""
    
    def __init__(self, parent, label_text, on_capture):
        """
        Cria um widget de captura de posição.
        
        Args:
            parent: Widget pai.
            label_text: Texto do botão.
            on_capture: Callback para captura.
        """
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(fill="x", pady=8, padx=15)
        
        self.position = None
        
        ctk.CTkButton(
            self.frame, text=label_text,
            command=on_capture, width=200, height=40,
            font=(UI_CONFIG['font_family'], 11, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.label = ctk.CTkLabel(
            self.frame, text="● Não configurada",
            text_color="#ef4444", font=(UI_CONFIG['font_family'], 10)
        )
        self.label.pack(side="left", padx=5)
    
    def set_position(self, x, y):
        """Define a posição capturada."""
        self.position = (x, y)
        self.label.configure(
            text=f"X: {x}, Y: {y}",
            text_color="#10b981"
        )
    
    def get_position(self):
        """Retorna a posição capturada."""
        return self.position
    
    def is_configured(self):
        """Verifica se a posição foi configurada."""
        return self.position is not None


class StatusBar:
    """Barra de status com ícones e cores."""
    
    def __init__(self, parent):
        """
        Cria uma barra de status.
        
        Args:
            parent: Widget pai.
        """
        self.label = ctk.CTkLabel(
            parent, text="● Aguardando configuração...",
            font=(UI_CONFIG['font_family'], 10),
            text_color="gray60"
        )
        self.label.pack(pady=(10, 0))
    
    def update(self, text, status_type='info'):
        """
        Atualiza o status.
        
        Args:
            text: Texto do status.
            status_type: Tipo ('success', 'warning', 'danger', 'info', 'running').
        """
        color_map = {
            'success': COLORS['success'],
            'warning': COLORS['warning'],
            'danger': COLORS['danger'],
            'info': COLORS['dark'],
            'running': COLORS['accent']
        }
        
        icon_map = {
            'success': '✓',
            'warning': '⚠',
            'danger': '✗',
            'info': '●',
            'running': '▶'
        }
        
        color = color_map.get(status_type, COLORS['success'])
        icon = icon_map.get(status_type, '●')
        
        self.label.configure(text=f"{icon} {text}", text_color=color)


class LogWindow:
    """Janela de log detalhado."""
    
    def __init__(self, parent):
        """
        Cria uma janela de log.
        
        Args:
            parent: Widget pai.
        """
        self.parent = parent
        self.window = None
        self.text_widget = None
    
    def open(self):
        """Abre a janela de log."""
        if self.window and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            self.window.focus_force()
            return
        
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("📊 Log Detalhado")
        self.window.geometry("750x500")
        self.window.attributes('-topmost', True)
        
        # Frame principal
        frame = ctk.CTkFrame(self.window, fg_color="#1a1a1a")
        frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="#2d2d2d", height=50)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, text="📊 Valores Capturados em Tempo Real",
            font=('Segoe UI', 16, 'bold'),
            text_color="white"
        ).pack(side="left", padx=15, pady=10)
        
        # Botão toggle topmost
        ctk.CTkButton(
            header, text="📌", width=40, height=30,
            font=("Segoe UI", 14),
            fg_color="#4b5563", hover_color="#374151",
            text_color="white",
            command=self._toggle_topmost
        ).pack(side="right", padx=5, pady=10)
        
        # Botão limpar
        ctk.CTkButton(
            header, text="🗑 Limpar", width=80, height=30,
            font=("Segoe UI", 11),
            fg_color="#7f1d1d", hover_color="#991b1b",
            text_color="white",
            command=self.clear
        ).pack(side="right", padx=5, pady=10)
        
        # Área de texto
        text_frame = ctk.CTkFrame(frame, fg_color="#1a1a1a")
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.text_widget = tk.Text(
            text_frame, wrap=tk.WORD,
            font=('Consolas', 12),
            bg="#1e1e1e", fg="#e0e0e0",
            insertbackground="white",
            selectbackground="#3d5a80",
            relief="flat", padx=10, pady=10
        )
        
        scrollbar = ctk.CTkScrollbar(text_frame, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurar tags de cores
        self.text_widget.tag_config('success', foreground='#4ade80', font=('Consolas', 12, 'bold'))
        self.text_widget.tag_config('warning', foreground='#fbbf24', font=('Consolas', 12, 'bold'))
        self.text_widget.tag_config('error', foreground='#f87171', font=('Consolas', 12, 'bold'))
        self.text_widget.tag_config('info', foreground='#60a5fa', font=('Consolas', 12))
        self.text_widget.tag_config('header', foreground='#c084fc', font=('Consolas', 13, 'bold'))
        
        self.log("Log detalhado iniciado.", 'info')
        self.log("Os valores capturados aparecerão aqui em tempo real.", 'info')
    
    def _toggle_topmost(self):
        """Alterna se a janela fica sempre no topo."""
        if self.window:
            current = self.window.attributes('-topmost')
            self.window.attributes('-topmost', not current)
    
    def log(self, message, tag='info'):
        """
        Adiciona mensagem ao log.
        
        Args:
            message: Mensagem para adicionar.
            tag: Tag de formatação.
        """
        try:
            if self.window and tk.Toplevel.winfo_exists(self.window) and self.text_widget:
                import time
                timestamp = time.strftime("%H:%M:%S")
                self.text_widget.insert(tk.END, f"[{timestamp}] {message}\n", tag)
                self.text_widget.see(tk.END)
                self.window.update_idletasks()
        except:
            pass
    
    def clear(self):
        """Limpa o log."""
        if self.text_widget:
            self.text_widget.delete(1.0, tk.END)
    
    def is_open(self):
        """Verifica se a janela está aberta."""
        return self.window and tk.Toplevel.winfo_exists(self.window)
