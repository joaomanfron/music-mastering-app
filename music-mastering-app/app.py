import os
import sqlite3
import re
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Usar backend não-interativo
import matplotlib.pyplot as plt
import numpy as np
import librosa
import soundfile as sf
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import traceback
from functools import wraps
import uuid
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, LowpassFilter


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Classe User para Flask-Login
class User(UserMixin):
    def __init__(self, id, nome, email, senha_hash):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash

# Funções do banco de dados
def init_db():
    try:
        print("Inicializando banco de dados...")
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verifica se a tabela já existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Criando tabela 'users'...")
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL
                )
            ''')
            conn.commit()
            print("Tabela 'users' criada com sucesso!")
        else:
            print("Tabela 'users' já existe!")
        
        # Criar tabela para tutoriais assistidos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tutorials_watched'")
        if not cursor.fetchone():
            print("Criando tabela 'tutorials_watched'...")
            cursor.execute('''
                CREATE TABLE tutorials_watched (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tutorial_id TEXT NOT NULL,
                    watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    progress INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            print("Tabela 'tutorials_watched' criada com sucesso!")
        
        # Criar tabela para músicas masterizadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mastered_songs'")
        if not cursor.fetchone():
            print("Criando tabela 'mastered_songs'...")
            cursor.execute('''
                CREATE TABLE mastered_songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    mastered_filename TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            print("Tabela 'mastered_songs' criada com sucesso!")
        
        # Criar tabela para downloads
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'")
        if not cursor.fetchone():
            print("Criando tabela 'downloads'...")
            cursor.execute('''
                CREATE TABLE downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            print("Tabela 'downloads' criada com sucesso!")
        
        # Criar tabela para solicitações de ghost producer
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ghost_producer_requests'")
        if not cursor.fetchone():
            print("Criando tabela 'ghost_producer_requests'...")
            cursor.execute('''
                CREATE TABLE ghost_producer_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    package TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    description TEXT,
                    budget REAL,
                    deadline TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            print("Tabela 'ghost_producer_requests' criada com sucesso!")
        
        # Verifica a estrutura da tabela
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print(f"Colunas na tabela: {[col[1] for col in columns]}")
        
        conn.close()
        print("Banco de dados inicializado com sucesso!")
    except Exception as e:
        import traceback
        print(f"Erro ao inicializar banco de dados: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise

def get_user_by_id(user_id):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(user_data[0], user_data[1], user_data[2], user_data[3])
        return None
    except Exception as e:
        print(f"Erro ao buscar usuário por ID: {str(e)}")
        return None

def get_user_by_email(email):
    try:
        print(f"Conectando ao banco de dados para buscar email: {email}")
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verifica se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Tabela 'users' não existe!")
            conn.close()
            return None
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            print(f"Usuário encontrado: ID={user_data[0]}, Nome={user_data[1]}")
            return User(user_data[0], user_data[1], user_data[2], user_data[3])
        else:
            print("Usuário não encontrado no banco")
            return None
    except Exception as e:
        import traceback
        print(f"Erro ao buscar usuário por email: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

# Funções para o dashboard do usuário
def get_user_dashboard_data(user_id):
    try:
        print(f"=== INÍCIO get_user_dashboard_data para usuário {user_id} ===")
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verificar se as tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"Tabelas existentes: {existing_tables}")
        
        # Contar tutoriais assistidos
        tutorials_watched = 0
        if 'tutorials_watched' in existing_tables:
            try:
                cursor.execute('SELECT COUNT(*) FROM tutorials_watched WHERE user_id = ?', (user_id,))
                tutorials_watched = cursor.fetchone()[0]
                print(f"Tutoriais assistidos: {tutorials_watched}")
            except Exception as e:
                print(f"Erro ao contar tutoriais assistidos: {str(e)}")
                tutorials_watched = 0
        
        # Contar músicas masterizadas
        mastered_songs = 0
        if 'mastered_songs' in existing_tables:
            try:
                cursor.execute('SELECT COUNT(*) FROM mastered_songs WHERE user_id = ?', (user_id,))
                mastered_songs = cursor.fetchone()[0]
                print(f"Músicas masterizadas: {mastered_songs}")
            except Exception as e:
                print(f"Erro ao contar músicas masterizadas: {str(e)}")
                mastered_songs = 0
        
        # Buscar histórico de downloads
        downloads = []
        if 'downloads' in existing_tables:
            try:
                print("Buscando downloads...")
                cursor.execute('''
                    SELECT file_type, filename, downloaded_at 
                    FROM downloads 
                    WHERE user_id = ? 
                    ORDER BY downloaded_at DESC 
                    LIMIT 10
                ''', (user_id,))
                raw_downloads = cursor.fetchall()
                print(f"Downloads encontrados: {len(raw_downloads)}")
                
                # Processar e limpar os dados, verificando se os arquivos ainda existem
                for download in raw_downloads:
                    cleaned_download = []
                    for i, field in enumerate(download):
                        if field is None:
                            cleaned_download.append('')
                        elif i == 1 and field:  # filename
                            # Verificar se o arquivo ainda existe
                            file_path = os.path.join('uploads', field)
                            if os.path.exists(file_path):
                                cleaned_download.append(str(field))
                            else:
                                cleaned_download.append('')  # Arquivo não existe mais
                        else:
                            cleaned_download.append(str(field))
                    
                    # Só adicionar se o arquivo ainda existir
                    if cleaned_download[1]:  # Se filename ainda existe
                        downloads.append(cleaned_download)
                
                print(f"Downloads válidos: {len(downloads)}")
                    
            except Exception as e:
                print(f"Erro ao buscar downloads: {str(e)}")
                downloads = []
        
        # Buscar solicitações de ghost producer
        ghost_requests = []
        if 'ghost_producer_requests' in existing_tables:
            try:
                print("Buscando solicitações de ghost producer...")
                # Verificar se as novas colunas existem
                cursor.execute("PRAGMA table_info(ghost_producer_requests)")
                columns = [column[1] for column in cursor.fetchall()]
                print(f"Colunas da tabela ghost_producer_requests: {columns}")
                
                if 'package' in columns and 'deadline' in columns:
                    cursor.execute('''
                        SELECT id, package, genre, description, budget, deadline, status, created_at, completed_at 
                        FROM ghost_producer_requests 
                        WHERE user_id = ? 
                        ORDER BY created_at DESC
                    ''', (user_id,))
                else:
                    # Fallback para versão antiga da tabela
                    cursor.execute('''
                        SELECT id, genre, description, budget, status, created_at, completed_at 
                        FROM ghost_producer_requests 
                        WHERE user_id = ? 
                        ORDER BY created_at DESC
                    ''', (user_id,))
                
                raw_requests = cursor.fetchall()
                print(f"Solicitações encontradas: {len(raw_requests)}")
                
                # Processar e limpar os dados
                for request in raw_requests:
                    cleaned_request = []
                    for field in request:
                        if field is None:
                            cleaned_request.append('')
                        else:
                            cleaned_request.append(str(field))
                    ghost_requests.append(cleaned_request)
                
                print(f"Solicitações processadas: {len(ghost_requests)}")
                    
            except Exception as e:
                print(f"Erro ao buscar solicitações ghost producer: {str(e)}")
                ghost_requests = []
        
        # Buscar músicas masterizadas recentes
        recent_masters = []
        if 'mastered_songs' in existing_tables:
            try:
                print("Buscando músicas masterizadas recentes...")
                cursor.execute('''
                    SELECT original_filename, mastered_filename, created_at, status 
                    FROM mastered_songs 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 5
                ''', (user_id,))
                raw_masters = cursor.fetchall()
                print(f"Músicas masterizadas encontradas: {len(raw_masters)}")
                
                # Processar e limpar os dados, verificando se os arquivos ainda existem
                for master in raw_masters:
                    cleaned_master = []
                    for i, field in enumerate(master):
                        if field is None:
                            cleaned_master.append('')
                        elif i in [0, 1] and field:  # original_filename ou mastered_filename
                            # Verificar se o arquivo ainda existe
                            file_path = os.path.join('uploads', field)
                            if os.path.exists(file_path):
                                cleaned_master.append(str(field))
                            else:
                                cleaned_master.append('')  # Arquivo não existe mais
                        else:
                            cleaned_master.append(str(field))
                    
                    # Só adicionar se pelo menos um dos arquivos ainda existir
                    if any(cleaned_master[0:2]):  # Se original ou mastered ainda existem
                        recent_masters.append(cleaned_master)
                
                print(f"Músicas masterizadas válidas: {len(recent_masters)}")
                    
            except Exception as e:
                print(f"Erro ao buscar músicas masterizadas recentes: {str(e)}")
                recent_masters = []
        
        conn.close()
        
        result = {
            'tutorials_watched': tutorials_watched,
            'mastered_songs': mastered_songs,
            'downloads': downloads,
            'ghost_requests': ghost_requests,
            'recent_masters': recent_masters
        }
        
        print(f"=== RESULTADO get_user_dashboard_data ===")
        print(f"Resultado final: {result}")
        print(f"=== FIM get_user_dashboard_data ===")
        
        return result
    except Exception as e:
        print(f"❌ ERRO CRÍTICO em get_user_dashboard_data: {str(e)}")
        import traceback
        print(f"Traceback completo:\n{traceback.format_exc()}")
        return None

def mark_tutorial_watched(user_id, tutorial_id):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tutorials_watched'")
        if not cursor.fetchone():
            print("Tabela 'tutorials_watched' não existe!")
            conn.close()
            return False
        
        # Verificar se já foi assistido
        cursor.execute('SELECT id FROM tutorials_watched WHERE user_id = ? AND tutorial_id = ?', (user_id, tutorial_id))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO tutorials_watched (user_id, tutorial_id) VALUES (?, ?)', (user_id, tutorial_id))
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao marcar tutorial como assistido: {str(e)}")
        return False

def record_mastered_song(user_id, session_id, original_filename, mastered_filename):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mastered_songs'")
        if not cursor.fetchone():
            print("Tabela 'mastered_songs' não existe!")
            conn.close()
            return False
        
        cursor.execute('''
            INSERT INTO mastered_songs (user_id, session_id, original_filename, mastered_filename) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, session_id, original_filename, mastered_filename))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao registrar música masterizada: {str(e)}")
        return False

def record_download(user_id, file_type, filename):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'")
        if not cursor.fetchone():
            print("Tabela 'downloads' não existe!")
            conn.close()
            return False
        
        cursor.execute('INSERT INTO downloads (user_id, file_type, filename) VALUES (?, ?, ?)', (user_id, file_type, filename))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao registrar download: {str(e)}")
        return False

# Callback para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        return get_user_by_id(int(user_id))
    except Exception as e:
        print(f"Erro no load_user: {str(e)}")
        return None

# Decorator personalizado para login obrigatório
def login_required_custom(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user or not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
                flash('Você precisa estar logado para acessar esta página.', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Erro no decorator de login: {str(e)}")
            flash('Erro de autenticação. Tente fazer login novamente.', 'error')
            return redirect(url_for('login'))
    return decorated_function

# Rotas principais
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/tutoriais')
def tutoriais():
    return render_template('tutoriais.html')

@app.route('/servicos')
@login_required_custom
def servicos():
    return render_template('servicos.html')

@app.route('/masterizacao')
@login_required_custom
def masterizacao():
    return render_template('masterizacao.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            print("Recebendo dados do formulário de login...")
            email = request.form.get('email')
            senha = request.form.get('senha')
            
            print(f"Email recebido: {email}")
            print(f"Senha recebida: {'*' * len(senha) if senha else 'None'}")
            
            if not email or not senha:
                print("Campos vazios detectados")
                flash('Por favor, preencha todos os campos.', 'error')
                return render_template('login.html')
            
            print("Buscando usuário no banco de dados...")
            user = get_user_by_email(email)
            print(f"Usuário encontrado: {user is not None}")
            
            if user:
                print("Verificando senha...")
                password_check = check_password_hash(user.senha_hash, senha)
                print(f"Senha válida: {password_check}")
                
                if password_check:
                    print("Fazendo login do usuário...")
                    login_user(user)
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('home'))
                else:
                    print("Senha incorreta")
                    flash('Email ou senha incorretos.', 'error')
            else:
                print("Usuário não encontrado")
                flash('Email ou senha incorretos.', 'error')
        return render_template('login.html')
    except Exception as e:
        import traceback
        print(f"Erro no login: {str(e)}")
        print(f"Traceback completo: {traceback.format_exc()}")
        flash('Ocorreu um erro interno. Tente novamente.', 'error')
        return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    try:
        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            confirmar_senha = request.form.get('confirmar_senha')

            if not nome or not email or not senha or not confirmar_senha:
                flash('Por favor, preencha todos os campos.', 'error')
                return render_template('cadastro.html')

            if senha != confirmar_senha:
                flash('As senhas não coincidem.', 'error')
                return render_template('cadastro.html')
            
            if len(senha) < 6:
                flash('A senha deve ter pelo menos 6 caracteres.', 'error')
                return render_template('cadastro.html')
                
            if get_user_by_email(email):
                flash('Este email já está cadastrado.', 'error')
                return render_template('cadastro.html')

            senha_hash = generate_password_hash(senha, method='pbkdf2:sha256')
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)', 
                          (nome, email, senha_hash))
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))

        return render_template('cadastro.html')
    except Exception as e:
        print(f"Erro no cadastro: {str(e)}")
        flash('Ocorreu um erro interno. Tente novamente.', 'error')
        return render_template('cadastro.html')

