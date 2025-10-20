"""
Handler para o fluxo completo de postagem.
Implementa todo o processo de criação, edição e publicação de posts.
"""

import logging
import config
import asyncio
import html
import time
from constants.user_states import UserStates
from datetime import datetime
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.types import InputMediaPhoto as AIOInputMediaPhoto, InputMediaVideo as AIOInputMediaVideo

from services.user_service import UserService
from services.post_service import PostService
from services.monetization_service import MonetizationService
from services.media_service import MediaService
from services.draft_repo import DraftRepo
from utils.ui_builder import UIBuilder, build_anonymous_label, create_post_interaction_keyboard, create_post_preview_keyboard
from utils.error_handler import ErrorHandler
from constants.callbacks import PostingCallbacks

logger = logging.getLogger(__name__)

# Estados da conversa de postagem
WAITING_CONTENT, WAITING_TITLE, WAITING_DESCRIPTION, WAITING_MEDIA, PREVIEW_POST, MONETIZATION_SETUP = range(6)

class PostingHandler:
    """Handler para o fluxo completo de postagem."""
    
    def __init__(self, bot=None, post_service=None, user_service=None, error_handler=None, media_service=None):
        self.bot = bot
        self.post_service = post_service or PostService()
        self.user_service = user_service or UserService()
        self.error_handler = error_handler or ErrorHandler()
        self.media_service = media_service or MediaService()
        self.draft_repo = DraftRepo()
        
        # Sessões de postagem em memória (para compatibilidade)
        self.posting_sessions = {}
        
        # UI Builder
        self.ui_builder = UIBuilder()

    async def start_posting_flow(self, user_id: int):
        """Inicia o fluxo de criação de post via deep link ou menu.

        Envia uma mensagem ao usuário para escolher o tipo de conteúdo
        e encaminha os próximos passos pelos callbacks de postagem.
        """
        try:
            # Opcionalmente atualizar estado do usuário para indicar início do fluxo
            try:
                await self.user_service.update_user_state(user_id, UserStates.AWAITING_POST_CONTENT)
            except Exception:
                logger.debug("Não foi possível atualizar o estado do usuário para AWAITING_POST_CONTENT.")

            text = (
                "📝 **Criar Novo Post**\n\n"
                "Vamos criar seu post! Escolha o tipo de conteúdo:\n\n"
                "• 📷 Imagem\n"
                "• 📹 Vídeo\n"
                "• 📝 Apenas Texto"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📷 Post com Imagem", callback_data="post_type_image")],
                [InlineKeyboardButton(text="📹 Post com Vídeo", callback_data="post_type_video")],
                [InlineKeyboardButton(text="📝 Post Apenas Texto", callback_data="post_type_text")],
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)],
            ])

            await self.bot.send_message(
                user_id,
                text,
                parse_mode='Markdown',
                reply_markup=keyboard,
            )

        except Exception as e:
            logger.error(f"Erro ao iniciar fluxo de postagem para user_id={user_id}: {e}", exc_info=True)
            try:
                await self.bot.send_message(user_id, "❌ Erro ao iniciar criação de post. Tente novamente mais tarde.")
            except Exception:
                pass

    async def handle_callback_query(self, call: CallbackQuery):
        """Processa callbacks relacionados à postagem."""
        callback_data = call.data
        user_id = call.from_user.id
        
        try:
            # Log estruturado para depuração
            logger.info(f"📝 POSTING CALLBACK: user_id={user_id}, callback={callback_data}")
            
            if callback_data.startswith('post_type_'):
                await self._start_post_creation(call, user_id, callback_data)
                
            elif callback_data == PostingCallbacks.PUBLISH:
                logger.info(f"📤 PUBLISH REQUEST: user_id={user_id}")
                await self._publish_post(call, user_id)
                
            elif callback_data.startswith("post_publish:"):
                logger.info(f"📤 PUBLISH WITH ID REQUEST: user_id={user_id}")
                await self._publish_post_with_id(call, user_id, callback_data)
                
            elif callback_data.startswith(PostingCallbacks.CANCEL):
                logger.info(f"❌ CANCEL REQUEST: user_id={user_id}")
                await self._cancel_post(call, user_id)
                
            elif callback_data.startswith("post_cancel:"):
                logger.info(f"❌ CANCEL WITH ID REQUEST: user_id={user_id}")
                await self._cancel_post_with_id(call, user_id, callback_data)
                
            elif callback_data.startswith('post_monetize'):
                logger.info(f"💰 MONETIZATION REQUEST: user_id={user_id}")
                await self._handle_monetization(call, user_id, callback_data)
                
            elif callback_data.startswith('monetize_price_') or callback_data.startswith('monetize_custom'):
                logger.info(f"💰 MONETIZATION PRICE: user_id={user_id}, callback={callback_data}")
                await self._handle_monetization_price(call, user_id, callback_data)
                
            elif callback_data == PostingCallbacks.EDIT:
                logger.info(f"✏️ EDIT REQUEST: user_id={user_id}")
                await self._edit_post(call, user_id)
                
            elif callback_data == PostingCallbacks.DELETE:
                logger.info(f"🗑️ DELETE REQUEST: user_id={user_id}")
                await self._delete_post(call, user_id)
                
            elif callback_data.startswith('post_preview'):
                logger.info(f"👀 PREVIEW REQUEST: user_id={user_id}")
                await self._show_post_preview(call, user_id)
                
            elif callback_data == 'post_add_media':
                logger.info(f"📎 ADD MEDIA REQUEST: user_id={user_id}")
                await self._add_media_prompt(call, user_id)
                
            elif callback_data == 'post_remove_media':
                logger.info(f"🗑️ REMOVE MEDIA REQUEST: user_id={user_id}")
                await self._remove_media(call, user_id)
                
            elif callback_data == 'continue_to_preview':
                logger.info(f"➡️ CONTINUE TO PREVIEW REQUEST: user_id={user_id}")
                await self._continue_to_preview(call, user_id)
                
            elif callback_data == 'skip_description':
                logger.info(f"⏭️ SKIP DESCRIPTION REQUEST: user_id={user_id}")
                await self._skip_description(call, user_id)
                
            elif callback_data == 'skip_media':
                logger.info(f"⏭️ SKIP MEDIA REQUEST: user_id={user_id}")
                await self._skip_media(call, user_id)
                
            else:
                logger.warning(f"❓ UNKNOWN POSTING CALLBACK: user_id={user_id}, callback={callback_data}")
                await call.answer("❌ Ação não reconhecida.", show_alert=True)
                
        except Exception as e:
            logger.error(f"💥 POSTING CALLBACK ERROR: user_id={user_id}, callback={callback_data}, error={e}", exc_info=True)
            await self.error_handler.handle_callback_error(call, "Erro ao processar postagem")

    async def handle_post_creation(self, message: Message):
        """Entrada unificada para criação de posts a partir de mensagens de mídia/texto.

        - Quando estiver aguardando título/descrição, processa mensagens de texto.
        - Quando estiver aguardando mídia, encaminha para o handler de mídia.
        - Ignora mensagens que não pertençam a uma sessão de postagem ativa.
        """
        try:
            user_id = message.from_user.id

            # Verificar se há sessão ativa de postagem para o usuário
            session = self.posting_sessions.get(user_id)
            if not session:
                # Sem sessão ativa; não interferir com outras funcionalidades (ex.: onboarding)
                return

            step = session.get('step')

            # Se recebeu mídia, delegar para o handler de mídia
            if getattr(message, 'photo', None) or getattr(message, 'video', None) or getattr(message, 'document', None):
                await self.handle_media_input(message)
                return

            # Mensagens de texto para título/descrição
            if message.text:
                if step == 'title':
                    await self.handle_title_input(message)
                    return
                elif step == 'description':
                    await self.handle_description_input(message)
                    return
                elif step == 'media':
                    # Está aguardando mídia mas recebeu texto; orientar usuário
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)],
                        [InlineKeyboardButton(text="⏭️ Pular Mídia", callback_data="skip_media")]
                    ])
                    await message.answer(
                        "📎 Neste passo, envie a mídia solicitada (foto/vídeo).\n"
                        "Se preferir, você pode pular a mídia.",
                        reply_markup=keyboard
                    )
                    return

            # Se não é texto nem mídia, ignorar silenciosamente
            return

        except Exception as e:
            logger.error(f"Erro em handle_post_creation: {e}", exc_info=True)
            try:
                await message.answer("❌ Ocorreu um erro ao processar seu conteúdo de postagem.")
            except Exception:
                pass

    async def _publish_post_final_corrected(self, call, user_id: int):
        """Implementa a lógica de publicação final conforme as instruções da auditoria."""
        try:
            user_data = await self.user_service.get_user_data(user_id)
            temp_post = user_data.get('temporary_post')
            
            if not temp_post:
                await call.message.answer("❌ Não foi possível encontrar o conteúdo para publicar. Tente criar novamente.")
                return False

            # Criar post no Firestore primeiro para obter ID real
            post_data = {
                'title': temp_post.get('title', 'Post sem título'),
                'description': temp_post.get('text', ''),
                'type': temp_post['type'],
                'media_urls': temp_post.get('media_urls', []),
                'is_monetized': False,
                'price': 0.0
            }
            
            # Criar post no Firestore e obter ID real
            real_post_id = await self.post_service.create_post(user_id, post_data)
            if not real_post_id:
                logger.error(f"Falha ao criar post no Firestore para user_id={user_id}")
                return False

            anonymous_label = build_anonymous_label(user_data)
            interaction_keyboard = create_post_interaction_keyboard(real_post_id, comment_count=0)
            
            final_caption = f"{temp_post.get('text', '')}\n\n{anonymous_label}"
            
            # Publicar o post e capturar o resultado
            publish_result = await self.post_service.publish_post(
                content_type=temp_post['type'],
                text=final_caption,
                file_id=temp_post.get('file_id'),
                keyboard=interaction_keyboard,
                target_group='both'  # Publicar em ambos os grupos
            )
            
            if publish_result:
                # Limpar dados temporários apenas se a publicação foi bem-sucedida
                await self.user_service.update_user_data(user_id, {'temporary_post': None})
                await self.user_service.set_user_state(user_id, UserStates.IDLE)
                return True
            else:
                logger.error(f"Falha na publicação do post para user_id={user_id}")
                return False

        except Exception as e:
            logging.error(f"Erro ao publicar o post: {e}", exc_info=True)
            return False

    async def _publish_post_final(self, query, user_id: int):
        """Implementa a lógica de publicação final conforme as instruções."""
        try:
            # 1. Recuperar o conteúdo do post temporário
            user_data = await self.user_service.get_user_data(user_id)
            temp_post = user_data.get('temporary_post')
            
            if not temp_post:
                await query.message.answer("❌ Não foi possível encontrar o conteúdo do post. Por favor, tente criar novamente.")
                return

            # 2. Gerar a etiqueta de anonimização e o teclado de interação final
            anonymous_label = build_anonymous_label(user_data)
            # Simular um ID de post único por enquanto. O ideal seria vir da base de dados.
            post_id = f"post_{int(time.time())}" 
            interaction_keyboard = create_post_interaction_keyboard(post_id, comment_count=0)
            
            # 3. Montar a legenda/texto final
            final_caption = f"{temp_post.get('text', '')}\n\n{anonymous_label}"
            
            # 4. Publicar no grupo
            await self.post_service.publish_post(
                content_type=temp_post['type'],
                text=final_caption,
                file_id=temp_post.get('file_id'),
                keyboard=interaction_keyboard
            )
            
            # 5. Limpar dados temporários e notificar o utilizador
            await self.user_service.update_user_data(user_id, {'temporary_post': None})
            await self.user_service.set_user_state(user_id, UserStates.IDLE)
            await query.message.edit_text("✅ Seu post foi publicado com sucesso no grupo!")

        except Exception as e:
            logging.error(f"Erro ao publicar o post: {e}", exc_info=True)
            await query.message.answer("❌ Ocorreu um erro ao publicar seu post.")
    
    async def _start_post_creation(self, query, user_id: int, callback_data: str):
        """Inicia o processo de criação de post."""
        try:
            # Extrair tipo de post do callback
            post_type = callback_data.replace('post_type_', '')
            
            # Verificar se o usuário pode criar posts
            user = await self.user_service.get_user_data(user_id)
            if not user:
                await query.message.edit_text("❌ Usuário não encontrado.")
                return
            
            # Inicializar sessão de postagem
            self.posting_sessions[user_id] = {
                'type': post_type,
                'title': '',
                'description': '',
                'media_files': [],
                'monetization': {
                    'enabled': False,
                    'price': 0,
                    'currency': 'BRL'
                },
                'created_at': datetime.now(),
                'step': 'title'
            }
            
            # Solicitar título do post
            text = f"📝 **Criar Post - {post_type.title()}**\n\n"
            text += "Vamos criar seu post! Primeiro, me diga:\n\n"
            text += "**Qual será o título do seu post?**\n"
            text += "_(Máximo 100 caracteres)_"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)]
            ])
            
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # Definir estado para aguardar título
            # Estado interno controlado via sessão
            self.posting_sessions[user_id]['step'] = 'title'
            
        except Exception as e:
            logger.error(f"Erro ao iniciar criação de post: {e}")
            await query.message.edit_text("❌ Erro ao iniciar criação de post.")
    
    async def handle_title_input(self, message: Message):
        """Processa o título do post."""
        user_id = message.from_user.id
        title = message.text
        
        try:
            if user_id not in self.posting_sessions:
                await message.answer("❌ Sessão de postagem não encontrada. Use /start para começar novamente.")
                return
            
            # Validar título
            if len(title) > 100:
                await message.answer(
                    "❌ Título muito longo! Use no máximo 100 caracteres.\n"
                    "Tente novamente:"
                )
                return WAITING_TITLE
            
            # Salvar título
            self.posting_sessions[user_id]['title'] = title
            self.posting_sessions[user_id]['step'] = 'description'
            
            # Solicitar descrição
            text = f"✅ **Título salvo:** {title}\n\n"
            text += "Agora, escreva uma **descrição** para seu post:\n"
            text += "_(Máximo 500 caracteres)_"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Pular Descrição", callback_data="skip_description")],
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)]
            ])
            
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

            return WAITING_DESCRIPTION
            
        except Exception as e:
            logger.error(f"Erro ao processar título: {e}")
            await message.answer("❌ Erro ao processar título.")
            return
    
    async def handle_description_input(self, message: Message):
        """Processa a descrição do post."""
        user_id = message.from_user.id
        description = message.text
        
        try:
            if user_id not in self.posting_sessions:
                await message.answer("❌ Sessão de postagem não encontrada.")
                return
            
            # Validar descrição
            if len(description) > 500:
                await message.answer(
                    "❌ Descrição muito longa! Use no máximo 500 caracteres.\n"
                    "Tente novamente:"
                )
                return WAITING_DESCRIPTION
            
            # Salvar descrição
            self.posting_sessions[user_id]['description'] = description
            
            # Verificar se precisa de mídia
            post_type = self.posting_sessions[user_id]['type']
            if post_type in ['image', 'video']:
                await self._request_media(message, user_id, post_type)
                return WAITING_MEDIA
            else:
                # Post apenas texto - ir para preview
                await self._show_post_preview_message(message, user_id)
                return PREVIEW_POST
            
        except Exception as e:
            logger.error(f"Erro ao processar descrição: {e}")
            await message.answer("❌ Erro ao processar descrição.")
            return
    
    async def _request_media(self, message: Message, user_id: int, media_type: str):
        """Solicita o envio de mídia."""
        try:
            session = self.posting_sessions[user_id]
            session['step'] = 'media'
            
            if media_type == 'image':
                text = "📷 **Envie a imagem** para seu post:\n\n"
                text += "• Formatos aceitos: JPG, PNG, GIF\n"
                text += "• Tamanho máximo: 10MB\n"
                text += "• Você pode enviar até 5 imagens"
            else:  # video
                text = "📹 **Envie o vídeo** para seu post:\n\n"
                text += "• Formatos aceitos: MP4, MOV, AVI\n"
                text += "• Tamanho máximo: 50MB\n"
                text += "• Duração máxima: 5 minutos"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Pular Mídia", callback_data="skip_media")],
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)]
            ])
            
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao solicitar mídia: {e}")
    
    async def handle_media_input(self, message: Message):
        """Processa o envio de mídia."""
        user_id = message.from_user.id
        
        try:
            if user_id not in self.posting_sessions:
                await message.answer("❌ Sessão de postagem não encontrada.")
                return
            
            session = self.posting_sessions[user_id]
            
            # Processar mídia baseado no tipo
            if message.photo:
                # Processar imagem
                photo = message.photo[-1]  # Maior resolução
                file_info = await self.bot.get_file(photo.file_id)
                
                media_data = {
                    'type': 'image',
                    'file_id': photo.file_id,
                    'file_size': photo.file_size,
                    'file_path': file_info.file_path
                }

                # Tentar processar e subir para Cloudinary
                try:
                    upload_result = await self.media_service.process_and_upload_media(photo.file_id, user_id, media_type='photo')
                    if upload_result.get('success'):
                        media_data['cloudinary_url'] = upload_result.get('url')
                        media_data['cloudinary_public_id'] = upload_result.get('public_id')
                        media_data['is_blurred'] = upload_result.get('is_blurred')
                    else:
                        media_data['cloudinary_url'] = None
                except Exception as e:
                    logger.warning(f"Falha ao processar imagem para {user_id}: {e}")
                    media_data['cloudinary_url'] = None
                
                session['media_files'].append(media_data)
                
                await message.answer(
                    f"✅ Imagem adicionada! ({len(session['media_files'])}/5)\n"
                    "Envie mais imagens ou continue para o próximo passo.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="➡️ Continuar", callback_data="continue_to_preview")],
                        [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)]
                    ])
                )
                
            elif message.video:
                # Processar vídeo
                video = message.video
                file_info = await self.bot.get_file(video.file_id)
                
                # Validar duração (5 minutos = 300 segundos)
                if video.duration > 300:
                    await message.answer(
                        "❌ Vídeo muito longo! Máximo 5 minutos.\n"
                        "Envie outro vídeo:"
                    )
                    return WAITING_MEDIA
                
                media_data = {
                    'type': 'video',
                    'file_id': video.file_id,
                    'file_size': video.file_size,
                    'duration': video.duration,
                    'file_path': file_info.file_path
                }

                # Tentar processar e subir para Cloudinary
                try:
                    upload_result = await self.media_service.process_and_upload_media(video.file_id, user_id, media_type='video')
                    if upload_result.get('success'):
                        media_data['cloudinary_url'] = upload_result.get('url')
                        media_data['cloudinary_public_id'] = upload_result.get('public_id')
                        media_data['is_blurred'] = upload_result.get('is_blurred')
                    else:
                        media_data['cloudinary_url'] = None
                except Exception as e:
                    logger.warning(f"Falha ao processar vídeo para {user_id}: {e}")
                    media_data['cloudinary_url'] = None
                
                session['media_files'].append(media_data)
                
                await message.answer(
                    "✅ Vídeo adicionado!\n"
                    "Pronto para continuar?",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="➡️ Continuar", callback_data="continue_to_preview")],
                        [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)]
                    ])
                )
            else:
                await message.answer(
                    "❌ Tipo de arquivo não suportado.\n"
                    "Envie uma imagem ou vídeo válido."
                )
                return WAITING_MEDIA
            
            return WAITING_MEDIA
            
        except Exception as e:
            logger.error(f"Erro ao processar mídia: {e}")
            await message.answer("❌ Erro ao processar mídia.")
            return
    
    async def _show_post_preview_message(self, message: Message, user_id: int):
        """Mostra o preview do post via mensagem."""
        try:
            session = self.posting_sessions[user_id]
            
            # Construir preview
            preview_text = "👀 <b>Preview do seu post:</b>\n\n"
            preview_text += f"<b>📝 Título:</b> {html.escape(session['title'] or '')}\n\n"
            
            if session['description']:
                preview_text += f"<b>📄 Descrição:</b>\n{html.escape(session['description'])}\n\n"
            
            if session['media_files']:
                preview_text += f"<b>📎 Mídia:</b> {len(session['media_files'])} arquivo(s)\n\n"

            # Mostrar configuração de monetização se ativada
            if session.get('monetization', {}).get('enabled'):
                preview_text += f"<b>💰 Monetização:</b> R$ {session['monetization']['price']:.2f}\n\n"
            
            preview_text += "<b>Opções:</b>"
            
            # Verificar se o usuário pode monetizar
            user = await self.user_service.get_user(user_id)
            can_monetize = user and user.get('is_creator') and user.get('monetization_enabled')

            # Persistir/atualizar rascunho antes de mostrar preview
            draft_payload = {
                'type': session['type'],
                'title': session['title'],
                'description': session['description'],
                'media_files': session['media_files'],
                'monetization': session.get('monetization', {'enabled': False, 'price': 0, 'currency': 'BRL'}),
                'created_at': session.get('created_at'),
            }
            existing_draft_id = session.get('draft_id')
            draft_id = await self.draft_repo.create_or_update(user_id, existing_draft_id, draft_payload)
            session['draft_id'] = draft_id

            # Construir teclado com draft_id
            keyboard = create_post_preview_keyboard(draft_id)
            # Se não puder monetizar, removemos o botão de monetização (ajuste simples)
            if not can_monetize:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Publicar", callback_data=f"post_publish:{draft_id}")],
                    [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"post_cancel:{draft_id}")]
                ])
            
            await message.answer(
                preview_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Erro ao mostrar preview: {e}")
    
    async def _show_post_preview(self, query, user_id: int):
        """Mostra o preview do post via callback."""
        try:
            session = self.posting_sessions.get(user_id)
            if not session:
                await query.message.edit_text("❌ Sessão de postagem não encontrada.")
                return
            
            # Construir preview
            preview_text = "👀 <b>Preview do seu post:</b>\n\n"
            preview_text += f"<b>📝 Título:</b> {html.escape(session['title'] or '')}\n\n"
            
            if session['description']:
                preview_text += f"<b>📄 Descrição:</b>\n{html.escape(session['description'])}\n\n"
            
            if session['media_files']:
                preview_text += f"<b>📎 Mídia:</b> {len(session['media_files'])} arquivo(s)\n\n"
            
            # Mostrar configuração de monetização se ativada
            if session['monetization']['enabled']:
                preview_text += f"<b>💰 Monetização:</b> R$ {session['monetization']['price']:.2f}\n\n"
            
            preview_text += "<b>Confirma a publicação?</b>"

            # Persistir/atualizar rascunho e obter draft_id
            draft_payload = {
                'type': session['type'],
                'title': session['title'],
                'description': session['description'],
                'media_files': session['media_files'],
                'monetization': session.get('monetization', {'enabled': False, 'price': 0, 'currency': 'BRL'}),
                'created_at': session.get('created_at'),
            }
            existing_draft_id = session.get('draft_id')
            draft_id = await self.draft_repo.create_or_update(user_id, existing_draft_id, draft_payload)
            session['draft_id'] = draft_id

            keyboard = create_post_preview_keyboard(draft_id)
            
            await query.message.edit_text(
                preview_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Erro ao mostrar preview: {e}")
    
    async def _cancel_post(self, query, user_id: int):
        """Cancela a criação do post."""
        try:
            # Limpar sessão se existir
            if user_id in self.posting_sessions:
                del self.posting_sessions[user_id]
            
            # Limpar dados temporários do usuário e resetar estado
            try:
                await self.user_service.update_user_data(user_id, {'temporary_post': None})
                await self.user_service.set_user_state(user_id, UserStates.IDLE)
            except Exception as inner_e:
                logger.warning(f"Falha ao limpar temporary_post/estado no cancelamento para {user_id}: {inner_e}")
            
            await query.message.edit_text(
                "❌ **Criação de post cancelada.**\n\n"
                "Você pode criar um novo post a qualquer momento!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Menu Principal", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao cancelar post: {e}")
    
    async def _cancel_post_with_id(self, query, user_id: int, callback_data: str):
        """Cancela a criação do post com ID específico."""
        try:
            # Extrair draft_id do callback
            draft_id = callback_data.split(":")[-1] if ":" in callback_data else None
            
            # Limpar sessão se existir
            if user_id in self.posting_sessions:
                del self.posting_sessions[user_id]
            
            # Limpar dados temporários do usuário e resetar estado
            try:
                await self.user_service.update_user_data(user_id, {'temporary_post': None})
                await self.user_service.set_user_state(user_id, UserStates.IDLE)
            except Exception as inner_e:
                logger.warning(f"Falha ao limpar temporary_post/estado no cancelamento para {user_id}: {inner_e}")

            # Excluir rascunho se houver
            if draft_id:
                try:
                    await self.draft_repo.delete(user_id, draft_id)
                except Exception as del_e:
                    logger.warning(f"Falha ao excluir draft {draft_id} para {user_id}: {del_e}")
            
            await query.message.edit_text(
                "❌ **Criação de post cancelada.**\n\n"
                "Você pode criar um novo post a qualquer momento!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Menu Principal", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
            logger.info(f"Post cancelado: user_id={user_id}, draft_id={draft_id}")
            
        except Exception as e:
            logger.error(f"Erro ao cancelar post com ID: {e}")
    
    async def _publish_post(self, query, user_id: int):
        """Publica o post sem ID específico."""
        try:
            result = await self._publish_post_final_corrected(query, user_id)
            if result:
                await query.message.edit_text("✅ O seu post foi publicado com sucesso!")
                logger.info(f"Post publicado com sucesso: user_id={user_id}")
            else:
                await query.message.edit_text("❌ Não foi possível publicar o post. Verifique se o bot tem permissões nos grupos.")
                logger.error(f"Falha na publicação do post: user_id={user_id}")
        except Exception as e:
            logger.error(f"Erro ao publicar post: {e}")
            await query.message.edit_text("❌ Ocorreu um erro interno. Tente novamente mais tarde.")
    
    async def _publish_post_with_id(self, query, user_id: int, callback_data: str):
        """Publica o post com ID específico."""
        try:
            # Extrair post_id do callback
            draft_id = callback_data.split(":")[-1] if ":" in callback_data else None

            # Carregar rascunho
            draft = await self.draft_repo.get(user_id, draft_id) if draft_id else None
            if not draft:
                await query.message.edit_text("❌ Rascunho não encontrado ou expirado. Crie o post novamente.")
                return

            data = draft.get('data', {})

            # Montar conteúdo final
            user_data = await self.user_service.get_user_data(user_id)
            anonymous_label = build_anonymous_label(user_data)
            publish_text = ""
            if data.get('title'):
                publish_text += f"<b>{html.escape(data['title'])}</b>\n\n"
            if data.get('description'):
                publish_text += f"{html.escape(data['description'])}\n\n"
            publish_text += anonymous_label

            # Escolher mídia se houver
            file_id = None
            content_type = data.get('type') or 'text'
            media_files = data.get('media_files') or []
            if media_files:
                primary_media = media_files[0]
                file_id = primary_media.get('file_id')

            # Obter dados de monetização
            monetization = data.get('monetization', {'enabled': False, 'price': 0.0})

            # Criar post no Firestore primeiro para obter ID real
            post_data = {
                'title': data.get('title', 'Post sem título'),
                'description': data.get('description', ''),
                'type': content_type,
                'media_urls': [media.get('file_id') for media in media_files] if media_files else [],
                'is_monetized': monetization.get('enabled', False),
                'price': monetization.get('price', 0.0)
            }
            
            # Criar post no Firestore e obter ID real
            real_post_id = await self.post_service.create_post(user_id, post_data)
            if not real_post_id:
                await query.message.edit_text("❌ Erro ao criar post. Tente novamente.")
                return

            # Teclado de interação do post publicado com ID real
            interaction_keyboard = create_post_interaction_keyboard(real_post_id, comment_count=0)

            # Determinar grupo alvo baseado na monetização
            # Posts monetizados vão apenas para o grupo premium
            # Posts não monetizados vão para ambos os grupos (freemium E premium)
            if monetization.get('enabled', False):
                target_group = 'premium'  # Apenas premium para posts monetizados
                logger.info(f"Post monetizado (R$ {monetization.get('price', 0):.2f}) - publicando apenas no grupo premium")
            else:
                target_group = 'both'  # Ambos os grupos para posts gratuitos
                logger.info(f"Post gratuito - publicando em ambos os grupos")

            # Determinar se é media group (múltiplas mídias)
            if len(media_files) > 1:
                content_type = 'media_group'
                
            # Publicar
            publish_result = await self.post_service.publish_post(
                content_type=content_type,
                text=publish_text,
                file_id=file_id,
                media_files=media_files if len(media_files) > 1 else None,
                keyboard=interaction_keyboard,
                target_group=target_group
            )

            # Limpar estado e remover rascunho
            await self.user_service.set_user_state(user_id, UserStates.IDLE)
            await self.draft_repo.delete(user_id, draft_id)
            if user_id in self.posting_sessions:
                del self.posting_sessions[user_id]

            # Verificar resultado da publicação
            if publish_result:
                await query.message.edit_text("✅ O seu post foi publicado com sucesso!")
                logger.info(f"Post publicado: user_id={user_id}, draft_id={draft_id}")
            else:
                await query.message.edit_text("❌ Não foi possível publicar o post. Verifique se o bot tem permissões nos grupos.")
                logger.error(f"Falha na publicação confirmada: user_id={user_id}, draft_id={draft_id}")
            
        except Exception as e:
            logger.error(f"Erro ao publicar post com ID: {e}")
            await query.message.edit_text("❌ Ocorreu um erro interno. Tente novamente mais tarde.")
    
    async def _handle_monetization(self, query, user_id: int, callback_data: str):
        """Processa configurações de monetização."""
        try:
            # Verificar se o usuário pode monetizar
            user = await self.user_service.get_user_data(user_id)
            if not user or user.get('category', '').lower() != 'criador':
                await query.answer("❌ Apenas Criadores de Conteúdo podem monetizar posts.", show_alert=True)
                return
            
            # Verificar se há sessão de postagem ativa
            session = self.posting_sessions.get(user_id)
            if not session:
                await query.message.edit_text("❌ Sessão de postagem não encontrada.")
                return
            # Extrair draft_id se presente
            draft_id = callback_data.split(":")[-1] if ":" in callback_data else session.get('draft_id')
            if draft_id:
                session['draft_id'] = draft_id

            # Mostrar opções de monetização
            text = "💰 <b>Configurar Monetização</b>\n\n"
            text += "Este conteúdo será exclusivo para assinantes Premium.\n\n"
            text += "Escolha o valor que deseja cobrar pelo acesso avulso:"
            
            # Incluir draft_id nos callbacks se disponível
            draft_suffix = f":{draft_id}" if draft_id else ""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="R$ 2,99", callback_data=f"monetize_price_2.99{draft_suffix}")],
                [InlineKeyboardButton(text="R$ 4,99", callback_data=f"monetize_price_4.99{draft_suffix}")],
                [InlineKeyboardButton(text="R$ 9,99", callback_data=f"monetize_price_9.99{draft_suffix}")],
                [InlineKeyboardButton(text="R$ 19,99", callback_data=f"monetize_price_19.99{draft_suffix}")],
                [InlineKeyboardButton(text="💰 Valor Personalizado", callback_data=f"monetize_custom{draft_suffix}")],
                [InlineKeyboardButton(text="🔙 Voltar", callback_data=f"post_preview{draft_suffix}")],
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"post_cancel{draft_suffix}")]
            ])
            
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Erro ao configurar monetização: {e}")
            await query.message.edit_text("❌ Erro ao configurar monetização.")
    
    async def _handle_monetization_price(self, query, user_id: int, callback_data: str):
        """Processa a seleção de preço de monetização."""
        try:
            session = self.posting_sessions.get(user_id)
            if not session:
                await query.message.edit_text("❌ Sessão de postagem não encontrada.")
                return
            
            # Separar ação e draft_id, se houver
            action_part, draft_id = (callback_data.split(":", 1) + [None])[:2]
            
            if action_part.startswith("monetize_price_"):
                # Extrair preço do callback
                price_str = action_part.replace("monetize_price_", "")
                price = float(price_str)
                
                # Configurar monetização na sessão
                session['monetization'] = {
                    'enabled': True,
                    'price': price,
                    'currency': 'BRL'
                }
                # Persistir atualização em rascunho
                draft_payload = {
                    'type': session['type'],
                    'title': session['title'],
                    'description': session['description'],
                    'media_files': session['media_files'],
                    'monetization': session['monetization'],
                    'created_at': session.get('created_at'),
                }
                saved_draft_id = await self.draft_repo.create_or_update(user_id, draft_id or session.get('draft_id'), draft_payload)
                session['draft_id'] = saved_draft_id
                
                # Mostrar confirmação e voltar ao preview
                text = f"✅ <b>Monetização configurada!</b>\n\n"
                text += f"💰 <b>Preço:</b> R$ {price:.2f}\n\n"
                text += "Seu conteúdo será exclusivo para assinantes Premium."
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Ver Preview", callback_data=f"post_preview:{session['draft_id']}")],
                    [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"post_cancel:{session['draft_id']}")]
                ])
                
                await query.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
            elif action_part == "monetize_custom":
                # Solicitar valor personalizado
                text = "💰 <b>Valor Personalizado</b>\n\n"
                text += "Digite o valor que deseja cobrar (ex: 15.99):\n\n"
                text += "⚠️ <i>Valores entre R$ 0,99 e R$ 99,99</i>"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Voltar", callback_data=f"post_monetize:{draft_id or session.get('draft_id')}")],
                    [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"post_cancel:{draft_id or session.get('draft_id')}")]
                ])
                
                await query.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
                # Definir estado para aguardar valor personalizado
                await self.user_service.set_user_state(user_id, UserStates.AWAITING_MONETIZATION_VALUE)
                # Guardar draft_id para uso na entrada personalizada
                session['pending_monetization_draft_id'] = draft_id or session.get('draft_id')
                
        except Exception as e:
            logger.error(f"Erro ao processar preço de monetização: {e}")
            await query.message.edit_text("❌ Erro ao processar preço.")
    
    async def handle_custom_monetization_value(self, message: Message):
        """Processa valor personalizado de monetização."""
        user_id = message.from_user.id
        
        try:
            session = self.posting_sessions.get(user_id)
            if not session:
                await message.answer("❌ Sessão de postagem não encontrada.")
                return
            
            # Validar valor
            try:
                price = float(message.text.replace(',', '.'))
                if price < 0.99 or price > 99.99:
                    await message.answer(
                        "❌ Valor inválido! Use valores entre R$ 0,99 e R$ 99,99.\n"
                        "Tente novamente:"
                    )
                    return
            except ValueError:
                await message.answer(
                    "❌ Formato inválido! Use apenas números (ex: 15.99).\n"
                    "Tente novamente:"
                )
                return
            
            # Configurar monetização
            session['monetization'] = {
                'enabled': True,
                'price': price,
                'currency': 'BRL'
            }
            # Persistir atualização do rascunho
            draft_id = session.get('draft_id') or session.get('pending_monetization_draft_id')
            draft_payload = {
                'type': session['type'],
                'title': session['title'],
                'description': session['description'],
                'media_files': session['media_files'],
                'monetization': session['monetization'],
                'created_at': session.get('created_at'),
            }
            saved_draft_id = await self.draft_repo.create_or_update(user_id, draft_id, draft_payload)
            session['draft_id'] = saved_draft_id
            
            # Resetar estado
            await self.user_service.set_user_state(user_id, UserStates.IDLE)
            
            # Mostrar confirmação
            text = f"✅ <b>Monetização configurada!</b>\n\n"
            text += f"💰 <b>Preço:</b> R$ {price:.2f}\n\n"
            text += "Seu conteúdo será exclusivo para assinantes Premium."
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Ver Preview", callback_data=f"post_preview:{session['draft_id']}")],
                [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"post_cancel:{session['draft_id']}")]
            ])
            
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar valor personalizado: {e}")
            await message.answer("❌ Erro ao processar valor.")

    async def _continue_to_preview(self, call: CallbackQuery, user_id: int):
        """Continua para o preview após adicionar mídia."""
        try:
            session = self.posting_sessions.get(user_id)
            if not session:
                await call.message.answer("❌ Sessão expirada. Inicie novamente.")
                return
            
            # Verificar se há conteúdo suficiente para preview
            if not session.get('title') and not session.get('description') and not session.get('media_files'):
                await call.message.answer("❌ Adicione pelo menos um título, descrição ou mídia antes de continuar.")
                return
            
            # Ir para o preview
            await self._show_post_preview(call, user_id)
            
        except Exception as e:
            logger.error(f"Erro ao continuar para preview: {e}")
            await call.message.answer("❌ Erro ao continuar. Tente novamente.")

    async def _skip_description(self, call: CallbackQuery, user_id: int):
        """Pula a descrição e continua para o próximo passo."""
        try:
            session = self.posting_sessions.get(user_id)
            if not session:
                await call.message.edit_text("❌ Sessão de postagem não encontrada.")
                return
            
            # Definir descrição como vazia
            session['description'] = ''
            
            # Verificar se precisa de mídia
            post_type = session['type']
            if post_type in ['image', 'video']:
                # Solicitar mídia via edit
                text = f"📷 **Envie a {'imagem' if post_type == 'image' else 'vídeo'}** para seu post:\n\n"
                if post_type == 'image':
                    text += "• Formatos aceitos: JPG, PNG, GIF\n"
                    text += "• Tamanho máximo: 10MB\n"
                    text += "• Você pode enviar até 5 imagens"
                else:
                    text += "• Formatos aceitos: MP4, MOV, AVI\n"
                    text += "• Tamanho máximo: 50MB\n"
                    text += "• Duração máxima: 5 minutos"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⏭️ Pular Mídia", callback_data="skip_media")],
                    [InlineKeyboardButton(text="❌ Cancelar", callback_data=PostingCallbacks.CANCEL)]
                ])
                
                session['step'] = 'media'
                await call.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                # Post apenas texto - ir para preview
                await self._show_post_preview(call, user_id)
            
        except Exception as e:
            logger.error(f"Erro ao pular descrição: {e}")
            await call.message.edit_text("❌ Erro ao pular descrição.")

    async def _skip_media(self, call: CallbackQuery, user_id: int):
        """Pula a mídia e vai direto para o preview."""
        try:
            session = self.posting_sessions.get(user_id)
            if not session:
                await call.message.edit_text("❌ Sessão de postagem não encontrada.")
                return
            
            # Não adicionar mídia - ir direto para preview
            await self._show_post_preview(call, user_id)
            
        except Exception as e:
            logger.error(f"Erro ao pular mídia: {e}")
            await call.message.edit_text("❌ Erro ao pular mídia.")

    def get_conversation_handler(self):
        """Retorna o ConversationHandler para postagem."""
        from telegram.ext import MessageHandler, CallbackQueryHandler, filters
        
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(self.handle_callback_query, pattern='^post_type_')],
            states={
                WAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_title_input)],
                WAITING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_description_input)],
                WAITING_MEDIA: [
                    MessageHandler(filters.PHOTO | filters.VIDEO, self.handle_media_input),
                    CallbackQueryHandler(self.handle_callback_query)
                ],
                PREVIEW_POST: [CallbackQueryHandler(self.handle_callback_query)],
                MONETIZATION_SETUP: [CallbackQueryHandler(self.handle_callback_query)]
            },
            fallbacks=[
                CallbackQueryHandler(self._cancel_post, pattern='^post_cancel(?::.*)?$'),
                MessageHandler(filters.COMMAND, self._cancel_post)
            ],
            per_user=True
        )