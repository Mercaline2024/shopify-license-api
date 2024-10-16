from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google.cloud import firestore
from flask_cors import CORS
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Aplica CORS a toda la aplicación

limiter = Limiter(app, key_func=get_remote_address)

db = firestore.Client()
licenses_collection = db.collection('licenses')

@app.route('/verify-license', methods=['POST'])
@limiter.limit("5 per minute")
def verify_license():
    data = request.json
    license_key = data.get('license_key')
    shop_domain = data.get('shop_domain')
    
    if not license_key or not shop_domain:
        return jsonify({"error": "License key and shop domain are required"}), 400
    
    license_doc = licenses_collection.document(license_key).get()
    
    if not license_doc.exists:
        return jsonify({"valid": False, "message": "Invalid license key"}), 403
    
    license_info = license_doc.to_dict()
    
    if license_info['shop_domain'] != shop_domain:
        return jsonify({"valid": False, "message": "License key is not valid for this shop"}), 403
    
    if datetime.now() > license_info['expiry_date'].replace(tzinfo=None):
        return jsonify({"valid": False, "message": "License has expired"}), 403
    
    return jsonify({"valid": True, "message": "License is valid"}), 200

@app.route('/create-license', methods=['POST'])
@limiter.limit("3 per minute")
def create_license():
    data = request.json
    shop_domain = data.get('shop_domain')
    duration_days = data.get('duration_days', 365)
    
    if not shop_domain:
        return jsonify({"error": "Shop domain is required"}), 400
    
    license_key = os.urandom(16).hex()
    expiry_date = datetime.now() + timedelta(days=duration_days)
    
    licenses_collection.document(license_key).set({
        "shop_domain": shop_domain,
        "expiry_date": expiry_date
    })
    
    return jsonify({"license_key": license_key, "expiry_date": expiry_date.isoformat()}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))