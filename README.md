# 🔥 Criador de Pendrive Bootável Linux — Python GUI

Versão com Licenciamento, Download de ISO, Escrita Segura e Interface em Tkinter

Este projeto é uma ferramenta completa em Python para criação de pendrives bootáveis Linux, com interface gráfica, validações, download de ISOs e mecanismo interno de licença.

O script foi projetado para ser simples de usar, seguro e amigável, enquanto executa tarefas avançadas como checagem de hash, desmontagem automática e gravação utilizando `dd`.


## 🚀 Recursos Principais (baseados no código real)

### 🎨 Interface gráfica (Tkinter)
- Janela principal moderna com tema escuro
- Botões grandes, labels dinâmicos e barra de progresso
- Popups informativos e mensagens de erro

### 📥 Download automático de ISOs
- Baixa ISOs diretamente da internet
- Exibe progresso de download
- Salva localmente na pasta escolhida

### 📂 Seleção de ISO manual
- Seleção via diálogo de arquivos (filedialog)
- Exibe tamanho e informações da ISO
- Calcula hash SHA256 para confirmar integridade

### 🔌 Detecção automática de pendrive
- Analisa dispositivos via `lsblk`
- Identifica automaticamente dispositivos USB
- Exibe nome, tamanho e caminho `/dev/sdX`
- Lista apenas dispositivos removíveis

### 📤 Desmontagem automática
- Antes de gravar, o script executa:
- umount /dev/sdX*

### 💾 Escrita segura com dd
- O script grava a ISO utilizando:  dd if=arquivo.iso of=/dev/sdX bs=4M status=progress
- Após a gravação: sync
- Garante integridade dos dados
- Verifica erros durante o processo

### 🧵 Processamento em threads
- A gravação ocorre em uma thread separada, mantendo a interface responsiva

### 🔐 Sistema de Licenciamento Integrado
- O script realiza:
- Consulta ao servidor usando `requests`
- Validação da chave de licença
- Bloqueio dos recursos caso inválida

### 📝 Logs e status em tempo real
- Log das ações no terminal
- Popups indicam falhas, progresso e sucesso


## 🧩 Dependências do Sistema

Instale os utilitários essenciais:

### Ubuntu/Debian
sudo apt install pv dd coreutils util-linux parted p7zip-full

### Fedora
bash
sudo dnf install pv util-linux coreutils parted p7zip

### Arch
bash
sudo pacman -S pv util-linux coreutils parted p7zip


**🐍 Ambiente Virtual (recomendado)**

Criar venv
python3 -m venv venv

Ativar
source venv/bin/activate

**Instalar dependências Python**
requests
psutil
tkinter (já vem no sistema)
hashlib e outros módulos nativos

Instale:

pip install requests psutil
Ou usando requirements.txt: requests, psutil

### 🖥️ Como Executar
Dentro da venv: python3 bootable_usb_creator_final.py
Ou torne executável: 
chmod +x bootable_usb_creator_final.py
./bootable_usb_creator_final.py

### 🔐 Permissões Necessárias
A gravação precisa de root: sudo venv/bin/python3 bootable_usb_creator_final.py


### 📊 Fluxo Completo (baseado no código real)
Abertura com splash screen animada
Verificação da licença no servidor
Tela principal é carregada
Usuário escolhe ISO ou faz download
Hash SHA256 é calculado
Pendrive USB é detectado
Partições são desmontadas
ISO é gravada via dd
sync finaliza a gravação
Mensagens de sucesso ou erro aparecem
A interface permanece responsiva via threading

### ⚠️ Avisos
Todo conteúdo do pendrive será apagado.
Confirme o dispositivo antes de continuar: lsblk -o NAME,SIZE,MODEL,TRAN
Nunca selecione /dev/sda (normalmente é o disco principal).

### 📁 Estrutura Recomendada
/
├── bootable_usb_creator_final.py
├── README.md
├── requirements.txt
└── assets/
    └── splash/
    
### 🛠️ Melhorias Futuras (compatíveis com seu código)

Verificar checksum via API oficial das distros
Opção para criar pendrive Windows
Exportação de logs
Transformar em AppImage ou .deb
