"""Cliente Firebase para o Bot LiberALL"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, db
from config import get_config
from core.env_config import env_config

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Cliente para interação com Firebase Realtime Database"""
    
    def __init__(self, simulation_mode: Optional[bool] = None):
        """Inicializa o cliente Firebase.
        
        Args:
            simulation_mode: Se True, usa dados simulados. Se None, usa configuração de ambiente
        """
        # Usar configuração de ambiente se não especificado
        if simulation_mode is None:
            simulation_mode = env_config.firebase_simulation
            
        self.simulation_mode = simulation_mode
        self.simulation_data = {}
        self.simulation_file = 'firebase_simulation_data.json'
        self.db_ref = None
        
        if simulation_mode:
            logger.info("Firebase client initialized in simulation mode")
            self._load_simulation_data()
        else:
            logger.info("Firebase client initialized in real mode")
            self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Inicializa conexão com Firebase usando credenciais do ambiente"""
        try:
            # Verificar se as credenciais são de teste/desenvolvimento
            if self._is_test_environment():
                logger.info("Credenciais de teste detectadas, ativando modo simulação")
                self.simulation_mode = True
                self._load_simulation_data()
                return
            
            # Configurar credenciais do Firebase usando env_config
            project_id = env_config.firebase_project_id
            private_key = env_config.firebase_private_key
            client_email = env_config.firebase_client_email

            # Validar presença de credenciais críticas
            if not project_id or not private_key or not client_email:
                logger.warning("Credenciais Firebase incompletas; ativando modo simulação")
                self.simulation_mode = True
                self._load_simulation_data()
                return

            # Normalizar quebra de linha da chave privada
            if isinstance(private_key, str):
                private_key = private_key.replace('\\n', '\n')
            else:
                logger.warning("Formato inválido para chave privada; ativando modo simulação")
                self.simulation_mode = True
                self._load_simulation_data()
                return

            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email}"
            }
            
            cred = credentials.Certificate(cred_dict)
            
            # Inicializar Firebase Admin SDK
            if not firebase_admin._apps:
                database_url = env_config.firebase_database_url or f"https://{project_id}-default-rtdb.firebaseio.com/"
                if not database_url:
                    logger.warning("FIREBASE_DATABASE_URL não definido; ativando modo simulação")
                    self.simulation_mode = True
                    self._load_simulation_data()
                    return
                firebase_admin.initialize_app(cred, {'databaseURL': database_url})
            
            self.db_ref = db.reference()
            logger.info("Firebase inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar Firebase: {e}")
            # Fallback para modo simulação
            logger.info("Ativando modo simulação como fallback")
            self.simulation_mode = True
            self._load_simulation_data()
    
    def _is_test_environment(self) -> bool:
        """Verifica se está em ambiente de teste baseado nas credenciais"""
        test_indicators = [
            'test',
            'MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB',
            'test_key_content_here',
            'test-project',
            'test@test-project.iam.gserviceaccount.com'
        ]
        
        # Verificar se algum indicador de teste está presente nas credenciais
        project_id = env_config.firebase_project_id or ''
        private_key = env_config.firebase_private_key or ''
        client_email = env_config.firebase_client_email or ''
        
        for indicator in test_indicators:
            if (indicator in project_id.lower() or 
                indicator in private_key or 
                indicator in client_email.lower()):
                return True
        
        # Verificar se FIREBASE_SIMULATION está ativo
        return env_config.firebase_simulation
    
    def _load_simulation_data(self):
        """Carrega dados de simulação"""
        simulation_file = 'firebase_simulation_data.json'
        if os.path.exists(simulation_file):
            try:
                with open(simulation_file, 'r', encoding='utf-8') as f:
                    self.simulation_data = json.load(f)
                logger.info("Dados de simulação carregados")
            except Exception as e:
                logger.error(f"Erro ao carregar dados de simulação: {e}")
                self.simulation_data = {}
        else:
            # Criar dados de simulação iniciais
            self.simulation_data = {
                'users': {},
                'matches': {},
                'posts': {},
                'settings': {}
            }
            logger.info("Dados de simulação inicializados")
    
    def _save_simulation_data(self):
        """Salva dados de simulação"""
        if self.simulation_mode:
            try:
                with open('firebase_simulation_data.json', 'w', encoding='utf-8') as f:
                    json.dump(self.simulation_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Erro ao salvar dados de simulação: {e}")
    
    def _get_nested_value(self, data: dict, path: str):
        """Obtém valor aninhado usando caminho com barras"""
        keys = path.strip('/').split('/')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: dict, path: str, value: Any):
        """Define valor aninhado usando caminho com barras"""
        keys = path.strip('/').split('/')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    async def get(self, path: str) -> Optional[Any]:
        """Obtém dados do Firebase ou simulação"""
        try:
            if self.simulation_mode:
                return self._get_nested_value(self.simulation_data, path)
            else:
                if self.db_ref:
                    return self.db_ref.child(path).get()
                return None
        except Exception as e:
            logger.error(f"Erro ao obter dados de {path}: {e}")
            return None
    
    async def set(self, path: str, data: Any) -> bool:
        """Define dados no Firebase ou simulação"""
        try:
            if self.simulation_mode:
                self._set_nested_value(self.simulation_data, path, data)
                self._save_simulation_data()
                return True
            else:
                if self.db_ref:
                    self.db_ref.child(path).set(data)
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao definir dados em {path}: {e}")
            return False
    
    async def update(self, path: str, data: Dict[str, Any]) -> bool:
        """Atualiza dados no Firebase ou simulação"""
        try:
            if self.simulation_mode:
                current = self._get_nested_value(self.simulation_data, path)
                if current is None:
                    current = {}
                
                if isinstance(current, dict):
                    current.update(data)
                    self._set_nested_value(self.simulation_data, path, current)
                else:
                    self._set_nested_value(self.simulation_data, path, data)
                
                self._save_simulation_data()
                return True
            else:
                if self.db_ref:
                    self.db_ref.child(path).update(data)
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao atualizar dados em {path}: {e}")
            return False
    
    async def push(self, path: str, data: Any) -> Optional[str]:
        """Adiciona dados com chave auto-gerada"""
        try:
            if self.simulation_mode:
                # Gera uma chave única simulada
                import time
                key = f"sim_{int(time.time() * 1000)}"
                full_path = f"{path}/{key}"
                self._set_nested_value(self.simulation_data, full_path, data)
                self._save_simulation_data()
                return key
            else:
                if self.db_ref:
                    ref = self.db_ref.child(path).push(data)
                    return ref.key
                return None
        except Exception as e:
            logger.error(f"Erro ao adicionar dados em {path}: {e}")
            return None
    
    async def delete(self, path: str) -> bool:
        """Remove dados do Firebase ou simulação"""
        try:
            if self.simulation_mode:
                keys = path.strip('/').split('/')
                current = self.simulation_data
                
                for key in keys[:-1]:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return True  # Já não existe
                
                if isinstance(current, dict) and keys[-1] in current:
                    del current[keys[-1]]
                    self._save_simulation_data()
                
                return True
            else:
                if self.db_ref:
                    self.db_ref.child(path).delete()
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao remover dados de {path}: {e}")
            return False
    
    async def increment_atomic(self, path: str, value: int = 1) -> bool:
        """Incrementa um valor atomicamente"""
        try:
            if self.simulation_mode:
                current = self._get_nested_value(self.simulation_data, path) or 0
                new_value = int(current) + value
                self._set_nested_value(self.simulation_data, path, new_value)
                self._save_simulation_data()
                return True
            else:
                if self.db_ref:
                    # Para Firebase real, usa transação
                    def transaction_update(current_data):
                        return (current_data or 0) + value
                    
                    self.db_ref.child(path).transaction(transaction_update)
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao incrementar {path}: {e}")
            return False
    
    async def append_to_array(self, path: str, item: Any) -> bool:
        """Adiciona item a um array atomicamente"""
        try:
            if self.simulation_mode:
                current = self._get_nested_value(self.simulation_data, path) or []
                if not isinstance(current, list):
                    current = []
                current.append(item)
                self._set_nested_value(self.simulation_data, path, current)
                self._save_simulation_data()
                return True
            else:
                if self.db_ref:
                    # Para Firebase real, usa transação
                    def transaction_update(current_data):
                        if current_data is None:
                            return [item]
                        if not isinstance(current_data, list):
                            return [item]
                        current_data.append(item)
                        return current_data
                    
                    self.db_ref.child(path).transaction(transaction_update)
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao adicionar item ao array {path}: {e}")
            return False
    
    async def remove_from_array(self, path: str, item: Any) -> bool:
        """Remove item de um array atomicamente"""
        try:
            if self.simulation_mode:
                current = self._get_nested_value(self.simulation_data, path) or []
                if isinstance(current, list) and item in current:
                    current.remove(item)
                    self._set_nested_value(self.simulation_data, path, current)
                    self._save_simulation_data()
                return True
            else:
                if self.db_ref:
                    # Para Firebase real, usa transação
                    def transaction_update(current_data):
                        if current_data is None or not isinstance(current_data, list):
                            return current_data
                        if item in current_data:
                            current_data.remove(item)
                        return current_data
                    
                    self.db_ref.child(path).transaction(transaction_update)
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao remover item do array {path}: {e}")
            return False
    
    async def atomic_update_user_data(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Atualiza dados do usuário atomicamente com validação"""
        try:
            user_path = f"users/{user_id}"
            
            if self.simulation_mode:
                current_user = self._get_nested_value(self.simulation_data, user_path) or {}
                
                # Validações básicas
                if 'karma' in updates and updates['karma'] < 0:
                    updates['karma'] = 0
                
                if 'last_activity' not in current_user:
                    updates['last_activity'] = datetime.now().isoformat()
                
                # Merge dos dados
                for key, value in updates.items():
                    if '.' in key:  # Suporte para nested updates
                        nested_path = f"{user_path}/{key.replace('.', '/')}"
                        self._set_nested_value(self.simulation_data, nested_path, value)
                    else:
                        current_user[key] = value
                
                self._set_nested_value(self.simulation_data, user_path, current_user)
                self._save_simulation_data()
                return True
            else:
                if self.db_ref:
                    # Para Firebase real, usa transação
                    def transaction_update(current_data):
                        if current_data is None:
                            current_data = {}
                        
                        # Aplicar validações
                        if 'karma' in updates and updates['karma'] < 0:
                            updates['karma'] = 0
                        
                        if 'last_activity' not in current_data:
                            updates['last_activity'] = datetime.now().isoformat()
                        
                        # Merge dos dados
                        current_data.update(updates)
                        return current_data
                    
                    self.db_ref.child(user_path).transaction(transaction_update)
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao atualizar dados do usuário {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados completos do usuário"""
        try:
            user_data = await self.get(f"users/{user_id}")
            if user_data:
                # Garantir campos obrigatórios
                defaults = {
                    'karma': 0,
                    'level': 1,
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat(),
                    'active': True,
                    'verified': False,
                    'premium': False
                }
                
                for key, default_value in defaults.items():
                    if key not in user_data:
                        user_data[key] = default_value
                
                return user_data
            return None
        except Exception as e:
            logger.error(f"Erro ao obter usuário {user_id}: {e}")
            return None
    
    async def create_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Cria um novo usuário com dados padrão"""
        try:
            # Dados padrão obrigatórios
            default_data = {
                'user_id': user_id,
                'karma': 0,
                'level': 1,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'active': True,
                'verified': False,
                'premium': False,
                'settings': {
                    'privacy': {
                        'profile_visibility': 'public',
                        'photo_visibility': 'public',
                        'online_status': True
                    },
                    'notifications': {
                        'matches': True,
                        'messages': True,
                        'likes': True,
                        'system': True
                    }
                },
                'stats': {
                    'total_matches': 0,
                    'total_likes_given': 0,
                    'total_likes_received': 0,
                    'posts_count': 0,
                    'photos_count': 0
                }
            }
            
            # Merge com dados fornecidos
            default_data.update(user_data)
            
            return await self.set(f"users/{user_id}", default_data)
        except Exception as e:
            logger.error(f"Erro ao criar usuário {user_id}: {e}")
            return False
    
    async def backup_data(self, backup_path: str = None) -> bool:
        """Cria backup dos dados"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_firebase_{timestamp}.json"
            
            if self.simulation_mode:
                # Backup dos dados de simulação
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.simulation_data, f, indent=2, ensure_ascii=False)
            else:
                if self.db_ref:
                    # Backup dos dados reais do Firebase
                    all_data = self.db_ref.get()
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(all_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup criado em: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica a saúde da conexão com Firebase"""
        try:
            if self.simulation_mode:
                return {
                    'status': 'healthy',
                    'mode': 'simulation',
                    'data_size': len(str(self.simulation_data)),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                if self.db_ref:
                    # Testa conexão com uma operação simples
                    test_path = f"health_check/{int(datetime.now().timestamp())}"
                    await self.set(test_path, {'timestamp': datetime.now().isoformat()})
                    await self.delete(test_path)
                    
                    return {
                        'status': 'healthy',
                        'mode': 'firebase',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'status': 'error',
                        'mode': 'firebase',
                        'error': 'No database reference',
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Erro no health check: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Instância global do cliente
firebase_client = FirebaseClient()
