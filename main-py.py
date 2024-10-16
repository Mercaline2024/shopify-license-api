from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(app, key_func=get_remote_address)

@app.route('/verify-license', methods=['POST'])
@limiter.limit("5 per minute")
def verify_license():
    data = request.json
    license_key = data.get('license_key')
    shop_domain = data.get('shop_domain')
    
    # Aquí iría tu lógica de verificación de licencia
    # Por ahora, simplemente devolvemos una respuesta de prueba
    return jsonify({"valid": True, "message": "License is valid"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
