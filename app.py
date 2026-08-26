from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Importar las rutas (blueprints)
from routes.leer_ine import leer_ine_bp
from routes.verificar_rostro import verificar_rostro_bp
from routes.lector_examenes import lector_examenes_bp
from routes.verificar_rostro_examen import verificar_rostro_examen_bp

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
app = Flask(__name__)

# Habilitar CORS para que el frontend de React (Vercel) pueda comunicarse sin bloqueos
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Registrar los Blueprints
app.register_blueprint(leer_ine_bp)
app.register_blueprint(verificar_rostro_bp)
app.register_blueprint(lector_examenes_bp)
app.register_blueprint(verificar_rostro_examen_bp)

@app.route('/')
def home():
    return "Centinela IA Backend en línea", 200

if __name__ == "__main__":
    # Gunicorn usará 'app' directamente, esto es solo para pruebas locales
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
