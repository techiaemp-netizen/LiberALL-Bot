"""
Post Interaction Handler V2 - Callbacks normalizados e idempotência.

Implementa todas as interações com posts seguindo padrão:
- match:post:<postId>
- gallery:post:<postId>
- favorite:post:<postId>
- info:post:<postId>
- comments:post:<postId>

Com idempotência e antispam integrados.
"""
import logging
import re
from typing import Optional
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from services.post_service_v2 import PostServiceV2
from services.match_service import MatchService
from services.antispam_service import get_antispam_service, RateLimitExceeded
from services.idempotency_service import get_idempotency_service
from constants.normalized_callbacks import CallbackPatterns, CallbackExtractor
from core.ui_builder_v2 import UIBuilderV2

logger = logging.getLogger(__name__)


class PostInteractionHandlerV2:
    """
    Handler de interações com posts usando callbacks normalizados.
    """
    
    def __init__(
        self,
        bot: Bot,
        post_service: PostServiceV2,
        user_service,
        match_service: MatchService,
        error_handler,
        bot_username: str
    ):
        """
        Inicializa o handler.
        
        Args:
            bot: Instância do bot
            post_service: Serviço de posts V2
            user_service: Serviço de usuários
            match_service: Serviço de matches
            error_handler: Handler de erros
            bot_username: Username do bot
        """
        self.bot = bot
        self.post_service = post_service
        self.user_service = user_service
        self.match_service = match_service
        self.error_handler = error_handler
        self.ui_builder = UIBuilderV2(bot_username)
        
        # Serviços auxiliares
        self.antispam = get_antispam_service()
        self.idempotency = get_idempotency_service()
        
        logger.info("PostInteractionHandlerV2 inicializado")
    
    async def handle_callback(self, callback: CallbackQuery):
        """
        Roteador principal de callbacks de interação.
        
        Args:
            callback: Callback query do Telegram
        """
        try:
            callback_data = callback.data
            user_id = callback.from_user.id
            
            # Extrair ação
            action = CallbackExtractor.extract_action(callback_data)
            
            # Rotear para handler específico
            if action == 'match':
                await self.handle_match(callback)
            elif action == 'gallery':
                await self.handle_gallery(callback)
            elif action == 'favorite':
                await self.handle_favorite(callback)
            elif action == 'info':
                await self.handle_info(callback)
            elif action == 'comments':
                await self.handle_comments(callback)
            else:
                logger.warning(f"Ação desconhecida: {action}")
                await callback.answer("Ação não reconhecida.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Erro ao processar callback: {e}", exc_info=True)
            await callback.answer("Erro ao processar ação. Tente novamente.", show_alert=True)
    
    async def handle_match(self, callback: CallbackQuery):
        """
        Processa match em um post.
        
        Validações:
        - Bloqueia match consigo mesmo
        - Idempotência (não permite match duplicado)
        - Antispam (1 match a cada 30s por alvo)
        """
        try:
            callback_data = callback.data
            user_id = callback.from_user.id
            
            # Extrair post_id
            post_id = CallbackExtractor.extract_post_id(callback_data)
            
            # Obter post
            post = await self.post_service.get_post(post_id)
            if not post:
                await callback.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = int(post['author_id'])
            
            # Validação: não pode dar match em si mesmo
            if user_id == author_id:
                await callback.answer(
                    "❌ Você não pode dar match no seu próprio post.",
                    show_alert=True
                )
                logger.warning(f"error.forbidden user={user_id} action=match_self post={post_id}")
                return
            
            # Antispam: 1 match a cada 30s por alvo
            allowed, retry_after = self.antispam.check_and_consume(
                user_id=user_id,
                action='match',
                scope_key=f"target_{author_id}"
            )
            
            if not allowed:
                await callback.answer(
                    f"⏳ Aguarde {retry_after:.0f}s antes de dar match novamente.",
                    show_alert=True
                )
                logger.warning(f"error.rate_limit user={user_id} action=match retry_after={retry_after}")
                return
            
            # Idempotência: verificar se já existe match
            idempotency_key = f"match:{user_id}:{author_id}:post_{post_id}"
            
            async def create_match_fn():
                # Criar match
                match_id = await self.match_service.create(
                    initiator_id=user_id,
                    target_id=author_id,
                    post_id=post_id
                )
                
                # Incrementar contador
                await self.post_service.increment_stat(post_id, 'matches')
                
                # Notificar partes
                await self.match_service.notify_parties(match_id)
                
                return match_id
            
            executed, match_id = await self.idempotency.run_once(
                key=idempotency_key,
                fn=create_match_fn,
                ttl=120
            )
            
            if not executed:
                await callback.answer(
                    "✅ Você já deu match neste usuário!",
                    show_alert=False
                )
                logger.info(f"error.already_exists user={user_id} action=match post={post_id}")
                return
            
            # Sucesso
            await callback.answer(
                "❤️ Match enviado! Você será notificado se houver reciprocidade.",
                show_alert=False
            )
            
            logger.info(f"match.created match_id={match_id} initiator={user_id} target={author_id} post={post_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar match: {e}", exc_info=True)
            await callback.answer("Erro ao processar match.", show_alert=True)
    
    async def handle_gallery(self, callback: CallbackQuery):
        """
        Mostra galeria do autor do post.
        """
        try:
            callback_data = callback.data
            user_id = callback.from_user.id
            
            # Extrair post_id
            post_id = CallbackExtractor.extract_post_id(callback_data)
            
            # Obter post
            post = await self.post_service.get_post(post_id)
            if not post:
                await callback.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = int(post['author_id'])
            
            # Obter posts do autor
            author_posts = await self.post_service.get_user_posts(author_id, limit=10)
            
            if not author_posts:
                await callback.answer(
                    "Este usuário ainda não tem posts na galeria.",
                    show_alert=True
                )
                return
            
            # Obter dados do autor
            author = await self.user_service.get_user(author_id)
            codename = author.get('codename', 'Anônimo') if author else 'Anônimo'
            
            # Criar teclado de galeria
            post_ids = [p['id'] for p in author_posts]
            keyboard = self.ui_builder.create_gallery_keyboard(
                user_id=user_id,
                posts=post_ids,
                page=0,
                has_more=len(author_posts) >= 10
            )
            
            # Enviar no DM
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🖼️ <b>Galeria de {codename}</b>\n\nTotal de posts: {len(author_posts)}",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            await callback.answer("Galeria enviada no privado!", show_alert=False)
            
            logger.info(f"gallery.opened user={user_id} author={author_id} post={post_id}")
            
        except Exception as e:
            logger.error(f"Erro ao abrir galeria: {e}", exc_info=True)
            await callback.answer("Erro ao abrir galeria.", show_alert=True)
    
    async def handle_favorite(self, callback: CallbackQuery):
        """
        Adiciona post aos favoritos.
        
        Validações:
        - Bloqueia favoritar próprio post
        - Idempotência (não permite favoritar duas vezes)
        """
        try:
            callback_data = callback.data
            user_id = callback.from_user.id
            
            # Extrair post_id
            post_id = CallbackExtractor.extract_post_id(callback_data)
            
            # Obter post
            post = await self.post_service.get_post(post_id)
            if not post:
                await callback.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = int(post['author_id'])
            
            # Validação: não pode favoritar próprio post
            if user_id == author_id:
                await callback.answer(
                    "❌ Você não pode favoritar seu próprio post.",
                    show_alert=True
                )
                logger.warning(f"error.forbidden user={user_id} action=favorite_self post={post_id}")
                return
            
            # Idempotência: verificar se já favoritou
            idempotency_key = f"favorite:{user_id}:post_{post_id}"
            
            async def add_favorite_fn():
                # Adicionar aos favoritos do usuário
                await self.user_service.favorite_post(user_id, post_id)
                
                # Incrementar contador (apenas na primeira vez)
                await self.post_service.increment_stat(post_id, 'favorites')
                
                return True
            
            executed, _ = await self.idempotency.run_once(
                key=idempotency_key,
                fn=add_favorite_fn,
                ttl=120
            )
            
            if not executed:
                await callback.answer(
                    "⭐ Este post já está nos seus favoritos!",
                    show_alert=False
                )
                logger.info(f"error.already_exists user={user_id} action=favorite post={post_id}")
                return
            
            # Sucesso
            await callback.answer(
                "⭐ Post adicionado aos favoritos!",
                show_alert=False
            )
            
            logger.info(f"favorite.added user={user_id} post={post_id}")
            
        except Exception as e:
            logger.error(f"Erro ao favoritar: {e}", exc_info=True)
            await callback.answer("Erro ao favoritar post.", show_alert=True)
    
    async def handle_info(self, callback: CallbackQuery):
        """
        Mostra informações do autor do post.
        """
        try:
            callback_data = callback.data
            user_id = callback.from_user.id
            
            # Extrair post_id
            post_id = CallbackExtractor.extract_post_id(callback_data)
            
            # Obter post
            post = await self.post_service.get_post(post_id)
            if not post:
                await callback.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = int(post['author_id'])
            
            # Obter dados do autor
            author = await self.user_service.get_user(author_id)
            if not author:
                await callback.answer("❌ Autor não encontrado.", show_alert=True)
                return
            
            # Montar card de informações
            codename = author.get('codename', 'Anônimo')
            category = author.get('category', 'Usuário')
            state = author.get('state', 'BR')
            age = author.get('age', '?')
            description = author.get('description', 'Sem descrição')
            
            # Informações físicas (se disponíveis)
            physical = author.get('physical', {})
            height = physical.get('height', '-')
            hair_color = physical.get('hair_color', '-')
            eye_color = physical.get('eye_color', '-')
            endowment = physical.get('endowment', '-')
            
            info_text = (
                f"👤 <b>{codename}</b>\n\n"
                f"📍 {category} | {state}\n"
                f"🎂 Idade: {age}\n\n"
                f"💬 <b>Bio:</b>\n{description}\n\n"
                f"📏 <b>Físico:</b>\n"
                f"• Altura: {height}\n"
                f"• Cabelo: {hair_color}\n"
                f"• Olhos: {eye_color}\n"
            )
            
            # Adicionar "dote" se aplicável
            if endowment and endowment != '-':
                info_text += f"• Dote: {endowment}\n"
            
            # Enviar no DM
            await self.bot.send_message(
                chat_id=user_id,
                text=info_text,
                parse_mode='HTML'
            )
            
            await callback.answer("Informações enviadas no privado!", show_alert=False)
            
            logger.info(f"info.opened user={user_id} author={author_id} post={post_id}")
            
        except Exception as e:
            logger.error(f"Erro ao mostrar info: {e}", exc_info=True)
            await callback.answer("Erro ao obter informações.", show_alert=True)
    
    async def handle_comments(self, callback: CallbackQuery):
        """
        Mostra comentários do post.
        """
        try:
            callback_data = callback.data
            user_id = callback.from_user.id
            
            # Extrair post_id
            post_id = CallbackExtractor.extract_post_id(callback_data)
            
            # Obter post
            post = await self.post_service.get_post(post_id)
            if not post:
                await callback.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            # Obter comentários (últimos 5)
            comments = await self._get_comments(post_id, limit=5)
            
            # Montar texto
            comments_count = post.get('stats', {}).get('comments', 0)
            
            if not comments:
                text = f"💭 <b>Comentários ({comments_count})</b>\n\nAinda não há comentários neste post."
            else:
                text = f"💭 <b>Comentários ({comments_count})</b>\n\n"
                
                for comment in comments:
                    author_id = int(comment['author_id'])
                    author = await self.user_service.get_user(author_id)
                    codename = author.get('codename', 'Anônimo') if author else 'Anônimo'
                    
                    text += f"<b>{codename}:</b> {comment['text']}\n\n"
            
            # Criar teclado
            keyboard = self.ui_builder.create_comments_keyboard(
                post_id=post_id,
                has_more=len(comments) >= 5,
                page=0
            )
            
            # Enviar no DM
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            await callback.answer("Comentários enviados no privado!", show_alert=False)
            
            logger.info(f"comments.opened user={user_id} post={post_id}")
            
        except Exception as e:
            logger.error(f"Erro ao mostrar comentários: {e}", exc_info=True)
            await callback.answer("Erro ao obter comentários.", show_alert=True)
    
    async def handle_comment_write(self, message: Message, post_id: str):
        """
        Processa escrita de comentário.
        
        Args:
            message: Mensagem do usuário
            post_id: ID do post
        """
        try:
            user_id = message.from_user.id
            text = message.text
            
            # Validar tamanho
            if not text or len(text) < 1 or len(text) > 600:
                await message.reply(
                    "❌ Comentário deve ter entre 1 e 600 caracteres."
                )
                return
            
            # Antispam: 1 comentário a cada 10s por usuário por post
            allowed, retry_after = self.antispam.check_and_consume(
                user_id=user_id,
                action='comment',
                scope_key=post_id
            )
            
            if not allowed:
                await message.reply(
                    f"⏳ Aguarde {retry_after:.0f}s antes de comentar novamente neste post."
                )
                logger.warning(f"error.rate_limit user={user_id} action=comment post={post_id}")
                return
            
            # Adicionar comentário
            comment_id = await self.post_service.add_comment(post_id, user_id, text)
            
            # Atualizar teclado do post no grupo (se necessário)
            await self._update_post_keyboard(post_id)
            
            await message.reply(
                "✅ Comentário adicionado com sucesso!"
            )
            
            logger.info(f"comment.added user={user_id} post={post_id} comment={comment_id}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar comentário: {e}", exc_info=True)
            await message.reply("Erro ao adicionar comentário.")
    
    async def _get_comments(self, post_id: str, limit: int = 5) -> list:
        """Obtém comentários de um post."""
        try:
            comments_ref = self.post_service.db.collection('comments').document(post_id).collection('items')
            query = comments_ref.order_by('created_at', direction='DESCENDING').limit(limit)
            
            docs = query.stream()
            
            comments = []
            for doc in docs:
                comment_data = doc.to_dict()
                comment_data['id'] = doc.id
                comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            logger.error(f"Erro ao obter comentários: {e}", exc_info=True)
            return []
    
    async def _update_post_keyboard(self, post_id: str):
        """
        Atualiza teclado do post no grupo após mudança de contador.
        
        Args:
            post_id: ID do post
        """
        try:
            # Obter post
            post = await self.post_service.get_post(post_id)
            if not post:
                return
            
            # Obter contadores atualizados
            counts = post.get('stats', {})
            
            # Criar novo teclado
            keyboard = self.ui_builder.create_combined_keyboard(
                post_id=post_id,
                counts=counts,
                viewer_user_id=0,
                current_index=post.get('telegram', {}).get('last_media_index', 0),
                total_media=len(post.get('media', []))
            )
            
            # Atualizar nos grupos
            telegram_data = post.get('telegram', {})
            
            # Freemium
            freemium = telegram_data.get('freemium', {})
            if freemium.get('chat_id') and freemium.get('message_id'):
                try:
                    # Se for album+panel, atualizar o painel
                    message_id = freemium.get('panel_message_id') or freemium.get('message_id')
                    
                    await self.bot.edit_message_reply_markup(
                        chat_id=freemium['chat_id'],
                        message_id=message_id,
                        reply_markup=keyboard
                    )
                except TelegramBadRequest as e:
                    logger.warning(f"Não foi possível atualizar teclado no Freemium: {e}")
            
            # Premium
            premium = telegram_data.get('premium', {})
            if premium.get('chat_id') and premium.get('message_id'):
                try:
                    message_id = premium.get('panel_message_id') or premium.get('message_id')
                    
                    await self.bot.edit_message_reply_markup(
                        chat_id=premium['chat_id'],
                        message_id=message_id,
                        reply_markup=keyboard
                    )
                except TelegramBadRequest as e:
                    logger.warning(f"Não foi possível atualizar teclado no Premium: {e}")
                    
        except Exception as e:
            logger.error(f"Erro ao atualizar teclado do post: {e}", exc_info=True)

