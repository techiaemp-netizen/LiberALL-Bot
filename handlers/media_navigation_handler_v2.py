"""
Media Navigation Handler V2 - Navegação de mídia com teclado combinado.

Implementa navegação prev/next mantendo teclado de ações.
Suporta modo carousel (editMessageMedia) e ignora no modo album+panel.
"""
import logging
from aiogram import Bot
from aiogram.types import CallbackQuery, InputMediaPhoto, InputMediaVideo
from aiogram.exceptions import TelegramBadRequest

from services.post_service_v2 import PostServiceV2
from services.antispam_service import get_antispam_service
from constants.normalized_callbacks import CallbackExtractor
from core.ui_builder_v2 import UIBuilderV2

logger = logging.getLogger(__name__)


class MediaNavigationHandlerV2:
    """
    Handler de navegação de mídia com callbacks normalizados.
    
    Formato: media:prev|next:<postId>:<index>
    """
    
    def __init__(
        self,
        bot: Bot,
        post_service: PostServiceV2,
        bot_username: str
    ):
        """
        Inicializa o handler.
        
        Args:
            bot: Instância do bot
            post_service: Serviço de posts V2
            bot_username: Username do bot
        """
        self.bot = bot
        self.post_service = post_service
        self.ui_builder = UIBuilderV2(bot_username)
        
        # Antispam para navegação
        self.antispam = get_antispam_service()
        
        logger.info("MediaNavigationHandlerV2 inicializado")
    
    async def handle_navigation(self, callback: CallbackQuery):
        """
        Processa navegação de mídia (prev/next).
        
        Args:
            callback: Callback query
        """
        try:
            callback_data = callback.data
            user_id = callback.from_user.id
            
            # Antispam: máx 5 navegações por segundo
            allowed, retry_after = self.antispam.check_and_consume(
                user_id=user_id,
                action='navigation',
                scope_key=None
            )
            
            if not allowed:
                await callback.answer(
                    "⏳ Você está navegando muito rápido. Aguarde um momento.",
                    show_alert=False
                )
                logger.warning(f"error.rate_limit user={user_id} action=navigation")
                return
            
            # Extrair partes: media:prev|next:<postId>:<index>
            parts = callback_data.split(':')
            
            if len(parts) != 4:
                logger.error(f"Callback de navegação inválido: {callback_data}")
                await callback.answer("Erro de navegação.", show_alert=True)
                return
            
            direction = parts[1]  # prev ou next
            post_id = parts[2]
            current_index = int(parts[3])
            
            # Obter post
            post = await self.post_service.get_post(post_id)
            if not post:
                await callback.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            # Verificar modo de renderização
            render_mode = post.get('render_mode', 'carousel')
            
            if render_mode == 'album+panel':
                # No modo album+panel, navegação não é suportada (álbum já mostra tudo)
                await callback.answer(
                    "Navegação não disponível neste formato.",
                    show_alert=False
                )
                return
            
            # Modo carousel: editar mídia
            await self._navigate_carousel(
                callback=callback,
                post=post,
                post_id=post_id,
                direction=direction,
                current_index=current_index
            )
            
        except Exception as e:
            logger.error(f"Erro na navegação de mídia: {e}", exc_info=True)
            await callback.answer("Erro ao navegar.", show_alert=True)
    
    async def _navigate_carousel(
        self,
        callback: CallbackQuery,
        post: dict,
        post_id: str,
        direction: str,
        current_index: int
    ):
        """
        Navega no modo carousel (editMessageMedia).
        
        Args:
            callback: Callback query
            post: Dados do post
            post_id: ID do post
            direction: 'prev' ou 'next'
            current_index: Índice atual
        """
        try:
            media_list = post.get('media', [])
            total_media = len(media_list)
            
            if total_media <= 1:
                await callback.answer("Apenas uma mídia disponível.", show_alert=False)
                return
            
            # Calcular novo índice
            if direction == 'prev':
                new_index = max(0, current_index - 1)
            else:  # next
                new_index = min(total_media - 1, current_index + 1)
            
            # Se não mudou, avisar
            if new_index == current_index:
                await callback.answer(
                    "Você já está no início/fim." if direction == 'prev' else "Você já está no final.",
                    show_alert=False
                )
                return
            
            # Obter nova mídia
            new_media = media_list[new_index]
            media_url = new_media['url']
            media_type = new_media['type']
            
            # Aplicar blur se necessário
            if post.get('monetized', False):
                # Verificar se estamos no grupo Lite
                chat_id = callback.message.chat.id
                if chat_id == self.post_service.freemium_group_id:
                    media_url = self.post_service._apply_blur_transform(media_url)
            
            # Criar teclado combinado atualizado
            counts = post.get('stats', {})
            keyboard = self.ui_builder.create_combined_keyboard(
                post_id=post_id,
                counts=counts,
                viewer_user_id=callback.from_user.id,
                current_index=new_index,
                total_media=total_media
            )
            
            # Editar mídia
            if media_type == 'photo':
                new_media_obj = InputMediaPhoto(media=media_url)
            else:  # video
                new_media_obj = InputMediaVideo(media=media_url)
            
            try:
                await callback.message.edit_media(
                    media=new_media_obj,
                    reply_markup=keyboard
                )
                
                # Atualizar last_media_index no Firestore
                await self._update_media_index(post_id, new_index)
                
                await callback.answer()
                
                logger.debug(f"media.navigated post={post_id} index={new_index}/{total_media}")
                
            except TelegramBadRequest as e:
                logger.error(f"Erro ao editar mídia: {e}")
                await callback.answer("Erro ao trocar mídia.", show_alert=True)
                
        except Exception as e:
            logger.error(f"Erro ao navegar no carousel: {e}", exc_info=True)
            await callback.answer("Erro ao navegar.", show_alert=True)
    
    async def _update_media_index(self, post_id: str, index: int):
        """
        Atualiza last_media_index no post.
        
        Args:
            post_id: ID do post
            index: Novo índice
        """
        try:
            post_ref = self.post_service.db.collection('posts').document(post_id)
            post_ref.update({
                'telegram.last_media_index': index
            })
            
        except Exception as e:
            logger.error(f"Erro ao atualizar media index: {e}", exc_info=True)

