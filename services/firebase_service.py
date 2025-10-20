import os
import logging
import asyncio
from typing import Optional, Dict, Any

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK não disponível")

class FirebaseService:
    def __init__(self):
        self.db = None
        self.initialized = False
        self._init_task = None
        self._init_attempted = False
        
        if not FIREBASE_AVAILABLE:
            logging.warning("🔥 Firebase desabilitado - SDK não disponível")
    
    def _is_test_credentials(self, cred_path: str) -> bool:
        """Verifica se as credenciais são de teste/desenvolvimento."""
        try:
            import json
            with open(cred_path, 'r') as f:
                cred_data = json.load(f)
            
            # Verifica se contém dados de teste
            test_indicators = [
                'test_key_id' in str(cred_data.get('private_key_id', '')),
                'liberall-test-project' in str(cred_data.get('project_id', '')),
                'firebase-adminsdk-test@' in str(cred_data.get('client_email', '')),
                'MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB' in str(cred_data.get('private_key', ''))
            ]
            return any(test_indicators)
        except Exception:
            return False
    
    async def _async_init(self):
        """Inicialização assíncrona do Firebase."""
        try:
            # Verifica se deve usar modo simulação
            simulate_firebase = os.getenv('FIREBASE_SIMULATION', 'False').strip().lower() in ('true', '1', 'yes', 'on')

            if simulate_firebase:
                logging.info("🔥 Firebase em modo simulação (FIREBASE_SIMULATION=True)")
                self.db = None
                self.initialized = False
                return

            if not firebase_admin._apps:
                # Tenta usar credenciais JSON do .env primeiro
                firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')

                if firebase_creds_json:
                    import json
                    try:
                        cred_dict = json.loads(firebase_creds_json)
                        cred = credentials.Certificate(cred_dict)
                        logging.info("🔥 Usando credenciais do .env (FIREBASE_CREDENTIALS_JSON)")
                    except json.JSONDecodeError as e:
                        logging.error(f"🔥 Erro ao decodificar FIREBASE_CREDENTIALS_JSON: {e}")
                        raise
                else:
                    # Fallback para arquivo de credenciais
                    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './firebase_credentials.json')
                    if os.path.exists(cred_path):
                        if self._is_test_credentials(cred_path):
                            logging.warning("🔥 Credenciais de teste detectadas - ativando modo simulação")
                            self.db = None
                            self.initialized = False
                            return
                        cred = credentials.Certificate(cred_path)
                        logging.info(f"🔥 Usando credenciais do arquivo: {cred_path}")
                    else:
                        # Fallback para Application Default Credentials
                        cred = credentials.ApplicationDefault()
                        logging.info("🔥 Usando Application Default Credentials")

                # Inicializa o app Firebase com opções apenas se disponíveis
                options = {}
                database_url = os.getenv('FIREBASE_DATABASE_URL')
                if database_url:
                    options['databaseURL'] = database_url
                firebase_admin.initialize_app(cred, options)

            self.db = firestore.client()
            self.initialized = True
            logging.info("🔥 Firebase inicializado com sucesso")
        except Exception as e:
            logging.warning(f"🔥 Firebase initialization failed: {e}")
            self.db = None
            self.initialized = False
    
    async def _ensure_initialized(self):
        """Garante que o Firebase está inicializado antes de usar."""
        if not FIREBASE_AVAILABLE:
            return
        
        if not self._init_attempted:
            self._init_attempted = True
            if not self._init_task:
                self._init_task = asyncio.create_task(self._async_init())
        
        if self._init_task and not self._init_task.done():
            try:
                await asyncio.wait_for(self._init_task, timeout=5.0)
            except asyncio.TimeoutError:
                logging.warning("🔥 Firebase initialization timeout - continuando sem Firebase")
                self.initialized = False

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        await self._ensure_initialized()
        if not self.db or not self.initialized:
            logging.warning(f"🔥 Firebase não disponível - get_user({telegram_id})")
            return None
        
        try:
            doc_ref = self.db.collection('users').document(str(telegram_id))
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logging.error(f"🔥 Erro ao buscar usuário {telegram_id}: {e}")
            return None

    async def create_user(self, user_data: dict) -> bool:
        await self._ensure_initialized()
        if not self.db or not self.initialized:
            logging.warning(f"🔥 Firebase não disponível - create_user")
            return False
        
        try:
            telegram_id = user_data.get("telegram_id")
            self.db.collection('users').document(str(telegram_id)).set(user_data)
            logging.info(f"User {telegram_id} created in Firestore.")
            return True
        except Exception as e:
            logging.error(f"🔥 Erro ao criar usuário: {e}")
            return False

    async def update_user(self, telegram_id: int, data: dict) -> bool:
        await self._ensure_initialized()
        if not self.db or not self.initialized:
            logging.warning(f"🔥 Firebase não disponível - update_user({telegram_id})")
            return False
        
        try:
            self.db.collection('users').document(str(telegram_id)).update(data)
            return True
        except Exception as e:
            logging.error(f"🔥 Erro ao atualizar usuário {telegram_id}: {e}")
            return False
    
    async def get_user_by_codename(self, codename: str) -> Optional[Dict[str, Any]]:
        """Busca um usuário pelo codinome."""
        await self._ensure_initialized()
        if not self.db or not self.initialized:
            logging.warning(f"🔥 Firebase não disponível - get_user_by_codename({codename})")
            return None
        
        try:
            # Busca na coleção users onde o campo codename é igual ao valor fornecido
            users_ref = self.db.collection('users')
            query = users_ref.where('codename', '==', codename).limit(1)
            docs = query.stream()
            
            for doc in docs:
                return doc.to_dict()
            
            return None
        except Exception as e:
            logging.error(f"🔥 Erro ao buscar usuário por codinome {codename}: {e}")
            return None

    async def save_post(self, post_data: dict, user_id: int) -> Optional[str]:
        await self._ensure_initialized()
        if not self.db or not self.initialized:
            logging.warning(f"🔥 Firebase não disponível - save_post")
            return None
        
        try:
            post_ref = self.db.collection('posts').document()
            post_to_save = {
                'author_id': user_id,
                'content': post_data,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            post_ref.set(post_to_save)
            logging.info(f"Post {post_ref.id} saved for user {user_id}")
            return post_ref.id
        except Exception as e:
            logging.error(f"🔥 Erro ao salvar post: {e}")
            return None

# Instância global do serviço
firebase_service = FirebaseService()