@app.route('/logout')
@login_required_custom
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required_custom
def dashboard():
    try:
        print(f"=== INÍCIO DA ROTA DASHBOARD ===")
        print(f"Usuário atual: {current_user}")
        print(f"ID do usuário: {current_user.id}")
        print(f"Usuário autenticado: {current_user.is_authenticated}")
        
        print("Chamando get_user_dashboard_data...")
        user_data = get_user_dashboard_data(current_user.id)
        
        if user_data is None:
            print("❌ ERRO: get_user_dashboard_data retornou None")
            flash('Erro ao carregar dados do dashboard.', 'error')
            return redirect(url_for('home'))
        
        print(f"✅ Dados do dashboard carregados: {user_data}")
        print("Renderizando template...")
        
        result = render_template('dashboard.html', dashboard_data=user_data)
        print("✅ Template renderizado com sucesso!")
        print(f"Tamanho do resultado: {len(result)} caracteres")
        
        return result
        
    except Exception as e:
        print(f"❌ ERRO NA ROTA DASHBOARD: {str(e)}")
        import traceback
        print(f"Traceback completo:\n{traceback.format_exc()}")
        flash('Erro interno ao carregar dashboard. Tente novamente.', 'error')
        return redirect(url_for('home'))

@app.route('/dashboard-test')
def dashboard_test():
    """Rota de teste para o dashboard sem autenticação"""
    try:
        # Dados de teste
        test_data = {
            'tutorials_watched': 0,
            'mastered_songs': 0,
            'downloads': [],
            'ghost_requests': [],
            'recent_masters': []
        }
        
        # Template simples para teste
        simple_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard Test</title>
        </head>
        <body>
            <h1>Dashboard Test</h1>
            <p>Tutoriais: {{ dashboard_data.tutorials_watched }}</p>
            <p>Músicas: {{ dashboard_data.mastered_songs }}</p>
            <p>Downloads: {{ dashboard_data.downloads|length }}</p>
            <p>Ghost Requests: {{ dashboard_data.ghost_requests|length }}</p>
            <p>Recent Masters: {{ dashboard_data.recent_masters|length }}</p>
        </body>
        </html>
        '''
        
        from flask import render_template_string
        return render_template_string(simple_template, dashboard_data=test_data)
    except Exception as e:
        return f'Erro no template: {str(e)}', 500

@app.route('/api/mark-tutorial-watched', methods=['POST'])
@login_required_custom
def api_mark_tutorial_watched():
    data = request.get_json()
    tutorial_id = data.get('tutorial_id')
    
    if not tutorial_id:
        return jsonify({'success': False, 'error': 'ID do tutorial não fornecido'})
    
    success = mark_tutorial_watched(current_user.id, tutorial_id)
    return jsonify({'success': success})

@app.route('/api/request-ghost-producer', methods=['POST'])
@login_required_custom
def api_request_ghost_producer():
    try:
        data = request.get_json()
        package = data.get('package')
        genre = data.get('genre')
        description = data.get('description')
        deadline = data.get('deadline')
        
        if not package or not genre or not description:
            return jsonify({'success': False, 'error': 'Pacote, gênero e descrição são obrigatórios'})
        
        # Validar pacote
        valid_packages = ['basico', 'profissional', 'premium']
        if package not in valid_packages:
            return jsonify({'success': False, 'error': 'Pacote inválido'})
        
        # Calcular orçamento baseado no pacote e prazo
        base_prices = {
            'basico': 500,
            'profissional': 800,
            'premium': 1200
        }
        
        deadline_fees = {
            'urgent': 0.20  # 20% do preço base
        }
        
        base_price = base_prices.get(package, 0)
        deadline_fee = 0
        if deadline == 'urgent':
            deadline_fee = base_price * deadline_fees['urgent']
        total_price = base_price + deadline_fee
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ghost_producer_requests'")
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Sistema de solicitações não disponível no momento'})
        
        # Verificar se a tabela tem os novos campos
        cursor.execute("PRAGMA table_info(ghost_producer_requests)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'package' not in columns:
            # Adicionar coluna package se não existir
            cursor.execute('ALTER TABLE ghost_producer_requests ADD COLUMN package TEXT')
        if 'deadline' not in columns:
            # Adicionar coluna deadline se não existir
            cursor.execute('ALTER TABLE ghost_producer_requests ADD COLUMN deadline TEXT')
        
        cursor.execute('''
            INSERT INTO ghost_producer_requests (user_id, package, genre, description, budget, deadline) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_user.id, package, genre, description, total_price, deadline))
        conn.commit()
        conn.close()
        
        # Mensagem personalizada baseada no pacote e prazo
        package_names = {
            'basico': 'Básico',
            'profissional': 'Profissional',
            'premium': 'Premium'
        }
        
        deadline_names = {
            'urgent': 'Urgente'
        }
        
        deadline_text = f" ({deadline_names.get(deadline, '')})" if deadline else ""
        fee_text = f" + Taxa de prazo urgente: 20% (R$ {deadline_fee:.2f})" if deadline_fee > 0 else ""
        
        message = f'Solicitação do pacote {package_names[package]}{deadline_text} enviada com sucesso! Orçamento: R$ {total_price:.2f}{fee_text}. Entraremos em contato em até 24 horas.'
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao enviar solicitação: {str(e)}'})

