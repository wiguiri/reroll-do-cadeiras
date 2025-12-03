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
            
            # Procura o .exe nos assets
            for asset in data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
            
            if self._is_newer_version(latest_version):
                return {
                    'available': True,
                    'version': latest_version,
                    'download_url': download_url,
                    'release_notes': data.get('body', 'Sem notas de atualização')
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
            
            # Baixa o arquivo com progresso
            def report_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    progress_callback(percent)
            
            urllib.request.urlretrieve(download_url, new_exe_path, report_progress)
            
            # Cria script batch para substituir o executável
            current_exe = sys.executable if getattr(sys, 'frozen', False) else None
            
            if current_exe:
                batch_path = os.path.join(temp_dir, "update_reroll.bat")
                batch_content = self._create_update_batch(new_exe_path, current_exe)
                
                with open(batch_path, 'w') as f:
                    f.write(batch_content)
                
                # Executa o batch e fecha o programa
                subprocess.Popen(
                    batch_path, 
                    shell=True, 
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                return True
            
            return False
            
        except Exception as e:
            print(f"Erro ao instalar atualização: {e}")
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
        return f'''@echo off
echo ========================================
echo    Atualizando Reroll do Cadeiras...
echo ========================================
timeout /t 2 /nobreak >nul
copy /Y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo ERRO: Falha ao copiar arquivo!
    pause
    exit /b 1
)
del "{new_exe_path}"
echo Atualizacao concluida! Reiniciando...
timeout /t 1 /nobreak >nul
start "" "{current_exe}"
del "%~f0"
'''
