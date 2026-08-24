import os
import json
import tempfile
import google.generativeai as genai
from flask import Blueprint, request, jsonify

lector_examenes_bp = Blueprint('lector_examenes', __name__)

@lector_examenes_bp.route('/api/lector_examenes', methods=['POST'])
def procesar_pdf_a_json():
    archivo_ia = None
    ruta_tmp = None
    try:
        if 'examen_pdf' not in request.files:
            return jsonify({"error": "No se envió ningún archivo PDF."}), 400
            
        archivo_pdf = request.files['examen_pdf']
        
        fd, ruta_tmp = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        archivo_pdf.save(ruta_tmp)
        
        # Ojo: la llave se configuró en app.py, por lo que genai ya la tiene lista
        archivo_ia = genai.upload_file(ruta_tmp, mime_type="application/pdf")
        
        modelo = genai.GenerativeModel('gemini-1.5-pro')
        
        instrucciones = """
        Eres un analizador de exámenes. Lee este examen en PDF y devuelve un objeto JSON válido.
        Tu respuesta debe ser EXCLUSIVAMENTE el JSON, sin texto antes ni después (sin bloques markdown).
        
        Sigue estrictamente esta estructura:
        {
          "titulo_examen": "Nombre o tema del examen",
          "preguntas": [
            {
              "numero": 1,
              "tipo": "opcion_multiple", 
              "texto": "¿Cuál es la pregunta?",
              "opciones": ["Opción A", "Opción B", "Opción C"],
              "respuesta_correcta": "Aquí va la respuesta correcta o null si no se infiere"
            }
          ]
        }
        """
        
        respuesta = modelo.generate_content(
            [archivo_ia, instrucciones],
            generation_config={"response_mime_type": "application/json"}
        )
        
        examen_estructurado = json.loads(respuesta.text)
        return jsonify(examen_estructurado), 200

    except json.JSONDecodeError:
        return jsonify({"error": "Gemini no devolvió un JSON válido."}), 500
    except Exception as e:
        return jsonify({"error": "Error al procesar el examen", "detalle": str(e)}), 500
    finally:
        if archivo_ia:
            try:
                genai.delete_file(archivo_ia.name)
            except:
                pass
        if ruta_tmp and os.path.exists(ruta_tmp):
            os.remove(ruta_tmp)
