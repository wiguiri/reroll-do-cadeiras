"""
Módulo de auto-atualização via GitHub Releases.
Gerencia verificação e instalação de atualizações.
"""
import urllib.request
import json
import os
import sys
import subprocess
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import APP_VERSION, GITHUB_REPO


class AutoUpdater:
    """Sistema de auto-atualização via GitHub Releases."""
    
    def __init__(self, current_version=None, github_repo=None):
        self.current_version = current_version or APP_VERSION
        self.github_repo = github_repo or GITHUB_REPO
        self.update_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
    
    def check_for_updates(self):
        """
        Verifica se há atualizações disponíveis.
        
        Returns:
            dict: Informações sobre a atualização disponível ou erro.
        """
        try:
            req = urllib.request.Request(
                self.update_url,
                headers={'User-Agent': 'RerollDoCadeiras-Updater'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            latest_version = data.get('tag_name', '').lstrip('v')
            download_url = None
            
            # Procura o .exe nos assets ou usa o zipball como fallback
            for asset in data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
            
            # Se não tem .exe, usa o zipball (código fonte)
            if not download_url:
                download_url = data.get('zipball_url')
            
            if self._is_newer_version(latest_version):
                return {
                    'available': True,
                    'version': latest_version,
                    'download_url': download_url,
                    'release_notes': data.get('body', 'Sem notas de atualização'),
                    'html_url': data.get('html_url', '')
                }
            
            return {'available': False}
            
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            return {'available': False, 'error': str(e)}
    
    def _is_newer_version(self, remote_version):
        """
        Compara versões no formato X.Y.Z.
        
        Args:
            remote_version: Versão remota para comparar.
            
        Returns:
            bool: True se a versão remota é mais nova.
        """
        try:
            local_parts = [int(x) for x in self.current_version.split('.')]
            remote_parts = [int(x) for x in remote_version.split('.')]
            return remote_parts > local_parts
        except (ValueError, AttributeError):
            return False
    
    def download_and_install(self, download_url, progress_callback=None):
        """
        Baixa e instala a atualização.
        
        Args:
            download_url: URL do arquivo para download.
            progress_callback: Função callback para reportar progresso (0-100).
            
        Returns:
            bool: True se a instalação foi iniciada com sucesso.
        """
        try:
            # Cria arquivo temporário
            temp_dir = tempfile.gettempdir()
            new_exe_path = os.path.join(temp_dir, "RerollDoCadeiras_new.exe")
            
            # Baixa o arquivo com chunks para melhor performance
            req = urllib.request.Request(
                download_url,
                headers={'User-Agent': 'RerollDoCadeiras-Updater'}
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 65536  # 64KB chunks para download mais rápido
                
                with open(new_exe_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            percent = min(100, (downloaded * 100) // total_size)
                            progress_callback(percent)
            
            # Verifica se o arquivo foi baixado
            if not os.path.exists(new_exe_path) or os.path.getsize(new_exe_path) < 1000:
                print("Erro: Arquivo baixado está vazio ou muito pequeno")
                return False
            
            # Cria script batch para substituir o executável
            current_exe = sys.executable if getattr(sys, 'frozen', False) else None
            
            if current_exe:
                batch_path = os.path.join(temp_dir, "update_reroll.bat")
                batch_content = self._create_update_batch(new_exe_path, current_exe)
                
                with open(batch_path, 'w', encoding='utf-8') as f:
                    f.write(batch_content)
                
                # Executa o batch em processo separado
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                subprocess.Popen(
                    ['cmd', '/c', batch_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP,
                    startupinfo=startupinfo,
                    close_fds=True
                )
                return True
            else:
                # Modo desenvolvimento - apenas notifica
                print(f"Modo dev: Novo exe baixado em {new_exe_path}")
                return False
            
        except Exception as e:
            print(f"Erro ao instalar atualização: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_update_batch(self, new_exe_path, current_exe):
        """
        Cria o conteúdo do script batch de atualização.
        
        Args:
            new_exe_path: Caminho do novo executável.
            current_exe: Caminho do executável atual.
            
        Returns:
            str: Conteúdo do script batch.
        """
        # Escapa caminhos para batch
        new_exe = new_exe_path.replace('/', '\\')
        cur_exe = current_exe.replace('/', '\\')
        
        return f'''@echo off
chcp 65001 >nul
echo ========================================
echo    Atualizando Reroll do Cadeiras...
echo ========================================
echo.
echo Aguardando programa fechar...

:WAIT_LOOP
tasklist /FI "IMAGENAME eq RerollDoCadeiras.exe" 2>NUL | find /I /N "RerollDoCadeiras.exe">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto WAIT_LOOP
)

echo Programa fechado. Copiando nova versao...
timeout /t 1 /nobreak >nul

copy /Y "{new_exe}" "{cur_exe}"
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao copiar arquivo!
    echo Verifique se o programa foi fechado corretamente.
    pause
    exit /b 1
)

echo.
echo Limpando arquivos temporarios...
del /f /q "{new_exe}" 2>nul

echo.
echo ========================================
echo    Atualizacao concluida com sucesso!
echo ========================================
echo.
echo Iniciando nova versao...
timeout /t 2 /nobreak >nul

start "" "{cur_exe}"

timeout /t 1 /nobreak >nul
del /f /q "%~f0" 2>nul
exit
'''
