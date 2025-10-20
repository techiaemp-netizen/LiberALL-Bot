"""
Serviço para operações em lote no Firebase para otimizar performance.
"""
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from services.firebase_service import FirebaseService


class BatchFirebaseService:
    """Serviço para agrupar e executar operações Firebase em lote."""
    
    def __init__(self, firebase_service: FirebaseService):
        self.firebase_service = firebase_service
        self.logger = logging.getLogger(__name__)
        self._pending_operations: Dict[int, Dict[str, Any]] = {}
        self._batch_lock = asyncio.Lock()
        
    async def queue_user_update(self, user_id: int, data: Dict[str, Any]) -> None:
        """Adiciona uma atualização de usuário à fila de operações em lote."""
        async with self._batch_lock:
            if user_id not in self._pending_operations:
                self._pending_operations[user_id] = {}
            
            # Mescla os dados com operações pendentes
            self._pending_operations[user_id].update(data)
            
    async def flush_user_updates(self, user_id: int = None) -> None:
        """Executa todas as operações pendentes para um usuário específico ou todos."""
        async with self._batch_lock:
            if user_id:
                # Flush apenas para um usuário específico
                if user_id in self._pending_operations:
                    data = self._pending_operations.pop(user_id)
                    await self.firebase_service.update_user(user_id, data)
                    self.logger.info(f"Batch update executado para usuário {user_id}")
            else:
                # Flush para todos os usuários pendentes
                operations = list(self._pending_operations.items())
                self._pending_operations.clear()
                
                # Executa todas as operações em paralelo
                tasks = []
                for uid, data in operations:
                    task = self.firebase_service.update_user(uid, data)
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    self.logger.info(f"Batch update executado para {len(tasks)} usuários")
    
    async def auto_flush_after_delay(self, delay_seconds: float = 0.5) -> None:
        """Executa flush automático após um delay para otimizar operações consecutivas."""
        await asyncio.sleep(delay_seconds)
        await self.flush_user_updates()
        
    async def get_pending_operations_count(self) -> int:
        """Retorna o número de operações pendentes."""
        async with self._batch_lock:
            return len(self._pending_operations)
            
    async def has_pending_operations(self, user_id: int) -> bool:
        """Verifica se há operações pendentes para um usuário."""
        async with self._batch_lock:
            return user_id in self._pending_operations