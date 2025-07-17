from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from services import FileBlockService, MachineService, SettingsService
import os

def register_routes(app):
    # Initialiser les services
    file_service = FileBlockService(app.config['DATABASE_PATH'])
    machine_service = MachineService(app.config['DATABASE_PATH'])
    settings_service = SettingsService(app.config['DATABASE_PATH'])
    
    @app.route('/')
    def index():
        """Page d'accueil avec la liste des fichiers"""
        files = file_service.get_files_list()
        distributed_files = [f for f in files if f['status'] == 'distributed']
        return render_template('index.html', files=distributed_files)
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        """Upload et distribution d'un fichier"""
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.url)
            
            if file:
                success, message, file_id = file_service.distribute_file(
                    file, app.config['UPLOAD_FOLDER']
                )
                
                if success:
                    flash(f'{message} (ID: {file_id})', 'success')
                    return redirect(url_for('index'))
                else:
                    flash(message, 'error')
        
        return render_template('upload.html')
    
    @app.route('/download/<int:file_id>')
    def download_file(file_id):
        """Télécharge et reassemble un fichier"""
        success, message, filepath = file_service.reassemble_file(
            file_id, app.config['DOWNLOAD_FOLDER']
        )
        
        if success and filepath is not None:
            flash(message, 'success')
            return send_file(filepath, as_attachment=True)
        else:
            flash(message, 'error')
            return redirect(url_for('index'))
    
    @app.route('/delete/<int:file_id>')
    def delete_file(file_id):
        """Supprime un fichier"""
        success, message = file_service.delete_file(file_id)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('index'))
    
    @app.route('/machines')
    def machines_list():
        """Liste des machines"""
        machines = machine_service.get_machines_list()
        return render_template('machines.html', machines=machines)
    
    @app.route('/machines/add', methods=['GET', 'POST'])
    def add_machine():
        """Ajouter une machine"""
        if request.method == 'POST':
            name = request.form['name']
            url = request.form['url']
            storage_path = request.form['storage_path']
            
            success, message = machine_service.add_machine(name, url, storage_path)
            flash(message, 'success' if success else 'error')
            
            if success:
                return redirect(url_for('machines_list'))
        
        return render_template('add_machine.html')
    
    @app.route('/machines/edit/<int:machine_id>', methods=['GET', 'POST'])
    def edit_machine(machine_id):
        """Éditer une machine"""
        machines = machine_service.get_machines_list()
        machine = next((m for m in machines if m['id'] == machine_id), None)
        
        if not machine:
            flash('Machine non trouvée', 'error')
            return redirect(url_for('machines_list'))
        
        if request.method == 'POST':
            name = request.form['name']
            url = request.form['url']
            storage_path = request.form['storage_path']
            
            success, message = machine_service.update_machine(machine_id, name, url, storage_path)
            flash(message, 'success' if success else 'error')
            
            if success:
                return redirect(url_for('machines_list'))
        
        return render_template('edit_machine.html', machine=machine)
    
    @app.route('/machines/toggle/<int:machine_id>')
    def toggle_machine(machine_id):
        """Active/désactive une machine"""
        success, message = machine_service.toggle_machine_status(machine_id)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('machines_list'))
    
    @app.route('/machines/delete/<int:machine_id>')
    def delete_machine(machine_id):
        """Supprime une machine"""
        success, message = machine_service.delete_machine(machine_id)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('machines_list'))
    
    @app.route('/settings')
    def settings():
        """Page des paramètres"""
        current_settings = settings_service.get_settings()
        return render_template('settings.html', settings=current_settings)
    
    @app.route('/settings/block-size', methods=['POST'])
    def update_block_size():
        """Met à jour la taille des blocs"""
        try:
            size_mb = int(request.form['block_size'])
            if size_mb < 1 or size_mb > 100:
                flash('La taille doit être entre 1 et 100 MB', 'error')
            else:
                size_bytes = size_mb * 1024 * 1024
                success = settings_service.set_block_size(size_bytes)
                flash('Taille des blocs mise à jour' if success else 'Erreur lors de la mise à jour', 'success' if success else 'error')
        except ValueError:
            flash('Taille invalide', 'error')
        
        return redirect(url_for('settings'))
    
    @app.route('/api/machines/status/<int:machine_id>')
    def check_machine_status(machine_id):
        """API pour vérifier le statut d'une machine"""
        machines = machine_service.get_machines_list()
        machine = next((m for m in machines if m['id'] == machine_id), None)
        
        if not machine:
            return jsonify({'error': 'Machine non trouvée'}), 404