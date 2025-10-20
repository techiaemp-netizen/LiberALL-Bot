"""
Módulo para o handler do teclado em Direct Message (DM).
Gerencia os menus principais, callbacks e o comando /start.
"""
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services.optimized_user_service import OptimizedUserService
from services.security_service import SecurityService
from handlers.onboarding_handler import OnboardingHandler
from handlers.posting_handler import PostingHandler
from utils.error_handler import ErrorHandler
from constants import emojis, callbacks, user_states
import logging

class DMKeyboardHandler:
    def __init__(self, bot, onboarding_handler: OnboardingHandler, user_service: OptimizedUserService, security_service: SecurityService, error_handler: ErrorHandler, posting_handler: PostingHandler):  # Compatível com aiogram Bot
        self.bot = bot
        self.onboarding_handler = onboarding_handler
        self.user_service = user_service
        self.security_service = security_service
        self.error_handler = error_handler
        self.posting_handler = posting_handler
        self.logger = logging.getLogger(__name__)

    async def start_command(self, message: Message):
        """
        Lida com o comando /start, diferenciando novos usuários,
        usuários existentes e deep-links.
        """
        user_id = message.from_user.id
        
        # Verificar se o usuário é um bot - bots não podem usar o sistema
        if message.from_user.is_bot:
            self.logger.warning(f"Bot {user_id} tentou usar o comando /start - ignorando")
            return
        
        command_parts = message.text.split(' ')
        payload = command_parts[1] if len(command_parts) > 1 else None

        user = await self.user_service.get_or_create_user(message.from_user)

        # Se o usuário ainda não completou o onboarding, o OnboardingHandler assume.
        if not user.profile.onboarded:
            await self.onboarding_handler.start_onboarding(message)
            return

        # Se o usuário já completou o onboarding, processa o payload ou mostra o menu.
        if payload == "menu" or payload == "abrir_menu":
            await self.send_main_menu(user_id)
        elif payload == "posting" or payload == "iniciar_postagem":
            await self.posting_handler.start_posting_flow(user_id)
        elif payload == "create_post":
            await self.user_service.set_user_state(user_id, user_states.AWAITING_POST_CONTENT)
            await self.bot.send_message(user_id, "Ok, vamos criar um post! Envie a mídia ou o texto que você deseja publicar.")
        else:
            # Se não houver payload, apenas mostra o menu principal.
            await self.send_main_menu(user_id)

    async def send_main_menu(self, user_id: int):
        """Envia o menu principal para o usuário no chat privado."""
        await self.security_service.log_user_action(user_id, 'main_menu_accessed')
        
        try:
            menu_text = f"{emojis.EMOJIS['menu']} <b>Menu Principal</b>\n\nEscolha uma das opções abaixo:"
            keyboard = await self._build_main_menu_keyboard(user_id)
            await self.bot.send_message(chat_id=user_id, text=menu_text, reply_markup=keyboard, parse_mode='HTML')
            self.logger.info(f"✅ Menu principal enviado para user_id={user_id}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar o menu principal para {user_id}: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Não foi possível exibir o menu.")

    async def handle_menu_button(self, message: Message):
        """Envia o menu principal para o usuário."""
        user_id = message.from_user.id
        await self.send_main_menu(user_id)

    async def _build_main_menu_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Meu Perfil", callback_data="menu:profile")],
            [InlineKeyboardButton(text="Minha Galeria", callback_data="menu:gallery")],
            [InlineKeyboardButton(text="Meus Matches", callback_data="menu:matches")],
            [InlineKeyboardButton(text="Favoritos", callback_data="menu:favorites")],
            [InlineKeyboardButton(text="Criar Post", callback_data="start_post")]
        ])
        return keyboard

    async def handle_deep_link(self, message: Message, payload: str):
        """
        Processa deep links com parâmetros específicos.
        """
        user_id = message.from_user.id
        self.logger.info(f"🔗 Deep link processado: '{payload}' para usuário {user_id}")
        
        try:
            # Verificar se o usuário completou o onboarding
            user = await self.user_service.get_or_create_user(message.from_user)
            
            if not user.profile.onboarded:
                # Se não completou onboarding, iniciar processo
                await self.onboarding_handler.start_onboarding(message)
                return
            
            # Processar diferentes tipos de deep links
            if payload in ["menu", "abrir_menu"]:
                await self.send_main_menu(user_id)
            elif payload in ["posting", "iniciar_postagem", "create_post"]:
                await self.posting_handler.start_posting_flow(user_id)
            else:
                # Deep link não reconhecido, mostrar menu principal
                self.logger.warning(f"Deep link não reconhecido: '{payload}' para usuário {user_id}")
                await self.send_main_menu(user_id)
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar deep link '{payload}' para usuário {user_id}: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar solicitação.")

    async def handle_callback_query(self, call: CallbackQuery):
        """Roteia os callbacks do menu principal e outros fluxos da DM."""
        user_id = call.from_user.id
        data = call.data
        
        # Verificar se o usuário é um bot - bots não podem usar callbacks
        if call.from_user.is_bot:
            self.logger.warning(f"Bot {user_id} tentou usar callback - ignorando")
            return

        # Rotear callbacks de onboarding para o OnboardingHandler
        if (data.startswith("start_onboarding") or 
            data.startswith("onboarding_") or 
            data in ["confirm_age", "reject_age", "accept_rules", "reject_rules", 
                     "accept_terms", "reject_terms", "accept_lgpd", "reject_lgpd",
                     "creator_yes", "creator_no", "accept_monetization", "reject_monetization",
                     "group_lite", "group_premium"] or
            data.startswith(("state_", "category_", "gender_", "profile_", "rel_")) or
            data == "finish_relationship_selection"):
            await self.onboarding_handler.handle_onboarding_callback(call)
            return

        if data == "start_post":
            # Responder ao callback imediatamente para evitar timeout
            try:
                await self.bot.answer_callback_query(call.id, cache_time=1)
            except Exception as callback_error:
                self.logger.warning(f"Erro ao responder callback: {callback_error}")
                # Continuar processamento mesmo se falhar ao responder callback
            await self.user_service.set_user_state(user_id, user_states.AWAITING_POST_CONTENT)
            await self.bot.send_message(user_id, "Envie a mídia ou o texto que você deseja publicar.")
        elif data.startswith("post_"):
            await self.posting_handler.handle_callback_query(call)
        elif data.startswith(("fav:", "match:", "gallery:", "comment:")):
            # Responder ao callback imediatamente para evitar timeout
            try:
                await self.bot.answer_callback_query(call.id, "Funcionalidade em desenvolvimento!", show_alert=True, cache_time=1)
            except Exception as callback_error:
                self.logger.warning(f"Erro ao responder callback: {callback_error}")
        else:
            # Responder ao callback imediatamente para evitar timeout
            try:
                await self.bot.answer_callback_query(call.id, "Ação não reconhecida.", cache_time=1)
            except Exception as callback_error:
                self.logger.warning(f"Erro ao responder callback: {callback_error}")
