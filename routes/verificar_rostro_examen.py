import os
import boto3
import requests
from flask import Blueprint, request, jsonify

verificar_rostro_examen_bp = Blueprint('verificar_rostro_examen', __name__)

@verificar_rostro_examen_bp.route('/api/verificar_rostro_examen', methods=['POST'])
def verificar_rostro_examen():
    try:
        foto_registro_url = request.form.get('foto_registro_url')
        if not foto_registro_url:
            return jsonify({"error": "Falta la URL de la foto maestra"}), 400

        if 'foto_actual' not in request.files:
            return jsonify({"error": "Falta la foto actual de la cámara"}), 400

        # Descargar la foto maestra desde Supabase Storage
        response_master = requests.get(foto_registro_url)
        if response_master.status_code != 200:
            return jsonify({"error": "No se pudo descargar la foto maestra de Supabase"}), 500
        foto_maestra_bytes = response_master.content

        foto_actual_bytes = request.files['foto_actual'].read()

        rekognition = boto3.client(
            'rekognition',
            region_name=os.environ.get('AWS_REGION', 'us-east-2')
        )

        response = rekognition.compare_faces(
            SourceImage={'Bytes': foto_maestra_bytes},
            TargetImage={'Bytes': foto_actual_bytes},
            SimilarityThreshold=80.0
        )

        if len(response['FaceMatches']) > 0:
            similitud = response['FaceMatches'][0]['Similarity']
            return jsonify({
                "match": True,
                "similitud": similitud,
                "mensaje": "¡Identidad verificada con éxito para el examen!"
            }), 200
        else:
            return jsonify({
                "match": False,
                "similitud": 0,
                "mensaje": "Los rostros no coinciden. Intenta de nuevo con mejor iluminación."
            }), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
