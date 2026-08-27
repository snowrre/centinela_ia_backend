import os
import boto3
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# El nombre del álbum en AWS.
# Si quieres resetear la base biométrica, cambia el nombre aquí (ej. 'centinela_v2').
COLECCION_ID = 'centinela_alumnos_v1'

rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-2')
)

biometria_duplicados_bp = Blueprint('biometria_duplicados', __name__)


# =======================================================
# 1. INICIALIZAR EL ÁLBUM (Ruta de configuración, llamar UNA SOLA VEZ)
# =======================================================
@biometria_duplicados_bp.route('/api/setup_coleccion', methods=['GET'])
def crear_coleccion():
    try:
        rekognition.create_collection(CollectionId=COLECCION_ID)
        return jsonify({"mensaje": f"Colección '{COLECCION_ID}' creada en AWS."})
    except rekognition.exceptions.ResourceAlreadyExistsException:
        return jsonify({"mensaje": "La colección ya existía, lista para usarse."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =======================================================
# 2. EL CANDADO: VERIFICAR SI EL ROSTRO YA EXISTE EN AWS
# =======================================================
@biometria_duplicados_bp.route('/api/verificar_duplicado_biometrico', methods=['POST'])
def verificar_duplicado_biometrico():
    """
    Recibe una foto y busca si ese rostro ya está indexado en la colección.
    Devuelve: { "duplicado": true/false, "mensaje": "..." }
    """
    if 'foto' not in request.files:
        return jsonify({"error": "No se envió foto"}), 400

    image_bytes = request.files['foto'].read()

    try:
        response = rekognition.search_faces_by_image(
            CollectionId=COLECCION_ID,
            Image={'Bytes': image_bytes},
            FaceMatchThreshold=80.0,  # Bajado de 95% a 80% para mayor agresividad
            MaxFaces=1
        )

        if len(response['FaceMatches']) > 0:
            # Rostro encontrado → Bloquear registro
            matricula_original = response['FaceMatches'][0]['Face']['ExternalImageId']
            similitud = response['FaceMatches'][0]['Similarity']
            print(f"[CandadoBiométrico] ⛔ Rostro duplicado detectado. Matrícula original: {matricula_original} ({similitud:.1f}%)")
            return jsonify({
                "duplicado": True,
                "mensaje": f"Este rostro ya está registrado con la matrícula {matricula_original}. Contacta a tu administrador si crees que es un error."
            })

        # Rostro limpio → Permitir continuar
        return jsonify({"duplicado": False})

    except rekognition.exceptions.InvalidParameterException:
        # Foto sin rostros o muy borrosa → dejamos pasar, la biometría de selfie lo filtrará
        return jsonify({"duplicado": False, "nota": "No se detectó rostro en la imagen"})
    except Exception as e:
        # Si la colección está vacía o hay error no crítico, dejamos pasar
        print(f"[CandadoBiométrico] Advertencia: {e}")
        return jsonify({"duplicado": False})


# =======================================================
# 3. SELLAR EL ROSTRO: INDEXAR EN AWS DESPUÉS DEL REGISTRO
# =======================================================
@biometria_duplicados_bp.route('/api/guardar_rostro_biometrico', methods=['POST'])
def guardar_rostro_biometrico():
    """
    Indexa la foto de registro del alumno en la colección AWS,
    etiquetada con su matrícula para identificarla si hay duplicados futuros.
    """
    if 'foto' not in request.files or 'matricula' not in request.form:
        return jsonify({"error": "Faltan datos: 'foto' y 'matricula' son requeridos"}), 400

    image_bytes = request.files['foto'].read()
    matricula = request.form['matricula'].strip()

    try:
        rekognition.index_faces(
            CollectionId=COLECCION_ID,
            Image={'Bytes': image_bytes},
            ExternalImageId=str(matricula),  # La matrícula es la etiqueta del rostro
            MaxFaces=1,
            DetectionAttributes=['DEFAULT']  # CORREGIDO: 'NONE' ya no es válido en la API actual
        )
        print(f"[CandadoBiométrico] ✅ Rostro de '{matricula}' sellado en AWS.")
        return jsonify({"exito": True, "mensaje": f"Rostro de {matricula} registrado exitosamente."})
    except Exception as e:
        print(f"[CandadoBiométrico] Error al indexar rostro: {e}")
        return jsonify({"error": str(e)}), 500


# =======================================================
# 4. MONITOR UNIVERSAL: CELULARES + SUPLANTACIÓN (2 en 1)
# =======================================================
@biometria_duplicados_bp.route('/api/monitoreo_continuo', methods=['POST'])
def monitoreo_continuo():
    """
    Recibe una foto + matrícula del alumno en examen.
    Devuelve en un solo viaje: is_phone, es_el_alumno, razon.
    """
    if 'foto' not in request.files or 'matricula' not in request.form:
        return jsonify({"error": "Faltan datos"}), 400

    image_bytes = request.files['foto'].read()
    matricula_esperada = request.form['matricula'].strip()

    reporte = {
        "is_phone": False,
        "es_el_alumno": False,
        "razon": ""
    }

    try:
        # TAREA A: Detectar celulares
        res_labels = rekognition.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=15,
            MinConfidence=80.0
        )
        for label in res_labels['Labels']:
            if label['Name'] in ['Cell Phone', 'Mobile Phone', 'Smartphone', 'Telephone']:
                reporte["is_phone"] = True
                print(f"[Monitor] 📱 Celular detectado: {label['Name']} ({label['Confidence']:.1f}%)")
                break

        # TAREA B: Verificar que el rostro pertenece al alumno registrado
        res_faces = rekognition.search_faces_by_image(
            CollectionId=COLECCION_ID,
            Image={'Bytes': image_bytes},
            FaceMatchThreshold=80.0,
            MaxFaces=1
        )

        if len(res_faces['FaceMatches']) > 0:
            matricula_detectada = res_faces['FaceMatches'][0]['Face']['ExternalImageId']
            similitud = res_faces['FaceMatches'][0]['Similarity']
            if matricula_detectada == matricula_esperada:
                reporte["es_el_alumno"] = True
                print(f"[Monitor] ✅ Alumno verificado: {matricula_detectada} ({similitud:.1f}%)")
            else:
                reporte["razon"] = f"SUPLANTACIÓN: Rostro de '{matricula_detectada}' en lugar de '{matricula_esperada}'."
                print(f"[Monitor] 🚨 {reporte['razon']}")
        else:
            reporte["razon"] = "SUPLANTACIÓN: Rostro desconocido o no registrado."

        return jsonify(reporte)

    except rekognition.exceptions.InvalidParameterException:
        # Cámara tapada o sin rostro claro
        reporte["razon"] = "No se detecta rostro claro"
        return jsonify(reporte)
    except Exception as e:
        print(f"🔥 [Monitor] Error crítico: {str(e)}")
        return jsonify({"error": str(e)}), 400
