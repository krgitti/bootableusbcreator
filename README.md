**🔥 Criador de Pendrive Bootável Linux — Python GUI**

Versão com Licenciamento, Download de ISO, Escrita Segura e Interface em Tkinter

Este projeto é uma ferramenta completa em Python para criação de pendrives bootáveis Linux, com interface gráfica, validações, download de ISOs e mecanismo interno de licença.

O script foi projetado para ser simples de usar, seguro e amigável, enquanto executa tarefas avançadas como checagem de hash, desmontagem automática e gravação utilizando dd.

**🚀 Recursos Principais (baseados no código real)
🎨 Interface gráfica (Tkint**er)

Janela principal moderna com tema escuro

Botões grandes, labels dinâmicos, barra de progresso

Popups informativos e mensagens de erro

**📥 Download automático de ISOs**

O script permite baixar a ISO diretamente da internet, salvando-a localmente com barra de progresso.

**📂 Seleção de ISO manual**

Seleção via diálogo do Tkinter (filedialog)

Exibe tamanho e informações da ISO

Calcula hash SHA256 da imagem

**🔌 Detecção automática de pendrive**

Utiliza lsblk + análise de interface (usb)

Lista apenas dispositivos removíveis

Exibe nome real, tamanho e caminho /dev/sdX

**📤 Desmontagem automática**

Antes de gravar, o script executa:

umount /dev/sdX*

**💾 Escrita segura com dd**

Baseado no código real:

Usa dd diretamente com:

dd if=arquivo.iso of=/dev/sdX bs=4M status=progress


**Executa sync ao final**

Verifica erros durante a execução

**🧵 Processamento em threads**

A gravação é feita em thread separada, evitando travar a interface.

**🔐 Sistema de Licenciamento Integrado**

O script:

Consulta servidor usando requests

Valida a chave informada

Bloqueia recursos caso a licença seja inválida

**📝 Logs e status em tempo real**

Cada etapa é exibida no terminal

Popups amigáveis indicam falhas, progresso e sucesso

**🧩 Dependências do Sistema**

Instale os utilitários essenciais:

Ubuntu/Debian
sudo apt install pv dd coreutils util-linux parted p7zip-full

Fedora
sudo dnf install pv util-linux coreutils parted p7zip

Arch
sudo pacman -S pv util-linux coreutils parted p7zip

**🐍 Ambiente Virtual (recomendado)**
Criar venv
python3 -m venv venv

Ativar
source venv/bin/activate

Instalar dependências Python

O script utiliza:

requests

psutil

tkinter (já vem no sistema)

hashlib e outros módulos nativos

Instale:

pip install requests psutil


Ou com requirements.txt:

requests
psutil

**🖥️ Como Executar**

Dentro da venv:

python3 bootable_usb_creator_final.py


Ou torne executável:

chmod +x bootable_usb_creator_final.py
./bootable_usb_creator_final.py

**🔐 Permissões Necessárias**

A gravação precisa de root:

sudo venv/bin/python3 bootable_usb_creator_final.py

**📊 Fluxo Completo (baseado no código real)**

Abertura com splash screen animada

Verificação de licença no servidor

Tela principal abre

Usuário escolhe ISO ou baixa da internet

Hash SHA256 é calculado

Pendrive USB é detectado automaticamente

Partições são desmontadas

ISO é gravada via dd

sync garante finalização completa

Mensagem de sucesso ou erro é exibida

Interface continua responsiva graças ao threading

**⚠️ Avisos**

Todo conteúdo do pendrive será apagado.

Confirme o dispositivo com:

lsblk -o NAME,SIZE,MODEL,TRAN


Nunca selecione /dev/sda.

**📁 Estrutura Recomendada**
/
├── bootable_usb_creator_final.py
├── README.md
├── requirements.txt
└── assets/
    └── splash/

**🛠️ Melhorias Futuras (compatíveis com seu código)**

Verificar checksum via API oficial das distros

Opção de criar pendrive Windows

Exportação de logs

Transformar em AppImage ou .deb
