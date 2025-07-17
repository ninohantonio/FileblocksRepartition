# Distributed File Blocks App

A Python/Flask application for distributing, storing, and retrieving files in blocks across multiple machines on a local network. Includes a web interface for file management, machine management, and settings.

---

## Features
- Upload files and distribute them in blocks across available machines
- Download and reassemble files from distributed blocks
- Manage storage machines (add, edit, delete, toggle status)
- Set block size (in MB) for file splitting
- Secure block storage with API key authorization
- Subnet scanning utility to discover available machines

---

## Prerequisites
- Python 3.8+
- pip
- (Recommended) Virtual environment

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Progres
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install extra tools for subnet scanning (optional):**
   ```bash
   pip install netifaces
   ```

---

## Configuration

Edit `config.py` to set paths for uploads, downloads, and the database. Example:
```python
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
DATABASE_PATH = 'file_blocks.db'
```

---

## Running the Main App (Web Interface)

```bash
python app.py
```
- Access the web interface at [http://localhost:5000](http://localhost:5000)
- Use the UI to upload files, manage machines, and change settings.

---

## Running the Receiver App (on Storage Machines)

On each machine that will store blocks:

1. **Set the API key (for security):**
   ```bash
   export BLOCK_RECEIVER_API_KEY="your-very-secret-key"
   ```
2. **Run the receiver app:**
   ```bash
   python receiver_app.py
   # or specify host/port:
   # flask run --app receiver_app --host=0.0.0.0 --port=5001
   ```
3. **Add the machine in the main app:**
   - Use the format: `http://<machine_ip>:<port>` (e.g., `http://192.168.1.42:5001`)
   - Set the storage path (e.g., `/home/user/blocks`)

---

## Subnet Scanning Utility

To discover available machines on your subnet:
```bash
python subnet_scan.py
```
- This will list all IPs with the specified port open (default: 5000).
- For a full device scan, use `nmap` or the provided ping sweep script.

---

## Security Notes
- **API Key:** Always set a strong, unique `BLOCK_RECEIVER_API_KEY` on each receiver machine.
- **.gitignore:** Sensitive files, user uploads, and environment files are excluded from git.
- **Firewall:** Ensure the receiver port is open and accessible only to trusted machines.

---

## Troubleshooting
- If upload or download fails, check the logs on both the main app and receiver for path and permission issues.
- Ensure the receiver app is running and accessible from the main app (test with `curl http://<ip>:<port>/status`).
- Make sure the machine URL in the main app matches the receiver's host and port.

---

## License
MIT (or specify your license)
