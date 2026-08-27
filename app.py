from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
import mercadopago
from flask import request, jsonify

# Importar las rutas (blueprints)
from routes.leer_ine import leer_ine_bp
from routes.verificar_rostro import verificar_rostro_bp
from routes.lector_examenes import lector_examenes_bp
from routes.verificar_rostro_examen import verificar_rostro_examen_bp
from routes.detectar_objetos import detectar_objetos_bp
from routes.biometria_duplicados import biometria_duplicados_bp

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
app.register_blueprint(detectar_objetos_bp)
app.register_blueprint(biometria_duplicados_bp)

# ── RUTA MERCADOPAGO ──────────────────────────────────────────
@app.route('/api/create-preference', methods=['POST'])
def create_preference():
    try:
        data = request.json
        plan = data.get('plan', 'departamental')
        
        # Precios según el plan
        price = 39999 if plan == 'campus' else 14999
        title = f"Licencia Centinela IA - {plan.capitalize()}"

        sdk = mercadopago.SDK(os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "TEST-4161746200257416-082622-44671e2ef63b4d4838b00ba7c2106e57-1961474241"))

        preference_data = {
            "items": [
                {
                    "title": title,
                    "quantity": 1,
                    "unit_price": float(price),
                    "currency_id": "MXN"
                }
            ],
            "back_urls": {
                "success": "https://centinela-ia-dashboard.vercel.app/success",
                "failure": "https://centinela-ia-dashboard.vercel.app/failure",
                "pending": "https://centinela-ia-dashboard.vercel.app/pending"
            },
            "auto_return": "approved"
        }
        
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            return jsonify({"id": preference_response["response"]["id"], "init_point": preference_response["response"]["init_point"]}), 200
        else:
            return jsonify({"error": "Error al crear preferencia", "details": preference_response}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Centinela IA Backend en línea", 200

if __name__ == "__main__":
    # Gunicorn usará 'app' directamente, esto es solo para pruebas locales
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
