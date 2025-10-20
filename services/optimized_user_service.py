"""
Serviço de usuário otimizado com batch operations e cache local.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from aiogram.types import User as TelegramUser
from services.firebase_service import FirebaseService
from services.security_service import SecurityService
from services.monetization_service import MonetizationService
from services.batch_firebase_service import BatchFirebaseService
from models.firebase_models import User


class OptimizedUserService:
    """Serviço de usuário otimizado com batch operations e cache local."""
    
    def __init__(self, firebase_service: FirebaseService, security_service: SecurityService, 
                 monetization_service: MonetizationService):
        self.firebase_service = firebase_service
        self.security_service = security_service
        self.monetization_service = monetization_service
        self.batch_service = BatchFirebaseService(firebase_service)
        self.logger = logging.getLogger(__name__)
        
        # Cache local temporário para reduzir consultas
        self._user_cache: Dict[int, User] = {}
        # Alias público para compatibilidade com referências existentes
        self.cache = self._user_cache
        self._cache_lock = asyncio.Lock()
        
        # Auto-flush task
        self._auto_flush_task = None
        self._auto_flush_delay = 0.5  # 500ms delay
        
        self.logger.info("Optimized User service initialized")

    async def get_or_create_user(self, telegram_user: TelegramUser) -> User:
        """Busca um usuário. Se não existir, cria um novo. Sempre retorna um objeto User."""
        user = await self.get_user(telegram_user.id)
        if user:
            return user
        return await self.create_user(telegram_user.id, telegram_user.username)

    async def get_user(self, telegram_id: int) -> User | None:
        """Busca um usuário com cache local."""
        try:
            # Verifica cache local primeiro
            async with self._cache_lock:
                if telegram_id in self._user_cache:
                    return self._user_cache[telegram_id]
            
            # Se não estiver no cache, busca no Firebase
            user_data = await self.firebase_service.get_user(telegram_id)
            if user_data:
                user = User.from_dict(user_data)
                # Adiciona ao cache
                async with self._cache_lock:
                    self._user_cache[telegram_id] = user
                return user
            return None
        except Exception as e:
            self.logger.error(f"Error getting user {telegram_id}: {e}")
            return None

    async def get_user_data(self, telegram_id: int) -> Dict[str, Any] | None:
        """Wrapper: retorna os dados brutos do usuário como dict (sem cache)."""
        try:
            return await self.firebase_service.get_user(telegram_id)
        except Exception as e:
            self.logger.error(f"Error getting user data {telegram_id}: {e}")
            return None

    async def create_user(self, telegram_id: int, username: str) -> User:
        """Cria um novo usuário e retorna o objeto User."""
        try:
            new_user = User(telegram_id=telegram_id, username=username)
            await self.firebase_service.create_user(new_user.to_dict())
            
            # Adiciona ao cache
            async with self._cache_lock:
                self._user_cache[telegram_id] = new_user
                
            await self.security_service.log_user_action(telegram_id, 'user_created')
            return new_user
        except Exception as e:
            self.logger.error(f"Error creating user {telegram_id}: {e}")
            raise

    async def update_user(self, telegram_id: int, data: dict, immediate: bool = False):
        """Atualiza os dados de um usuário usando batch operations."""
        if immediate:
            # Atualização imediata
            await self.firebase_service.update_user(telegram_id, data)
        else:
            # Adiciona à fila de batch operations
            await self.batch_service.queue_user_update(telegram_id, data)
            # Inicia auto-flush se não estiver rodando
            await self._schedule_auto_flush()
            
        # Atualiza cache local
        await self._update_local_cache(telegram_id, data)
        # Removido log automático de data_update que estava causando loop infinito
        # await self.security_service.log_user_action(telegram_id, 'data_update')

    async def update_user_data(self, telegram_id: int, data: Dict[str, Any]):
        """Wrapper: atualiza dados do usuário (alias para update_user, imediato)."""
        await self.update_user(telegram_id, data, immediate=True)

    async def set_user_state(self, telegram_id: int, state: str, immediate: bool = False):
        """Define o estado de um usuário."""
        await self.update_user(telegram_id, {"state": state}, immediate)

    async def update_user_state(self, telegram_id: int, state: str):
        """Wrapper: atualiza estado do usuário (alias para set_user_state, imediato)."""
        await self.set_user_state(telegram_id, state, immediate=True)

    async def batch_update_user_data(self, telegram_id: int, updates: List[Dict[str, Any]]):
        """Executa múltiplas atualizações em uma única operação batch."""
        # Mescla todas as atualizações
        merged_data = {}
        for update in updates:
            merged_data.update(update)
            
        await self.update_user(telegram_id, merged_data, immediate=True)

    async def update_user_context(self, telegram_id: int, context_data: dict):
        """Atualiza o contexto de um usuário."""
        await self.update_user(telegram_id, {"context_data": context_data})

    async def clear_user_context(self, telegram_id: int):
        """Limpa o contexto de um usuário."""
        await self.update_user_context(telegram_id, {})

    async def update_user_onboarding_state(self, telegram_id: int, onboarding_state: str):
        """Atualiza o estado do onboarding de um usuário."""
        await self.update_user(telegram_id, {"onboarding_state": onboarding_state})
    
    async def get_user_state(self, telegram_id: int) -> str:
        """Obtém o estado atual de um usuário."""
        try:
            user = await self.get_user(telegram_id)
            return user.state if user and hasattr(user, 'state') else "INITIAL"
        except Exception as e:
            self.logger.error(f"Error getting user state {telegram_id}: {e}")
            return "INITIAL"

    async def get_user_by_codename(self, codename: str) -> User | None:
        """Busca um usuário pelo codinome."""
        try:
            user_data = await self.firebase_service.get_user_by_codename(codename)
            return User.from_dict(user_data) if user_data else None
        except Exception as e:
            self.logger.error(f"Error getting user by codename {codename}: {e}")
            return None

    async def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Wrapper: retorna o perfil do usuário (objeto User)."""
        return await self.get_user(telegram_id)
            
    async def flush_pending_updates(self, user_id: int = None):
        """Força a execução de todas as operações pendentes."""
        await self.batch_service.flush_user_updates(user_id)
        
    async def _schedule_auto_flush(self):
        """Agenda um auto-flush automático se não estiver rodando."""
        if self._auto_flush_task is None or self._auto_flush_task.done():
            self._auto_flush_task = asyncio.create_task(self._auto_flush_after_delay())
    
    async def _auto_flush_after_delay(self):
        """Executa flush automático após delay."""
        try:
            await asyncio.sleep(self._auto_flush_delay)
            pending_count = await self.batch_service.get_pending_operations_count()
            if pending_count > 0:
                await self.batch_service.flush_user_updates()
                self.logger.info(f"Auto-flush executado para {pending_count} operações pendentes")
        except Exception as e:
            self.logger.error(f"Erro no auto-flush: {e}")
        
    async def _update_local_cache(self, telegram_id: int, data: Dict[str, Any]):
        """Atualiza o cache local com novos dados."""
        async with self._cache_lock:
            if telegram_id in self._user_cache:
                user = self._user_cache[telegram_id]
                # Atualiza os campos do usuário no cache
                for key, value in data.items():
                    if '.' in key:
                        # Lida com campos aninhados (ex: 'profile.onboarded')
                        parts = key.split('.')
                        obj = user
                        # Navega até o objeto pai
                        for part in parts[:-1]:
                            if hasattr(obj, part):
                                attr = getattr(obj, part)
                                # Se o atributo for um dicionário, converte para objeto
                                if isinstance(attr, dict):
                                    if part == 'profile':
                                        from models.firebase_models import Profile
                                        setattr(obj, part, Profile(**attr))
                                    elif part == 'agreements':
                                        from models.firebase_models import Agreements
                                        setattr(obj, part, Agreements(**attr))
                                    elif part == 'monetization':
                                        from models.firebase_models import Monetization
                                        setattr(obj, part, Monetization(**attr))
                                obj = getattr(obj, part)
                            else:
                                break
                        else:
                            # Define o valor no campo final
                            if hasattr(obj, parts[-1]):
                                setattr(obj, parts[-1], value)
                    else:
                        # Campo simples
                        if hasattr(user, key):
                            setattr(user, key, value)
                            # Se o campo for um sub-objeto que pode ser dicionário, converte
                            if key == 'profile' and isinstance(value, dict):
                                from models.firebase_models import Profile
                                setattr(user, key, Profile(**value))
                            elif key == 'agreements' and isinstance(value, dict):
                                from models.firebase_models import Agreements
                                setattr(user, key, Agreements(**value))
                            elif key == 'monetization' and isinstance(value, dict):
                                from models.firebase_models import Monetization
                                setattr(user, key, Monetization(**value))
                        
    async def clear_cache(self, telegram_id: int = None):
        """Limpa o cache local."""
        async with self._cache_lock:
            if telegram_id:
                self._user_cache.pop(telegram_id, None)
            else:
                self._user_cache.clear()
                
    async def get_cache_size(self) -> int:
        """Retorna o tamanho do cache local."""
        async with self._cache_lock:
            return len(self._user_cache)