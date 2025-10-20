from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from services.optimized_user_service import OptimizedUserService
from services.security_service import SecurityService
from utils.error_handler import ErrorHandler
from models.firebase_models import User
from constants import user_states
from handlers.onboarding_steps import OnboardingSteps
from aiogram.exceptions import TelegramAPIError
from utils.ui_builder import build_anonymous_label, create_welcome_keyboard
from config import FREEMIUM_GROUP_ID, PREMIUM_GROUP_ID
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.invite_link_helper import get_group_invite_url
import logging
import time

class OnboardingHandler:
    def __init__(self, bot, user_service: OptimizedUserService, security_service: SecurityService, error_handler: ErrorHandler):  # Compatível com aiogram Bot
        self.bot = bot
        self.user_service = user_service
        self.security_service = security_service
        self.error_handler = error_handler
        self.steps = OnboardingSteps(bot, user_service, security_service, error_handler, self)
        self.dm_keyboard_handler = None
        self.logger = logging.getLogger(__name__)
        # Sistema de deduplicação de callbacks otimizado
        self.processed_callbacks = set()
        self.callback_timeout = 10  # segundos - reduzido para melhor performance
        
        # Dicionário para armazenar estados temporários de usuários
        # IMPORTANTE: Este dicionário é limpo automaticamente para evitar vazamento de memória
        self.user_states = {}
        
        # Configuração de limpeza automática
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutos
        self.max_user_state_age = 1800  # 30 minutos

    def set_dm_keyboard_handler(self, dm_keyboard_handler):
        self.dm_keyboard_handler = dm_keyboard_handler

    async def _cleanup_old_user_states(self):
        """Limpa estados antigos de usuários para evitar vazamento de memória."""
        try:
            current_time = time.time()
            
            # Verificar se é hora de fazer limpeza
            if current_time - self.last_cleanup < self.cleanup_interval:
                return
            
            # Identificar usuários com estados antigos
            users_to_remove = []
            for user_id, state_data in self.user_states.items():
                last_activity = state_data.get('last_activity', 0)
                if current_time - last_activity > self.max_user_state_age:
                    users_to_remove.append(user_id)
            
            # Remover estados antigos
            for user_id in users_to_remove:
                del self.user_states[user_id]
                self.logger.info(f"Estado limpo para usuário inativo: {user_id}")
            
            self.last_cleanup = current_time
            
            if users_to_remove:
                self.logger.info(f"Limpeza automática: removidos {len(users_to_remove)} estados antigos")
                
        except Exception as e:
            self.logger.error(f"Erro na limpeza automática de estados: {e}")

    async def clear_user_state(self, user_id: int):
        """Limpa o estado específico de um usuário."""
        try:
            if user_id in self.user_states:
                del self.user_states[user_id]
                self.logger.info(f"Estado limpo manualmente para usuário: {user_id}")
        except Exception as e:
            self.logger.error(f"Erro ao limpar estado do usuário {user_id}: {e}")

    async def set_user_state_data(self, user_id: int, state: str, data: dict = None):
        """Define dados de estado para um usuário com timestamp."""
        try:
            self.user_states[user_id] = {
                'state': state,
                'data': data or {},
                'last_activity': time.time(),
                'created_at': time.time()
            }
            
            # Executar limpeza automática se necessário
            await self._cleanup_old_user_states()
            
        except Exception as e:
            self.logger.error(f"Erro ao definir estado para usuário {user_id}: {e}")

    async def get_user_state_data(self, user_id: int):
        """Obtém dados de estado de um usuário."""
        try:
            state_data = self.user_states.get(user_id)
            if state_data:
                # Atualizar timestamp de atividade
                state_data['last_activity'] = time.time()
            return state_data
        except Exception as e:
            self.logger.error(f"Erro ao obter estado do usuário {user_id}: {e}")
            return None

    async def start_onboarding(self, message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        await self.user_service.batch_update_user_data(user_id, [
            {'state': user_states.ONBOARDING}
        ])
        await self.steps.start_onboarding(user_id, chat_id)

    async def handle_onboarding_callback(self, call: CallbackQuery):
        user_id = call.from_user.id
        user = await self.user_service.get_user(user_id)
        if not user:
            return

        try:
            current_state = user.state
            callback_data = call.data

            # Refresh de link de convite do grupo (independente do estado atual)
            if callback_data and callback_data.startswith("onboarding_refresh_invite_"):
                try:
                    group_type = callback_data.replace("onboarding_refresh_invite_", "")
                    if group_type == "lite":
                        group_id = FREEMIUM_GROUP_ID
                        group_label = "Lite"
                    else:
                        group_id = PREMIUM_GROUP_ID
                        group_label = "Premium"

                    # Gerar novo link com refresh e preferência por join request
                    new_link = await get_group_invite_url(
                        self.bot,
                        group_id,
                        logger=self.logger,
                        force_refresh=True,
                        prefer_join_request=True,
                    )

                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=f"🔗 Entrar no Grupo {group_label}", url=new_link)],
                        [InlineKeyboardButton(text="♻️ Gerar novo link", callback_data=f"onboarding_refresh_invite_{group_type}")]
                    ])

                    # Atualiza o teclado da mensagem atual com o novo link
                    try:
                        await self.bot.edit_message_reply_markup(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=keyboard
                        )
                    except Exception as edit_err:
                        # Se não for possível editar (mensagem antiga), envia uma nova mensagem com o link
                        self.logger.warning(f"Falha ao editar mensagem com novo link, enviando nova: {edit_err}")
                        await self.bot.send_message(
                            chat_id=call.message.chat.id,
                            text=f"🔗 Clique abaixo para entrar no grupo {group_label}:",
                            reply_markup=keyboard
                        )

                    # Responde ao callback informando que o link foi atualizado
                    try:
                        await self.bot.answer_callback_query(call.id, text="✅ Novo link gerado", cache_time=1)
                    except Exception as callback_error:
                        self.logger.warning(f"Erro ao responder callback de refresh: {callback_error}")
                    return
                except Exception as e:
                    self.logger.error(f"Erro ao atualizar link de convite: {e}", exc_info=True)
                    try:
                        await self.bot.answer_callback_query(call.id, text="❌ Erro ao gerar novo link", cache_time=1)
                    except Exception:
                        pass
                    return
            
            # Fluxo inicial - botão "Iniciar"
            if current_state == user_states.ONBOARDING and callback_data == "start_onboarding":
                # Usar batch operation para atualizar estado e enviar mensagem
                await self.user_service.batch_update_user_data(user_id, [
                    {'state': user_states.AWAITING_AGE_INPUT}
                ])
                await self.steps.request_age_input(user_id, call.message.chat.id)
            
            # Confirmação de idade
            elif current_state == user_states.AWAITING_AGE_CONFIRMATION:
                if callback_data == "confirm_age":
                    # Atualizar age_confirmed e estado em batch
                    await self.user_service.batch_update_user_data(user_id, [
                        {'profile.age_confirmed': True},
                        {'state': user_states.AWAITING_RULES_AGREEMENT}
                    ])
                    await self.steps.show_rules_terms(user_id, call.message.chat.id)
                elif callback_data == "reject_age":
                    await self.bot.send_message(call.message.chat.id, "❌ Você precisa ter 18 anos ou mais para usar o LiberALL.")
                    await self.user_service.batch_update_user_data(user_id, [
                        {'state': user_states.IDLE}
                    ])
            
            # Regras do grupo
            elif current_state == user_states.AWAITING_RULES_AGREEMENT:
                if callback_data == "accept_rules":
                    # Atualizar rules_accepted e estado em batch
                    await self.user_service.batch_update_user_data(user_id, [
                        {'agreements.rules_accepted': True},
                        {'state': user_states.AWAITING_TERMS_AGREEMENT}
                    ])
                    await self.steps.show_terms_conditions(user_id, call.message.chat.id)
                elif callback_data == "reject_rules":
                    await self.bot.send_message(call.message.chat.id, "❌ Você não pode prosseguir sem aceitar as regras. O processo foi encerrado.")
                    await self.user_service.batch_update_user_data(user_id, [
                        {'state': user_states.IDLE}
                    ])
            
            # Termos e condições
            elif current_state == user_states.AWAITING_TERMS_AGREEMENT:
                if callback_data == "accept_terms":
                    # Atualizar privacy_accepted e estado em batch
                    await self.user_service.batch_update_user_data(user_id, [
                        {'agreements.privacy_accepted': True},
                        {'state': user_states.AWAITING_LGPD_AGREEMENT}
                    ])
                    await self.steps.show_lgpd_terms(user_id, call.message.chat.id)
                elif callback_data == "reject_terms":
                    await self.bot.send_message(call.message.chat.id, "❌ Você não pode prosseguir sem aceitar os termos. O processo foi encerrado.")
                    await self.user_service.batch_update_user_data(user_id, [
                        {'state': user_states.IDLE}
                    ])
            
            # LGPD
            elif current_state == user_states.AWAITING_LGPD_AGREEMENT:
                if callback_data == "accept_lgpd":
                    # Atualizar lgpd_accepted e estado em batch
                    await self.user_service.batch_update_user_data(user_id, [
                        {'agreements.lgpd_accepted': True},
                        {'state': user_states.AWAITING_PROFILE_TYPE}
                    ])
                    await self.steps.show_profile_type_selection(user_id, call.message.chat.id)
                elif callback_data == "reject_lgpd":
                    await self.bot.send_message(call.message.chat.id, "❌ Você não pode prosseguir sem aceitar os termos de proteção de dados. O processo foi encerrado.")
                    await self.user_service.batch_update_user_data(user_id, [
                        {'state': user_states.IDLE}
                    ])
            
            # Seleção do tipo de perfil
            elif current_state == user_states.AWAITING_PROFILE_TYPE:
                if callback_data.startswith("profile_"):
                    profile_type = callback_data.replace("profile_", "")
                    await self.steps.handle_profile_type_selection(user_id, call.message.chat.id, profile_type)
            
            # Seleção de perfis para relacionamento
            elif current_state == user_states.AWAITING_RELATIONSHIP_PROFILES:
                if callback_data.startswith("rel_"):
                    profile_type = callback_data.replace("rel_", "")
                    await self.steps.handle_relationship_profile_selection(user_id, call.message.chat.id, profile_type, call.message.message_id)
                elif callback_data == "finish_relationship_selection":
                    await self.steps.handle_finish_relationship_selection(user_id, call.message.chat.id)
            
            # Seleção de localização (estado)
            elif current_state == user_states.AWAITING_LOCATION:
                if callback_data.startswith("state_"):
                    await self.steps.handle_location_selection(call, user)
            
            # Pergunta sobre criador de conteúdo
            elif current_state == user_states.AWAITING_CONTENT_CREATOR_CHOICE:
                self.logger.info(f"[DEBUG] Processando callback de criador de conteúdo - callback_data: {callback_data}")
                is_creator = callback_data == "creator_yes"
                self.logger.info(f"[DEBUG] is_creator determinado como: {is_creator}")
                try:
                    await self.steps.handle_content_creator_choice(user_id, call.message.chat.id, is_creator)
                    self.logger.info(f"[DEBUG] handle_content_creator_choice executado com sucesso")
                except Exception as e:
                    self.logger.error(f"[DEBUG] Erro em handle_content_creator_choice: {e}")
                    raise
            
            # Acordo de monetização
            elif current_state == user_states.AWAITING_MONETIZATION_CHOICE:
                accepted = callback_data == "accept_monetization"
                await self.steps.handle_monetization_agreement(user_id, call.message.chat.id, accepted)
            
            # Seleção do grupo
            elif current_state == user_states.AWAITING_GROUP_CHOICE:
                if callback_data.startswith("group_"):
                    group_type = callback_data.replace("group_", "")
                    await self.steps.handle_group_selection(user_id, call.message.chat.id, group_type)
        except TelegramAPIError as e:
            if "bots can't send messages to bots" in str(e):
                self.logger.warning(f"Tentativa de interação de bot com bot bloqueada para o user_id: {user_id}.")
            else:
                self.logger.error(f"Erro de API do Telegram no callback do onboarding: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Erro no callback do onboarding: {e}", exc_info=True)

    async def handle_callback_query(self, call: CallbackQuery):
        """Processa callbacks de onboarding com validação de bot e deduplicação otimizada"""
        try:
            user_id = call.from_user.id
            
            # Verificar se o usuário é um bot - bots não podem usar callbacks
            if call.from_user.is_bot:
                self.logger.warning(f"Bot {user_id} tentou usar callback de onboarding - ignorando")
                return
            
            # Sistema de deduplicação otimizado - usar apenas user_id e data para reduzir overhead
            callback_key = f"{user_id}_{call.data}"
            
            # Verificar se já processamos este callback recentemente
            if callback_key in self.processed_callbacks:
                self.logger.debug(f"Callback duplicado ignorado: {call.data} do usuário {user_id}")
                # Responder ao callback imediatamente para evitar timeout
                try:
                    await self.bot.answer_callback_query(call.id, "✅ Já processado", cache_time=1)
                except Exception as callback_error:
                    self.logger.warning(f"Erro ao responder callback duplicado: {callback_error}")
                return
            
            # Adicionar à lista de processados
            self.processed_callbacks.add(callback_key)
            
            # Limpeza otimizada do cache - manter apenas os últimos 100 callbacks
            if len(self.processed_callbacks) > 100:
                # Remove os mais antigos para manter performance
                old_callbacks = list(self.processed_callbacks)[:50]
                for old_callback in old_callbacks:
                    self.processed_callbacks.discard(old_callback)
            
            # Responder ao callback imediatamente para evitar timeout
            try:
                await self.bot.answer_callback_query(call.id, cache_time=1)
            except Exception as callback_error:
                self.logger.warning(f"Erro ao responder callback: {callback_error}")
                # Continuar processamento mesmo se falhar ao responder callback
            
            # Log otimizado - apenas para callbacks importantes
            if call.data in ["start_onboarding", "confirm_age", "accept_rules", "group_lite", "group_premium"]:
                self.logger.info(f"Callback importante: {call.data} do usuário {user_id}")
            else:
                self.logger.debug(f"Callback: {call.data} do usuário {user_id}")
            
            # Processar o callback de onboarding de forma assíncrona para melhor performance
            await self.handle_onboarding_callback(call)
                    
        except Exception as e:
            # Filtrar erros específicos para evitar spam no log
            error_msg = str(e)
            if "bots can't send messages to bots" in error_msg:
                self.logger.debug(f"Callback de bot ignorado para usuário {user_id}: {error_msg}")
            elif "query is too old" in error_msg or "query ID is invalid" in error_msg:
                self.logger.debug(f"Callback expirado para usuário {user_id}: {error_msg}")
            else:
                self.logger.error(f"Erro geral no handle_callback_query de onboarding: {e}")

    async def _send_welcome_to_group(self, user_id: int):
        """Envia a mensagem de boas-vindas anônima para o grupo principal."""
        try:
            user_data = await self.user_service.get_user(user_id)
            if not user_data:
                logging.error(f"Não foi possível obter os dados do utilizador {user_id} para enviar as boas-vindas ao grupo.")
                return

            # Construir a etiqueta e o teclado
            anonymous_label = build_anonymous_label(user_data)
            bot_username = (await self.bot.get_me()).username
            welcome_keyboard = create_welcome_keyboard(user_id, bot_username)

            # Montar a mensagem
            welcome_message = (
                f"🎉 Um(a) novo(a) Liberal acaba de chegar!\n\n"
                f"{anonymous_label}\n\n"
                "Dê as boas-vindas e interaja de forma anónima através dos botões abaixo."
            )

            # Enviar para o grupo
            await self.bot.send_message(
                chat_id=FREEMIUM_GROUP_ID,
                text=welcome_message,
                reply_markup=welcome_keyboard
            )
            logging.info(f"Mensagem de boas-vindas enviada para o grupo para o novo utilizador {user_id}.")

        except Exception as e:
            logging.error(f"Falha ao enviar mensagem de boas-vindas ao grupo para o utilizador {user_id}: {e}", exc_info=True)

    async def handle_onboarding_message(self, message: Message):
        user_id = message.from_user.id
        user = await self.user_service.get_user(user_id)
        if not user:
            return

        current_state = user.state
        if current_state == user_states.AWAITING_AGE_INPUT:
            await self.steps.handle_age_input(user_id, message.chat.id, message.text)
        elif current_state == user_states.AWAITING_AGE_CONFIRMATION:
            # Usuário está aguardando confirmação de idade via botão, não mensagem de texto
            await self.bot.send_message(
                message.chat.id,
                "⚠️ Por favor, use os botões acima para confirmar sua idade. Não é necessário enviar mensagens de texto."
            )
        elif current_state == user_states.AWAITING_CODENAME:
            await self.steps.handle_codename(user_id, message.chat.id, message.text)
        elif current_state == user_states.AWAITING_PIX_KEY:
            await self.steps.handle_pix_key_input(user_id, message.chat.id, message.text)