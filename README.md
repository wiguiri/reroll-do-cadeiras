# ⚡ Reroll do Cadeiras v1.2.0

Ferramenta de automação para reroll de atributos em jogos.

**por Victor Gomes de Sá**

## ✨ Funcionalidades

- **🎯 Valores Específicos** - Rola até atingir valores mínimos de atributos
- **🔍 Busca de Atributos** - Procura por atributos específicos (todos ou mínimo)
- **⭐ Buscar T7** - Rola até encontrar atributos Tier 7 (qualquer ou específico)
- **🔑 Automação de Chaves** - Automação com Orb of Chance
- **⚡ Skill Spam** - Envia teclas automaticamente para um programa (novo!)

## 🆕 Novidades v1.2.0

- Nova aba **Skill Spam** para enviar teclas automaticamente
- Aba **Buscar T7** com detecção de tiers
- Abas maiores e mais legíveis
- Correção de bugs nos hotkeys remapeados
- Código refatorado em módulos

## 📁 Estrutura do Projeto

```
windsurf-project-2/
├── main.py                    # Ponto de entrada principal
├── game_automation.py         # Versão legada (arquivo único)
├── requirements.txt           # Dependências Python
├── src/                       # Módulos refatorados
│   ├── __init__.py
│   ├── config.py              # Configurações e constantes
│   ├── app.py                 # Aplicação principal (GameAutomation)
│   ├── automation.py          # Motor de automação
│   ├── ocr_engine.py          # Motor de OCR (Tesseract)
│   ├── presets.py             # Gerenciamento de presets
│   ├── splash.py              # Splash screen
│   ├── updater.py             # Sistema de auto-atualização
│   └── ui/                    # Componentes de interface
│       ├── __init__.py
│       ├── components.py      # Widgets reutilizáveis
│       ├── dialogs.py         # Diálogos e modais
│       └── tabs.py            # Abas da interface
├── tesseract_portable/        # Tesseract OCR portátil
├── icone.png                  # Ícone da aplicação
└── icone.ico                  # Ícone para Windows
```

## 🚀 Como Executar

### Versão Refatorada (Recomendada)
```bash
python main.py
```

### Versão Legada (Arquivo Único)
```bash
python game_automation.py
```

## 📦 Dependências

```bash
pip install -r requirements.txt
```

Dependências principais:
- `customtkinter` - Interface moderna
- `pytesseract` - OCR
- `pyautogui` - Automação de mouse/teclado
- `keyboard` - Captura de teclas globais
- `Pillow` - Processamento de imagens

## 🔧 Módulos

### `config.py`
Centraliza todas as configurações:
- Versão do app
- Caminhos do sistema
- Cores e temas
- Atalhos padrão
- Atributos especiais do jogo

### `app.py`
Classe principal `GameAutomation`:
- Gerencia a interface
- Coordena os outros módulos
- Salva/carrega configurações

### `automation.py`
Motor de automação `AutomationEngine`:
- Loop de valores específicos
- Loop de busca de atributos
- Loop de automação de chaves

### `ocr_engine.py`
Motor de OCR `OCREngine`:
- Captura de tela
- Extração de texto
- Processamento de imagem
- Correções de OCR

### `presets.py`
Gerenciadores:
- `PresetManager` - Presets de configuração
- `ConfigManager` - Configurações gerais

### `ui/components.py`
Widgets reutilizáveis:
- `AttributeRow` - Linha de atributo
- `PresetSelector` - Seletor de presets
- `PositionCapture` - Captura de posição
- `LogWindow` - Janela de log

### `ui/tabs.py`
Abas da interface:
- `ValuesTab` - Valores específicos
- `SearchTab` - Busca de atributos
- `KeysTab` - Automação de chaves

### `ui/dialogs.py`
Diálogos:
- `HotkeySettingsDialog` - Configuração de atalhos
- `NewPresetDialog` - Criar preset
- `UpdateDialog` - Atualização disponível

## ⌨️ Atalhos Padrão

| Ação | Tecla |
|------|-------|
| Selecionar Região | F1 |
| Testar Captura | F3 |
| Iniciar | F5 |
| Parar | F6 |

## 🔄 Versionamento

Versão atual: **1.1.0**

O sistema verifica atualizações automaticamente via GitHub Releases.

## 📝 Licença

Projeto pessoal de Victor Gomes de Sá.
