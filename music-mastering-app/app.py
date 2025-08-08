from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import os
import librosa
import soundfile as sf
import numpy as np
import base64
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pedalboard import Pedalboard, Compressor, Limiter, Gain
from werkzeug.utils import secure_filename
import yt_dlp
import re
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta_aqui')

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_youtube_url(url):
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    ]
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def download_youtube_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{output_path}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return f"{output_path}.wav" # Retorna o caminho completo do arquivo .wav
    except Exception as e:
        print(f"Erro ao baixar do YouTube: {e}")
        return None

def create_waveform_plot(audio, sr, title):
    plt.figure(figsize=(12, 4))
    time = np.linspace(0, len(audio) / sr, len(audio))
    plt.plot(time, audio, color='#00ff88', linewidth=0.5, alpha=0.8)
    plt.fill_between(time, audio, 0, color='#00ff88', alpha=0.3)
    plt.fill_between(time, audio, 0, where=(audio < 0), color='#ff4444', alpha=0.3)
    plt.xlabel('Tempo (segundos)')
    plt.ylabel('Amplitude')
    plt.title(title, color='white', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, color='#666666')
    plt.axhline(y=0, color='#ffffff', linestyle='-', alpha=0.5)
    plt.ylim(-1, 1)
    plt.gca().set_facecolor('#1a1a1a')
    plt.gcf().set_facecolor('#1a1a1a')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_color('#ffffff')
    plt.gca().spines['bottom'].set_color('#ffffff')
    plt.gca().tick_params(colors='#ffffff')
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=100, facecolor='#1a1a1a')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def masterize_audio_with_params(target_audio, target_sr, params):
    plugins = []
    if params.get('use_compressor', True):
        plugins.append(Compressor(
            threshold_db=params.get('compressor_threshold', -25.0),
            ratio=params.get('compressor_ratio', 1.5),
            attack_ms=params.get('compressor_attack', 20.0),
            release_ms=params.get('compressor_release', 150.0)
        ))
    if params.get('gain_db', 0) != 0:
        plugins.append(Gain(gain_db=params.get('gain_db', 0)))
    if params.get('use_limiter', True):
        plugins.append(Limiter(
            threshold_db=params.get('limiter_threshold', -0.5),
            release_ms=params.get('limiter_release', 100.0)
        ))
    if plugins:
        board = Pedalboard(plugins)
        return board.process(target_audio.reshape(1, -1), target_sr).flatten()
    return target_audio

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'target_file' not in request.files:
            return jsonify({'success': False, 'error': 'Arquivo para masterizar não encontrado.'})

        target_file = request.files['target_file']
        reference_input = request.form.get('reference_input', '').strip()
        reference_file = request.files.get('reference_file')

        if target_file.filename == '':
            return jsonify({'success': False, 'error': 'Selecione o arquivo para masterizar.'})
        if not allowed_file(target_file.filename):
            return jsonify({'success': False, 'error': 'Formato de arquivo inválido. Use WAV ou MP3.'})
        if not reference_input and not reference_file:
            return jsonify({'success': False, 'error': 'Forneça uma referência (arquivo ou URL).'})

        try:
            session_id = str(uuid.uuid4())
            target_filename = secure_filename(target_file.filename)
            target_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{target_filename}")
            target_file.save(target_path)
            
            reference_path = None
            if reference_file and reference_file.filename != '':
                ref_filename = secure_filename(reference_file.filename)
                reference_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{ref_filename}")
                reference_file.save(reference_path)
            elif is_youtube_url(reference_input):
                youtube_output_base = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_youtube_ref")
                reference_path = download_youtube_audio(reference_input, youtube_output_base)
                if not reference_path:
                    return jsonify({'success': False, 'error': 'Erro ao baixar áudio do YouTube.'})
            else:
                 return jsonify({'success': False, 'error': 'Referência inválida.'})

            target_audio, target_sr = librosa.load(target_path, sr=None, mono=True)
            reference_audio, reference_sr = librosa.load(reference_path, sr=None, mono=True)

            if target_sr != reference_sr:
                target_audio = librosa.resample(y=target_audio, orig_sr=target_sr, target_sr=reference_sr)
                target_sr = reference_sr

            reference_rms = np.sqrt(np.mean(reference_audio**2))
            target_rms = np.sqrt(np.mean(target_audio**2))
            if target_rms > 0:
                volume_adjustment = (reference_rms / target_rms) * 0.8
                target_audio *= volume_adjustment
            
            original_waveform = create_waveform_plot(target_audio, target_sr, "Waveform Original")

            params = {
                'use_compressor': True, 'compressor_threshold': -25.0, 'compressor_ratio': 1.5,
                'compressor_attack': 20.0, 'compressor_release': 150.0, 'gain_db': 1.0,
                'use_limiter': True, 'limiter_threshold': -0.5, 'limiter_release': 100.0
            }
            mastered_audio = masterize_audio_with_params(target_audio, target_sr, params)
            mastered_waveform = create_waveform_plot(mastered_audio, target_sr, "Waveform Masterizado")

            name_without_ext = os.path.splitext(target_filename)[0]
            output_filename = f"{name_without_ext}_MASTERIZADO_{session_id}.wav"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            sf.write(output_path, mastered_audio, target_sr)

            # Salvar previews com nomes únicos
            original_preview_path = os.path.join(app.config['UPLOAD_FOLDER'], f"original_preview_{session_id}.wav")
            mastered_preview_path = os.path.join(app.config['UPLOAD_FOLDER'], f"mastered_preview_{session_id}.wav")
            sf.write(original_preview_path, target_audio, target_sr)
            sf.write(mastered_preview_path, mastered_audio, target_sr)

            return jsonify({
                'success': True,
                'original_waveform': original_waveform,
                'mastered_waveform': mastered_waveform,
                'output_filename': output_filename,
                'params': params,
                'session_id': session_id,
                'target_path': target_path
            })
            
        except Exception as e:
            app.logger.error(f"Erro no processamento: {e}", exc_info=True)
            return jsonify({'success': False, 'error': f'Ocorreu um erro interno: {e}'})
    
    return render_template('index.html')

