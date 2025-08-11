# Sobre o projeto

O projeto é uma aplicação web que masteriza músicas automaticamente. O usuário envia um arquivo de áudio ou indica uma música de referência, e o sistema aplica ajustes de volume, equalização e dinâmica usando técnicas de processamento digital de sinais. Tudo é feito em Python com Flask e bibliotecas como Librosa e Pedalboard, garantindo um fluxo simples e rápido.

### Como funciona tecnicamente

#### Front-end: HTML/CSS/JS (com Flask servindo páginas)
 #### Back-end: Python + Flask
#### Bibliotecas utilizadas:
- librosa: leitura e análise de áudio
- pedalboard: aplicação de efeitos DSP (compressor, limiter, ganho)
- matplotlib: geração de forma de onda para comparação
- yt_dlp: download de referência de áudio do YouTube
- soundfile: exportação do áudio processado
#### Fluxo:

Usuário envia música ou link do YouTube.
Sistema converte para WAV (se necessário).
Calcula parâmetros (volume, dinâmica) comparando com áudio de referência.
Aplica processamento digital (compressão, ganho, limitação).
Gera visualização da forma de onda original e masterizada.
Permite baixar o áudio final.

# 💻 Como rodar o projeto:

## ✅ COM AMBIENTE VIRTUAL (RECOMENDADO)

### Abra o terminal e vá para a pasta do seu projeto:

```
cd /caminho/do/seu/projeto
```

### Crie o ambiente virtual:

```
python3 -m venv venv
```

### Ative o ambiente virtual:

#### No Linux/macOS:

```
source venv/bin/activate
```

#### No Windows (PowerShell):

```
.\venv\Scripts\Activate.ps1
```

### Instale as dependências:

#### ⚠️  OBS: Usuário deve estar localizado na pasta raíz do projeto

```
pip install -r requirements.txt
```

### Rode seu app Flask dentro do ambiente ativado:

```
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5002
```

### Para sair do ambiente virtual

```
deactivate
````

## 🚫 SEM AMBIENTE VIRTUAL

### Instale as dependências:

#### ⚠️  OBS : Usuário deve estar localizado na pasta raíz do projeto

```
pip install -r requirements.txt
```

### Abra o terminal, vá até a pasta raiz e execute:

```
cd music-mastering-app && python3 app.py
```

### Após isso, abrir o serividor web que vai estar rodando, neste caso:

```
Running on http://127.0.0.1:5002
```