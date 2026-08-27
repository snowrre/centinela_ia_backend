import os
from flask import Blueprint, request, jsonify
import boto3
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar el cliente de AWS Rekognition
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-2')
)

# Crear el Blueprint (módulo de Flask)
detectar_objetos_bp = Blueprint('detectar_objetos', __name__)

@detectar_objetos_bp.route('/api/detectar_objetos', methods=['POST'])
def detectar_celular():
    # 1. Validar que llegó la foto
    if 'foto_actual' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['foto_actual']
    image_bytes = file.read() # Leer la imagen en binario

    try:
        # 2. Llamada al Francotirador de AWS Rekognition (DetectLabels)
        # MinConfidence=65.0: Un punto de equilibrio perfecto para no alucinar
        response = rekognition.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=15,
            MinConfidence=65.0
        )

        is_phone = False
        nombre_etiqueta = ""

        # 3. Analizar la respuesta JSON de AWS
        for label in response['Labels']:
            # Buscamos estas palabras clave en las etiquetas devueltas por AWS
            if label['Name'] in ['Cell Phone', 'Mobile Phone', 'Electronics', 'Smart Phone', 'Phone']:
                is_phone = True
                nombre_etiqueta = label['Name'] # Guardamos cuál detectó
                print(f"--- ¡AWS REKOGNITION DETECTÓ UN TELÉFONO! ({label['Name']} con {label['Confidence']:.2f}% de confianza) ---")
                break # En cuanto detecte uno, detenemos la búsqueda

        # 4. Regresar el veredicto al Frontend
        return jsonify({
            "is_phone": is_phone,
            "etiqueta_detectada": nombre_etiqueta if is_phone else None
        })

    except Exception as e:
        print(f"Error AWS Rekognition: {e}")
        return jsonify({"error": str(e)}), 500
