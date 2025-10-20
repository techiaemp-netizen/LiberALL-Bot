"""
Handler para processar interações com posts (match, info, galeria, favoritos, comentários).
Implementa toda a lógica de interação do usuário com posts no grupo.
"""

import logging
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.user_service import UserService
from services.post_service import PostService
from services.match_service import MatchService
from utils.ui_builder import UIBuilder
from utils.error_handler import ErrorHandler
from constants.callbacks import PostingCallbacks, MatchCallbacks, FavoritesCallbacks

logger = logging.getLogger(__name__)

class PostInteractionHandler:
    """Handler para processar interações com posts."""
    
    def __init__(self, bot=None, user_service=None, post_service=None, error_handler=None, bot_username=None, match_service: MatchService = None):
        self.bot = bot
        self.bot_username = bot_username
        self.user_service = user_service or UserService()
        self.post_service = post_service or PostService()
        # Exigir MatchService injetado para consistência com FirebaseService e simulação
        if match_service is None:
            raise ValueError("PostInteractionHandler requer 'match_service' injetado")
        self.match_service = match_service
        self.ui_builder = UIBuilder()
        self.error_handler = error_handler or ErrorHandler()
    
    async def handle_info_request(self, call):
        """Busca e envia informações sobre o autor do post ou do novo membro."""
        try:
            # Extrair dados do callback
            parts = call.data.split(':')
            target_type = parts[1]
            target_id = parts[2]
            
            author_id = None
            # CORREÇÃO PRINCIPAL AQUI:
            if target_type == "welcome":
                author_id = int(target_id)
            elif target_type == "post":
                # Lógica futura: Obter o author_id a partir do post_id da base de dados.
                # post_data = await self.post_service.get_post_by_id(target_id)
                # author_id = post_data.get('author_id')
                await self.bot.send_message(call.from_user.id, "A funcionalidade de 'Info' para posts específicos estará disponível em breve.")
                return
            
            if author_id:
                user_data = await self.user_service.get_user_data(author_id)
                if user_data:
                    info_text = (
                        f"ℹ️ **Informações do Utilizador**\n\n"
                        f"**Codinome:** {user_data.get('codename', 'N/A')}\n"
                        f"**Categoria:** {user_data.get('category', 'N/A')}\n"
                        f"**Estado:** {user_data.get('state', 'N/A')}"
                    )
                    await self.bot.send_message(call.from_user.id, info_text, parse_mode='Markdown')
                else:
                    await self.bot.send_message(call.from_user.id, "Não foi possível encontrar informações sobre este utilizador.")
                    
        except Exception as e:
            logging.error(f"Erro em handle_info_request: {e}", exc_info=True)
            await self.bot.send_message(call.from_user.id, "Ocorreu um erro ao buscar as informações.")
    
    async def handle_match_request(self, call):
        """Processa um pedido de match (funcionalidade diferenciada para welcome vs post)."""
        try:
            # Extrair dados do callback
            parts = call.data.split(':')
            target_type = parts[1]
            target_id = parts[2]
            
            if target_type == "welcome":
                # Lógica para match com novo utilizador
                target_user_id = int(target_id)
                user_data = await self.user_service.get_user_data(target_user_id)
                if user_data:
                    await self.bot.send_message(
                        call.from_user.id,
                        f"💕 Match enviado para {user_data.get('codename', 'utilizador')}! "
                        f"A funcionalidade de matches entre utilizadores estará disponível em breve."
                    )
                else:
                    await self.bot.send_message(call.from_user.id, "Utilizador não encontrado.")
            elif target_type == "post":
                # Lógica para match com post
                await self.bot.send_message(
                    call.from_user.id,
                    "A funcionalidade de match para posts específicos estará disponível em breve."
                )
                
        except Exception as e:
            logging.error(f"Erro em handle_match_request: {e}", exc_info=True)
            await self.bot.send_message(call.from_user.id, "Ocorreu um erro ao processar o match.")
    
    async def handle_favorite_request(self, call):
        """Processa um pedido de favorito (funcionalidade diferenciada para welcome vs post)."""
        try:
            # Extrair dados do callback
            parts = call.data.split(':')
            target_type = parts[1]
            target_id = parts[2]
            
            if target_type == "welcome":
                # Lógica para favoritar novo utilizador
                target_user_id = int(target_id)
                user_data = await self.user_service.get_user_data(target_user_id)
                if user_data:
                    # Adicionar aos favoritos
                    await self.user_service.add_favorite(call.from_user.id, target_user_id)
                    await self.bot.send_message(
                        call.from_user.id,
                        f"⭐ {user_data.get('codename', 'utilizador')} foi adicionado aos favoritos!"
                    )
                else:
                    await self.bot.send_message(call.from_user.id, "Utilizador não encontrado.")
            elif target_type == "post":
                # Lógica para favoritar post
                await self.user_service.add_favorite_post(call.from_user.id, target_id)
                await self.bot.send_message(
                    call.from_user.id,
                    "⭐ Post adicionado aos favoritos!"
                )
                
        except Exception as e:
            logging.error(f"Erro em handle_favorite_request: {e}", exc_info=True)
            await self.bot.send_message(call.from_user.id, "Ocorreu um erro ao processar o favorito.")
    
    async def handle_comment_request(self, call):
        """Processa um pedido de comentário."""
        try:
            # Extrair dados do callback
            parts = call.data.split(':')
            target_type = parts[1]
            target_id = parts[2]
            
            # Criar teclado para comentários
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Escrever Comentário", callback_data=f"write_comment:{target_type}:{target_id}")],
                [InlineKeyboardButton(text="👀 Ver Comentários", callback_data=f"view_comments:{target_type}:{target_id}")],
                [InlineKeyboardButton(text="❌ Fechar", callback_data="close_comments")]
            ])
            
            await self.bot.send_message(
                call.from_user.id,
                "💭 **Sistema de Comentários**\n\nEscolha uma opção:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logging.error(f"Erro em handle_comment_request: {e}", exc_info=True)
            await self.bot.send_message(call.from_user.id, "Ocorreu um erro ao processar o comentário.")
    
    async def handle_post_interaction(self, update, context=None):
        """Processa interações com posts."""
        if hasattr(update, 'callback_query'):
            query = update.callback_query
        else:
            query = update
            
        callback_data = query.data
        user_id = query.from_user.id
        
        try:
            await query.answer()
            
            logger.info(f"Processando interação com post: {callback_data} para usuário {user_id}")
            
            # Extrair post_id do callback_data
            post_id = self._extract_post_id(callback_data)
            if not post_id:
                logger.error(f"Post ID não encontrado no callback: {callback_data}")
                await query.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            # Roteamento baseado no tipo de interação (formato novo: ação:post:id)
            if callback_data.startswith('match:post:'):
                await self._handle_match_action(query, user_id, post_id, callback_data)
                
            elif callback_data.startswith('info:post:'):
                await self._handle_info_action(query, user_id, post_id)
                
            elif callback_data.startswith('gallery:post:'):
                await self._handle_gallery_action(query, user_id, post_id)
                
            elif callback_data.startswith('favorite:post:'):
                await self._handle_favorite_action(query, user_id, post_id, callback_data)
                
            elif callback_data.startswith('comments:post:'):
                await self._handle_comment_action(query, user_id, post_id)
                
            # Roteamento baseado no tipo de interação (formato legado)
            elif callback_data.startswith('match_post_'):
                await self._handle_match_action(query, user_id, post_id, callback_data)
                
            elif callback_data.startswith('info_post_'):
                await self._handle_info_action(query, user_id, post_id)
                
            elif callback_data.startswith('gallery_post_'):
                await self._handle_gallery_action(query, user_id, post_id)
                
            elif callback_data.startswith('favorite_post_'):
                await self._handle_favorite_action(query, user_id, post_id, callback_data)
                
            elif callback_data.startswith('comment_post_'):
                await self._handle_comment_action(query, user_id, post_id)
                
            # Adicionar suporte para callbacks de fechamento
            elif callback_data == "close_info":
                await self.handle_close_info(query)
                
            else:
                logger.warning(f"Callback de interação não reconhecido: {callback_data}")
                await query.answer("❌ Ação não reconhecida.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Erro ao processar interação com post {callback_data}: {e}", exc_info=True)
            await self.error_handler.handle_callback_error(query, "Erro ao processar interação")
    
    def _extract_post_id(self, callback_data: str) -> str:
        """Extrai o post_id do callback_data."""
        try:
            # Suporte para formato novo: ação:post:id
            if ':' in callback_data:
                parts = callback_data.split(':')
                if len(parts) >= 3 and parts[1] == 'post':
                    post_id = parts[2]
                    # Validar se é um UUID válido (formato do Firestore)
                    if post_id and len(post_id) > 5 and post_id != 'post':
                        logger.debug(f"Post ID extraído (formato novo): {post_id} de {callback_data}")
                        return post_id
            
            # Formato legado: action_post_POST_ID
            # Ex: match_post_post_1760569943, gallery_post_post_1760569943
            
            # Procurar pelo padrão "post_" seguido do ID
            if "post_" in callback_data:
                # Encontrar a última ocorrência de "post_"
                last_post_index = callback_data.rfind("post_")
                if last_post_index != -1:
                    # Extrair tudo após "post_"
                    post_id = callback_data[last_post_index + 5:]  # +5 para pular "post_"
                    # Validar se não é apenas "post" ou vazio
                    if post_id and post_id != 'post' and len(post_id) > 5:
                        logger.debug(f"Post ID extraído: {post_id} de {callback_data}")
                        return post_id
            
            # Fallback: tentar extrair usando split
            parts = callback_data.split('_')
            if len(parts) >= 3 and 'post' in parts:
                # Encontrar a posição da palavra "post" e pegar as partes seguintes
                post_indices = [i for i, part in enumerate(parts) if part == 'post']
                if post_indices:
                    last_post_index = post_indices[-1]
                    if last_post_index + 1 < len(parts):
                        # Pegar apenas a parte após "post"
                        post_id = parts[last_post_index + 1]
                        # Validar se é um ID válido
                        if post_id and post_id != 'post' and len(post_id) > 5:
                            logger.debug(f"Post ID extraído (fallback): {post_id} de {callback_data}")
                            return post_id
            
            # Fallback adicional: se callback_data contém apenas "post", retornar None
            if callback_data.strip() == "post":
                logger.warning(f"Callback data inválido (apenas 'post'): {callback_data}")
                return None
            
            logger.warning(f"Não foi possível extrair post_id válido de: {callback_data}")
            return None
        except Exception as e:
            logger.error(f"Erro ao extrair post_id de {callback_data}: {e}")
            return None
    
    async def _handle_match_action(self, query, user_id: int, post_id: str, callback_data: str):
        """Processa ação de match com post."""
        try:
            # Obter dados do post
            post = await self.post_service.get_post(post_id)
            if not post:
                await query.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = post.get('author_id')
            if not author_id:
                await query.answer("❌ Autor do post não encontrado.", show_alert=True)
                return
            
            if author_id == user_id:
                await query.answer("❌ Você não pode dar match no seu próprio post.", show_alert=True)
                return
            
            # Verificar se já existe match
            existing_match = await self.match_service.check_match_exists(user_id, author_id)
            if existing_match:
                await query.answer("💕 Você já deu match neste perfil!", show_alert=True)
                return
            
            # Criar match
            match_result = await self.match_service.create_match(user_id, author_id, post_id)
            
            if match_result:
                # Obter dados do autor para resposta
                author_data = await self.user_service.get_user_data(author_id)
                author_name = author_data.get('codename', 'Usuário') if author_data else 'Usuário'
                
                await query.answer(f"💕 Match enviado para {author_name}!", show_alert=True)
                
                # Notificar o autor do post (se estiver online)
                try:
                    user_data = await self.user_service.get_user_data(user_id)
                    user_name = user_data.get('codename', 'Alguém') if user_data else 'Alguém'
                    
                    await self.bot.send_message(
                        author_id,
                        f"💕 <b>Novo Match!</b>\n\n"
                        f"{user_name} deu match no seu post!\n"
                        f"Acesse seus matches para conversar.",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.warning(f"Não foi possível notificar autor do match: {e}")
            else:
                await query.answer("❌ Erro ao processar match. Tente novamente.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Erro ao processar match: {e}", exc_info=True)
            await query.answer("❌ Erro interno. Tente novamente.", show_alert=True)
    
    async def _handle_info_action(self, query, user_id: int, post_id: str):
        """Processa ação de visualizar informações do autor do post."""
        try:
            # Obter dados do post
            post = await self.post_service.get_post(post_id)
            if not post:
                await query.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = post.get('author_id')
            if not author_id:
                await query.answer("❌ Autor do post não encontrado.", show_alert=True)
                return
            
            # Obter dados do autor
            author_data = await self.user_service.get_user_data(author_id)
            if not author_data:
                await query.answer("❌ Informações do autor não encontradas.", show_alert=True)
                return
            
            # Criar mensagem com informações
            info_text = self._build_author_info_text(author_data)
            
            # Criar teclado com opções
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💕 Match", callback_data=f"match:post:{post_id}"),
                    InlineKeyboardButton(text="⭐ Favoritar", callback_data=f"favorite:post:{post_id}")
                ],
                [
                    InlineKeyboardButton(text="🖼️ Ver Galeria", callback_data=f"gallery:post:{post_id}"),
                    InlineKeyboardButton(text="❌ Fechar", callback_data="close_info")
                ]
            ])
            
            # Enviar informações em mensagem privada
            await self.bot.send_message(
                user_id,
                info_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            await query.answer("ℹ️ Informações enviadas no privado!")
            
        except Exception as e:
            logger.error(f"Erro ao processar info: {e}", exc_info=True)
            await query.answer("❌ Erro ao obter informações.", show_alert=True)
    
    async def _handle_gallery_action(self, query, user_id: int, post_id: str):
        """Processa ação de visualizar galeria do autor do post."""
        try:
            # Obter dados do post
            post = await self.post_service.get_post(post_id)
            if not post:
                await query.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = post.get('author_id')
            if not author_id:
                await query.answer("❌ Autor do post não encontrado.", show_alert=True)
                return
            
            # Obter posts do autor
            author_posts = await self.post_service.get_user_posts(author_id, limit=10)
            
            if not author_posts:
                await query.answer("📷 Este usuário ainda não possui posts na galeria.", show_alert=True)
                return
            
            # Obter dados do autor
            author_data = await self.user_service.get_user_data(author_id)
            author_name = author_data.get('codename', 'Usuário') if author_data else 'Usuário'
            
            # Criar mensagem da galeria
            gallery_text = f"🖼️ <b>Galeria de {author_name}</b>\n\n"
            gallery_text += f"📊 Total de posts: {len(author_posts)}\n\n"
            
            # Mostrar preview dos posts
            for i, post_item in enumerate(author_posts[:5], 1):
                media_count = len(post_item.get('media_files', []))
                post_text = post_item.get('text', '')[:50] + '...' if len(post_item.get('text', '')) > 50 else post_item.get('text', '')
                
                gallery_text += f"{i}. "
                if media_count > 0:
                    gallery_text += f"📷 {media_count} mídia(s)"
                if post_text:
                    gallery_text += f" - {post_text}"
                gallery_text += "\n"
            
            if len(author_posts) > 5:
                gallery_text += f"\n... e mais {len(author_posts) - 5} posts"
            
            # Criar teclado
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💕 Match", callback_data=f"match:post:{post_id}"),
                    InlineKeyboardButton(text="⭐ Favoritar", callback_data=f"favorite:post:{post_id}")
                ],
                [InlineKeyboardButton(text="❌ Fechar", callback_data="close_info")]
            ])
            
            # Enviar galeria em mensagem privada
            await self.bot.send_message(
                user_id,
                gallery_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            await query.answer("🖼️ Galeria enviada no privado!")
            
        except Exception as e:
            logger.error(f"Erro ao processar galeria: {e}", exc_info=True)
            await query.answer("❌ Erro ao carregar galeria.", show_alert=True)
    
    async def _handle_favorite_action(self, query, user_id: int, post_id: str, callback_data: str):
        """Processa ação de favoritar/desfavoritar post."""
        try:
            # Obter dados do post
            post = await self.post_service.get_post(post_id)
            if not post:
                await query.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            author_id = post.get('author_id')
            if not author_id:
                await query.answer("❌ Autor do post não encontrado.", show_alert=True)
                return
            
            if author_id == user_id:
                await query.answer("❌ Você não pode favoritar seu próprio post.", show_alert=True)
                return
            
            # Verificar se já está favoritado
            is_favorited = await self.post_service.is_favorited(user_id, post_id)
            
            if is_favorited:
                # Remover dos favoritos
                success = await self.post_service.remove_favorite(user_id, post_id)
                if success:
                    await query.answer("💔 Post removido dos favoritos.", show_alert=True)
                else:
                    await query.answer("❌ Erro ao remover dos favoritos.", show_alert=True)
            else:
                # Adicionar aos favoritos
                success = await self.post_service.add_favorite(user_id, post_id)
                if success:
                    await query.answer("⭐ Post adicionado aos favoritos!", show_alert=True)
                else:
                    await query.answer("❌ Erro ao adicionar aos favoritos.", show_alert=True)
                    
        except Exception as e:
            logger.error(f"Erro ao processar favorito: {e}", exc_info=True)
            await query.answer("❌ Erro interno. Tente novamente.", show_alert=True)
    
    async def _handle_comment_action(self, query, user_id: int, post_id: str):
        """Processa ação de comentar no post."""
        try:
            # Obter dados do post
            post = await self.post_service.get_post(post_id)
            if not post:
                await query.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            # Obter comentários existentes
            comments = await self.post_service.get_post_comments(post_id)
            comment_count = len(comments) if comments else 0
            
            # Criar mensagem com comentários
            comments_text = f"💭 <b>Comentários ({comment_count})</b>\n\n"
            
            if comments:
                for comment in comments[-5:]:  # Mostrar últimos 5 comentários
                    author_data = await self.user_service.get_user_data(comment.get('author_id'))
                    author_name = author_data.get('codename', 'Anônimo') if author_data else 'Anônimo'
                    
                    comments_text += f"👤 <b>{author_name}</b>\n"
                    comments_text += f"{comment.get('text', '')}\n"
                    comments_text += f"🕐 {comment.get('created_at', '')}\n\n"
                
                if comment_count > 5:
                    comments_text += f"... e mais {comment_count - 5} comentários\n\n"
            else:
                comments_text += "Ainda não há comentários neste post.\n\n"
            
            comments_text += "💬 <i>Digite seu comentário para adicionar:</i>"
            
            # Definir estado do usuário para aguardar comentário
            from constants.user_states import UserStates
            await self.user_service.set_user_state(user_id, UserStates.AWAITING_COMMENT)
            await self.user_service.update_user_context(user_id, {'commenting_post_id': post_id})
            
            # Criar teclado
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel_comment")]
            ])
            
            # Enviar comentários em mensagem privada
            await self.bot.send_message(
                user_id,
                comments_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            await query.answer("💭 Comentários enviados no privado! Digite seu comentário.")
            
        except Exception as e:
            logger.error(f"Erro ao processar comentários: {e}", exc_info=True)
            await query.answer("❌ Erro ao carregar comentários.", show_alert=True)

    async def handle_comment_text(self, message, user_id: int):
        """Processa texto de comentário enviado pelo usuário."""
        try:
            # Verificar se o usuário está no estado de comentário
            user_data = await self.user_service.get_user_data(user_id)
            if not user_data or user_data.get('state') != 'awaiting_comment':
                return False
            
            # Obter contexto do comentário
            context = user_data.get('context_data', {})
            post_id = context.get('commenting_post_id')
            
            if not post_id:
                await message.reply("❌ Sessão de comentário expirada. Tente novamente.")
                await self.user_service.set_user_state(user_id, 'idle')
                return True
            
            comment_text = message.text
            if not comment_text or len(comment_text.strip()) < 3:
                await message.reply("❌ Comentário muito curto. Digite pelo menos 3 caracteres.")
                return True
            
            if len(comment_text) > 500:
                await message.reply("❌ Comentário muito longo. Máximo de 500 caracteres.")
                return True
            
            # Adicionar comentário
            success = await self.post_service.add_comment(post_id, user_id, comment_text.strip())
            
            if success:
                await message.reply("✅ Comentário adicionado com sucesso!")
                
                # Notificar autor do post (se não for o próprio usuário)
                post = await self.post_service.get_post(post_id)
                if post and post.get('author_id') != user_id:
                    try:
                        user_data = await self.user_service.get_user_data(user_id)
                        commenter_name = user_data.get('codename', 'Alguém') if user_data else 'Alguém'
                        
                        await self.bot.send_message(
                            post.get('author_id'),
                            f"💭 <b>Novo comentário!</b>\n\n"
                            f"{commenter_name} comentou no seu post:\n"
                            f"<i>\"{comment_text[:100]}{'...' if len(comment_text) > 100 else ''}\"</i>",
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.warning(f"Não foi possível notificar autor do comentário: {e}")
            else:
                await message.reply("❌ Erro ao adicionar comentário. Tente novamente.")
            
            # Resetar estado do usuário
            await self.user_service.set_user_state(user_id, 'idle')
            await self.user_service.update_user_context(user_id, {})
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar comentário: {e}", exc_info=True)
            await message.reply("❌ Erro interno. Tente novamente.")
            await self.user_service.set_user_state(user_id, 'idle')
            return True

    async def handle_cancel_comment(self, query):
        """Cancela o processo de comentário."""
        try:
            user_id = query.from_user.id
            
            # Resetar estado do usuário
            await self.user_service.set_user_state(user_id, 'idle')
            await self.user_service.update_user_context(user_id, {})
            
            await query.message.edit_text("❌ Comentário cancelado.")
            await query.answer("Comentário cancelado.")
            
        except Exception as e:
            logger.error(f"Erro ao cancelar comentário: {e}", exc_info=True)
            await query.answer("❌ Erro ao cancelar.")

    def _build_author_info_text(self, author_data: dict) -> str:
        """Constrói texto com informações do autor."""
        info_text = "ℹ️ <b>Informações do Perfil</b>\n\n"
        
        # Informações básicas
        info_text += f"👤 <b>Codinome:</b> {author_data.get('codename', 'N/A')}\n"
        info_text += f"📍 <b>Estado:</b> {author_data.get('state', 'N/A')}\n"
        info_text += f"🏷️ <b>Categoria:</b> {author_data.get('category', 'N/A')}\n"
        
        # Informações adicionais se disponíveis
        if author_data.get('age'):
            info_text += f"🎂 <b>Idade:</b> {author_data['age']} anos\n"
        
        if author_data.get('description'):
            info_text += f"\n📝 <b>Descrição:</b>\n{author_data['description']}\n"
        
        # Informações físicas se disponíveis
        physical_info = []
        if author_data.get('height'):
            physical_info.append(f"Altura: {author_data['height']}")
        if author_data.get('hair_color'):
            physical_info.append(f"Cabelos: {author_data['hair_color']}")
        if author_data.get('eye_color'):
            physical_info.append(f"Olhos: {author_data['eye_color']}")
        
        if physical_info:
            info_text += f"\n👁️ <b>Características:</b> {' • '.join(physical_info)}\n"
        
        return info_text
    
    async def handle_close_info(self, query):
        """Fecha mensagem de informações."""
        try:
            await query.message.delete()
            await query.answer("✅ Fechado!")
        except Exception as e:
            logger.error(f"Erro ao fechar info: {e}")
            await query.answer("❌ Erro ao fechar.")