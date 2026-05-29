from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
import sqlite3
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurar OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('contenido.db')
    c = conn.cursor()
    
    # Tabla de consultas
    c.execute('''CREATE TABLE IF NOT EXISTS consultas
                 (id INTEGER PRIMARY KEY,
                  tema TEXT,
                  respuesta TEXT,
                  fecha TIMESTAMP)''')
    
    # Tabla de datos de videos (datos de ejemplo)
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                 (id INTEGER PRIMARY KEY,
                  titulo TEXT,
                  creador TEXT,
                  tema TEXT,
                  duracion_minutos INTEGER,
                  edad_promedio INTEGER,
                  mejor_hora_subida TEXT,
                  plataforma TEXT,
                  visualizaciones INTEGER)''')
    
    # Tabla de creadores destacados
    c.execute('''CREATE TABLE IF NOT EXISTS creadores
                 (id INTEGER PRIMARY KEY,
                  nombre TEXT,
                  tema TEXT,
                  plataforma TEXT,
                  seguidores INTEGER,
                  rating REAL)''')
    
    conn.commit()
    conn.close()

# Insertar datos de ejemplo en la base de datos
def insert_sample_data():
    conn = sqlite3.connect('contenido.db')
    c = conn.cursor()
    
    # Verificar si ya existen datos
    c.execute('SELECT COUNT(*) FROM videos')
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    # Videos de ejemplo - Minecraft
    videos_minecraft = [
        ('Minecraft Survival en Dificultad Hardcore', 'ElRichMC', 'Minecraft', 25, 18, '19:00', 'YouTube', 500000),
        ('Building Castillo Épico en Minecraft', 'Willyrex', 'Minecraft', 30, 15, '18:00', 'YouTube', 450000),
        ('Minecraft Challenges Divertidos', 'Vegetta777', 'Minecraft', 28, 16, '20:00', 'YouTube', 520000),
        ('TikTok Minecraft Builds Rápidos', 'MinecraftBuilder', 'Minecraft', 1, 14, '17:00', 'TikTok', 200000),
    ]
    
    # Videos de ejemplo - Ropa
    videos_ropa = [
        ('HAUL de Ropa de Moda 2024', 'ChicaFashion', 'Ropa', 15, 22, '18:00', 'YouTube', 300000),
        ('Outfits para Cada Ocasión', 'EstiloYTendencia', 'Ropa', 20, 21, '19:00', 'YouTube', 280000),
        ('OOTD - Outfit del Día', 'FashionAddict', 'Ropa', 3, 20, '16:00', 'TikTok', 150000),
        ('Ropa de Verano 2024', 'ModaChic', 'Ropa', 18, 23, '17:00', 'YouTube', 320000),
    ]
    
    # Videos de ejemplo - Maquillaje
    videos_maquillaje = [
        ('Maquillaje Natural Paso a Paso', 'MaquillajePro', 'Maquillaje', 25, 24, '18:00', 'YouTube', 400000),
        ('Makeup Tutorial Fiesta', 'BeautyQueen', 'Maquillaje', 22, 25, '19:00', 'YouTube', 380000),
        ('Maquillaje Rápido para el Trabajo', 'BeautyTips', 'Maquillaje', 5, 26, '17:00', 'TikTok', 180000),
        ('Contouring Avanzado', 'MakeupArtist', 'Maquillaje', 20, 23, '20:00', 'YouTube', 420000),
    ]
    
    for video in videos_minecraft + videos_ropa + videos_maquillaje:
        c.execute('''INSERT INTO videos 
                     (titulo, creador, tema, duracion_minutos, edad_promedio, mejor_hora_subida, plataforma, visualizaciones)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', video)
    
    # Creadores destacados
    creadores = [
        ('ElRichMC', 'Minecraft', 'YouTube', 5000000, 4.8),
        ('Willyrex', 'Minecraft', 'YouTube', 4500000, 4.7),
        ('ChicaFashion', 'Ropa', 'YouTube', 2000000, 4.6),
        ('MaquillajePro', 'Maquillaje', 'YouTube', 1800000, 4.9),
        ('BeautyQueen', 'Maquillaje', 'YouTube', 1600000, 4.7),
    ]
    
    for creador in creadores:
        c.execute('''INSERT INTO creadores 
                     (nombre, tema, plataforma, seguidores, rating)
                     VALUES (?, ?, ?, ?, ?)''', creador)
    
    conn.commit()
    conn.close()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Mensaje vacío'}), 400
    
    try:
        # Obtener datos de la base de datos relevantes al tema
        tema = extract_topic(user_message)
        db_info = get_db_info(tema)
        
        # Crear prompt con contexto de la base de datos
        system_prompt = f"""Eres un asistente de IA especializado en análisis de contenido para creadores.
        Tienes acceso a una base de datos con información sobre videos, creadores y tendencias.
        
        Información disponible sobre '{tema}':
        {db_info}
        
        Proporciona análisis detallado sobre:
        1. La mejor hora para subir el vídeo
        2. El promedio de edad de los espectadores
        3. La duración promedio de los mejores vídeos
        4. Los creadores de contenido destacados
        5. Ideas para contenido a futuro
        
        Sé específico, usa los datos disponibles y proporciona recomendaciones prácticas."""
        
        # Llamar a OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message['content']
        
        # Guardar consulta en base de datos
        save_query(user_message, assistant_message, tema)
        
        return jsonify({
            'response': assistant_message,
            'topic': tema,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_topic(message):
    """Extrae el tema de la consulta del usuario"""
    message_lower = message.lower()
    
    if 'minecraft' in message_lower:
        return 'Minecraft'
    elif 'ropa' in message_lower or 'fashion' in message_lower or 'moda' in message_lower:
        return 'Ropa'
    elif 'maquillaje' in message_lower or 'makeup' in message_lower or 'beauty' in message_lower:
        return 'Maquillaje'
    else:
        return 'General'

def get_db_info(tema):
    """Obtiene información de la base de datos sobre un tema"""
    conn = sqlite3.connect('contenido.db')
    c = conn.cursor()
    
    # Obtener información de videos
    c.execute('SELECT * FROM videos WHERE tema = ?', (tema,))
    videos = c.fetchall()
    
    # Obtener creadores destacados
    c.execute('SELECT * FROM creadores WHERE tema = ?', (tema,))
    creadores = c.fetchall()
    
    conn.close()
    
    info = f"Videos encontrados sobre {tema}: {len(videos)}\n"
    
    if videos:
        duraciones = [v[4] for v in videos]
        edades = [v[5] for v in videos]
        info += f"- Duración promedio: {sum(duraciones)/len(duraciones):.1f} minutos\n"
        info += f"- Edad promedio de espectadores: {sum(edades)/len(edades):.1f} años\n"
    
    if creadores:
        info += f"\nCreadores destacados:\n"
        for creador in creadores:
            info += f"- {creador[1]}: {creador[4]:,} seguidores (Rating: {creador[5]}/5)\n"
    
    return info

def save_query(user_message, response, tema):
    """Guarda la consulta en la base de datos"""
    conn = sqlite3.connect('contenido.db')
    c = conn.cursor()
    c.execute('''INSERT INTO consultas (tema, respuesta, fecha)
                 VALUES (?, ?, ?)''', (tema, response, datetime.now()))
    conn.commit()
    conn.close()

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """Obtiene los temas disponibles"""
    conn = sqlite3.connect('contenido.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT tema FROM videos')
    topics = [row[0] for row in c.fetchall()]
    conn.close()
    
    return jsonify({'topics': topics})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Obtiene el historial de consultas"""
    conn = sqlite3.connect('contenido.db')
    c = conn.cursor()
    c.execute('SELECT tema, respuesta, fecha FROM consultas ORDER BY fecha DESC LIMIT 10')
    history = [{'topic': row[0], 'response': row[1], 'date': row[2]} for row in c.fetchall()]
    conn.close()
    
    return jsonify({'history': history})

if __name__ == '__main__':
    init_db()
    insert_sample_data()
    app.run(debug=True, port=5000)
