# 🎵 Plataforma para Produtores Musicais

Uma plataforma web completa desenvolvida em Python com Flask, oferecendo ferramentas profissionais para produtores musicais.

## ✨ Funcionalidades

### 🏠 **Home** (`/`)
- Página de apresentação da plataforma
- Explicação clara das funcionalidades disponíveis
- Botões de login/cadastro para usuários não autenticados
- **Acesso**: Público (não requer login)

### 📚 **Tutoriais** (`/tutoriais`)
- Biblioteca de vídeos tutoriais sobre produção musical
- Links para canais recomendados do YouTube
- Recursos adicionais (livros, software)
- **Acesso**: Público (não requer login)

### 👻 **Serviços** (`/servicos`)
- Divulgação de serviços de ghost producer
- Pacotes com diferentes níveis de serviço
- Formulário de contato integrado
- **Acesso**: Apenas usuários logados

### 🎛️ **Masterização** (`/masterizacao`)
- Ferramenta avançada de masterização baseada em referência
- Upload de arquivos WAV/MP3 ou URLs do YouTube
- Controles personalizáveis (compressor, limiter, gain)
- Visualização de waveforms em tempo real
- Preview de áudio antes e depois
- **Acesso**: Apenas usuários logados

### 🔐 **Sistema de Autenticação**
- **Login** (`/login`): Acesso à conta existente
- **Cadastro** (`/cadastro`): Criação de nova conta
- **Logout** (`/logout`): Encerramento de sessão
- Senhas armazenadas com hash seguro (Werkzeug)
- Gerenciamento de sessões com Flask-Login

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.8+
- **Framework**: Flask
- **Autenticação**: Flask-Login
- **Banco de Dados**: SQLite
- **Processamento de Áudio**: Librosa, Pedalboard, SoundFile
- **Frontend**: HTML5, CSS3, JavaScript
- **Download de Vídeos**: yt-dlp
- **Visualização**: Matplotlib

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- FFmpeg (para processamento de áudio)

### Instalação no macOS

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd music-mastering-app
   ```

2. **Crie um ambiente virtual**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instale o FFmpeg** (se ainda não tiver)
   ```bash
   # Usando Homebrew
   brew install ffmpeg
   
   # Ou usando MacPorts
   sudo port install ffmpeg
   ```

### Instalação no Windows

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd music-mastering-app
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instale o FFmpeg**
   - Baixe de: https://ffmpeg.org/download.html
   - Adicione ao PATH do sistema

### Instalação no Linux (Ubuntu/Debian)

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd music-mastering-app
   ```

2. **Crie um ambiente virtual**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instale o FFmpeg**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

## 🚀 Executando o Projeto

1. **Ative o ambiente virtual**
   ```bash
   # macOS/Linux
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

2. **Configure a variável de ambiente** (opcional)
   ```bash
   # macOS/Linux
   export FLASK_APP=app.py
   export SECRET_KEY=sua_chave_secreta_aqui
   
   # Windows
   set FLASK_APP=app.py
   set SECRET_KEY=sua_chave_secreta_aqui
   ```

3. **Execute a aplicação**
   ```bash
   python app.py
   ```

4. **Acesse no navegador**
   ```
   http://localhost:5002
   ```

## 📁 Estrutura do Projeto

```
music-mastering-app/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── users.db              # Banco de dados SQLite (criado automaticamente)
├── static/               # Arquivos estáticos
│   └── style.css        # Estilos CSS
├── templates/            # Templates HTML
│   ├── base.html        # Template base
│   ├── home.html        # Página inicial
│   ├── tutoriais.html   # Página de tutoriais
│   ├── servicos.html    # Página de serviços
│   ├── masterizacao.html # Página de masterização
│   ├── login.html       # Página de login
│   └── cadastro.html    # Página de cadastro
└── uploads/             # Pasta para arquivos enviados
```

## 🔒 Segurança

- **Senhas**: Armazenadas com hash seguro usando Werkzeug
- **Sessões**: Gerenciadas com Flask-Login
- **Uploads**: Validação de tipos de arquivo permitidos
- **Autenticação**: Páginas protegidas com decorator `@login_required`

## 🎵 Funcionalidades de Áudio

### Formatos Suportados
- **Entrada**: WAV, MP3
- **Saída**: WAV

### Processamento
- **Compressor**: Threshold, ratio, attack, release configuráveis
- **Limiter**: Threshold e release ajustáveis
- **Gain**: Ajuste de volume em dB
- **Referência**: Arquivo local ou URL do YouTube

### Visualização
- Waveforms em tempo real
- Comparação antes/depois
- Preview de áudio

## 🌐 Rotas da Aplicação

| Rota | Método | Descrição | Acesso |
|------|--------|-----------|---------|
| `/` | GET | Página inicial | Público |
| `/tutoriais` | GET | Tutoriais de produção | Público |
| `/servicos` | GET | Serviços de ghost producer | Logado |
| `/masterizacao` | GET | Ferramenta de masterização | Logado |
| `/login` | GET, POST | Autenticação | Público |
| `/cadastro` | GET, POST | Criação de conta | Público |
| `/logout` | GET | Encerrar sessão | Logado |
| `/processar_masterizacao` | POST | Processar áudio | Logado |
| `/masterize` | POST | Aplicar mudanças | Logado |
| `/download/<filename>` | GET | Download de arquivo | Logado |
| `/enviar_contato` | POST | Formulário de contato | Logado |

## 🐛 Solução de Problemas

### Erro: "FFmpeg not found"
- Instale o FFmpeg seguindo as instruções acima
- Verifique se está no PATH do sistema

### Erro: "Port already in use"
- Altere a porta no arquivo `app.py` (linha 244)
- Ou pare outros processos usando a porta 5002

### Erro: "Module not found"
- Verifique se o ambiente virtual está ativado
- Execute `pip install -r requirements.txt` novamente

### Problemas de áudio
- Verifique se os arquivos são WAV ou MP3 válidos
- URLs do YouTube devem ser válidas e públicas

## 🔧 Configuração Avançada

### Variáveis de Ambiente
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY=sua_chave_super_secreta
export UPLOAD_FOLDER=uploads
export MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Personalização
- **Porta**: Altere a linha 244 em `app.py`
- **Host**: Altere a linha 244 em `app.py`
- **Tamanho máximo de upload**: Configure no código
- **Formatos de áudio**: Modifique `ALLOWED_EXTENSIONS`

## 📱 Recursos Mobile

- Design responsivo para dispositivos móveis
- Interface otimizada para touch
- Navegação adaptativa

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte ou dúvidas:
- Abra uma issue no repositório
- Entre em contato via formulário na página de serviços

## 🚀 Roadmap

- [ ] Sistema de pagamentos integrado
- [ ] API REST para integração com outros sistemas
- [ ] Mais formatos de áudio suportados
- [ ] Sistema de templates de masterização
- [ ] Integração com DAWs populares
- [ ] Sistema de colaboração em tempo real

---

**Desenvolvido com ❤️ para a comunidade de produtores musicais**