@app.route('/api/delete-ghost-request', methods=['POST'])
@login_required_custom
def api_delete_ghost_request():
    """Rota para excluir solicitação de ghost producer"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({'success': False, 'error': 'ID da solicitação não fornecido'})
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verificar se a solicitação existe e pertence ao usuário
        cursor.execute('''
            SELECT id FROM ghost_producer_requests 
            WHERE id = ? AND user_id = ?
        ''', (request_id, current_user.id))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Solicitação não encontrada ou não pertence a você'})
        
        # Excluir a solicitação
        cursor.execute('DELETE FROM ghost_producer_requests WHERE id = ?', (request_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Solicitação excluída com sucesso!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao excluir solicitação: {str(e)}'})

@app.route('/cleanup-files')
@login_required_custom
def cleanup_files_route():
    """Rota para limpar arquivos ausentes (apenas para administradores)"""
    try:
        # Verificar se é admin (você pode ajustar essa lógica)
        if current_user.id == 1:  # Assumindo que ID 1 é admin
            cleanup_missing_files()
            return jsonify({'success': True, 'message': 'Limpeza concluída com sucesso'})
        else:
            return jsonify({'success': False, 'error': 'Acesso negado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ======================
# NOVA FUNÇÃO + ROTA 🔽
# ======================



@app.route('/api/youtube-tutorials')
def get_youtube_tutorials():
    # Dados estáticos dos tutoriais (sem chamadas à API)
    basic_tutorials = [
        {
            'id': 'H_yZyEdymfA',
            'title': 'Introdução ao Áudio e Produção Musical',
            'description': 'Introdução ao Áudio e Produção Musical.',
            'channel': 'Rafa Dutra',
            'view_count': 125000,
            'like_count': 8500,
            'thumbnail': 'https://img.youtube.com/vi/H_yZyEdymfA/maxresdefault.jpg',
            'embed_url': 'https://www.youtube.com/embed/H_yZyEdymfA'
        },
        {
            'id': 'xWJym2N6X7U',
            'title': 'como fazer seu PRIMEIRO BEAT (Tutorial FL Studio)',
            'description': 'como fazer seu PRIMEIRO BEAT (Tutorial FL Studio).',
            'channel': 'PMM Beats',
            'view_count': 89000,
            'like_count': 6200,
            'thumbnail': 'https://img.youtube.com/vi/xWJym2N6X7U/maxresdefault.jpg',
            'embed_url': 'https://www.youtube.com/embed/xWJym2N6X7U'
        }
    ]
    
    premium_tutorials = [
        {
            'id': 'ji1Uv6Mvpys',
            'title': 'The Best FREE Plugins for 2025',
            'description': 'The Best FREE Plugins for 2025.',
            'channel': 'EdTalenti',
            'view_count': 156000,
            'like_count': 9200,
            'thumbnail': 'https://img.youtube.com/vi/ji1Uv6Mvpys/maxresdefault.jpg',
            'embed_url': 'https://www.youtube.com/embed/ji1Uv6Mvpys'
        },
        {
            'id': 'jhSQaAm76P0',
            'title': 'Qual melhor programa de gravação de áudio (DAW) e Produção Musical? Como escolher a melhor DAW',
            'description': 'CQual melhor programa de gravação de áudio (DAW) e Produção Musical? Como escolher a melhor DAW.',
            'channel': 'Studio Lego',
            'view_count': 203000,
            'like_count': 15400,
            'thumbnail': 'https://img.youtube.com/vi/jhSQaAm76P0/maxresdefault.jpg',
            'embed_url': 'https://www.youtube.com/embed/jhSQaAm76P0'
        },
        {
            'id': 'TovdcbfNQoc',
            'title': '5 Dicas Pra Começar Sua Carreira Como PRODUTOR MUSICAL - Checklist',
            'description': '5 Dicas Pra Começar Sua Carreira Como PRODUTOR MUSICAL - Checklist.',
            'channel': 'Novo Artista',
            'view_count': 98000,
            'like_count': 7800,
            'thumbnail': 'https://img.youtube.com/vi/TovdcbfNQoc/maxresdefault.jpg',
            'embed_url': 'https://www.youtube.com/embed/TovdcbfNQoc'
        },
        {
            'id': 'qNByGNJVsnI',
            'title': 'A Revolução da IA na Produção Musical Já Começou',
            'description': 'CA Revolução da IA na Produção Musical Já Começou.',
            'channel': 'Studio do Compositor',
            'view_count': 134000,
            'like_count': 8900,
            'thumbnail': 'https://img.youtube.com/vi/qNByGNJVsnI/maxresdefault.jpg',
            'embed_url': 'https://www.youtube.com/embed/qNByGNJVsnI'
        }
    ]
    
    # Determina quais tutoriais mostrar baseado no status de login
    if current_user.is_authenticated:
        tutorials = basic_tutorials + premium_tutorials
    else:
        tutorials = basic_tutorials

    return jsonify({
        'success': True,
        'tutorials': tutorials,
        'total': len(tutorials),
        'is_authenticated': current_user.is_authenticated
    })

# ======================

# Rota de processamento de masterização
@app.route('/processar_masterizacao', methods=['POST'])
@login_required_custom
def processar_masterizacao():
    try:
        if 'target_file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo de música enviado'})

        target_file = request.files['target_file']
        reference_type = request.form.get('reference_type', 'file')

        if target_file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo de música selecionado'})

        session_id = str(uuid.uuid4())
        target_filename = f"{session_id}_target.wav"
        target_path = os.path.join('uploads', target_filename)
        target_file.save(target_path)

        reference_path = None
        reference_filename = None

        if reference_type == 'file':
            if 'reference_file' not in request.files:
                return jsonify({'success': False, 'error': 'Arquivo de referência não enviado'})
            reference_file = request.files['reference_file']
            if reference_file.filename == '':
                return jsonify({'success': False, 'error': 'Nenhum arquivo de referência selecionado'})
            reference_filename = f"{session_id}_reference.wav"
            reference_path = os.path.join('uploads', reference_filename)
            reference_file.save(reference_path)
        elif reference_type == 'youtube':
            youtube_url = request.form.get('youtube_url')
            if not youtube_url:
                return jsonify({'success': False, 'error': 'Link do YouTube não fornecido'})
            
            # Criar um arquivo de áudio placeholder para YouTube
            reference_filename = f"{session_id}_youtube_reference.wav"
            reference_path = os.path.join('uploads', reference_filename)
            
            try:
                import numpy as np
                # Criar um arquivo de áudio de exemplo (1 segundo de silêncio)
                sample_rate = 44100
                duration = 1.0
                samples = int(sample_rate * duration)
                audio_data = np.zeros(samples)
                sf.write(reference_path, audio_data, sample_rate)
            except Exception as e:
                return jsonify({'success': False, 'error': f'Erro ao processar link do YouTube: {str(e)}'})

        # Processar a música imediatamente para gerar os resultados
        try:
            target_audio, target_sr = librosa.load(target_path, sr=None)
            
            # Se não houver arquivo de referência, usar o próprio arquivo como referência
            if os.path.exists(reference_path):
                reference_audio, reference_sr = librosa.load(reference_path, sr=None)
            else:
                reference_audio = target_audio
                reference_sr = target_sr

            # Aplicar masterização profissional
            mastering_params = {
                'compressor_threshold': -24,
                'compressor_ratio': 1.8,
                'gain_db': 1.2,
                'limiter_threshold': -0.8
            }
            mastered_audio = apply_professional_mastering(target_audio, target_sr, mastering_params)

            mastered_filename = f"mastered_{session_id}.wav"
            mastered_path = os.path.join('uploads', mastered_filename)
            sf.write(mastered_path, mastered_audio, target_sr)

            # Gerar waveform da música original
            original_waveform_filename, original_waveform_path = generate_beautiful_waveform(target_audio, target_sr, 'Música Original', session_id, 'original_waveform')

            # Gerar waveform da música masterizada
            mastered_waveform_filename, mastered_waveform_path = generate_beautiful_waveform(mastered_audio, target_sr, 'Música Masterizada', session_id, 'mastered_waveform')

            # Converter waveforms para base64
            with open(original_waveform_path, 'rb') as f:
                original_waveform_b64 = base64.b64encode(f.read()).decode()
            with open(mastered_waveform_path, 'rb') as f:
                mastered_waveform_b64 = base64.b64encode(f.read()).decode()

            # Registrar música masterizada no banco de dados
            original_filename = os.path.basename(target_path)
            record_mastered_song(current_user.id, session_id, original_filename, mastered_filename)

            return jsonify({
                'success': True,
                'session_id': session_id,
                'target_path': target_path,
                'reference_path': reference_path,
                'output_filename': mastered_filename,
                'original_waveform': original_waveform_b64,
                'mastered_waveform': mastered_waveform_b64,
                'params': {
                    'use_compressor': True,
                    'compressor_threshold': -24,
                    'compressor_ratio': 1.8,
                    'gain_db': 1.2,
                    'use_limiter': True,
                    'limiter_threshold': -0.8
                }
            })

        except Exception as e:
            return jsonify({'success': False, 'error': f'Erro na masterização: {str(e)}'})

    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro geral: {str(e)}'})

@app.route('/masterize', methods=['POST'])
@login_required_custom
def masterize():
    try:
        # Aceitar tanto form data quanto JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'session_id': request.form.get('session_id'),
                'params': {
                    'compressor_threshold': request.form.get('compressor_threshold', -24),
                    'compressor_ratio': request.form.get('compressor_ratio', 1.8),
                    'gain_db': request.form.get('gain_db', 1.2),
                    'limiter_threshold': request.form.get('limiter_threshold', -0.8)
                },
                'target_path': request.form.get('target_path')
            }
        
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'})
        
        session_id = data.get('session_id')
        params = data.get('params', {})
        target_path = data.get('target_path')
        
        if not session_id or not target_path:
            return jsonify({'success': False, 'error': 'Session ID ou target path não fornecidos'})

        compressor_threshold = float(params.get('compressor_threshold', -24))
        compressor_ratio = float(params.get('compressor_ratio', 1.8))
        gain_db = float(params.get('gain_db', 1.2))
        limiter_threshold = float(params.get('limiter_threshold', -0.8))

        if not os.path.exists(target_path):
            return jsonify({'success': False, 'error': 'Arquivo de música não encontrado'})

        # Verificar se existe arquivo de referência
        reference_path = target_path.replace('_target.wav', '_reference.wav')
        if not os.path.exists(reference_path):
            reference_path = target_path  # Usar o próprio arquivo como referência

        try:
            target_audio, target_sr = librosa.load(target_path, sr=None)
            
            # Se não houver arquivo de referência, usar o próprio arquivo como referência
            if os.path.exists(reference_path) and reference_path != target_path:
                reference_audio, reference_sr = librosa.load(reference_path, sr=None)
            else:
                reference_audio = target_audio
                reference_sr = target_sr

            # Aplicar masterização profissional
            mastering_params = {
                'compressor_threshold': compressor_threshold,
                'compressor_ratio': compressor_ratio,
                'gain_db': gain_db,
                'limiter_threshold': limiter_threshold
            }
            mastered_audio = apply_professional_mastering(target_audio, target_sr, mastering_params)

            mastered_filename = f"mastered_{session_id}.wav"
            mastered_path = os.path.join('uploads', mastered_filename)
            sf.write(mastered_path, mastered_audio, target_sr)

            # Gerar waveform otimizado (mais rápido)
            mastered_waveform_filename, mastered_waveform_path = generate_fast_waveform(mastered_audio, target_sr, 'Música Masterizada', session_id, 'mastered_waveform')

            # Converter waveform para base64
            with open(mastered_waveform_path, 'rb') as f:
                waveform_b64 = base64.b64encode(f.read()).decode()

            return jsonify({
                'success': True,
                'mastered_filename': mastered_filename,
                'waveform_filename': mastered_waveform_filename,
                'mastered_waveform': waveform_b64,
                'output_filename': mastered_filename,
                'message': 'Masterização concluída com sucesso!'
            })

        except Exception as e:
            return jsonify({'success': False, 'error': f'Erro na masterização: {str(e)}'})

    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro geral: {str(e)}'})

@app.route('/download/<filename>')
@login_required_custom
def download(filename):
    file_path = os.path.join('uploads', filename)
    if os.path.exists(file_path):
        # Registrar download no banco de dados
        file_type = 'mastered' if filename.startswith('mastered_') else 'original'
        record_download(current_user.id, file_type, filename)
        
        return send_file(file_path, as_attachment=True)
    else:
        flash('Arquivo não encontrado.', 'error')
        return redirect(url_for('masterizacao'))

@app.route('/audio/original/<session_id>')
@login_required_custom
def audio_original(session_id):
    file_path = os.path.join('uploads', f"{session_id}_target.wav")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='audio/wav')
    else:
        return jsonify({'error': 'Arquivo não encontrado'})

@app.route('/audio/mastered/<session_id>')
@login_required_custom
def audio_mastered(session_id):
    file_path = os.path.join('uploads', f"mastered_{session_id}.wav")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='audio/wav')
    else:
        return jsonify({'error': 'Arquivo não encontrado'})

@app.route('/enviar_contato', methods=['POST'])
@login_required_custom
def enviar_contato():
    nome = request.form.get('nome')
    email = request.form.get('email')
    mensagem = request.form.get('mensagem')
    flash('Mensagem enviada com sucesso! Entraremos em contato em breve.', 'success')
    return redirect(url_for('servicos'))

def generate_beautiful_waveform(audio_data, sample_rate, title, session_id, filename_suffix):
    """
    Gera um waveform bonito e profissional como no FL Studio (música completa otimizada)
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    
    # Configurar estilo do matplotlib para visualização profissional
    plt.style.use('dark_background')
    
    # Calcular dados para o waveform - MÚSICA COMPLETA
    duration = len(audio_data) / sample_rate
    
    # Otimização para músicas longas - limitar pontos para evitar erro de cell block
    max_points = 50000  # Limite seguro para matplotlib
    if len(audio_data) > max_points:
        # Decimar o áudio para músicas muito longas
        decimation_factor = len(audio_data) // max_points
        audio_trimmed = audio_data[::decimation_factor]
        time_trimmed = np.linspace(0, duration, len(audio_trimmed))
    else:
        # Usar áudio completo para músicas curtas
        audio_trimmed = audio_data
        time_trimmed = np.linspace(0, duration, len(audio_data))
    
    # Normalizar o áudio para melhor visualização
    audio_normalized = audio_trimmed / np.max(np.abs(audio_trimmed)) if np.max(np.abs(audio_trimmed)) > 0 else audio_trimmed
    
    # Criar figura com fundo escuro
    fig, ax = plt.subplots(figsize=(16, 6), facecolor='#0a0a0a')
    ax.set_facecolor('#0a0a0a')
    
    # Plotar o waveform principal com cor gradiente
    ax.plot(time_trimmed, audio_normalized, 
            color='#00d4ff', linewidth=1.0, alpha=0.9)
    
    # Adicionar envelope de amplitude
    envelope = np.abs(audio_normalized)
    ax.fill_between(time_trimmed, -envelope, envelope, 
                   alpha=0.15, color='#00d4ff', linewidth=0)
    
    # Adicionar linha central
    ax.axhline(y=0, color='#ffffff', alpha=0.3, linewidth=0.5)
    
    # Configurar eixos
    ax.set_xlim(0, duration)
    ax.set_ylim(-1.1, 1.1)
    
    # Estilo dos eixos
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#444444')
    ax.spines['bottom'].set_color('#444444')
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)
    
    # Grade sutil
    ax.grid(True, alpha=0.1, color='#444444', linewidth=0.3)
    
    # Labels dos eixos
    ax.set_xlabel('Tempo (segundos)', color='#ffffff', fontsize=9, fontweight='500')
    ax.set_ylabel('Amplitude', color='#ffffff', fontsize=9, fontweight='500')
    
    # Título
    ax.set_title(title, color='#00d4ff', fontsize=14, fontweight='bold', 
                pad=15, fontfamily='Arial')
    
    # Ticks dos eixos
    ax.tick_params(axis='both', colors='#888888', labelsize=8)
    
    # Informações técnicas com duração completa
    if len(audio_data) > max_points:
        info_text = f'SR: {sample_rate}Hz | Duração: {duration:.1f}s | Otimizado para visualização'
    else:
        info_text = f'SR: {sample_rate}Hz | Duração: {duration:.1f}s | Música Completa'
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
            fontsize=7, color='#888888', 
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a1a', alpha=0.7))
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar com resolução otimizada (150 DPI em vez de 300)
    waveform_filename = f"{filename_suffix}_{session_id}.png"
    waveform_path = os.path.join('static', 'results', waveform_filename)
    plt.savefig(waveform_path, dpi=150, bbox_inches='tight', 
                facecolor='#0a0a0a', edgecolor='none')
    plt.close()
    
    return waveform_filename, waveform_path

