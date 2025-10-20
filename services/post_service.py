"""
Serviço para gerenciar posts.
Implementa toda a lógica de criação, edição, visualização e interação com posts.
Inclui utilitário de publicação para enviar posts aos grupos configurados.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from firebase_admin import firestore
import uuid
import config

logger = logging.getLogger(__name__)

class PostService:
    """Serviço para gerenciar posts."""
    
    def __init__(self, firebase_service=None, bot=None):
        if firebase_service:
            self.db = firebase_service.db
        else:
            self.db = firestore.client()
        
        # Inicializar bot se não fornecido
        if bot:
            self.bot = bot
        else:
            # Criar instância do bot usando o token do ambiente
            import os
            from dotenv import load_dotenv
            from aiogram import Bot
            
            load_dotenv()
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if bot_token:
                self.bot = Bot(token=bot_token)
                logger.info("Bot inicializado automaticamente no PostService")
            else:
                logger.error("TELEGRAM_BOT_TOKEN não encontrado no ambiente")
                self.bot = None
        
        # Coleções do Firestore
        self.posts_collection = 'posts'
        self.users_collection = 'users'
        self.favorites_collection = 'favorites'
        self.views_collection = 'post_views'

        # IDs de grupos (configurados via variáveis de ambiente)
        # Se não configurados, os métodos de publicação usarão fallback seguro
        self.freemium_group_id = getattr(config, 'FREEMIUM_GROUP_ID', None)
        self.premium_group_id = getattr(config, 'PREMIUM_GROUP_ID', None)
    
    async def create_post(self, creator_id: int, post_data: Dict) -> Optional[str]:
        """
        Cria um novo post.
        
        Args:
            creator_id: ID do criador do post
            post_data: Dados do post
            
        Returns:
            str: ID do post criado ou None se houve erro
        """
        try:
            # Validar dados obrigatórios
            required_fields = ['title', 'type']
            for field in required_fields:
                if field not in post_data:
                    logger.error(f"Campo obrigatório ausente: {field}")
                    return None
            
            # Gerar ID único para o post
            post_id = str(uuid.uuid4())
            
            # Preparar dados do post
            now = datetime.now()
            complete_post_data = {
                'id': post_id,
                'creator_id': creator_id,
                'title': post_data['title'],
                'description': post_data.get('description', ''),
                'type': post_data['type'],
                'media_urls': post_data.get('media_urls', []),
                'tags': post_data.get('tags', []),
                'location': post_data.get('location', ''),
                'is_monetized': post_data.get('is_monetized', False),
                'price': post_data.get('price', 0.0),
                'status': 'active',
                'created_at': now,
                'updated_at': now,
                'view_count': 0,
                'match_count': 0,
                'favorite_count': 0,
                'comment_count': 0
            }
            
            # Salvar no Firestore
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_ref.set(complete_post_data)
            
            logger.info(f"Post criado: {post_id} por usuário {creator_id}")
            
            # Registrar atividade do usuário
            await self._log_user_activity(creator_id, 'post_created', {
                'post_id': post_id,
                'post_type': post_data['type'],
                'is_monetized': post_data.get('is_monetized', False)
            })
            
            return post_id
            
        except Exception as e:
            logger.error(f"Erro ao criar post: {e}")
            return None
    
    async def get_post(self, post_id: str, viewer_id: Optional[int] = None) -> Optional[Dict]:
        """
        Obtém um post por ID.
        
        Args:
            post_id: ID do post
            viewer_id: ID do usuário que está visualizando (opcional)
            
        Returns:
            Dict: Dados do post ou None se não encontrado
        """
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                logger.warning(f"Post não encontrado: {post_id}")
                return None
            
            post_data = post_doc.to_dict()
            
            # Verificar se o post está ativo
            if post_data.get('status') != 'active':
                logger.warning(f"Post inativo: {post_id}")
                return None
            
            # Enriquecer com dados do criador
            creator_id = post_data.get('creator_id')
            if creator_id:
                creator_summary = await self._get_creator_summary(creator_id)
                post_data['creator'] = creator_summary
            
            # Registrar visualização se houver viewer_id
            if viewer_id and viewer_id != creator_id:
                await self.record_view(post_id, viewer_id)
            
            logger.info(f"Post obtido: {post_id}")
            return post_data
            
        except Exception as e:
            logger.error(f"Erro ao obter post {post_id}: {e}")
            return None
    
    async def update_post(self, post_id: str, user_id: int, updates: Dict) -> bool:
        """
        Atualiza um post.
        
        Args:
            post_id: ID do post
            user_id: ID do usuário que está atualizando
            updates: Dados a serem atualizados
            
        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                logger.error(f"Post não encontrado: {post_id}")
                return False
            
            post_data = post_doc.to_dict()
            
            # Verificar permissão (apenas o criador pode editar)
            if post_data.get('creator_id') != user_id:
                logger.error(f"Usuário {user_id} não tem permissão para editar post {post_id}")
                return False
            
            # Preparar atualizações
            updates['updated_at'] = datetime.now()
            
            # Atualizar no Firestore
            post_ref.update(updates)
            
            logger.info(f"Post atualizado: {post_id} por usuário {user_id}")
            
            # Registrar atividade
            await self._log_user_activity(user_id, 'post_updated', {
                'post_id': post_id,
                'updated_fields': list(updates.keys())
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar post {post_id}: {e}")
            return False
    
    async def delete_post(self, post_id: str, user_id: int) -> bool:
        """
        Deleta um post (soft delete).
        
        Args:
            post_id: ID do post
            user_id: ID do usuário que está deletando
            
        Returns:
            bool: True se deletado com sucesso
        """
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                logger.error(f"Post não encontrado: {post_id}")
                return False
            
            post_data = post_doc.to_dict()
            
            # Verificar permissão (apenas o criador pode deletar)
            if post_data.get('creator_id') != user_id:
                logger.error(f"Usuário {user_id} não tem permissão para deletar post {post_id}")
                return False
            
            # Soft delete
            post_ref.update({
                'status': 'deleted',
                'deleted_at': datetime.now(),
                'updated_at': datetime.now()
            })
            
            logger.info(f"Post deletado: {post_id} por usuário {user_id}")
            
            # Registrar atividade
            await self._log_user_activity(user_id, 'post_deleted', {
                'post_id': post_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar post {post_id}: {e}")
            return False
    
    async def get_user_posts(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Obtém posts de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de posts a retornar
            
        Returns:
            List[Dict]: Lista de posts do usuário
        """
        try:
            posts_query = self.db.collection(self.posts_collection)\
                .where('creator_id', '==', user_id)\
                .where('status', '==', 'active')\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            posts = posts_query.get()
            
            result = []
            for post_doc in posts:
                post_data = post_doc.to_dict()
                post_data['id'] = post_doc.id
                result.append(post_data)
            
            logger.info(f"Obtidos {len(result)} posts do usuário {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter posts do usuário {user_id}: {e}")
            return []
    
    async def get_recent_posts(self, limit: int = 50, exclude_user_id: Optional[int] = None) -> List[Dict]:
        """
        Obtém posts recentes.
        
        Args:
            limit: Limite de posts a retornar
            exclude_user_id: ID do usuário a excluir dos resultados
            
        Returns:
            List[Dict]: Lista de posts recentes
        """
        try:
            posts_query = self.db.collection(self.posts_collection)\
                .where('status', '==', 'active')\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit * 2)  # Buscar mais para filtrar depois
            
            posts = posts_query.get()
            
            result = []
            for post_doc in posts:
                post_data = post_doc.to_dict()
                post_data['id'] = post_doc.id
                
                # Excluir posts do usuário especificado
                if exclude_user_id and post_data.get('creator_id') == exclude_user_id:
                    continue
                
                # Enriquecer com dados do criador
                creator_id = post_data.get('creator_id')
                if creator_id:
                    creator_summary = await self._get_creator_summary(creator_id)
                    post_data['creator'] = creator_summary
                
                result.append(post_data)
                
                # Parar quando atingir o limite
                if len(result) >= limit:
                    break
            
            logger.info(f"Obtidos {len(result)} posts recentes")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter posts recentes: {e}")
            return []
    
    async def get_featured_posts(self, limit: int = 20) -> List[Dict]:
        """
        Obtém posts em destaque (baseado em engajamento).
        
        Args:
            limit: Limite de posts a retornar
            
        Returns:
            List[Dict]: Lista de posts em destaque
        """
        try:
            # Buscar posts com maior engajamento (matches + views + favorites)
            posts_query = self.db.collection(self.posts_collection)\
                .where('status', '==', 'active')\
                .order_by('match_count', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            posts = posts_query.get()
            
            result = []
            for post_doc in posts:
                post_data = post_doc.to_dict()
                post_data['id'] = post_doc.id
                
                # Calcular score de engajamento
                match_count = post_data.get('match_count', 0)
                view_count = post_data.get('view_count', 0)
                favorite_count = post_data.get('favorite_count', 0)
                
                engagement_score = (match_count * 3) + (favorite_count * 2) + (view_count * 0.1)
                post_data['engagement_score'] = engagement_score
                
                # Enriquecer com dados do criador
                creator_id = post_data.get('creator_id')
                if creator_id:
                    creator_summary = await self._get_creator_summary(creator_id)
                    post_data['creator'] = creator_summary
                
                result.append(post_data)
            
            # Ordenar por score de engajamento
            result.sort(key=lambda x: x.get('engagement_score', 0), reverse=True)
            
            logger.info(f"Obtidos {len(result)} posts em destaque")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter posts em destaque: {e}")
            return []
    
    async def add_favorite(self, user_id: int, post_id: str) -> bool:
        """
        Adiciona um post aos favoritos do usuário.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se adicionado com sucesso
        """
        try:
            # Verificar se já está nos favoritos
            if await self.is_favorited(user_id, post_id):
                logger.warning(f"Post {post_id} já está nos favoritos do usuário {user_id}")
                return False
            
            # Verificar se o post existe
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                logger.error(f"Post não encontrado: {post_id}")
                return False
            
            # Gerar ID único para o favorito
            favorite_id = str(uuid.uuid4())
            
            # Criar documento de favorito
            favorite_data = {
                'id': favorite_id,
                'user_id': user_id,
                'post_id': post_id,
                'created_at': datetime.now(),
                'status': 'active'
            }
            
            # Usar transação para garantir consistência
            transaction = self.db.transaction()
            
            @firestore.transactional
            def add_favorite_transaction(transaction):
                # Criar favorito
                favorite_ref = self.db.collection(self.favorites_collection).document(favorite_id)
                transaction.set(favorite_ref, favorite_data)
                
                # Incrementar contador no post
                transaction.update(post_ref, {
                    'favorite_count': firestore.Increment(1),
                    'updated_at': datetime.now()
                })
            
            add_favorite_transaction(transaction)
            
            logger.info(f"Post {post_id} adicionado aos favoritos do usuário {user_id}")
            
            # Registrar atividade
            await self._log_user_activity(user_id, 'favorite_added', {
                'post_id': post_id,
                'favorite_id': favorite_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar favorito: {e}")
            return False
    
    async def remove_favorite(self, user_id: int, post_id: str) -> bool:
        """
        Remove um post dos favoritos do usuário.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            # Buscar o favorito ativo
            favorites_query = self.db.collection(self.favorites_collection)\
                .where('user_id', '==', user_id)\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .limit(1)
            
            favorites = favorites_query.get()
            
            if not favorites:
                logger.warning(f"Favorito não encontrado para usuário {user_id} e post {post_id}")
                return False
            
            favorite_doc = favorites[0]
            favorite_ref = favorite_doc.reference
            
            # Usar transação para garantir consistência
            transaction = self.db.transaction()
            
            @firestore.transactional
            def remove_favorite_transaction(transaction):
                # Marcar favorito como removido
                transaction.update(favorite_ref, {
                    'status': 'removed',
                    'removed_at': datetime.now()
                })
                
                # Decrementar contador no post
                post_ref = self.db.collection(self.posts_collection).document(post_id)
                transaction.update(post_ref, {
                    'favorite_count': firestore.Increment(-1),
                    'updated_at': datetime.now()
                })
            
            remove_favorite_transaction(transaction)
            
            logger.info(f"Post {post_id} removido dos favoritos do usuário {user_id}")
            
            # Registrar atividade
            await self._log_user_activity(user_id, 'favorite_removed', {
                'post_id': post_id,
                'favorite_id': favorite_doc.id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover favorito: {e}")
            return False
    
    async def is_favorited(self, user_id: int, post_id: str) -> bool:
        """
        Verifica se um post está nos favoritos do usuário.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se está nos favoritos
        """
        try:
            favorites_query = self.db.collection(self.favorites_collection)\
                .where('user_id', '==', user_id)\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .limit(1)
            
            favorites = favorites_query.get()
            return len(favorites) > 0
            
        except Exception as e:
            logger.error(f"Erro ao verificar favorito: {e}")
            return False
    
    async def get_user_favorites(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Obtém posts favoritos de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de favoritos a retornar
            
        Returns:
            List[Dict]: Lista de posts favoritos
        """
        try:
            favorites_query = self.db.collection(self.favorites_collection)\
                .where('user_id', '==', user_id)\
                .where('status', '==', 'active')\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            favorites = favorites_query.get()
            
            result = []
            for favorite_doc in favorites:
                favorite_data = favorite_doc.to_dict()
                post_id = favorite_data['post_id']
                
                # Obter dados do post
                post_data = await self.get_post(post_id)
                if post_data:
                    favorite_data['post'] = post_data
                    result.append(favorite_data)
            
            logger.info(f"Obtidos {len(result)} favoritos do usuário {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter favoritos do usuário {user_id}: {e}")
            return []
    
    async def record_view(self, post_id: str, viewer_id: int) -> bool:
        """
        Registra uma visualização de post.
        
        Args:
            post_id: ID do post
            viewer_id: ID do usuário que visualizou
            
        Returns:
            bool: True se registrado com sucesso
        """
        try:
            # Verificar se já visualizou hoje (evitar spam)
            today = datetime.now().date()
            views_query = self.db.collection(self.views_collection)\
                .where('post_id', '==', post_id)\
                .where('viewer_id', '==', viewer_id)\
                .where('date', '==', today)\
                .limit(1)
            
            existing_views = views_query.get()
            
            if existing_views:
                # Já visualizou hoje, não contar novamente
                return True
            
            # Registrar nova visualização
            view_data = {
                'post_id': post_id,
                'viewer_id': viewer_id,
                'timestamp': datetime.now(),
                'date': today
            }
            
            # Usar transação para garantir consistência
            transaction = self.db.transaction()
            
            @firestore.transactional
            def record_view_transaction(transaction):
                # Criar registro de visualização
                view_ref = self.db.collection(self.views_collection).document()
                transaction.set(view_ref, view_data)
                
                # Incrementar contador no post
                post_ref = self.db.collection(self.posts_collection).document(post_id)
                transaction.update(post_ref, {
                    'view_count': firestore.Increment(1),
                    'updated_at': datetime.now()
                })
            
            record_view_transaction(transaction)
            
            logger.info(f"Visualização registrada: post {post_id} por usuário {viewer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar visualização: {e}")
            return False
    
    async def get_post_stats(self, post_id: str) -> Dict:
        """
        Obtém estatísticas detalhadas de um post.
        
        Args:
            post_id: ID do post
            
        Returns:
            Dict: Estatísticas do post
        """
        try:
            # Obter dados básicos do post
            post_data = await self.get_post(post_id)
            if not post_data:
                return {}
            
            # Calcular estatísticas por período
            now = datetime.now()
            
            # Visualizações por período
            views_today = await self._count_views_by_period(post_id, 1)
            views_week = await self._count_views_by_period(post_id, 7)
            views_month = await self._count_views_by_period(post_id, 30)
            
            # Matches por período
            matches_today = await self._count_matches_by_period(post_id, 1)
            matches_week = await self._count_matches_by_period(post_id, 7)
            matches_month = await self._count_matches_by_period(post_id, 30)
            
            stats = {
                'post_id': post_id,
                'total_views': post_data.get('view_count', 0),
                'total_matches': post_data.get('match_count', 0),
                'total_favorites': post_data.get('favorite_count', 0),
                'views_by_period': {
                    'today': views_today,
                    'week': views_week,
                    'month': views_month
                },
                'matches_by_period': {
                    'today': matches_today,
                    'week': matches_week,
                    'month': matches_month
                },
                'engagement_rate': 0.0
            }
            
            # Calcular taxa de engajamento
            total_views = stats['total_views']
            if total_views > 0:
                total_interactions = stats['total_matches'] + stats['total_favorites']
                stats['engagement_rate'] = (total_interactions / total_views) * 100
            
            logger.info(f"Estatísticas calculadas para post {post_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do post {post_id}: {e}")
            return {}
    
    async def search_posts(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict]:
        """
        Busca posts por texto e filtros.
        
        Args:
            query: Texto de busca
            filters: Filtros adicionais (tipo, localização, etc.)
            limit: Limite de resultados
            
        Returns:
            List[Dict]: Lista de posts encontrados
        """
        try:
            # Construir query base
            posts_query = self.db.collection(self.posts_collection)\
                .where('status', '==', 'active')
            
            # Aplicar filtros se fornecidos
            if filters:
                if 'type' in filters:
                    posts_query = posts_query.where('type', '==', filters['type'])
                
                if 'location' in filters:
                    posts_query = posts_query.where('location', '==', filters['location'])
                
                if 'is_monetized' in filters:
                    posts_query = posts_query.where('is_monetized', '==', filters['is_monetized'])
            
            # Ordenar por relevância (match_count + view_count)
            posts_query = posts_query.order_by('match_count', direction=firestore.Query.DESCENDING)\
                .limit(limit * 2)  # Buscar mais para filtrar por texto depois
            
            posts = posts_query.get()
            
            result = []
            query_lower = query.lower()
            
            for post_doc in posts:
                post_data = post_doc.to_dict()
                post_data['id'] = post_doc.id
                
                # Filtrar por texto (título e descrição)
                title = post_data.get('title', '').lower()
                description = post_data.get('description', '').lower()
                
                if query_lower in title or query_lower in description:
                    # Enriquecer com dados do criador
                    creator_id = post_data.get('creator_id')
                    if creator_id:
                        creator_summary = await self._get_creator_summary(creator_id)
                        post_data['creator'] = creator_summary
                    
                    result.append(post_data)
                    
                    # Parar quando atingir o limite
                    if len(result) >= limit:
                        break
            
            logger.info(f"Encontrados {len(result)} posts para busca: {query}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar posts: {e}")
            return []

    async def publish_post(
        self,
        content_type: str,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        media_files: Optional[List[Dict]] = None,
        keyboard: Optional[Any] = None,
        target_group: str = 'both'
    ) -> bool:
        """Publica um post nos grupos configurados.

        Args:
            content_type: Tipo de conteúdo ('photo', 'video', 'text', 'media_group').
            text: Texto/legenda final do post (HTML formatado).
            file_id: ID do arquivo do Telegram (para fotos/vídeos únicos).
            media_files: Lista de arquivos de mídia para media_group.
            keyboard: Teclado inline para interações.
            target_group: 'freemium', 'premium' ou 'both' (padrão - publica em ambos).

        Returns:
            bool: True se pelo menos um envio foi bem-sucedido, False caso contrário.
        """
        try:
            # Verificar bot
            if not self.bot:
                logger.error("Bot não está inicializado no PostService.")
                return False

            caption = text or ""
            success_count = 0
            total_attempts = 0

            # Determinar grupos de destino
            groups_to_publish = []
            
            if target_group == 'freemium' or target_group == 'both':
                if self.freemium_group_id:
                    groups_to_publish.append(('freemium', self.freemium_group_id))
                else:
                    logger.warning("FREEMIUM_GROUP_ID não configurado")
            
            if target_group == 'premium' or target_group == 'both':
                if self.premium_group_id:
                    groups_to_publish.append(('premium', self.premium_group_id))
                else:
                    logger.warning("PREMIUM_GROUP_ID não configurado")

            if not groups_to_publish:
                error_msg = "Erro: Nenhum grupo configurado para publicação. "
                if target_group == 'both' or target_group == 'freemium':
                    if not self.freemium_group_id:
                        error_msg += "FREEMIUM_GROUP_ID não definido no .env. "
                if target_group == 'both' or target_group == 'premium':
                    if not self.premium_group_id:
                        error_msg += "PREMIUM_GROUP_ID não definido no .env. "
                logger.error(error_msg)
                raise ValueError(error_msg)
                return False

            # Publicar em cada grupo
            for group_name, chat_id in groups_to_publish:
                total_attempts += 1
                try:
                    # Enviar conforme tipo de conteúdo
                    if content_type == "media_group" and media_files and len(media_files) > 1:
                        # Múltiplas mídias - usar media_group
                        from aiogram.types import InputMediaPhoto, InputMediaVideo
                        
                        media_group = []
                        for i, media in enumerate(media_files):
                            if media.get('type') == 'image':
                                media_item = InputMediaPhoto(
                                    media=media['file_id'],
                                    caption=caption if i == 0 else None,  # Caption apenas na primeira mídia
                                    parse_mode='HTML' if i == 0 else None
                                )
                            elif media.get('type') == 'video':
                                media_item = InputMediaVideo(
                                    media=media['file_id'],
                                    caption=caption if i == 0 else None,
                                    parse_mode='HTML' if i == 0 else None
                                )
                            else:
                                continue
                            media_group.append(media_item)
                        
                        if media_group:
                            # Enviar media group
                            messages = await self.bot.send_media_group(chat_id, media_group)
                            
                            # Criar teclado apropriado baseado no número de mídias
                            if messages and keyboard:
                                final_keyboard = keyboard
                                
                                # Se há múltiplas mídias, criar teclado combinado
                                if len(media_files) > 1:
                                    from handlers.media_navigation_handler import MediaNavigationHandler
                                    media_nav_handler = MediaNavigationHandler(self.bot, self, None)
                                    
                                    # Extrair post_id do teclado de interação existente
                                    post_id = None
                                    if keyboard and keyboard.inline_keyboard:
                                        for row in keyboard.inline_keyboard:
                                            for button in row:
                                                if button.callback_data and ':post:' in button.callback_data:
                                                    post_id = button.callback_data.split(':post:')[-1]
                                                    break
                                            if post_id:
                                                break
                                    
                                    if not post_id:
                                        post_id = f"post_{int(datetime.now().timestamp())}"
                                    
                                    # Criar teclado combinado: navegação + interações
                                    final_keyboard = media_nav_handler._create_combined_keyboard(
                                        post_id=post_id,
                                        current_index=0,
                                        total_media=len(media_files),
                                        interaction_keyboard=keyboard
                                    )
                                
                                # Adicionar o teclado final (simples ou combinado) em uma única operação
                                try:
                                    await self.bot.edit_message_reply_markup(
                                        chat_id=chat_id,
                                        message_id=messages[0].message_id,
                                        reply_markup=final_keyboard
                                    )
                                except Exception as e:
                                    logger.warning(f"Não foi possível adicionar teclado ao media group: {e}")
                        
                    elif content_type in ("photo", "image"):
                        if not file_id:
                            logger.error("file_id é obrigatório para conteúdo de foto.")
                            continue
                        await self.bot.send_photo(chat_id, file_id, caption=caption, reply_markup=keyboard, parse_mode='HTML')
                    elif content_type == "video":
                        if not file_id:
                            logger.error("file_id é obrigatório para conteúdo de vídeo.")
                            continue
                        await self.bot.send_video(chat_id, file_id, caption=caption, reply_markup=keyboard, parse_mode='HTML')
                    else:
                        # Fallback para texto
                        await self.bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode='HTML')

                    logger.info(f"Post publicado com sucesso no grupo '{group_name}' (ID: {chat_id}) com tipo '{content_type}'.")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao publicar post no grupo '{group_name}' (ID: {chat_id}): {e}")
                    continue

            # Retornar True se pelo menos uma publicação foi bem-sucedida
            if success_count > 0:
                logger.info(f"Post publicado com sucesso em {success_count}/{total_attempts} grupos.")
                return True
            else:
                logger.error("Falha ao publicar post em todos os grupos.")
                return False
                
        except Exception as e:
            logger.error(f"Erro geral ao publicar post: {e}", exc_info=True)
            return False
    
    async def _get_creator_summary(self, creator_id: int) -> Dict:
        """Obtém resumo anônimo do criador."""
        try:
            user_ref = self.db.collection(self.users_collection).document(str(creator_id))
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return {
                    'id': creator_id,
                    'name': 'Criador Anônimo',
                    'state': 'Não informado',
                    'is_creator': False
                }
            
            user_data = user_doc.to_dict()
            
            # Retornar dados anônimos do criador
            return {
                'id': creator_id,
                'name': user_data.get('name', 'Criador Anônimo'),
                'state': user_data.get('state', 'Não informado'),
                'is_creator': user_data.get('is_creator', False),
                'profile_type': user_data.get('profile_type', 'Não informado')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo do criador {creator_id}: {e}")
            return {
                'id': creator_id,
                'name': 'Criador Anônimo',
                'state': 'Não informado',
                'is_creator': False
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
    
    async def _count_views_by_period(self, post_id: str, days: int) -> int:
        """Conta visualizações por período."""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days)
            
            views_query = self.db.collection(self.views_collection)\
                .where('post_id', '==', post_id)\
                .where('date', '>=', cutoff_date)
            
            views = views_query.get()
            return len(views)
            
        except Exception as e:
            logger.error(f"Erro ao contar visualizações: {e}")
            return 0
    
    async def _count_matches_by_period(self, post_id: str, days: int) -> int:
        """Conta matches por período."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            matches_query = self.db.collection('matches')\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .where('created_at', '>=', cutoff_date)
            
            matches = matches_query.get()
            return len(matches)
            
        except Exception as e:
            logger.error(f"Erro ao contar matches: {e}")
            return 0
    
    async def cleanup_old_data(self, days_old: int = 365) -> Dict[str, int]:
        """
        Remove dados antigos para otimizar performance.
        
        Args:
            days_old: Idade em dias para considerar dados como antigos
            
        Returns:
            Dict[str, int]: Contadores de itens removidos
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            counters = {
                'deleted_posts': 0,
                'old_views': 0,
                'removed_favorites': 0
            }
            
            # Remover posts deletados antigos
            deleted_posts_query = self.db.collection(self.posts_collection)\
                .where('status', '==', 'deleted')\
                .where('deleted_at', '<', cutoff_date)
            
            deleted_posts = deleted_posts_query.get()
            
            batch = self.db.batch()
            for post_doc in deleted_posts:
                batch.delete(post_doc.reference)
                counters['deleted_posts'] += 1
                
                if counters['deleted_posts'] % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            if counters['deleted_posts'] % 500 != 0:
                batch.commit()
            
            # Remover visualizações antigas
            old_views_query = self.db.collection(self.views_collection)\
                .where('timestamp', '<', cutoff_date)
            
            old_views = old_views_query.get()
            
            batch = self.db.batch()
            for view_doc in old_views:
                batch.delete(view_doc.reference)
                counters['old_views'] += 1
                
                if counters['old_views'] % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            if counters['old_views'] % 500 != 0:
                batch.commit()
            
            # Remover favoritos removidos antigos
            removed_favorites_query = self.db.collection(self.favorites_collection)\
                .where('status', '==', 'removed')\
                .where('removed_at', '<', cutoff_date)
            
            removed_favorites = removed_favorites_query.get()
            
            batch = self.db.batch()
            for favorite_doc in removed_favorites:
                batch.delete(favorite_doc.reference)
                counters['removed_favorites'] += 1
                
                if counters['removed_favorites'] % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            if counters['removed_favorites'] % 500 != 0:
                batch.commit()
            
            logger.info(f"Limpeza concluída: {counters}")
            return counters
            
        except Exception as e:
            logger.error(f"Erro ao limpar dados antigos: {e}")
            return {'deleted_posts': 0, 'old_views': 0, 'removed_favorites': 0}
    
    async def add_to_favorites(self, user_id: int, post_id: str) -> bool:
        """
        Adiciona um post aos favoritos do usuário.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se adicionado com sucesso
        """
        return await self.add_favorite(user_id, post_id)
    
    async def remove_from_favorites(self, user_id: int, post_id: str) -> bool:
        """
        Remove um post dos favoritos do usuário.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se removido com sucesso
        """
        return await self.remove_favorite(user_id, post_id)
    
    async def is_post_favorited(self, user_id: int, post_id: str) -> bool:
        """
        Verifica se um post está nos favoritos do usuário.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se está nos favoritos
        """
        return await self.is_favorited(user_id, post_id)
    
    async def get_post_comments(self, post_id: str) -> List[Dict]:
        """
        Obtém comentários de um post.
        
        Args:
            post_id: ID do post
            
        Returns:
            List[Dict]: Lista de comentários do post
        """
        try:
            comments_query = self.db.collection('comments')\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .order_by('created_at', direction=firestore.Query.ASCENDING)
            
            comments = comments_query.get()
            
            result = []
            for comment_doc in comments:
                comment_data = comment_doc.to_dict()
                comment_data['id'] = comment_doc.id
                result.append(comment_data)
            
            logger.info(f"Obtidos {len(result)} comentários do post {post_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter comentários do post {post_id}: {e}")
            return []
    
    async def add_comment(self, post_id: str, user_id: int, comment_text: str) -> bool:
        """
        Adiciona um comentário a um post.
        
        Args:
            post_id: ID do post
            user_id: ID do usuário que está comentando
            comment_text: Texto do comentário
            
        Returns:
            bool: True se o comentário foi adicionado com sucesso
        """
        try:
            # Verificar se o post existe
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                logger.warning(f"Post não encontrado para comentário: {post_id}")
                return False
            
            # Criar comentário
            comment_id = str(uuid.uuid4())
            comment_data = {
                'id': comment_id,
                'post_id': post_id,
                'author_id': user_id,
                'text': comment_text,
                'status': 'active',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Usar transação para adicionar comentário e incrementar contador
            transaction = self.db.transaction()
            
            @firestore.transactional
            def add_comment_transaction(transaction):
                # Criar comentário
                comment_ref = self.db.collection('comments').document(comment_id)
                transaction.set(comment_ref, comment_data)
                
                # Incrementar contador no post
                transaction.update(post_ref, {
                    'comment_count': firestore.Increment(1),
                    'updated_at': datetime.now()
                })
            
            add_comment_transaction(transaction)
            
            logger.info(f"Comentário adicionado ao post {post_id} pelo usuário {user_id}")
            
            # Registrar atividade
            await self._log_user_activity(user_id, 'comment_added', {
                'post_id': post_id,
                'comment_id': comment_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar comentário: {e}")
            return False