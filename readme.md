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