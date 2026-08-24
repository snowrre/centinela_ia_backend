import os
import json
from flask import Blueprint, request, jsonify
from google.cloud import vision
from google.oauth2 import service_account

leer_ine_bp = Blueprint('leer_ine', __name__)

def obtener_cliente_vision():
    credenciales_texto = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not credenciales_texto:
        raise ValueError("Falta la llave de Google Vision")
    
    credenciales_dict = json.loads(credenciales_texto)
    credenciales = service_account.Credentials.from_service_account_info(credenciales_dict)
    return vision.ImageAnnotatorClient(credentials=credenciales)

def extraer_datos_ine(texto_completo):
    lineas = texto_completo.split('\n')
    for i, linea in enumerate(lineas):
        if "NOMBRE" in linea.upper():
            try:
                paterno = lineas[i+1].strip()
                materno = lineas[i+2].strip()
                nombres = lineas[i+3].strip()
                
                if "DOMICILIO" in nombres.upper():
                    return f"{materno} {paterno}".strip()
                
                return f"{nombres} {paterno} {materno}".strip()
            except IndexError:
                pass
    return "No detectado"

@leer_ine_bp.route('/api/leer_ine', methods=['POST'])
def leer_ine():
    try:
        if 'foto' not in request.files:
            return jsonify({"error": "Falta la foto"}), 400
            
        foto = request.files['foto']
        
        content = foto.read()
        client = obtener_cliente_vision()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            return jsonify({"error": f"Error de Vision: {response.error.message}"}), 500
            
        textos = response.text_annotations
        if not textos:
            return jsonify({"error": "No se detectó texto en la INE"}), 400
            
        texto_crudo = textos[0].description
        nombre_extraido = extraer_datos_ine(texto_crudo)
        
        return jsonify({
            "mensaje": "INE procesada con éxito",
            "nombre": nombre_extraido
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
