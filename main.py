import sys
import traceback
import os
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google.cloud import firestore
from flask_cors import CORS
from datetime import datetime, timedelta

print("Iniciando la aplicación...", file=sys.stderr)

app = Flask(__name__)
print("Aplicación Flask creada", file=sys.stderr)

try:
    print("Configurando CORS...", file=sys.stderr)
    CORS(app, resources={r"/*": {"origins": "*"}})
    print("CORS configurado con éxito", file=sys.stderr)

    print("Inicializando Limiter...", file=sys.stderr)
    limiter = Limiter(app, key_func=get_remote_address)
    print("Limiter inicializado con éxito", file=sys.stderr)

    print("Conectando a Firestore...", file=sys.stderr)
    db = firestore.Client()
    licenses_collection = db.collection('licenses')
    print("Conexión a Firestore establecida con éxito", file=sys.stderr)

    print("Inicialización completada con éxito", file=sys.stderr)
except Exception as e:
    print(f"Error crítico durante la inicialización: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

@app.route('/verify-license', methods=['POST'])
@limiter.limit("5 per minute")
def verify_license():
    print("Iniciando verificación de licencia...", file=sys.stderr)
    try:
        data = request.json
        license_key = data.get('license_key')
        shop_domain = data.get('shop_domain')
        
        print(f"Datos recibidos: license_key={license_key}, shop_domain={shop_domain}", file=sys.stderr)
        
        if not license_key or not shop_domain:
            print("Error: Faltan datos requeridos", file=sys.stderr)
            return jsonify({"error": "License key and shop domain are required"}), 400
        
        print(f"Buscando licencia en Firestore: {license_key}", file=sys.stderr)
        license_doc = licenses_collection.document(license_key).get()
        
        if not license_doc.exists:
            print(f"Licencia no encontrada: {license_key}", file=sys.stderr)
            return jsonify({"valid": False, "message": "Invalid license key"}), 403
        
        license_info = license_doc.to_dict()
        print(f"Información de licencia recuperada: {license_info}", file=sys.stderr)
        
        if license_info['shop_domain'] != shop_domain:
            print(f"Dominio de tienda no coincide: {shop_domain} != {license_info['shop_domain']}", file=sys.stderr)
            return jsonify({"valid": False, "message": "License key is not valid for this shop"}), 403
        
        if datetime.now() > license_info['expiry_date'].replace(tzinfo=None):
            print(f"Licencia expirada: {license_info['expiry_date']}", file=sys.stderr)
            return jsonify({"valid": False, "message": "License has expired"}), 403
        
        print("Licencia verificada con éxito", file=sys.stderr)
        return jsonify({"valid": True, "message": "License is valid"}), 200
    except Exception as e:
        print(f"Error en verify_license: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/create-license', methods=['POST'])
@limiter.limit("3 per minute")
def create_license():
    print("Iniciando creación de licencia...", file=sys.stderr)
    try:
        data = request.json
        shop_domain = data.get('shop_domain')
        duration_days = data.get('duration_days', 365)
        
        print(f"Datos recibidos: shop_domain={shop_domain}, duration_days={duration_days}", file=sys.stderr)
        
        if not shop_domain:
            print("Error: Falta el dominio de la tienda", file=sys.stderr)
            return jsonify({"error": "Shop domain is required"}), 400
        
        license_key = os.urandom(16).hex()
        expiry_date = datetime.now() + timedelta(days=duration_days)
        
        print(f"Creando licencia: key={license_key}, expiry={expiry_date}", file=sys.stderr)
        
        licenses_collection.document(license_key).set({
            "shop_domain": shop_domain,
            "expiry_date": expiry_date
        })
        
        print("Licencia creada con éxito", file=sys.stderr)
        return jsonify({"license_key": license_key, "expiry_date": expiry_date.isoformat()}), 201
    except Exception as e:
        print(f"Error en create_license: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/')
def hello():
    print("Ruta raíz accedida", file=sys.stderr)
    return "Shopify License API is running!", 200

if __name__ == '__main__':
    print(f"Iniciando servidor en el puerto {os.environ.get('PORT', 8080)}...", file=sys.stderr)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    print("Configuración de la aplicación completada", file=sys.stderr)

if __name__ == '__main__':
    print(f"Iniciando servidor en modo de desarrollo...", file=sys.stderr)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
else:
    print("Aplicación iniciada por Gunicorn", file=sys.stderr)

# No es necesario llamar a app.run() aquí, Gunicorn se encargará de eso