def generate_fast_waveform(audio_data, sample_rate, title, session_id, filename_suffix):
    """
    Gera um waveform otimizado para velocidade (música completa otimizada)
    """
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Configurar estilo básico
    plt.style.use('default')
    
    # Calcular dados para o waveform - MÚSICA COMPLETA
    duration = len(audio_data) / sample_rate
    
    # Otimização para músicas longas - limitar pontos para evitar erro de cell block
    max_points = 30000  # Limite mais baixo para velocidade
    if len(audio_data) > max_points:
        # Decimar o áudio para músicas muito longas
        decimation_factor = len(audio_data) // max_points
        audio_trimmed = audio_data[::decimation_factor]
        time_trimmed = np.linspace(0, duration, len(audio_trimmed))
    else:
        # Usar áudio completo para músicas curtas
        audio_trimmed = audio_data
        time_trimmed = np.linspace(0, duration, len(audio_data))
    
    # Normalizar o áudio
    audio_normalized = audio_trimmed / np.max(np.abs(audio_trimmed)) if np.max(np.abs(audio_trimmed)) > 0 else audio_trimmed
    
    # Criar figura simples
    fig, ax = plt.subplots(figsize=(14, 5), facecolor='#0a0a0a')
    ax.set_facecolor('#0a0a0a')
    
    # Plotar o waveform principal
    ax.plot(time_trimmed, audio_normalized, 
            color='#00d4ff', linewidth=1.0, alpha=0.8)
    
    # Adicionar envelope simples
    envelope = np.abs(audio_normalized)
    ax.fill_between(time_trimmed, -envelope, envelope, 
                   alpha=0.1, color='#00d4ff', linewidth=0)
    
    # Linha central
    ax.axhline(y=0, color='#ffffff', alpha=0.2, linewidth=0.5)
    
    # Configurar eixos
    ax.set_xlim(0, duration)
    ax.set_ylim(-1.0, 1.0)
    
    # Estilo básico dos eixos
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#444444')
    ax.spines['bottom'].set_color('#444444')
    
    # Grade simples
    ax.grid(True, alpha=0.1, color='#444444', linewidth=0.2)
    
    # Labels básicos
    ax.set_xlabel('Tempo (s)', color='#ffffff', fontsize=8)
    ax.set_ylabel('Amplitude', color='#ffffff', fontsize=8)
    
    # Título simples
    ax.set_title(title, color='#00d4ff', fontsize=12, fontweight='bold')
    
    # Ticks
    ax.tick_params(axis='both', colors='#888888', labelsize=7)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar com resolução baixa para máxima velocidade
    waveform_filename = f"{filename_suffix}_{session_id}.png"
    waveform_path = os.path.join('static', 'results', waveform_filename)
    plt.savefig(waveform_path, dpi=100, bbox_inches='tight', 
                facecolor='#0a0a0a', edgecolor='none')
    plt.close()
    
    return waveform_filename, waveform_path

