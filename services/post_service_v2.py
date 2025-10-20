"""
PostService V2 - Serviço de posts com renderização dual.

Implementa dois modos de renderização conforme PRD:
- carousel: 1 mensagem com primeira mídia + navegação inline
- album+panel: álbum sem teclado + painel separado com teclado

Estrutura de dados telegram.* por espelho (freemium/premium).
"""
import os
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from firebase_admin import firestore
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, FSInputFile
from aiogram.exceptions import TelegramBadRequest

from core.ui_builder_v2 import UIBuilderV2
from services.idempotency_service import get_idempotency_service
from services.antispam_service import get_antispam_service

logger = logging.getLogger(__name__)

# Configurações
POST_RENDER_MODE = os.getenv('POST_RENDER_MODE', 'carousel')
BLUR_PREVIEW_FOR_MONETIZED = os.getenv('BLUR_PREVIEW_FOR_MONETIZED', 'true').lower() == 'true'


class PostServiceV2:
    """
    Serviço de posts com suporte a renderização dual e callbacks normalizados.
    """
    
    def __init__(self, bot: Bot, firebase_service, user_service, bot_username: str):
        """
        Inicializa o serviço.
        
        Args:
            bot: Instância do bot Telegram
            firebase_service: Serviço Firebase
            user_service: Serviço de usuários
            bot_username: Username do bot
        """
        self.bot = bot
        self.db = firebase_service.db
        self.user_service = user_service
        self.ui_builder = UIBuilderV2(bot_username)
        
        # Serviços auxiliares
        self.idempotency = get_idempotency_service()
        self.antispam = get_antispam_service()
        
        # Coleções
        self.posts_collection = 'posts'
        self.comments_collection = 'comments'
        self.favorites_collection = 'favorites'
        
        # IDs dos grupos
        self.freemium_group_id = int(os.getenv('FREEMIUM_GROUP_ID', '-1002620620239'))
        self.premium_group_id = int(os.getenv('PREMIUM_GROUP_ID', '-1002680323844'))
        
        logger.info(f"PostServiceV2 inicializado - modo: {POST_RENDER_MODE}")
    
    async def create_post(
        self,
        author_id: int,
        text: Optional[str] = None,
        media: Optional[List[Dict]] = None,
        monetized: bool = False,
        price: Optional[float] = None,
        title: Optional[str] = None
    ) -> str:
        """
        Cria um novo post no Firestore.
        
        Args:
            author_id: ID do autor
            text: Texto/descrição do post
            media: Lista de mídias [{id, url, type}]
            monetized: Se é monetizado
            price: Preço (se monetizado)
            title: Título opcional
            
        Returns:
            post_id: ID do post criado
        """
        try:
            # Gerar ID único
            post_id = str(uuid.uuid4())
            
            # Preparar dados
            now = datetime.now()
            post_data = {
                'author_id': str(author_id),
                'title': title or '',
                'text': text or '',
                'media': media or [],
                'monetized': monetized,
                'price': price,
                'stats': {
                    'comments': 0,
                    'favorites': 0,
                    'matches': 0
                },
                'mirrors': {
                    'sent_to_freemium': False,
                    'sent_to_premium': False
                },
                'telegram': {
                    'freemium': {
                        'chat_id': None,
                        'message_id': None,
                        'panel_message_id': None,
                        'album_message_ids': []
                    },
                    'premium': {
                        'chat_id': None,
                        'message_id': None,
                        'panel_message_id': None,
                        'album_message_ids': []
                    },
                    'last_media_index': 0
                },
                'render_mode': POST_RENDER_MODE,
                'created_at': now,
                'updated_at': now
            }
            
            # Salvar no Firestore
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_ref.set(post_data)
            
            logger.info(f"post.created {post_id=} {author_id=} {monetized=}")
            
            return post_id
            
        except Exception as e:
            logger.error(f"Erro ao criar post: {e}", exc_info=True)
            raise
    
    async def publish_post(
        self,
        post_id: str,
        target: str = "both",
        render_mode: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Publica post nos grupos conforme política de monetização.
        
        Args:
            post_id: ID do post
            target: "both" | "freemium" | "premium"
            render_mode: "carousel" | "album+panel" (override)
            
        Returns:
            Dicionário com informações de publicação por espelho
        """
        try:
            # Obter post
            post = await self.get_post(post_id)
            if not post:
                raise ValueError(f"Post não encontrado: {post_id}")
            
            # Obter autor
            author = await self.user_service.get_user(int(post['author_id']))
            if not author:
                raise ValueError(f"Autor não encontrado: {post['author_id']}")
            
            # Determinar modo de renderização
            mode = render_mode or post.get('render_mode', POST_RENDER_MODE)
            
            # Determinar destinos
            monetized = post.get('monetized', False)
            publish_to_freemium = not monetized or target == "freemium"
            publish_to_premium = target in ["both", "premium"]
            
            result = {}
            
            # Publicar no Freemium
            if publish_to_freemium and target != "premium":
                freemium_info = await self._publish_to_group(
                    post_id=post_id,
                    post=post,
                    author=author,
                    group_id=self.freemium_group_id,
                    group_type='freemium',
                    mode=mode,
                    apply_blur=monetized and BLUR_PREVIEW_FOR_MONETIZED
                )
                result['freemium'] = freemium_info
                
                # Atualizar mirror
                await self.set_mirror(post_id, freemium=True)
            
            # Publicar no Premium
            if publish_to_premium:
                premium_info = await self._publish_to_group(
                    post_id=post_id,
                    post=post,
                    author=author,
                    group_id=self.premium_group_id,
                    group_type='premium',
                    mode=mode,
                    apply_blur=False
                )
                result['premium'] = premium_info
                
                # Atualizar mirror
                await self.set_mirror(post_id, premium=True)
            
            logger.info(f"post.published {post_id=} {mode=} mirrors={list(result.keys())}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao publicar post {post_id}: {e}", exc_info=True)
            raise
    
    async def _publish_to_group(
        self,
        post_id: str,
        post: Dict,
        author: Dict,
        group_id: int,
        group_type: str,
        mode: str,
        apply_blur: bool = False
    ) -> Dict:
        """
        Publica post em um grupo específico.
        
        Args:
            post_id: ID do post
            post: Dados do post
            author: Dados do autor
            group_id: ID do grupo Telegram
            group_type: 'freemium' ou 'premium'
            mode: 'carousel' ou 'album+panel'
            apply_blur: Se deve aplicar blur nas mídias
            
        Returns:
            Dicionário com informações da publicação
        """
        try:
            # Preparar caption com etiqueta
            caption = self._build_caption(post, author, apply_blur)
            
            # Obter mídias
            media_list = post.get('media', [])
            
            if mode == 'carousel':
                return await self._publish_carousel(
                    post_id, caption, media_list, group_id, group_type, apply_blur
                )
            else:  # album+panel
                return await self._publish_album_panel(
                    post_id, caption, media_list, group_id, group_type, apply_blur
                )
                
        except Exception as e:
            logger.error(f"Erro ao publicar no grupo {group_type}: {e}", exc_info=True)
            raise
    
    async def _publish_carousel(
        self,
        post_id: str,
        caption: str,
        media_list: List[Dict],
        group_id: int,
        group_type: str,
        apply_blur: bool
    ) -> Dict:
        """
        Publica no modo carousel (1 mensagem + navegação inline).
        """
        # Pegar primeira mídia
        first_media = media_list[0] if media_list else None
        
        # Criar teclado combinado
        keyboard = self.ui_builder.create_combined_keyboard(
            post_id=post_id,
            counts={'comments': 0, 'favorites': 0, 'matches': 0},
            viewer_user_id=0,  # Será substituído por deep link
            current_index=0,
            total_media=len(media_list)
        )
        
        # Enviar mensagem
        if first_media:
            media_url = first_media['url']
            if apply_blur:
                media_url = self._apply_blur_transform(media_url)
            
            if first_media['type'] == 'photo':
                msg = await self.bot.send_photo(
                    chat_id=group_id,
                    photo=media_url,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            else:  # video
                msg = await self.bot.send_video(
                    chat_id=group_id,
                    video=media_url,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        else:
            # Post sem mídia
            msg = await self.bot.send_message(
                chat_id=group_id,
                text=caption,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        # Atualizar telegram.* no post
        await self._update_telegram_refs(
            post_id=post_id,
            group_type=group_type,
            chat_id=group_id,
            message_id=msg.message_id,
            panel_message_id=None,
            album_message_ids=[]
        )
        
        return {
            'chat_id': group_id,
            'message_id': msg.message_id,
            'mode': 'carousel'
        }
    
    async def _publish_album_panel(
        self,
        post_id: str,
        caption: str,
        media_list: List[Dict],
        group_id: int,
        group_type: str,
        apply_blur: bool
    ) -> Dict:
        """
        Publica no modo album+panel (álbum + painel separado).
        """
        album_message_ids = []
        
        # Enviar álbum (se houver mídias)
        if media_list:
            media_group = []
            for i, media_item in enumerate(media_list[:10]):  # Máx 10 mídias
                media_url = media_item['url']
                if apply_blur:
                    media_url = self._apply_blur_transform(media_url)
                
                # Primeira mídia leva o caption
                item_caption = caption if i == 0 else None
                
                if media_item['type'] == 'photo':
                    media_group.append(
                        InputMediaPhoto(media=media_url, caption=item_caption, parse_mode='HTML')
                    )
                else:  # video
                    media_group.append(
                        InputMediaVideo(media=media_url, caption=item_caption, parse_mode='HTML')
                    )
            
            # Enviar álbum
            album_messages = await self.bot.send_media_group(
                chat_id=group_id,
                media=media_group
            )
            
            album_message_ids = [msg.message_id for msg in album_messages]
        
        # Enviar painel com teclado
        keyboard = self.ui_builder.create_combined_keyboard(
            post_id=post_id,
            counts={'comments': 0, 'favorites': 0, 'matches': 0},
            viewer_user_id=0,
            current_index=0,
            total_media=len(media_list)
        )
        
        panel_msg = await self.bot.send_message(
            chat_id=group_id,
            text="⬆️ Interaja com o post acima:",
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # Atualizar telegram.* no post
        await self._update_telegram_refs(
            post_id=post_id,
            group_type=group_type,
            chat_id=group_id,
            message_id=album_message_ids[0] if album_message_ids else panel_msg.message_id,
            panel_message_id=panel_msg.message_id,
            album_message_ids=album_message_ids
        )
        
        return {
            'chat_id': group_id,
            'message_id': album_message_ids[0] if album_message_ids else panel_msg.message_id,
            'panel_message_id': panel_msg.message_id,
            'album_message_ids': album_message_ids,
            'mode': 'album+panel'
        }
    
    def _build_caption(self, post: Dict, author: Dict, apply_blur: bool) -> str:
        """Constrói caption do post com etiqueta do autor."""
        # Etiqueta do autor
        codename = author.get('codename', 'Anônimo')
        category = author.get('category', 'Usuário')
        state = author.get('state', 'BR')
        
        etiqueta = f"👤 {codename} | {category} | {state}"
        
        # Texto do post
        text = post.get('text', '')
        
        # Aviso de blur (se aplicável)
        blur_warning = ""
        if apply_blur:
            price = post.get('price', 0.0)
            blur_warning = (
                f"\n\n💰 <b>Conteúdo Monetizado</b>\n"
                f"Preço: R$ {price:.2f}\n"
                f"✨ Assine o Premium para acesso completo!"
            )
        
        return f"{etiqueta}\n\n{text}{blur_warning}"
    
    def _apply_blur_transform(self, media_url: str) -> str:
        """
        Aplica transformação de blur via Cloudinary.
        
        Args:
            media_url: URL original da mídia
            
        Returns:
            URL com transformação de blur
        """
        # Transformação Cloudinary: e_blur:1000,q_10
        if 'cloudinary.com' in media_url:
            parts = media_url.split('/upload/')
            if len(parts) == 2:
                return f"{parts[0]}/upload/e_blur:1000,q_10/{parts[1]}"
        
        return media_url
    
    async def _update_telegram_refs(
        self,
        post_id: str,
        group_type: str,
        chat_id: int,
        message_id: int,
        panel_message_id: Optional[int],
        album_message_ids: List[int]
    ):
        """Atualiza referências do Telegram no post."""
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            
            update_data = {
                f'telegram.{group_type}.chat_id': chat_id,
                f'telegram.{group_type}.message_id': message_id,
                f'telegram.{group_type}.panel_message_id': panel_message_id,
                f'telegram.{group_type}.album_message_ids': album_message_ids
            }
            
            post_ref.update(update_data)
            
            logger.debug(f"Telegram refs atualizadas: {post_id} {group_type}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar telegram refs: {e}", exc_info=True)
    
    async def get_post(self, post_id: str) -> Optional[Dict]:
        """Obtém um post do Firestore."""
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_doc = post_ref.get()
            
            if not post_doc.exists:
                return None
            
            post_data = post_doc.to_dict()
            post_data['id'] = post_id
            
            return post_data
            
        except Exception as e:
            logger.error(f"Erro ao obter post {post_id}: {e}", exc_info=True)
            return None
    
    async def increment_stat(self, post_id: str, field: str):
        """
        Incrementa contador de estatística do post.
        
        Args:
            post_id: ID do post
            field: Campo a incrementar (comments|favorites|matches)
        """
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            post_ref.update({
                f'stats.{field}': firestore.Increment(1)
            })
            
            logger.info(f"post.counter.updated {post_id=} {field=}")
            
        except Exception as e:
            logger.error(f"Erro ao incrementar stat {field} do post {post_id}: {e}", exc_info=True)
    
    async def set_mirror(
        self,
        post_id: str,
        freemium: Optional[bool] = None,
        premium: Optional[bool] = None
    ):
        """
        Atualiza flags de espelho (sent_to_*).
        
        Args:
            post_id: ID do post
            freemium: Flag para freemium
            premium: Flag para premium
        """
        try:
            post_ref = self.db.collection(self.posts_collection).document(post_id)
            
            update_data = {}
            if freemium is not None:
                update_data['mirrors.sent_to_freemium'] = freemium
            if premium is not None:
                update_data['mirrors.sent_to_premium'] = premium
            
            if update_data:
                post_ref.update(update_data)
                logger.debug(f"Mirrors atualizados: {post_id}")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar mirrors: {e}", exc_info=True)
    
    async def add_comment(self, post_id: str, author_id: int, text: str) -> str:
        """
        Adiciona comentário a um post.
        
        Args:
            post_id: ID do post
            author_id: ID do autor do comentário
            text: Texto do comentário
            
        Returns:
            comment_id: ID do comentário criado
        """
        try:
            # Gerar ID do comentário
            comment_id = str(uuid.uuid4())
            
            # Salvar comentário
            comment_ref = self.db.collection(self.comments_collection).document(post_id).collection('items').document(comment_id)
            comment_ref.set({
                'author_id': str(author_id),
                'text': text,
                'created_at': datetime.now()
            })
            
            # Incrementar contador
            await self.increment_stat(post_id, 'comments')
            
            logger.info(f"comment.added {post_id=} {comment_id=} {author_id=}")
            
            return comment_id
            
        except Exception as e:
            logger.error(f"Erro ao adicionar comentário: {e}", exc_info=True)
            raise
    
    async def get_user_posts(self, author_id: int, limit: int = 10) -> List[Dict]:
        """
        Obtém posts de um usuário.
        
        Args:
            author_id: ID do autor
            limit: Limite de posts
            
        Returns:
            Lista de posts
        """
        try:
            posts_ref = self.db.collection(self.posts_collection)
            query = posts_ref.where('author_id', '==', str(author_id)).order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            
            posts = []
            for doc in docs:
                post_data = doc.to_dict()
                post_data['id'] = doc.id
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            logger.error(f"Erro ao obter posts do usuário {author_id}: {e}", exc_info=True)
            return []

