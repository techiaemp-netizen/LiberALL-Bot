from aiogram.types import User as TelegramUser
from services.firebase_service import FirebaseService
from services.security_service import SecurityService
from services.monetization_service import MonetizationService
from models.firebase_models import User
import logging
from typing import Any, Dict, List

class UserService:
    def __init__(self, firebase_service: FirebaseService, security_service: SecurityService, monetization_service: MonetizationService):
        self.firebase_service = firebase_service
        self.security_service = security_service
        self.monetization_service = monetization_service
        self.logger = logging.getLogger(__name__)
        self.logger.info("User service initialized")

    async def get_or_create_user(self, telegram_user: TelegramUser) -> User:
        """Busca um usuário. Se não existir, cria um novo. Sempre retorna um objeto User."""
        user = await self.get_user(telegram_user.id)
        if user:
            return user
        return await self.create_user(telegram_user.id, telegram_user.username)

    async def get_user(self, telegram_id: int) -> User | None:
        """Busca um usuário e retorna um objeto User ou None."""
        try:
            user_data = await self.firebase_service.get_user(telegram_id)
            return User.from_dict(user_data) if user_data else None
        except Exception as e:
            self.logger.error(f"Error getting user {telegram_id}: {e}")
            return None

    async def get_user_data(self, telegram_id: int) -> Dict[str, Any] | None:
        """Wrapper: retorna os dados do usuário como dict, compatível com handlers."""
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
            await self.security_service.log_user_action(telegram_id, 'user_created')
            return new_user
        except Exception as e:
            self.logger.error(f"Error creating user {telegram_id}: {e}")
            raise

    async def update_user(self, telegram_id: int, data: dict):
        """Atualiza os dados de um usuário."""
        await self.firebase_service.update_user(telegram_id, data)
        # Removido log automático de data_update que estava causando loop infinito
        # await self.security_service.log_user_action(telegram_id, 'data_update')

    async def update_user_data(self, telegram_id: int, data: Dict[str, Any]):
        """Wrapper: atualiza dados do usuário (alias para update_user)."""
        await self.update_user(telegram_id, data)

    async def set_user_state(self, telegram_id: int, state: str):
        """Define o estado de um usuário."""
        await self.update_user(telegram_id, {"state": state})

    async def update_user_state(self, telegram_id: int, state: str):
        """Wrapper: atualiza estado do usuário (alias para set_user_state)."""
        await self.set_user_state(telegram_id, state)

    async def update_user_context(self, telegram_id: int, context_data: dict):
        """Atualiza o contexto de um usuário."""
        await self.update_user(telegram_id, {"context_data": context_data})

    async def clear_user_context(self, telegram_id: int):
        """Limpa o contexto de um usuário."""
        await self.update_user_context(telegram_id, {})

    async def update_user_onboarding_state(self, telegram_id: int, onboarding_state: str):
        """Atualiza o estado do onboarding de um usuário."""
        await self.update_user(telegram_id, {"onboarding_state": onboarding_state})

    async def batch_update_user_data(self, telegram_id: int, updates: List[Dict[str, Any]]):
        """Wrapper: aplica uma lista de updates como um único update."""
        try:
            merged: Dict[str, Any] = {}
            for upd in updates:
                if isinstance(upd, dict):
                    merged.update(upd)
            if merged:
                await self.update_user(telegram_id, merged)
        except Exception as e:
            self.logger.error(f"Error batch updating user {telegram_id}: {e}")
    
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