import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
import time

logger = logging.getLogger(__name__)

class AtomicPersistence:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AtomicPersistence, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.simulation_mode = os.getenv('FIREBASE_SIMULATION', 'false').lower() == 'true'
        self.in_memory_db = {}
        self.db = None

        logger.info("🔥 Iniciando configuração do Firebase...")

        if self.simulation_mode:
            logger.warning("🧪 MODO SIMULAÇÃO ATIVADO PELO .ENV - Firebase será simulado em memória")
            return

        for attempt in range(1, 4):
            try:
                if not firebase_admin._apps:
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
                    })
                self.db = firestore.client()
                logger.info(f"🔥 Firebase inicializado com sucesso via Application Default Credentials (Tentativa {attempt}/3)")
                return
            except Exception as e:
                logger.error(f"ERRO na Tentativa {attempt}/3 de inicializar Firebase: {e}")
                if attempt < 3:
                    time.sleep(attempt)
                else:
                    logger.critical("NÃO FOI POSSÍVEL INICIALIZAR O FIREBASE APÓS 3 TENTATIVAS.")
                    raise SystemExit("Falha na conexão com o Firebase. O bot não pode continuar.")

    async def get_user(self, telegram_id: int):
        if self.simulation_mode:
            return self.in_memory_db.get(str(telegram_id))
        doc_ref = self.db.collection('users').document(str(telegram_id))
        doc = await doc_ref.get()
        return doc.to_dict() if doc.exists else None

    async def update_user(self, telegram_id: int, data: dict):
        if self.simulation_mode:
            if str(telegram_id) not in self.in_memory_db: self.in_memory_db[str(telegram_id)] = {}
            self.in_memory_db[str(telegram_id)].update(data)
            return
        await self.db.collection('users').document(str(telegram_id)).update(data)

    async def create_user(self, telegram_id: int, user_data: dict):
        if self.simulation_mode:
            self.in_memory_db[str(telegram_id)] = user_data
            return
        await self.db.collection('users').document(str(telegram_id)).set(user_data)