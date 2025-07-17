import os
import hashlib
import math
import requests
from typing import List, Dict, Optional, Tuple
from werkzeug.datastructures import FileStorage
from models import Database, FileModel, BlockModel, MachineModel, SettingsModel

class FileBlockService:
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.file_model = FileModel(self.db)
        self.block_model = BlockModel(self.db)
        self.machine_model = MachineModel(self.db)
        self.settings_model = SettingsModel(self.db)

    def calculate_file_hash(self, filepath: str) -> str:
        """Calcule le hash SHA-256 d'un fichier"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def split_file_into_blocks(self, filepath: str, block_size: int) -> List[Dict]:
        """Divise un fichier en blocs"""
        file_size = os.path.getsize(filepath)
        block_count = math.ceil(file_size / block_size)
        blocks = []
        
        with open(filepath, 'rb') as f:
            for i in range(block_count):
                block_data = f.read(block_size)
                if not block_data:
                    break
                
                block_hash = hashlib.sha256(block_data).hexdigest()
                blocks.append({
                    'number': i,
                    'data': block_data,
                    'hash': block_hash,
                    'size': len(block_data)
                })
        
        return blocks
    
    def send_block_to_machine(self, block_data: bytes, machine_url: str, storage_path: str) -> bool:
        """Envoie un bloc vers une machine distante"""
        try:
            files = {'block': block_data}
            data = {'path': storage_path}
            
            headers = {'X-API-KEY': 'super-secret-key'} # TODO: change this to a real secret key
            response = requests.post(
                f"{machine_url}/upload_block",
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Erreur lors de l'envoi du bloc : {e}")
            return False
    
    def download_block_from_machine(self, machine_url: str, storage_path: str) -> Optional[bytes]:
        """Télécharge un bloc depuis une machine distante"""
        try:
            response = requests.get(
                f"{machine_url}/download_block",
                params={'path': storage_path},
                timeout=60
            )
            
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print(f"Erreur lors du téléchargement du bloc : {e}")
            return None
    
    def distribute_file(self, file_storage: FileStorage, upload_folder: str) -> Tuple[bool, str, Optional[int]]:
        """Distribue un fichier sur les machines disponibles"""
        try:
            # Sauvegarder le fichier temporairement
            filename = file_storage.filename
            if filename is None:
                return False, "Nom de fichier manquant", None
            filepath = os.path.join(upload_folder, filename)
            file_storage.save(filepath)
            
            # Calculer les informations du fichier
            file_hash = self.calculate_file_hash(filepath)
            file_size = os.path.getsize(filepath)
            block_size = self.settings_model.get_block_size()
            
            # Diviser en blocs
            blocks = self.split_file_into_blocks(filepath, block_size)
            
            # Vérifier les machines disponibles
            machines = self.machine_model.get_active_machines()
            if not machines:
                return False, "Aucune machine disponible", None
            
            # Créer l'entrée du fichier
            file_id = self.file_model.create_file(
                filename, file_hash, file_size, len(blocks), block_size
            )
            if file_id is None:
                return False, "Erreur lors de la création du fichier en base", None

            # Distribuer les blocs
            for i, block in enumerate(blocks):
                machine = machines[i % len(machines)]
                block_filename = f"{file_hash}_block_{block['number']}"
                storage_path = f"{machine['storage_path']}/{block_filename}"
                
                success = self.send_block_to_machine(
                    block['data'], machine['url'], storage_path
                )
                
                if success:
                    self.block_model.create_block(
                        file_id, block['number'], block['hash'], 
                        block['size'], machine['url'], storage_path
                    )
                else:
                    # Nettoyer en cas d'échec
                    self.file_model.delete_file(file_id)
                    self.block_model.delete_blocks_by_file_id(file_id)
                    return False, f"Échec de l'envoi du bloc {block['number']}", None
            
            # Nettoyer le fichier temporaire
            os.remove(filepath)
            
            return True, "Fichier distribué avec succès", file_id
            
        except Exception as e:
            return False, f"Erreur lors de la distribution : {str(e)}", None
    
    def reassemble_file(self, file_id: int, download_folder: str) -> Tuple[bool, str, Optional[str]]:
        """Reassemble un fichier à partir de ses blocs"""
        try:
            # Récupérer les informations du fichier
            file_info = self.file_model.get_file_by_id(file_id)
            if not file_info:
                return False, "Fichier non trouvé", None
            
            # Récupérer les blocs
            blocks = self.block_model.get_blocks_by_file_id(file_id)
            if not blocks:
                return False, "Aucun bloc trouvé", None
            
            # Créer le fichier de sortie
            output_path = os.path.join(download_folder, file_info['original_name'])
            
            with open(output_path, 'wb') as output_file:
                for block in blocks:    
                    block_data = self.download_block_from_machine(
                        block['machine_url'], block['storage_path']
                    )
                    
                    if block_data is None:
                        return False, f"Échec du téléchargement du bloc {block['block_number']}", None
                    
                    # Vérifier l'intégrité
                    if hashlib.sha256(block_data).hexdigest() != block['block_hash']:
                        return False, f"Erreur d'intégrité pour le bloc {block['block_number']}", None
                    
                    output_file.write(block_data)
            
            return True, "Fichier reassemblé avec succès", output_path
            
        except Exception as e:
            return False, f"Erreur lors du reassemblage : {str(e)}", None
    
    def get_files_list(self) -> List[Dict]:
        """Récupère la liste des fichiers avec informations formatées"""
        files = self.file_model.get_all_files()
        for file in files:
            file['size_mb'] = round(file['total_size'] / (1024 * 1024), 2)
            file['block_size_mb'] = round(file['block_size'] / (1024 * 1024), 2)
        return files
    
    def delete_file(self, file_id: int) -> Tuple[bool, str]:
        """Supprime un fichier et ses blocs"""
        try:
            # Récupérer les blocs pour les supprimer des machines
            blocks = self.block_model.get_blocks_by_file_id(file_id)
            
            # Supprimer les blocs des machines distantes
            for block in blocks:
                try:
                    requests.delete(
                        f"{block['machine_url']}/delete_block",
                        params={'path': block['storage_path']},
                        timeout=30
                    )
                except:
                    pass  # Ignorer les erreurs de suppression distante
            
            # Supprimer de la base de données
            self.block_model.delete_blocks_by_file_id(file_id)
            self.file_model.delete_file(file_id)
            
            return True, "Fichier supprimé avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de la suppression : {str(e)}"
            

class MachineService:
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.machine_model = MachineModel(self.db)
    
    def add_machine(self, name: str, url: str, storage_path: str) -> Tuple[bool, str]:
        """Ajoute une nouvelle machine"""
        try:
            # Nettoyer l'URL
            if not url.startswith('http'):
                url = 'http://' + url
            
            self.machine_model.create_machine(name, url, storage_path)
            return True, "Machine ajoutée avec succès"
        except Exception as e:
            return False, f"Erreur lors de l'ajout : {str(e)}"
    
    def get_machines_list(self) -> List[Dict]:
        """Récupère la liste des machines"""
        return self.machine_model.get_all_machines()
    
    def update_machine(self, machine_id: int, name: str, url: str, storage_path: str) -> Tuple[bool, str]:
        """Met à jour une machine"""
        try:
            if not url.startswith('http'):
                url = 'http://' + url
            
            self.machine_model.update_machine(machine_id, name, url, storage_path)
            return True, "Machine mise à jour avec succès"
        except Exception as e:
            return False, f"Erreur lors de la mise à jour : {str(e)}"
    
    def toggle_machine_status(self, machine_id: int) -> Tuple[bool, str]:
        """Active/désactive une machine"""
        try:
            self.machine_model.toggle_machine_status(machine_id)
            return True, "Statut de la machine modifié"
        except Exception as e:
            return False, f"Erreur lors du changement de statut : {str(e)}"
    
    def delete_machine(self, machine_id: int) -> Tuple[bool, str]:
        """Supprime une machine"""
        try:
            self.machine_model.delete_machine(machine_id)
            return True, "Machine supprimée avec succès"
        except Exception as e:
            return False, f"Erreur lors de la suppression : {str(e)}"
    
    def check_machine_status(self, machine_url: str) -> bool:
        """Vérifie si une machine est accessible"""
        try:
            response = requests.get(f"{machine_url}/status", timeout=10)
            return response.status_code == 200
        except:
            return False




class SettingsService:
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.settings_model = SettingsModel(self.db)        

    def get_block_size(self) -> int:
        """Récupère la taille des blocs"""
        return self.settings_model.get_block_size()
    
    def set_block_size(self, size: int) -> bool:
        """Définit la taille des blocs"""
        self.settings_model.set_block_size(size)
        return True

    def get_settings(self) -> Dict:
        """Récupère les paramètres de configuration"""
        return {
            'block_size': self.get_block_size()
        }
    
    def set_settings(self, settings: Dict) -> bool:
        """Définit les paramètres de configuration"""
        if 'block_size' in settings:
            self.set_block_size(settings['block_size'])
        return True