def apply_professional_mastering(audio_data, sample_rate, params):
    """
    Aplica masterização profissional com parâmetros otimizados para som limpo
    """
    from pedalboard import Pedalboard, Compressor, Gain, Limiter
    
    # Parâmetros otimizados para masterização limpa e profissional
    compressor_threshold = float(params.get('compressor_threshold', -24))
    compressor_ratio = float(params.get('compressor_ratio', 1.8))
    gain_db = float(params.get('gain_db', 1.2))
    limiter_threshold = float(params.get('limiter_threshold', -0.8))
    
    try:
        # Tentar usar filtros se disponíveis
        from pedalboard import HighpassFilter, LowpassFilter
        
        board = Pedalboard([
            # High-pass filter mais alto para remover ruídos de baixa frequência
            HighpassFilter(cutoff_frequency_hz=30),
            
            # Compressor mais suave para preservar dinâmica natural
            Compressor(
                threshold_db=compressor_threshold,
                ratio=compressor_ratio,
                attack_ms=15,  # Ataque mais lento para preservar transientes
                release_ms=200  # Release mais longo para naturalidade
            ),
            
            # Gain mais baixo para evitar distorção
            Gain(gain_db=gain_db),
            
            # Low-pass filter mais baixo para reduzir chiado
            LowpassFilter(cutoff_frequency_hz=18000),
            
            # Limiter mais suave para evitar clipping
            Limiter(
                threshold_db=limiter_threshold,
                release_ms=100  # Release mais longo para suavidade
            )
        ])
    except ImportError:
        # Fallback para versão básica se filtros não estiverem disponíveis
        board = Pedalboard([
            # Compressor mais suave para preservar dinâmica natural
            Compressor(
                threshold_db=compressor_threshold,
                ratio=compressor_ratio,
                attack_ms=15,  # Ataque mais lento para preservar transientes
                release_ms=200  # Release mais longo para naturalidade
            ),
            
            # Gain mais baixo para evitar distorção
            Gain(gain_db=gain_db),
            
            # Limiter mais suave para evitar clipping
            Limiter(
                threshold_db=limiter_threshold,
                release_ms=100  # Release mais longo para suavidade
            )
        ])
    
    # Aplicar masterização
    mastered_audio = board(audio_data, sample_rate)
    
    # Normalização mais suave para preservar dinâmica
    max_amplitude = np.max(np.abs(mastered_audio))
    if max_amplitude > 0.98:
        normalization_factor = 0.98 / max_amplitude
        mastered_audio = mastered_audio * normalization_factor
    
    return mastered_audio

