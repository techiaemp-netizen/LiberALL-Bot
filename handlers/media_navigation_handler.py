"""
Handler para navegação de mídia em posts com múltiplas fotos/vídeos.
Implementa a funcionalidade de navegação anterior/próximo para media groups.
"""

import logging
from typing import List, Dict, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from services.post_service import PostService
from utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class MediaNavigationHandler:
    """Handler para navegação de mídia em posts."""
    
    def __init__(self, bot, post_service: PostService, error_handler: ErrorHandler):
        self.bot = bot
        self.post_service = post_service
        self.error_handler = error_handler
    
    async def handle_media_navigation(self, query: CallbackQuery):
        """Processa callbacks de navegação de mídia."""
        try:
            callback_data = query.data
            user_id = query.from_user.id
            
            # Parse do callback: nav_media_{post_id}_{action}_{current_index}
            parts = callback_data.split('_')
            if len(parts) < 4:
                await query.answer("❌ Dados de navegação inválidos.", show_alert=True)
                return
            
            post_id = parts[2]
            action = parts[3]  # 'prev' ou 'next'
            current_index = int(parts[4]) if len(parts) > 4 else 0
            
            # Obter dados do post
            post = await self.post_service.get_post(post_id)
            if not post:
                await query.answer("❌ Post não encontrado.", show_alert=True)
                return
            
            media_files = post.get('media_files', [])
            if not media_files or len(media_files) <= 1:
                await query.answer("📷 Este post não possui múltiplas mídias.", show_alert=True)
                return
            
            # Calcular novo índice
            if action == 'prev':
                new_index = (current_index - 1) % len(media_files)
            elif action == 'next':
                new_index = (current_index + 1) % len(media_files)
            else:
                await query.answer("❌ Ação de navegação inválida.", show_alert=True)
                return
            
            # Obter mídia atual
            current_media = media_files[new_index]
            media_type = current_media.get('type', 'image')
            file_id = current_media.get('file_id')
            
            if not file_id:
                await query.answer("❌ Mídia não encontrada.", show_alert=True)
                return
            
            # Criar teclado de navegação
            navigation_keyboard = self._create_navigation_keyboard(post_id, new_index, len(media_files))
            
            # Criar caption com informações
            caption = self._create_media_caption(post, new_index, len(media_files))
            
            # Editar mensagem com nova mídia
            if media_type in ['image', 'photo']:
                await query.message.edit_media(
                    media=query.message.photo[-1].file_id if query.message.photo else file_id,
                    reply_markup=navigation_keyboard
                )
                # Como não podemos editar o tipo de mídia, enviamos nova mensagem
                await query.message.delete()
                await self.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=file_id,
                    caption=caption,
                    reply_markup=navigation_keyboard,
                    parse_mode='HTML'
                )
            elif media_type == 'video':
                await query.message.delete()
                await self.bot.send_video(
                    chat_id=query.message.chat.id,
                    video=file_id,
                    caption=caption,
                    reply_markup=navigation_keyboard,
                    parse_mode='HTML'
                )
            
            await query.answer(f"📷 Mídia {new_index + 1} de {len(media_files)}")
            
        except Exception as e:
            logger.error(f"Erro na navegação de mídia: {e}", exc_info=True)
            await query.answer("❌ Erro ao navegar pela mídia.", show_alert=True)
    
    def _create_navigation_keyboard(self, post_id: str, current_index: int, total_media: int) -> InlineKeyboardMarkup:
        """Cria teclado de navegação para mídia."""
        buttons = []
        
        # Primeira linha: navegação
        nav_buttons = []
        if total_media > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Anterior",
                    callback_data=f"nav_media_{post_id}_prev_{current_index}"
                )
            )
            nav_buttons.append(
                InlineKeyboardButton(
                    text=f"{current_index + 1}/{total_media}",
                    callback_data="noop"  # Botão informativo
                )
            )
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Próximo ▶️",
                    callback_data=f"nav_media_{post_id}_next_{current_index}"
                )
            )
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Segunda linha: ações do post
        action_buttons = [
            InlineKeyboardButton(text="❤️ Match", callback_data=f"match:post:{post_id}"),
            InlineKeyboardButton(text="⭐ Favoritar", callback_data=f"favorite:post:{post_id}"),
            InlineKeyboardButton(text="ℹ️ Info", callback_data=f"info:post:{post_id}")
        ]
        buttons.append(action_buttons)
        
        # Terceira linha: comentários e fechar
        final_buttons = [
            InlineKeyboardButton(text="💭 Comentários", callback_data=f"comments:post:{post_id}"),
            InlineKeyboardButton(text="❌ Fechar", callback_data="close_media_nav")
        ]
        buttons.append(final_buttons)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def _create_combined_keyboard(self, post_id: str, current_index: int, total_media: int, interaction_keyboard: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
        """Cria teclado combinado com navegação de mídia e interações do post."""
        buttons = []
        
        # Primeira linha: navegação de mídia (apenas se há múltiplas mídias)
        if total_media > 1:
            nav_buttons = [
                InlineKeyboardButton(
                    text="◀️ Anterior",
                    callback_data=f"nav_media_{post_id}_prev_{current_index}"
                ),
                InlineKeyboardButton(
                    text=f"{current_index + 1}/{total_media}",
                    callback_data="noop"
                ),
                InlineKeyboardButton(
                    text="Próximo ▶️",
                    callback_data=f"nav_media_{post_id}_next_{current_index}"
                )
            ]
            buttons.append(nav_buttons)
        
        # Adicionar todas as linhas do teclado de interação original
        if interaction_keyboard and interaction_keyboard.inline_keyboard:
            for row in interaction_keyboard.inline_keyboard:
                buttons.append(row)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def _create_media_caption(self, post: Dict, current_index: int, total_media: int) -> str:
        """Cria caption para a mídia com informações do post."""
        caption = f"📷 <b>Mídia {current_index + 1} de {total_media}</b>\n\n"
        
        # Adicionar informações do post
        if post.get('text'):
            caption += f"{post['text']}\n\n"
        
        # Adicionar informações do autor (anônimo)
        author_info = post.get('author_info', {})
        if author_info:
            caption += f"👤 {author_info.get('codename', 'Anônimo')} · "
            caption += f"{author_info.get('category', 'Indefinido')} · "
            caption += f"{author_info.get('state', 'BR')}\n"
        
        return caption
    
    async def create_media_group_with_navigation(self, chat_id: int, post_id: str, media_files: List[Dict], caption: str = "") -> bool:
        """Cria um media group com navegação integrada."""
        try:
            if not media_files or len(media_files) <= 1:
                return False
            
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            
            # Preparar media group
            media_group = []
            for i, media in enumerate(media_files):
                if media.get('type') in ['image', 'photo']:
                    media_item = InputMediaPhoto(
                        media=media['file_id'],
                        caption=caption if i == 0 else None,
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
            
            if not media_group:
                return False
            
            # Enviar media group
            messages = await self.bot.send_media_group(chat_id, media_group)
            
            # Adicionar teclado de navegação na primeira mensagem
            if messages:
                navigation_keyboard = self._create_navigation_keyboard(post_id, 0, len(media_files))
                try:
                    await self.bot.edit_message_reply_markup(
                        chat_id=chat_id,
                        message_id=messages[0].message_id,
                        reply_markup=navigation_keyboard
                    )
                except Exception as e:
                    logger.warning(f"Não foi possível adicionar navegação ao media group: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar media group com navegação: {e}")
            return False