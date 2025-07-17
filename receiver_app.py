from flask import Flask, request, abort, jsonify, send_file
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Store your API key securely (env variable, config file, etc.)
API_KEY = os.environ.get("BLOCK_RECEIVER_API_KEY", "super-secret-key")

@app.route('/upload_block', methods=['POST'])
def upload_block():
    # Authorization check
    if request.headers.get('X-API-KEY') != API_KEY:
        abort(403, description="Unauthorized")

    block = request.files.get('block')
    storage_path = request.form.get('path')
    logging.info(f"UPLOAD: block={block is not None}, storage_path={storage_path}")
    if not block or not storage_path:
        logging.warning("UPLOAD: Missing block or path")
        return jsonify({'error': 'Missing block or path'}), 400

    try:
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        block.save(storage_path)
        logging.info(f"UPLOAD: Block saved at {storage_path}")
        return jsonify({'status': 'Block stored successfully'}), 200
    except Exception as e:
        logging.error(f"UPLOAD: Error saving block: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_block')
def download_block():
    storage_path = request.args.get('path')
    logging.info(f"DOWNLOAD: Requested path: {storage_path}")
    if not storage_path or not os.path.exists(storage_path):
        logging.warning(f"DOWNLOAD: File not found at {storage_path}")
        return jsonify({'error': 'Block not found'}), 404
    try:
        logging.info(f"DOWNLOAD: File found, sending {storage_path}")
        return send_file(storage_path, as_attachment=True)
    except Exception as e:
        logging.error(f"DOWNLOAD: Error sending file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    return jsonify({'status': 'ok'}), 200

if __name__ == "__main__":
    app.run(host="192.168.43.63", port=5001)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     