def apply_basic_mastering(audio_data, sample_rate):
    """
    Aplica masterização básica com parâmetros seguros
    """
    from pedalboard import Pedalboard, Compressor, Gain, Limiter
    
    # Parâmetros seguros para masterização básica
    board = Pedalboard([
        # Compressor suave para controlar picos
        Compressor(
            threshold_db=-16,  # Menos agressivo
            ratio=2.0,         # Ratio mais suave
            attack_ms=10,      # Ataque mais lento
            release_ms=150     # Release mais longo
        ),
        
        # Gain moderado
        Gain(gain_db=1.5),
        
        # Limiter com threshold mais alto
        Limiter(
            threshold_db=-0.3,
            release_ms=100
        )
    ])
    
    # Aplicar masterização
    mastered_audio = board(audio_data, sample_rate)
    
    # Normalizar suavemente
    max_amplitude = np.max(np.abs(mastered_audio))
    if max_amplitude > 0.98:
        normalization_factor = 0.98 / max_amplitude
        mastered_audio = mastered_audio * normalization_factor
    
    return mastered_audio

def cleanup_missing_files():
    """
    Remove registros de arquivos que não existem mais na pasta uploads
    """
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verificar se as tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        # Limpar mastered_songs
        if 'mastered_songs' in existing_tables:
            cursor.execute('SELECT id, original_filename, mastered_filename FROM mastered_songs')
            songs = cursor.fetchall()
            
            for song_id, original_file, mastered_file in songs:
                original_exists = os.path.exists(os.path.join('uploads', original_file)) if original_file else False
                mastered_exists = os.path.exists(os.path.join('uploads', mastered_file)) if mastered_file else False
                
                # Se nenhum dos arquivos existe, remover o registro
                if not original_exists and not mastered_exists:
                    cursor.execute('DELETE FROM mastered_songs WHERE id = ?', (song_id,))
                    print(f"Removido registro de música masterizada: {song_id}")
        
        # Limpar downloads
        if 'downloads' in existing_tables:
            cursor.execute('SELECT id, filename FROM downloads')
            downloads = cursor.fetchall()
            
            for download_id, filename in downloads:
                if filename and not os.path.exists(os.path.join('uploads', filename)):
                    cursor.execute('DELETE FROM downloads WHERE id = ?', (download_id,))
                    print(f"Removido registro de download: {download_id}")
        
        conn.commit()
        conn.close()
        print("Limpeza de arquivos ausentes concluída")
        
    except Exception as e:
        print(f"Erro ao limpar arquivos ausentes: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    try:
        print("Iniciando aplicação...")
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('static/results', exist_ok=True)
        print("Diretórios criados/verificados")
        
        init_db()
        print("Aplicação pronta para execução!")
        app.run(debug=True, host='0.0.0.0', port=5002)
    except Exception as e:
        import traceback
        print(f"Erro ao iniciar aplicação: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
