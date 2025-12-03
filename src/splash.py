"""
Módulo da Splash Screen.
Tela de loading com animações.
"""
import tkinter as tk
import time
import random

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import APP_VERSION, SPLASH_CONFIG


class SplashScreen:
    """Tela de loading moderna com animações de partículas."""
    
    def __init__(self):
        """Cria a splash screen."""
        self.splash = tk.Tk()
        self.splash.overrideredirect(True)
        self.splash.attributes('-topmost', True)
        
        self.width = SPLASH_CONFIG['width']
        self.height = SPLASH_CONFIG['height']
        
        # Centralizar
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        self.splash.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Canvas
        self.canvas = tk.Canvas(
            self.splash, width=self.width, height=self.height,
            bg=SPLASH_CONFIG['bg_color'], highlightthickness=0
        )
        self.canvas.pack()
        
        self._draw_background()
        self._create_particles()
        self._draw_content()
        self._create_progress_bar()
        
        self.splash.update()
    
    def _draw_background(self):
        """Desenha o fundo com gradiente simulado."""
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#0f0f1a", outline="")
        self.canvas.create_rectangle(10, 10, self.width-10, self.height-10, fill="#1a1a2e", outline="")
        self.canvas.create_rectangle(15, 15, self.width-15, self.height-15, fill="#16213e", outline="")
        
        # Borda brilhante
        self.canvas.create_rectangle(
            15, 15, self.width-15, self.height-15,
            outline=SPLASH_CONFIG['accent_color'], width=2
        )
    
    def _create_particles(self):
        """Cria partículas de fundo."""
        self.particles = []
        colors = ["#4a5de0", "#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe"]
        
        for _ in range(20):
            px = random.randint(30, self.width-30)
            py = random.randint(30, self.height-30)
            size = random.randint(2, 5)
            color = random.choice(colors)
            
            p = self.canvas.create_oval(
                px-size, py-size, px+size, py+size,
                fill=color, outline=""
            )
            
            self.particles.append({
                'id': p, 'x': px, 'y': py,
                'dx': random.uniform(-0.8, 0.8),
                'dy': random.uniform(-0.8, 0.8),
                'size': size
            })
    
    def _draw_content(self):
        """Desenha o conteúdo principal."""
        # Ícone
        self.canvas.create_text(
            self.width//2, 90, text="⚡",
            font=("Segoe UI", 55), fill=SPLASH_CONFIG['accent_color']
        )
        
        # Título
        self.canvas.create_text(
            self.width//2, 170, text="REROLL DO",
            font=("Segoe UI", 28, "bold"), fill="#e0e7ff"
        )
        self.canvas.create_text(
            self.width//2, 215, text="CADEIRAS",
            font=("Segoe UI", 36, "bold"), fill="#818cf8"
        )
        
        # Subtítulo
        self.canvas.create_text(
            self.width//2, 260, text="por Victor Gomes de Sá",
            font=("Segoe UI", 10), fill="#64748b"
        )
        
        # Versão
        self.canvas.create_text(
            self.width//2, self.height-25, text=f"v{APP_VERSION}",
            font=("Segoe UI", 9), fill="#475569"
        )
    
    def _create_progress_bar(self):
        """Cria a barra de progresso."""
        self.bar_x = 80
        self.bar_y = 310
        self.bar_width = self.width - 160
        self.bar_height = 12
        
        # Fundo da barra
        self.canvas.create_rectangle(
            self.bar_x-2, self.bar_y-2,
            self.bar_x + self.bar_width+2, self.bar_y + self.bar_height+2,
            fill="#0f172a", outline="#334155"
        )
        
        # Barra de progresso
        self.progress_bar = self.canvas.create_rectangle(
            self.bar_x, self.bar_y,
            self.bar_x, self.bar_y + self.bar_height,
            fill=SPLASH_CONFIG['accent_color'], outline=""
        )
        
        # Texto de status
        self.status_text = self.canvas.create_text(
            self.width//2, 350, text="Iniciando...",
            font=("Segoe UI", 11), fill="#94a3b8"
        )
    
    def animate_particles(self):
        """Anima as partículas de fundo."""
        for p in self.particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            
            # Bounce nas bordas
            if p['x'] < 40 or p['x'] > self.width-40:
                p['dx'] *= -1
            if p['y'] < 40 or p['y'] > self.height-40:
                p['dy'] *= -1
            
            self.canvas.coords(
                p['id'],
                p['x']-p['size'], p['y']-p['size'],
                p['x']+p['size'], p['y']+p['size']
            )
    
    def update_progress(self, value, status="Carregando..."):
        """
        Atualiza a barra de progresso.
        
        Args:
            value: Valor de 0 a 1.
            status: Texto de status.
        """
        fill_width = int(self.bar_width * value)
        self.canvas.coords(
            self.progress_bar,
            self.bar_x, self.bar_y,
            self.bar_x + fill_width, self.bar_y + self.bar_height
        )
        self.canvas.itemconfig(self.status_text, text=status)
        
        self.animate_particles()
        self.splash.update()
    
    def run_animation(self):
        """Executa a animação completa de loading."""
        status_messages = [
            (0.0, "Inicializando..."),
            (0.25, "Carregando módulos..."),
            (0.50, "Configurando interface..."),
            (0.75, "Preparando automação..."),
            (0.95, "Pronto!")
        ]
        
        fps = SPLASH_CONFIG['animation_fps']
        duration = SPLASH_CONFIG['duration_seconds']
        total_steps = fps * duration
        
        for i in range(int(total_steps) + 1):
            progress = i / total_steps
            
            current_status = "Iniciando..."
            for threshold, msg in status_messages:
                if progress >= threshold:
                    current_status = msg
            
            self.update_progress(progress, current_status)
            time.sleep(1.0 / fps)
        
        time.sleep(0.2)
    
    def destroy(self):
        """Fecha a splash com fade out."""
        try:
            for alpha in [0.8, 0.6, 0.4, 0.2, 0]:
                self.splash.attributes('-alpha', alpha)
                self.splash.update()
                time.sleep(0.03)
            self.splash.destroy()
        except:
            pass
