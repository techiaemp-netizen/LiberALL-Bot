"""
Repositório de rascunhos com TTL curto (2 horas).
Integra com FirebaseService/Firestore para persistência temporária de previews.

Uso previsto:
- Salvar/atualizar rascunho durante a construção de prévia.
- Recuperar rascunho por draft_id para publicar/cancelar.
- Limpar rascunhos expirados automaticamente via verificação na leitura.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

try:
    from firebase_admin import firestore
except Exception:
    firestore = None

from services.firebase_service import FirebaseService

logger = logging.getLogger(__name__)


class DraftRepo:
    """Camada simples de acesso a dados para rascunhos com TTL de 2h."""

    def __init__(self, firebase_service: Optional[FirebaseService] = None):
        # Usar cliente Firestore do FirebaseService se fornecido; caso contrário, tentar firestore.client()
        if firebase_service:
            self.db = firebase_service.db
        else:
            if firestore is None:
                raise RuntimeError("Firestore não disponível; inicialize FirebaseService antes de usar DraftRepo.")
            self.db = firestore.client()

        self.collection = "drafts"
        self.ttl_hours = 2

    def _is_expired(self, draft_data: Dict[str, Any]) -> bool:
        expires_at = draft_data.get("expires_at")
        if not expires_at:
            return False
        
        # Converter timestamp do Firebase para datetime se necessário
        if hasattr(expires_at, 'timestamp'):
            # É um objeto Timestamp do Firebase, converter para datetime
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        elif hasattr(expires_at, 'tzinfo'):
            # É um datetime, verificar se tem timezone
            if expires_at.tzinfo is None:
                # Assumir UTC se não tiver timezone
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        else:
            # Caso seja string ou outro formato, tentar converter
            try:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                else:
                    # Se for timestamp numérico
                    expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            except (ValueError, TypeError):
                logger.warning(f"Formato de expires_at não reconhecido: {type(expires_at)} - {expires_at}")
                return False
        
        # Sempre usar datetime com timezone UTC para comparação
        now = datetime.now(timezone.utc)
        return expires_at < now

    async def create_or_update(self, user_id: int, draft_id: Optional[str], data: Dict[str, Any]) -> str:
        """Cria ou atualiza um rascunho com TTL de 2h.

        Args:
            user_id: ID do usuário dono do rascunho
            draft_id: ID do rascunho (se None, gera novo)
            data: conteúdo do rascunho (title, description, media_files, monetization, etc.)

        Returns:
            str: draft_id persistido
        """
        try:
            if not draft_id:
                draft_id = str(uuid.uuid4())

            # Usar datetime com timezone UTC para consistência
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=self.ttl_hours)

            payload = {
                "id": draft_id,
                "user_id": user_id,
                "data": data,
                "created_at": data.get("created_at") or now,
                "updated_at": now,
                "expires_at": expires_at,
                "status": "active",
            }

            ref = self.db.collection(self.collection).document(draft_id)
            ref.set(payload)
            logger.info(f"Draft salvo/atualizado: {draft_id} para user {user_id}")
            return draft_id
        except Exception as e:
            logger.error(f"Erro ao salvar draft: {e}", exc_info=True)
            raise

    async def get(self, user_id: int, draft_id: str) -> Optional[Dict[str, Any]]:
        """Obtém rascunho por ID, valida dono e TTL; se expirado, apaga."""
        try:
            ref = self.db.collection(self.collection).document(draft_id)
            doc = ref.get()
            if not doc.exists:
                return None
            data = doc.to_dict()
            if data.get("user_id") != user_id:
                logger.warning(f"Draft {draft_id} não pertence ao user {user_id}")
                return None
            if self._is_expired(data):
                logger.info(f"Draft expirado {draft_id}; removendo.")
                try:
                    ref.delete()
                except Exception:
                    logger.warning(f"Falha ao excluir draft expirado {draft_id}")
                return None
            return data
        except Exception as e:
            logger.error(f"Erro ao obter draft {draft_id}: {e}", exc_info=True)
            return None

    async def delete(self, user_id: int, draft_id: str) -> bool:
        """Exclui rascunho se pertencer ao usuário."""
        try:
            ref = self.db.collection(self.collection).document(draft_id)
            doc = ref.get()
            if not doc.exists:
                return True
            data = doc.to_dict()
            if data.get("user_id") != user_id:
                logger.warning(f"Tentativa de excluir draft de outro usuário {draft_id} por {user_id}")
                return False
            ref.delete()
            logger.info(f"Draft excluído {draft_id} por user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao excluir draft {draft_id}: {e}", exc_info=True)
            return False

    async def cleanup_expired(self, batch_limit: int = 100) -> int:
        """Remove rascunhos expirados. Retorna quantidade removida."""
        try:
            now = datetime.now()
            query = (
                self.db.collection(self.collection)
                .where("expires_at", "<", now)
                .limit(batch_limit)
            )
            docs = query.get()
            removed = 0
            for doc in docs:
                try:
                    doc.reference.delete()
                    removed += 1
                except Exception:
                    logger.warning(f"Falha ao excluir draft expirado {doc.id}")
            if removed:
                logger.info(f"Limpeza de rascunhos expirados: {removed} removidos")
            return removed
        except Exception as e:
            logger.error(f"Erro em cleanup_expired: {e}", exc_info=True)
            return 0