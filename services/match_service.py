"""
Serviço para gerenciar matches entre usuários e posts.
Implementa toda a lógica de criação, remoção e consulta de matches.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import firebase_admin
from firebase_admin import firestore
import uuid

logger = logging.getLogger(__name__)

class MatchService:
    """Serviço para gerenciar matches."""
    
    def __init__(self, firebase_service=None):
        self.firebase_service = firebase_service
        self.db = None
        self.simulation_mode = False
        
        try:
            # Usar instância do Firebase se fornecida e inicializada
            if self.firebase_service and getattr(self.firebase_service, 'db', None):
                self.db = self.firebase_service.db
            else:
                # Tentar usar cliente Firestore se app estiver inicializado
                if firebase_admin._apps:
                    self.db = firestore.client()
                else:
                    self.simulation_mode = True
        except Exception as e:
            logger.warning(f"Falha ao inicializar Firestore no MatchService: {e}")
            self.db = None
            self.simulation_mode = True
        
        # Coleções do Firestore
        self.matches_collection = 'matches'
        self.posts_collection = 'posts'
        self.users_collection = 'users'
        
        # Estruturas em memória para simulação
        if self.simulation_mode or not self.db:
            self._sim_matches = {}  # key: (user_id, post_id) -> data
    
    async def create_match(self, user_id: int, post_id: str) -> Optional[str]:
        """
        Cria um match entre usuário e post.
        
        Args:
            user_id: ID do usuário que está dando match
            post_id: ID do post
            
        Returns:
            str: ID do match criado ou None se houve erro
        """
        try:
            # Caminho de simulação/in-memory
            if self.simulation_mode or not self.db:
                key = (user_id, post_id)
                existing = self._sim_matches.get(key)
                if existing and existing.get('status') == 'active':
                    logger.warning(f"Match já existe entre usuário {user_id} e post {post_id}")
                    return None
                match_id = str(uuid.uuid4())
                self._sim_matches[key] = {
                    'id': match_id,
                    'user_id': user_id,
                    'post_id': post_id,
                    'created_at': datetime.now(),
                    'status': 'active'
                }
                await self._log_user_activity(user_id, 'match_created', {
                    'match_id': match_id,
                    'post_id': post_id
                })
                logger.info(f"[SIM] Match criado: {match_id} entre usuário {user_id} e post {post_id}")
                return match_id

            # Verificar se já existe match
            if await self.is_matched(user_id, post_id):
                logger.warning(f"Match já existe entre usuário {user_id} e post {post_id}")
                return None
            
            # Verificar se o usuário não está tentando dar match no próprio post
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                logger.error(f"Post não encontrado: {post_id}")
                return None
            
            post_data = post_doc.to_dict()
            if post_data.get('creator_id') == user_id:
                logger.warning(f"Usuário {user_id} tentou dar match no próprio post {post_id}")
                return None
            
            # Gerar ID único para o match
            match_id = str(uuid.uuid4())
            
            # Criar documento de match
            match_data = {
                'id': match_id,
                'user_id': user_id,
                'post_id': post_id,
                'creator_id': post_data.get('creator_id'),
                'created_at': datetime.now(),
                'status': 'active',
                'type': 'like'  # Pode ser expandido para outros tipos
            }
            
            # Usar transação para garantir consistência
            transaction = self.db.transaction()
            
            @firestore.transactional
            def create_match_transaction(transaction):
                # Criar match
                match_ref = self.db.collection(self.matches_collection).document(match_id)
                transaction.set(match_ref, match_data)
                
                # Incrementar contador no post
                transaction.update(post_ref, {
                    'match_count': firestore.Increment(1),
                    'updated_at': datetime.now()
                })
                
                return match_id
            
            result_id = create_match_transaction(transaction)
            
            logger.info(f"Match criado: {match_id} entre usuário {user_id} e post {post_id}")
            
            # Registrar atividade do usuário
            await self._log_user_activity(user_id, 'match_created', {
                'match_id': match_id,
                'post_id': post_id,
                'creator_id': post_data.get('creator_id')
            })
            
            return result_id
            
        except Exception as e:
            logger.error(f"Erro ao criar match: {e}")
            return None
    
    async def remove_match(self, user_id: int, post_id: str) -> bool:
        """
        Remove um match existente.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se o match foi removido com sucesso
        """
        try:
            # Caminho de simulação/in-memory
            if self.simulation_mode or not self.db:
                key = (user_id, post_id)
                data = self._sim_matches.get(key)
                if not data or data.get('status') != 'active':
                    logger.warning(f"[SIM] Match não encontrado entre usuário {user_id} e post {post_id}")
                    return False
                data['status'] = 'removed'
                data['removed_at'] = datetime.now()
                await self._log_user_activity(user_id, 'match_removed', {'post_id': post_id})
                logger.info(f"[SIM] Match removido: user_id={user_id}, post_id={post_id}")
                return True

            # Buscar o match ativo
            matches_query = self.db.collection(self.matches_collection)\
                .where('user_id', '==', user_id)\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .limit(1)
            
            matches = matches_query.get()
            
            if not matches:
                logger.warning(f"Match não encontrado entre usuário {user_id} e post {post_id}")
                return False
            
            match_doc = matches[0]
            match_ref = match_doc.reference
            
            # Usar transação para garantir consistência
            transaction = self.db.transaction()
            
            @firestore.transactional
            def remove_match_transaction(transaction):
                # Marcar match como removido
                transaction.update(match_ref, {
                    'status': 'removed',
                    'removed_at': datetime.now()
                })
                
                # Decrementar contador no post
                post_ref = self.db.collection(self.posts_collection).document(post_id)
                transaction.update(post_ref, {
                    'match_count': firestore.Increment(-1),
                    'updated_at': datetime.now()
                })
            
            remove_match_transaction(transaction)
            
            logger.info(f"Match removido entre usuário {user_id} e post {post_id}")
            
            # Registrar atividade
            await self._log_user_activity(user_id, 'match_removed', {
                'match_id': match_doc.id,
                'post_id': post_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover match: {e}")
            return False
    
    async def is_matched(self, user_id: int, post_id: str) -> bool:
        """
        Verifica se existe um match ativo entre usuário e post.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se existe match ativo
        """
        try:
            # Caminho de simulação/in-memory
            if self.simulation_mode or not self.db:
                data = self._sim_matches.get((user_id, post_id))
                return bool(data and data.get('status') == 'active')

            matches_query = self.db.collection(self.matches_collection)\
                .where('user_id', '==', user_id)\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .limit(1)
            
            matches = matches_query.get()
            return len(matches) > 0
            
        except Exception as e:
            logger.error(f"Erro ao verificar match: {e}")
            return False
    
    async def get_user_matches(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Obtém matches de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de matches a retornar
            
        Returns:
            List[Dict]: Lista de matches com dados dos posts
        """
        try:
            # Caminho de simulação/in-memory
            if self.simulation_mode or not self.db:
                result = []
                for (u_id, p_id), data in self._sim_matches.items():
                    if u_id != user_id:
                        continue
                    if data.get('status') != 'active':
                        continue
                    # Montar estrutura compatível
                    item = {
                        'id': data.get('id'),
                        'user_id': user_id,
                        'post_id': p_id,
                        'created_at': data.get('created_at'),
                        'status': 'active',
                        'post': {
                            'id': p_id,
                            'title': 'Post (simulado)',
                            'type': 'unknown',
                            'status': 'simulated'
                        }
                    }
                    result.append(item)
                    if len(result) >= limit:
                        break
                logger.info(f"[SIM] Obtidos {len(result)} matches para usuário {user_id}")
                return result

            matches_query = self.db.collection(self.matches_collection)\
                .where('user_id', '==', user_id)\
                .where('status', '==', 'active')\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            matches = matches_query.get()
            
            result = []
            for match_doc in matches:
                match_data = match_doc.to_dict()
                match_data['id'] = match_doc.id
                
                # Enriquecer com dados do post
                post_id = match_data['post_id']
                post_summary = await self._get_post_summary(post_id)
                match_data['post'] = post_summary
                
                result.append(match_data)
            
            logger.info(f"Obtidos {len(result)} matches para usuário {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter matches do usuário {user_id}: {e}")
            return []
    
    async def get_post_matches(self, post_id: str, limit: int = 50) -> List[Dict]:
        """
        Obtém matches de um post.
        
        Args:
            post_id: ID do post
            limit: Limite de matches a retornar
            
        Returns:
            List[Dict]: Lista de matches com dados dos usuários (anônimos)
        """
        try:
            matches_query = self.db.collection(self.matches_collection)\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            matches = matches_query.get()
            
            result = []
            for match_doc in matches:
                match_data = match_doc.to_dict()
                match_data['id'] = match_doc.id
                
                # Enriquecer com dados anônimos do usuário
                user_id = match_data['user_id']
                user_summary = await self._get_user_summary(user_id)
                match_data['user'] = user_summary
                
                result.append(match_data)
            
            logger.info(f"Obtidos {len(result)} matches para post {post_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter matches do post {post_id}: {e}")
            return []
    
    async def get_match_statistics(self, user_id: int) -> Dict:
        """
        Obtém estatísticas de matches de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict: Estatísticas de matches
        """
        try:
            # Matches dados pelo usuário
            given_matches_query = self.db.collection(self.matches_collection)\
                .where('user_id', '==', user_id)\
                .where('status', '==', 'active')
            
            given_matches = given_matches_query.get()
            
            # Matches recebidos nos posts do usuário
            received_matches_query = self.db.collection(self.matches_collection)\
                .where('creator_id', '==', user_id)\
                .where('status', '==', 'active')
            
            received_matches = received_matches_query.get()
            
            # Calcular estatísticas por período
            now = datetime.now()
            
            def count_matches_by_period(matches, hours):
                cutoff = now - timedelta(hours=hours)
                return len([
                    match for match in matches 
                    if match.to_dict().get('created_at', datetime.min) >= cutoff
                ])
            
            stats = {
                'user_id': user_id,
                'matches_given': {
                    'total': len(given_matches),
                    'today': count_matches_by_period(given_matches, 24),
                    'week': count_matches_by_period(given_matches, 168),
                    'month': count_matches_by_period(given_matches, 720)
                },
                'matches_received': {
                    'total': len(received_matches),
                    'today': count_matches_by_period(received_matches, 24),
                    'week': count_matches_by_period(received_matches, 168),
                    'month': count_matches_by_period(received_matches, 720)
                }
            }
            
            # Calcular taxa de match (matches recebidos / posts criados)
            user_posts_query = self.db.collection(self.posts_collection)\
                .where('creator_id', '==', user_id)\
                .where('status', '==', 'active')
            
            user_posts = user_posts_query.get()
            total_posts = len(user_posts)
            
            if total_posts > 0:
                stats['match_rate'] = (stats['matches_received']['total'] / total_posts) * 100
            else:
                stats['match_rate'] = 0.0
            
            logger.info(f"Estatísticas calculadas para usuário {user_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de matches do usuário {user_id}: {e}")
            return {}
    
    async def get_mutual_matches(self, user_id: int) -> List[Dict]:
        """
        Obtém matches mútuos (quando dois usuários deram match nos posts um do outro).
        
        Args:
            user_id: ID do usuário
            
        Returns:
            List[Dict]: Lista de matches mútuos
        """
        try:
            # Buscar usuários que deram match nos posts do usuário atual
            received_matches_query = self.db.collection(self.matches_collection)\
                .where('creator_id', '==', user_id)\
                .where('status', '==', 'active')
            
            received_matches = received_matches_query.get()
            
            mutual_matches = []
            
            for match_doc in received_matches:
                match_data = match_doc.to_dict()
                other_user_id = match_data['user_id']
                
                # Verificar se o usuário atual também deu match em algum post do outro usuário
                given_match_query = self.db.collection(self.matches_collection)\
                    .where('user_id', '==', user_id)\
                    .where('creator_id', '==', other_user_id)\
                    .where('status', '==', 'active')\
                    .limit(1)
                
                given_matches = given_match_query.get()
                
                if given_matches:
                    # É um match mútuo
                    mutual_match = {
                        'user_id': other_user_id,
                        'received_match': match_data,
                        'given_match': given_matches[0].to_dict(),
                        'user_summary': await self._get_user_summary(other_user_id)
                    }
                    mutual_matches.append(mutual_match)
            
            logger.info(f"Encontrados {len(mutual_matches)} matches mútuos para usuário {user_id}")
            return mutual_matches
            
        except Exception as e:
            logger.error(f"Erro ao obter matches mútuos do usuário {user_id}: {e}")
            return []
    
    async def _get_post_summary(self, post_id: str) -> Dict:
        """Obtém resumo de um post."""
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                return {
                    'id': post_id,
                    'title': 'Post não encontrado',
                    'type': 'unknown',
                    'status': 'not_found'
                }
            
            post_data = post_doc.to_dict()
            
            return {
                'id': post_id,
                'title': post_data.get('title', 'Sem título'),
                'type': post_data.get('type', 'unknown'),
                'created_at': post_data.get('created_at'),
                'view_count': post_data.get('view_count', 0),
                'match_count': post_data.get('match_count', 0),
                'status': post_data.get('status', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo do post {post_id}: {e}")
            return {
                'id': post_id,
                'title': 'Erro ao carregar',
                'type': 'unknown',
                'status': 'error'
            }
    
    async def _get_user_summary(self, user_id: int) -> Dict:
        """Obtém resumo anônimo de um usuário."""
        try:
            # Importação dinâmica para evitar circular import
            from services.user_service import UserService
            
            user_ref = self.db.collection(self.users_collection).document(str(user_id))
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return {
                    'id': user_id,
                    'name': 'Usuário Anônimo',
                    'state': 'Não informado',
                    'profile_type': 'Não informado'
                }
            
            user_data = user_doc.to_dict()
            
            # Retornar dados anônimos
            return {
                'id': user_id,
                'name': user_data.get('name', 'Usuário Anônimo'),
                'state': user_data.get('state', 'Não informado'),
                'profile_type': user_data.get('profile_type', 'Não informado'),
                'is_creator': user_data.get('is_creator', False)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo do usuário {user_id}: {e}")
            return {
                'id': user_id,
                'name': 'Usuário Anônimo',
                'state': 'Não informado',
                'profile_type': 'Não informado'
            }
    
    async def _log_user_activity(self, user_id: int, activity_type: str, metadata: Dict):
        """Registra atividade do usuário."""
        try:
            activity_data = {
                'user_id': user_id,
                'type': activity_type,
                'metadata': metadata,
                'timestamp': datetime.now()
            }
            
            self.db.collection('user_activities').add(activity_data)
            
        except Exception as e:
            logger.error(f"Erro ao registrar atividade do usuário {user_id}: {e}")
    
    async def cleanup_old_matches(self, days_old: int = 365) -> int:
        """
        Remove matches antigos com status 'removed' para otimizar performance.
        
        Args:
            days_old: Idade em dias para considerar matches como antigos
            
        Returns:
            int: Número de matches removidos
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            old_matches_query = self.db.collection(self.matches_collection)\
                .where('status', '==', 'removed')\
                .where('removed_at', '<', cutoff_date)
            
            old_matches = old_matches_query.get()
            
            # Remover em lotes
            batch = self.db.batch()
            count = 0
            
            for match_doc in old_matches:
                batch.delete(match_doc.reference)
                count += 1
                
                # Commit a cada 500 documentos
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # Commit final se houver documentos restantes
            if count % 500 != 0:
                batch.commit()
            
            logger.info(f"Removidos {count} matches antigos")
            return count
            
        except Exception as e:
            logger.error(f"Erro ao limpar matches antigos: {e}")
            return 0