@app.route('/masterize', methods=['POST'])
def masterize():
    try:
        data = request.get_json()
        params = data.get('params', {})
        target_path = data.get('target_path')
        session_id = data.get('session_id')

        if not all([params, target_path, session_id]):
             return jsonify({'success': False, 'error': 'Dados incompletos.'})

        target_audio, target_sr = librosa.load(target_path, sr=None, mono=True)
        mastered_audio = masterize_audio_with_params(target_audio, target_sr, params)
        mastered_waveform = create_waveform_plot(mastered_audio, target_sr, "Waveform Masterizado")
        
        preview_path = os.path.join(app.config['UPLOAD_FOLDER'], f"mastered_preview_{session_id}.wav")
        sf.write(preview_path, mastered_audio, target_sr)

        name_without_ext = os.path.splitext(os.path.basename(target_path).split('_', 1)[1])[0]
        output_filename = f"{name_without_ext}_MASTERIZADO_{session_id}.wav"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        sf.write(output_path, mastered_audio, target_sr)
        
        return jsonify({
            'success': True,
            'mastered_waveform': mastered_waveform,
            'output_filename': output_filename
        })
        
    except Exception as e:
        app.logger.error(f"Erro na remasterização: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download(filename):
    try:
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(path, as_attachment=True)
    except Exception as e:
        flash(f'Erro ao baixar arquivo: {str(e)}')
        return redirect(url_for('index'))

@app.route('/audio/original/<session_id>')
def serve_original_audio(session_id):
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, f"original_preview_{session_id}.wav"), mimetype='audio/wav')
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/audio/mastered/<session_id>')
def serve_mastered_audio(session_id):
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, f"mastered_preview_{session_id}.wav"), mimetype='audio/wav')
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)