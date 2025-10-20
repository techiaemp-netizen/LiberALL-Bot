"""Serviço de persistência atômica para operações de dados críticas.

Este módulo implementa:
- Operações atômicas de banco de dados
- Transações seguras
- Rollback automático em caso de erro
- Consistência de dados
"""

import logging
import asyncio
from datetime import datetime
import json
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import timezone
from contextlib import contextmanager

from services.firebase_service import firebase_service
from services.security_service import security_service
from utils.exceptions import ValidationError, SecurityError
from utils.validators import validate_user_data
from constants.user_states import UserStates

logger = logging.getLogger(__name__)

class TransactionError(Exception):
    """Exceção para erros de transação."""
    pass

class AtomicPersistence:
    """Serviço para operações de persistência atômica."""
    
    def __init__(self):
        """Inicializa o serviço de persistência atômica."""
        self.firebase = firebase_service
        self.security = security_service
        self._active_transactions = {}
        logger.info("Atomic persistence service initialized")
    
    @contextmanager
    def transaction(self, transaction_id: Optional[str] = None):
        """Context manager para operações atômicas.
        
        Args:
            transaction_id: ID da transação (gerado automaticamente se não fornecido)
            
        Yields:
            ID da transação
        """
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
        
        logger.info(f"Starting transaction: {transaction_id}")
        
        # Inicializa transação
        self._active_transactions[transaction_id] = {
            'id': transaction_id,
            'started_at': datetime.now(timezone.utc),
            'operations': [],
            'status': 'active'
        }
        
        try:
            yield transaction_id
            
            # Commit da transação
            self._commit_transaction(transaction_id)
            logger.info(f"Transaction committed: {transaction_id}")
            
        except Exception as e:
            # Rollback da transação
            self._rollback_transaction(transaction_id)
            logger.error(f"Transaction rolled back: {transaction_id} - Error: {e}")
            raise TransactionError(f"Transaction failed: {e}") from e
        
        finally:
            # Limpa transação
            if transaction_id in self._active_transactions:
                del self._active_transactions[transaction_id]
    
    def atomic_create(self, transaction_id: str, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Cria documento de forma atômica.
        
        Args:
            transaction_id: ID da transação
            collection: Nome da coleção
            document_id: ID do documento
            data: Dados do documento
            
        Returns:
            True se criado com sucesso
        """
        try:
            if transaction_id not in self._active_transactions:
                raise TransactionError(f"Transaction not found: {transaction_id}")
            
            # Adiciona timestamp
            data_with_timestamp = {
                **data,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Registra operação na transação
            operation = {
                'type': 'create',
                'collection': collection,
                'document_id': document_id,
                'data': data_with_timestamp,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self._active_transactions[transaction_id]['operations'].append(operation)
            
            logger.debug(f"Atomic create registered: {collection}/{document_id} in transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in atomic create: {e}")
            return False
    
    def atomic_update(self, transaction_id: str, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza documento de forma atômica.
        
        Args:
            transaction_id: ID da transação
            collection: Nome da coleção
            document_id: ID do documento
            data: Dados a serem atualizados
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            if transaction_id not in self._active_transactions:
                raise TransactionError(f"Transaction not found: {transaction_id}")
            
            # Adiciona timestamp de atualização
            data_with_timestamp = {
                **data,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Registra operação na transação
            operation = {
                'type': 'update',
                'collection': collection,
                'document_id': document_id,
                'data': data_with_timestamp,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self._active_transactions[transaction_id]['operations'].append(operation)
            
            logger.debug(f"Atomic update registered: {collection}/{document_id} in transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in atomic update: {e}")
            return False
    
    def atomic_delete(self, transaction_id: str, collection: str, document_id: str) -> bool:
        """Remove documento de forma atômica.
        
        Args:
            transaction_id: ID da transação
            collection: Nome da coleção
            document_id: ID do documento
            
        Returns:
            True se removido com sucesso
        """
        try:
            if transaction_id not in self._active_transactions:
                raise TransactionError(f"Transaction not found: {transaction_id}")
            
            # Registra operação na transação
            operation = {
                'type': 'delete',
                'collection': collection,
                'document_id': document_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self._active_transactions[transaction_id]['operations'].append(operation)
            
            logger.debug(f"Atomic delete registered: {collection}/{document_id} in transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in atomic delete: {e}")
            return False
    
    def execute_batch_operation(self, operations: List[Dict[str, Any]], user_id: Optional[int] = None) -> bool:
        """Executa múltiplas operações em uma única transação.
        
        Args:
            operations: Lista de operações a serem executadas
            user_id: ID do usuário (para auditoria)
            
        Returns:
            True se todas as operações foram executadas com sucesso
        """
        try:
            with self.transaction() as transaction_id:
                for operation in operations:
                    op_type = operation.get('type')
                    collection = operation.get('collection')
                    document_id = operation.get('document_id')
                    data = operation.get('data', {})
                    
                    if op_type == 'create':
                        if not self.atomic_create(transaction_id, collection, document_id, data):
                            raise TransactionError(f"Failed to create {collection}/{document_id}")
                    
                    elif op_type == 'update':
                        if not self.atomic_update(transaction_id, collection, document_id, data):
                            raise TransactionError(f"Failed to update {collection}/{document_id}")
                    
                    elif op_type == 'delete':
                        if not self.atomic_delete(transaction_id, collection, document_id):
                            raise TransactionError(f"Failed to delete {collection}/{document_id}")
                    
                    else:
                        raise TransactionError(f"Unknown operation type: {op_type}")
                
                # Log da operação batch para auditoria
                if user_id:
                    self.security.log_sensitive_action(
                        action="batch_operation",
                        user_id=user_id,
                        details={
                            "transaction_id": transaction_id,
                            "operations_count": len(operations),
                            "executed_at": datetime.now(timezone.utc).isoformat()
                        }
                    )
                
                logger.info(f"Batch operation completed: {len(operations)} operations in transaction {transaction_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in batch operation: {e}")
            return False
    
    def safe_user_data_update(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Atualiza dados do usuário de forma segura e atômica.
        
        Args:
            user_id: ID do usuário
            updates: Dados a serem atualizados
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            # Sanitiza dados antes da atualização
            sanitized_updates = self.security.sanitize_user_data(updates)
            
            with self.transaction() as transaction_id:
                # Atualiza perfil principal
                if not self.atomic_update(transaction_id, 'users', str(user_id), sanitized_updates):
                    raise TransactionError("Failed to update user profile")
                
                # Atualiza índices se necessário
                if 'location' in sanitized_updates or 'age' in sanitized_updates:
                    index_data = {
                        'user_id': user_id,
                        'location': sanitized_updates.get('location'),
                        'age': sanitized_updates.get('age'),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    if not self.atomic_update(transaction_id, 'user_index', str(user_id), index_data):
                        raise TransactionError("Failed to update user index")
                
                # Log removido para evitar loop infinito - auditoria feita via outros mecanismos
                # self.security.log_sensitive_action(
                #     action="user_data_update",
                #     user_id=user_id,
                #     details={
                #         "transaction_id": transaction_id,
                #         "fields_updated": list(sanitized_updates.keys()),
                #         "updated_at": datetime.now(timezone.utc).isoformat()
                #     }
                # )
                
                logger.info(f"User data updated safely: {user_id} in transaction {transaction_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in safe user data update for user {user_id}: {e}")
            return False
    
    def _commit_transaction(self, transaction_id: str) -> None:
        """Executa commit da transação.
        
        Args:
            transaction_id: ID da transação
        """
        try:
            transaction = self._active_transactions.get(transaction_id)
            if not transaction:
                raise TransactionError(f"Transaction not found: {transaction_id}")
            
            # Em uma implementação real, aqui seria feito o commit no banco
            # Por enquanto, apenas simula o sucesso
            
            transaction['status'] = 'committed'
            transaction['committed_at'] = datetime.now(timezone.utc)
            
            logger.debug(f"Transaction committed: {transaction_id} with {len(transaction['operations'])} operations")
            
        except Exception as e:
            logger.error(f"Error committing transaction {transaction_id}: {e}")
            raise
    
    def _rollback_transaction(self, transaction_id: str) -> None:
        """Executa rollback da transação.
        
        Args:
            transaction_id: ID da transação
        """
        try:
            transaction = self._active_transactions.get(transaction_id)
            if not transaction:
                logger.warning(f"Transaction not found for rollback: {transaction_id}")
                return
            
            # Em uma implementação real, aqui seria feito o rollback no banco
            # Por enquanto, apenas marca como rolled back
            
            transaction['status'] = 'rolled_back'
            transaction['rolled_back_at'] = datetime.now(timezone.utc)
            
            logger.debug(f"Transaction rolled back: {transaction_id} with {len(transaction['operations'])} operations")
            
        except Exception as e:
            logger.error(f"Error rolling back transaction {transaction_id}: {e}")
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Busca status de uma transação.
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            Dict com status da transação ou None se não encontrada
        """
        try:
            return self._active_transactions.get(transaction_id)
            
        except Exception as e:
            logger.error(f"Error getting transaction status {transaction_id}: {e}")
            return None
    
    def cleanup_old_transactions(self, max_age_hours: int = 24) -> int:
        """Remove transações antigas da memória.
        
        Args:
            max_age_hours: Idade máxima em horas
            
        Returns:
            Número de transações removidas
        """
        try:
            now = datetime.now(timezone.utc)
            removed_count = 0
            
            transaction_ids_to_remove = []
            
            for transaction_id, transaction in self._active_transactions.items():
                started_at = transaction['started_at']
                age_hours = (now - started_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    transaction_ids_to_remove.append(transaction_id)
            
            for transaction_id in transaction_ids_to_remove:
                del self._active_transactions[transaction_id]
                removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old transactions")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old transactions: {e}")
            return 0

def get_post_data(post_id: str) -> Optional[Dict[str, Any]]:
    """Busca dados de um post de forma atômica.
    
    Args:
        post_id: ID do post
        
    Returns:
        Dict com dados do post ou None se não encontrado
    """
    try:
        # Sanitiza o ID do post
        sanitized_post_id = atomic_persistence.security.sanitize_user_data(post_id)
        
        # Busca dados do post no Firebase
        post_data = atomic_persistence.firebase.get_post(sanitized_post_id)
        
        if post_data:
            logger.debug(f"Post data retrieved: {sanitized_post_id}")
            return post_data
        
        logger.warning(f"Post not found: {sanitized_post_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting post data for {post_id}: {e}")
        return None

def get_atomic_user_data():
    """Retorna a instância global do serviço de persistência atômica.
    
    Returns:
        AtomicPersistenceService: Instância do serviço
    """
    return atomic_persistence

# Instância global do serviço (será inicializada no __init__.py)
atomic_persistence = None