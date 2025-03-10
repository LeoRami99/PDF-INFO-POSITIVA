from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
import base64
import re
import io
import requests
import os

# Configuración de la API y credenciales
AUTH_API_URL = "https://0fyl9sz8k3.execute-api.us-east-1.amazonaws.com/login/oauth/authenticate/v1"
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError("Las credenciales no están configuradas como variables de entorno")


app = Flask(__name__)

def get_token_auth():
    """
    Obtiene un nuevo token de acceso desde la API de autenticación.
    """
    try:
        response = requests.post(AUTH_API_URL, json={"username": USERNAME, "password": PASSWORD})
        response.raise_for_status()  
        token_data = response.json()
        access_token = token_data["data"]["AccessToken"]
        return access_token
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error al obtener el token: {e}")

def fetch_document_number_from_api(type_document, num_documento, form_type):
    """
    Realiza una solicitud a la API externa para validar el número de documento.
    """
    try:
        token = get_token_auth()  # Obtener un token válido

        types_form = ["FCC-STA", "FCC-SIM"]
        document_prefixes = [
            "CC", "NIT", "CE", "CN", "TI", "RC", "PA", "AS", "MS", 
            "CD", "PE", "SC", "DE", "SI", "PT", "NS"
        ]

        if type_document not in document_prefixes:
            raise ValueError("Tipo de documento no válido")
        
        if form_type not in types_form:
            raise ValueError("Tipo de formulario no válido")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"https://7ifsjev272.execute-api.us-east-1.amazonaws.com/fcc/validate-document/{type_document}/{num_documento}?form_type={form_type}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error al consultar la API externa: {e}")

