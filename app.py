# app.py
from flask import Flask, render_template, request, send_file, Response, stream_with_context
import yt_dlp
import requests
import os
from urllib.parse import quote

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

class MusicPlayer:
    def __init__(self):
        self.current_url = None
        self.current_title = None

player = MusicPlayer()

def get_audio_stream(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        player.current_title = info.get('title', 'Unknown Title')
        return info['url']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url')
    if not url:
        return {'error': 'No URL provided'}, 400
    
    try:
        audio_url = get_audio_stream(url)
        player.current_url = url
        return {'audio_url': f'/stream_audio?url={quote(audio_url)}', 'title': player.current_title}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/stream_audio')
def stream_audio():
    audio_url = request.args.get('url')
    
    def generate():
        with requests.get(audio_url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk
                
    return Response(stream_with_context(generate()), content_type='audio/mpeg')

@app.route('/download')
def download():
    if not player.current_url:
        return {'error': 'No audio to download'}, 400
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(player.current_url, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
