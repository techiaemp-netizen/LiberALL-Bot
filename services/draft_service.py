"""
Serviço para gerenciar rascunhos de posts.
Implementa persistência temporária de rascunhos antes da publicação final.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from firebase_admin import firestore
import uuid

logger = logging.getLogger(__name__)

class DraftService:
    """Serviço para gerenciar rascunhos de posts."""
    
    def __init__(self, firebase_service=None):
        if firebase_service:
            self.db = firebase_service.db
        else:
            self.db = firestore.client()
        
        # Coleção do Firestore para rascunhos
        self.drafts_collection = 'drafts'
        
        # Tempo de expiração dos rascunhos (24 horas)
        self.expiration_hours = 24
    
    async def save_draft(self, user_id: int, draft_data: Dict) -> str:
        """
        Salva um rascunho de post.
        
        Args:
            user_id: ID do usuário
            draft_data: Dados do rascunho
            
        Returns:
            str: ID do rascunho criado
        """
        try:
            # Gerar ID único para o rascunho
            draft_id = str(uuid.uuid4())
            
            # Preparar dados do rascunho
            now = datetime.now()
            expires_at = now + timedelta(hours=self.expiration_hours)
            
            complete_draft_data = {
                'id': draft_id,
                'user_id': user_id,
                'title': draft_data.get('title', ''),
                'description': draft_data.get('description', ''),
                'type': draft_data.get('type', 'text'),
                'media_files': draft_data.get('media_files', []),
                'media_urls': draft_data.get('media_urls', []),
                'monetization': draft_data.get('monetization', {}),
                'is_monetized': draft_data.get('is_monetized', False),
                'price': draft_data.get('price', 0.0),
                'created_at': now,
                'expires_at': expires_at,
                'status': 'draft'
            }
            
            # Salvar no Firestore
            draft_ref = self.db.collection(self.drafts_collection).document(draft_id)
            draft_ref.set(complete_draft_data)
            
            logger.info(f"Rascunho salvo: {draft_id} para usuário {user_id}")
            return draft_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar rascunho: {e}")
            return None
    
    async def get_draft(self, user_id: int, draft_id: str) -> Optional[Dict]:
        """
        Obtém um rascunho por ID.
        
        Args:
            user_id: ID do usuário (para validação)
            draft_id: ID do rascunho
            
        Returns:
            Dict: Dados do rascunho ou None se não encontrado/expirado
        """
        try:
            draft_ref = self.db.collection(self.drafts_collection).document(draft_id)
            draft_doc = draft_ref.get()
            
            if not draft_doc.exists:
                logger.warning(f"Rascunho não encontrado: {draft_id}")
                return None
            
            draft_data = draft_doc.to_dict()
            
            # Verificar se o rascunho pertence ao usuário
            if draft_data.get('user_id') != user_id:
                logger.warning(f"Rascunho {draft_id} não pertence ao usuário {user_id}")
                return None
            
            # Verificar se o rascunho não expirou
            expires_at = draft_data.get('expires_at')
            if expires_at and expires_at < datetime.now():
                logger.info(f"Rascunho expirado: {draft_id}")
                # Remover rascunho expirado
                await self.delete_draft(user_id, draft_id)
                return None
            
            logger.info(f"Rascunho obtido: {draft_id}")
            return draft_data
            
        except Exception as e:
            logger.error(f"Erro ao obter rascunho {draft_id}: {e}")
            return None
    
    async def delete_draft(self, user_id: int, draft_id: str) -> bool:
        """
        Remove um rascunho.
        
        Args:
            user_id: ID do usuário (para validação)
            draft_id: ID do rascunho
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            # Verificar se o rascunho existe e pertence ao usuário
            draft_data = await self.get_draft(user_id, draft_id)
            if not draft_data:
                return False
            
            # Remover do Firestore
            draft_ref = self.db.collection(self.drafts_collection).document(draft_id)
            draft_ref.delete()
            
            logger.info(f"Rascunho removido: {draft_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover rascunho {draft_id}: {e}")
            return False
    
    async def get_user_drafts(self, user_id: int, limit: int = 10) -> list:
        """
        Obtém todos os rascunhos de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de rascunhos retornados
            
        Returns:
            List[Dict]: Lista de rascunhos do usuário
        """
        try:
            drafts_query = self.db.collection(self.drafts_collection)\
                .where('user_id', '==', user_id)\
                .where('status', '==', 'draft')\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            drafts = drafts_query.get()
            
            result = []
            now = datetime.now()
            
            for draft_doc in drafts:
                draft_data = draft_doc.to_dict()
                
                # Verificar se não expirou
                expires_at = draft_data.get('expires_at')
                if expires_at and expires_at < now:
                    # Remover rascunho expirado
                    await self.delete_draft(user_id, draft_doc.id)
                    continue
                
                draft_data['id'] = draft_doc.id
                result.append(draft_data)
            
            logger.info(f"Encontrados {len(result)} rascunhos para usuário {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter rascunhos do usuário {user_id}: {e}")
            return []
    
    async def cleanup_expired_drafts(self) -> int:
        """
        Remove todos os rascunhos expirados.
        
        Returns:
            int: Número de rascunhos removidos
        """
        try:
            now = datetime.now()
            
            # Buscar rascunhos expirados
            expired_query = self.db.collection(self.drafts_collection)\
                .where('expires_at', '<', now)\
                .limit(100)  # Processar em lotes
            
            expired_drafts = expired_query.get()
            
            removed_count = 0
            for draft_doc in expired_drafts:
                try:
                    draft_doc.reference.delete()
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Erro ao remover rascunho expirado {draft_doc.id}: {e}")
            
            if removed_count > 0:
                logger.info(f"Removidos {removed_count} rascunhos expirados")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro ao limpar rascunhos expirados: {e}")
            return 0
    
    async def update_draft(self, user_id: int, draft_id: str, updates: Dict) -> bool:
        """
        Atualiza um rascunho existente.
        
        Args:
            user_id: ID do usuário
            draft_id: ID do rascunho
            updates: Dados para atualizar
            
        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            # Verificar se o rascunho existe e pertence ao usuário
            draft_data = await self.get_draft(user_id, draft_id)
            if not draft_data:
                return False
            
            # Adicionar timestamp de atualização
            updates['updated_at'] = datetime.now()
            
            # Atualizar no Firestore
            draft_ref = self.db.collection(self.drafts_collection).document(draft_id)
            draft_ref.update(updates)
            
            logger.info(f"Rascunho atualizado: {draft_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar rascunho {draft_id}: {e}")
            return False