def extract_pdf_text(file_bytes, password=None):
    """
    Extrae texto de un archivo PDF desde bytes.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            if password:
                reader.decrypt(password)
            else:
                raise ValueError("El archivo PDF está protegido y no se proporcionó una contraseña.")
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise ValueError(f"Error al procesar el PDF: {e}")

def parse_form_to_json(text):
    """
    Parsea el texto del formulario en un diccionario JSON estructurado.
    """
    form_data = {}

    # Función auxiliar para extraer información con regex
    def extract_field(pattern, text, default=None):
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else default

    # Función para limpiar texto adicional
    def clean_field(value):
        if value:
            return re.sub(r"\s+", " ", value).strip()
        return value

    

    # Función para limpiar campos específicos como "Pais" y "Ciudad"
    def clean_pais(value):
        if value:
            # Tomamos solo el primer término relevante (después de "País")
            value = re.search(r"nacimiento\s+(.+?)$", value, re.MULTILINE)
            if value:
                return value.group(1).strip()
        return "Colombia"  # Valor por defecto si no se encuentra un patrón válido

    def clean_ciudad(value):
        if value:
            # Filtramos cualquier contenido irrelevante
            value = re.search(r"residencia\s+(.+?)$", value, re.MULTILINE)
            if value:
                return value.group(1).strip()
        return "BOGOTÁ"  # Valor por defecto si no se encuentra un patrón válido

    # Datos del Riesgo
    form_data["Datos_del_Riesgo"] = {
        "Tipo_cliente_vinculacion": extract_field(r"Tipo cliente/vinculación\s+(.+?)\s+Tipo solicitud", text),
        "Tipo_solicitud": extract_field(r"Tipo solicitud\s+(.+?)\s+Canal", text),
        "Canal": extract_field(r"Canal\s+(.+?)\s+Sucursal", text),
        "Sucursal": extract_field(r"Sucursal\s+(.+?)\s+Ramo", text),
        "Ramo": extract_field(r"Ramo\s+(.+?)\s+Producto", text),
        "Producto": extract_field(r"Producto\s+(.+?)\s+No\. formulario", text),
        "Fecha_formulario": extract_field(r"Fecha formulario\s+(\d{4}-\d{2}-\d{2})", text),
    }

    # Información personal
    form_data["Informacion_Personal"] = {
        "Primer_nombre": clean_field(extract_field(r"Primer nombre\s+(.+?)\s+Segundo nombre", text)),
        "Segundo_nombre": clean_field(extract_field(r"Segundo nombre\s+(.+?)\s+Primer apellido", text)),
        "Primer_apellido": clean_field(extract_field(r"Primer apellido\s+(.+?)\s+Segundo apellido", text)),
        "Segundo_apellido": clean_field(extract_field(r"Segundo apellido\s+(.+?)\s+Tipo documento", text)),
        "Tipo_documento": clean_field(extract_field(r"Tipo documento\s+(.+?)\s+Número documento", text)),
        "Numero_documento": extract_field(r"Número documento\s+(\d+)", text),
        "Fecha_expedicion": extract_field(r"Fecha expedición\s+(\d{4}-\d{2}-\d{2})", text),
        "Genero": extract_field(r"Género\s+(.+?)\s+Estado civil", text),
        "Estado_civil": extract_field(r"Estado civil\s+(.+?)\s+Fecha nacimiento", text),
        "Fecha_nacimiento": extract_field(r"Fecha nacimiento\s+(\d{4}-\d{2}-\d{2})", text),
        "Pais_nacimiento": clean_field(extract_field(r"País nacimiento\s+(.+?)\s+País nacionalidad", text)),
        "Pais_nacionalidad": clean_field(extract_field(r"País nacionalidad\s+(.+?)\s+¿Otra nacionalidad\?", text)),
        "Otra_nacionalidad": extract_field(r"¿Otra nacionalidad\?\s+(.+?)\s+Otras nacionalidades", text),
    }

    # Información de contacto
    form_data["Informacion_Contacto"] = {
        "Correo_electronico": clean_field(extract_field(r"Correo electrónico\s+(.+?)\s+Celular", text)),
        "Celular": extract_field(r"Celular\s+(\d+)", text),
        "Direccion": clean_field(extract_field(r"Dirección\s+(.+?)\s+Código postal", text)),
        "Codigo_postal": extract_field(r"Código postal\s+(\d+)", text),
        "Pais_residencia": extract_field(r"País de residencia\s+(.+?)\s+Departamento de residencia", text),
        "Departamento_residencia": extract_field(r"Departamento de residencia\s+(.+?)\s+Ciudad de residencia", text),
        "Ciudad_residencia": extract_field(r"Ciudad de residencia\s+(.+?)\s+Información laboral", text),
    }

    # Información laboral
    form_data["Informacion_Laboral"] = {
        "Situacion_laboral": extract_field(r"Situación laboral\s+(.+?)\s+Profesión", text),
        "Profesion": extract_field(r"Profesión\s+(.+?)\s+NIT", text),
        "NIT": extract_field(r"NIT\s+(.+?)\s+Nombre empresa", text),
        "Nombre_empresa": extract_field(r"Nombre empresa\s+(.+?)\s+País", text),
        "Pais": clean_pais(extract_field(r"País\s+(.+?)\s+Ciudad", text)),
        "Ciudad": clean_ciudad(extract_field(r"Ciudad\s+(.+?)\s+Dirección empresa", text)),
        "Direccion_empresa": extract_field(r"Dirección empresa\s+(.+?)\s+Cargo que desempeña", text),
        "Cargo": extract_field(r"Cargo que desempeña\s+(.+?)\s+Código CIIU", text),
        "Codigo_CIIU": extract_field(r"Código CIIU\s+(.+?)\s+Nombre de la actividad", text),
        "Nombre_actividad": extract_field(r"Nombre de la actividad\s+(.+?)\s+Formulario", text),
    }

    # Información financiera
    form_data["Informacion_Financiera"] = {
        "Total_activos": extract_field(r"Total activos\s+\$(\d{1,3}(,\d{3})*(\.\d+)?)", text),
        "Total_pasivos": extract_field(r"Total pasivos\s+\$(\d{1,3}(,\d{3})*(\.\d+)?)", text),
        "Total_patrimonio": extract_field(r"Total patrimonio\s+\$(\d{1,3}(,\d{3})*(\.\d+)?)", text),
        "Ingresos_totales_anuales": extract_field(r"Ingresos totales anuales\s+\$(\d{1,3}(,\d{3})*(\.\d+)?)", text),
        "Egresos_totales_anuales": extract_field(r"Egresos totales anuales\s+\$(\d{1,3}(,\d{3})*(\.\d+)?)", text),
        "Realiza_operaciones_moneda_extranjera": extract_field(r"¿Realiza operaciones en moneda extranjera\?\s+(Sí|No)", text),
    }

    return form_data

@app.route('/extract-info-pdf', methods=['GET'])
def process_pdf():
    """
    Endpoint para procesar un PDF desde Base64.
    """
    try:
        data_params = request.args
        
        if not data_params:
            return jsonify({"status": "error", "message": "No se proporcionaron parámetros en la solicitud"}), 400

        type_document = data_params.get("type_document")
        num_document = data_params.get("num_document")
        form_type = data_params.get("form_type")

        if not type_document or not num_document or not form_type:
            return jsonify({"status": "error", "message": "Faltan parámetros en la solicitud"}), 400
        
        resultPdf = fetch_document_number_from_api(type_document, num_document, form_type)

        base64_pdf = resultPdf["data"]["file"]
        password = num_document

        try:
            file_bytes = base64.b64decode(base64_pdf)
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error decodificando Base64: {e}"}), 400

        pdf_text = extract_pdf_text(file_bytes, password)

        form_data = parse_form_to_json(pdf_text)
        print(form_data)

        return jsonify({"status": "success", "data": form_data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, port=5000)
