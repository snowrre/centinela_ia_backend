import os
import boto3
from flask import Blueprint, request, jsonify

verificar_rostro_bp = Blueprint('verificar_rostro', __name__)

@verificar_rostro_bp.route('/api/verificar_rostro', methods=['POST'])
def verificar_rostro():
    try:
        if 'foto_ine' not in request.files or 'foto_selfie' not in request.files:
            return jsonify({"error": "Faltan imágenes para la verificación"}), 400

        foto_ine    = request.files['foto_ine'].read()
        foto_selfie = request.files['foto_selfie'].read()

        rekognition = boto3.client(
            'rekognition',
            region_name=os.environ.get('AWS_REGION', 'us-east-2')
        )

        response = rekognition.compare_faces(
            SourceImage={'Bytes': foto_ine},
            TargetImage={'Bytes': foto_selfie},
            SimilarityThreshold=80.0
        )

        if len(response['FaceMatches']) > 0:
            similitud = response['FaceMatches'][0]['Similarity']
            return jsonify({
                "match":    True,
                "similitud": similitud,
                "mensaje":  "¡Identidad verificada con éxito!"
            }), 200
        else:
            return jsonify({
                "match":   False,
                "similitud": 0,
                "mensaje": "Los rostros no coinciden. Intenta de nuevo con mejor iluminación."
            }), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
