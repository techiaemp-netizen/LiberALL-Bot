"""
Módulo para gerenciar os passos do processo de onboarding.
"""
import logging
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services.user_service import UserService
from services.security_service import SecurityService
from utils.error_handler import ErrorHandler
from constants import user_states
from constants.user_states import UserStates


class OnboardingSteps:
    """Classe para gerenciar os passos do onboarding."""
    
    def __init__(self, bot, user_service: UserService, security_service: SecurityService, 
                 error_handler: ErrorHandler, onboarding_handler):  # Aceita tanto Bot quanto RobustTelegramClient
        self.bot = bot
        self.user_service = user_service
        self.security_service = security_service
        self.error_handler = error_handler
        self.onboarding_handler = onboarding_handler
        self.logger = logging.getLogger(__name__)
        
    async def start_onboarding(self, user_id: int, chat_id: int) -> None:
        """Inicia o processo de onboarding com mensagem de boas-vindas."""
        try:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Iniciar Cadastro",
                            callback_data="start_onboarding"
                        )
                    ]
                ]
            )
            
            message = (
                "🌀 *Bem-vindo(a) ao LiberALL!*\n\n"
                "Aqui você participa de uma comunidade anônima e segura, "
                "feita para interação, afinidade e liberdade.\n\n"
                "▶️ Para começar seu cadastro, clique em Iniciar."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem de boas-vindas: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao iniciar onboarding.")
    
    async def request_age_input(self, user_id: int, chat_id: int) -> None:
        """Solicita a idade do usuário."""
        try:
            message = (
                "👤 *Digite sua idade:*\n\n"
                "Por favor, informe sua idade em números."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao solicitar idade: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao solicitar idade.")
    
    async def show_rules_terms(self, user_id: int, chat_id: int) -> None:
        """Mostra as regras do grupo."""
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Aceito",
                        callback_data="accept_rules"
                    ),
                    InlineKeyboardButton(
                        text="❌ Não Aceito",
                        callback_data="decline_rules"
                    )
                ]
            ])
            
            message = (
                "🔒 *Regras Básicas do LiberALL*\n\n"
                "🚫 Proibido menores de 18 anos.\n"
                "🤝 Respeito mútuo é obrigatório.\n"
                "📵 Proibido conteúdo de violência, drogas ilícitas ou envolvendo pessoas vulneráveis.\n"
                "👤 Proibido expor identidade real de outros membros.\n"
                "💳 Comércio só pode ser feito pelas ferramentas oficiais do grupo.\n"
                "🛡 A moderação pode excluir perfis que violem as regras sem aviso prévio."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar regras: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar regras.")
    
    async def show_terms_conditions(self, user_id: int, chat_id: int) -> None:
        """Mostra os termos e condições."""
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Concordo", callback_data="accept_terms")],
                [InlineKeyboardButton(text="❌ Não Concordo", callback_data="reject_terms")]
            ])
            
            message = (
                "📖 *Termos de Uso – LiberALL*\n\n"
                "O LiberALL é um espaço digital de interação, restrito a maiores de 18 anos.\n\n"
                "• Cada usuário é responsável pelo que publica.\n"
                "• O grupo não se responsabiliza por atos individuais de membros.\n"
                "• Conteúdos pagos só podem ser vendidos via sistema oficial (taxa 20%).\n"
                "• Afiliados recebem 20% de indicações confirmadas no Premium.\n"
                "• A administração pode excluir usuários que descumprirem os termos."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar termos e condições: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar termos e condições.")

    async def show_privacy_terms(self, user_id: int, chat_id: int) -> None:
        """Mostra os termos de privacidade."""
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Aceito", callback_data="accept_terms")],
                [InlineKeyboardButton(text="❌ Não aceito", callback_data="reject_terms")]
            ])
            
            message = (
                "🔒 <b>Política de Privacidade</b>\n\n"
                "Informamos sobre:\n\n"
                "• Como coletamos seus dados\n"
                "• Como usamos suas informações\n"
                "• Como protegemos sua privacidade\n"
                "• Seus direitos sobre os dados\n\n"
                "Aceita nossa política de privacidade?"
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar política de privacidade: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar política de privacidade.")

    async def show_lgpd_terms(self, user_id: int, chat_id: int) -> None:
        """Mostra os termos LGPD."""
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Concordo", callback_data="accept_lgpd")],
                [InlineKeyboardButton(text="❌ Não Concordo", callback_data="reject_lgpd")]
            ])
            
            message = (
                "🔐 *Proteção de Dados (LGPD)*\n\n"
                "Coletamos apenas idade, categoria de perfil, codinome, estado e chave Pix (se fornecida).\n\n"
                "• Os dados são usados somente para o funcionamento do grupo.\n"
                "• Não compartilhamos informações com terceiros.\n"
                "• Você pode solicitar correção ou exclusão dos seus dados a qualquer momento."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar termos LGPD: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar termos LGPD.")
    
    async def show_profile_type_selection(self, user_id: int, chat_id: int) -> None:
        """Mostra seleção do tipo de perfil."""
        try:
            
            profiles = [
                ("👩‍❤️‍👨", "Casal", "profile_casal"),
                ("👨", "Solteiro", "profile_solteiro"),
                ("👩", "Solteira", "profile_solteira"),
                ("🎥", "Criador de Conteúdo", "profile_criador"),
                ("🔥", "Casada Hotwife", "profile_hotwife"),
                ("👀", "Cuckold", "profile_cuckold"),
                ("💋", "Casal BI", "profile_casal_bi"),
                ("👩‍❤️‍👩", "Casal Mulher-Mulher", "profile_casal_mm"),
                ("👨‍❤️‍👨", "Casal Homem-Homem", "profile_casal_hh"),
                ("🏳️‍🌈", "Trans", "profile_trans"),
                ("🌊", "Fluido(a)", "profile_fluido"),
                ("❓", "Curioso(a)", "profile_curioso"),
                ("💍", "Casado(a)", "profile_casado")
            ]
            
            buttons = []
            for emoji, name, callback in profiles:
                buttons.append(InlineKeyboardButton(text=f"{emoji} {name}", callback_data=callback))
            
            # Criar teclado com botões em pares
            keyboard_rows = []
            for i in range(0, len(buttons), 2):
                row = []
                row.append(buttons[i])
                if i + 1 < len(buttons):
                    row.append(buttons[i + 1])
                keyboard_rows.append(row)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            
            message = (
                "👥 *Selecione seu perfil:*\n\n"
                "Escolha a opção que melhor descreve você."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar seleção de perfil: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar seleção de perfil.")
    
    async def show_state_selection(self, user_id: int, chat_id: int) -> None:
        """Mostra seleção de estado."""
        try:
            states = [
                ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
                ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"), ("ES", "Espírito Santo"),
                ("GO", "Goiás"), ("MA", "Maranhão"), ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"),
                ("MG", "Minas Gerais"), ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"),
                ("PE", "Pernambuco"), ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
                ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"), ("SC", "Santa Catarina"),
                ("SP", "São Paulo"), ("SE", "Sergipe"), ("TO", "Tocantins")
            ]
            
            buttons = []
            for code, name in states:
                buttons.append(InlineKeyboardButton(text=f"{code} - {name}", callback_data=f"state_{code}"))
            
            # Criar teclado com botões em pares
            keyboard_rows = []
            for i in range(0, len(buttons), 2):
                row = []
                row.append(buttons[i])
                if i + 1 < len(buttons):
                    row.append(buttons[i + 1])
                keyboard_rows.append(row)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            
            message = (
                "🗺️ *Seleção de Estado*\n\n"
                "Em qual estado você está localizado?\n"
                "Isso nos ajuda a personalizar o conteúdo para sua região."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar seleção de estado: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar seleção de estado.")
    
    async def show_relationship_profiles_selection(self, user_id: int, chat_id: int, message_id: int = None) -> None:
        """Mostra seleção de perfis para relacionar (múltipla escolha)."""
        try:
            # CORREÇÃO: Sempre inicializar selected_profiles como lista vazia para novo usuário
            # Isso evita que seleções de usuários anteriores apareçam para novos usuários
            selected_profiles = []
            
            # Apenas carregar seleções existentes se o usuário já tem dados salvos
            user_data = await self.user_service.get_user(user_id)
            if user_data and hasattr(user_data, 'profile') and hasattr(user_data.profile, 'relationship_profiles'):
                if user_data.profile.relationship_profiles and isinstance(user_data.profile.relationship_profiles, list):
                    selected_profiles = user_data.profile.relationship_profiles.copy()
                    self.logger.info(f"Carregando perfis já selecionados para usuário {user_id}: {selected_profiles}")
            else:
                self.logger.info(f"Iniciando seleção de perfis limpa para usuário {user_id}")
            
            profiles = [
                ("👩‍❤️‍👨", "Casal", "rel_casal"),
                ("👨", "Solteiro", "rel_solteiro"),
                ("👩", "Solteira", "rel_solteira"),
                ("🎥", "Criador de Conteúdo", "rel_criador"),
                ("🔥", "Casada Hotwife", "rel_hotwife"),
                ("👀", "Cuckold", "rel_cuckold"),
                ("💋", "Casal BI", "rel_casal_bi"),
                ("👩‍❤️‍👩", "Casal Mulher-Mulher", "rel_casal_mm"),
                ("👨‍❤️‍👨", "Casal Homem-Homem", "rel_casal_hh"),
                ("🏳️‍🌈", "Trans", "rel_trans"),
                ("🌊", "Fluido(a)", "rel_fluido"),
                ("❓", "Curioso(a)", "rel_curioso"),
                ("💍", "Casado(a)", "rel_casado")
            ]
            
            buttons = []
            for emoji, name, callback in profiles:
                # Extrair o tipo do callback (remover 'rel_')
                profile_type = callback.replace('rel_', '')
                
                # Adicionar ✅ se o perfil estiver selecionado
                if profile_type in selected_profiles:
                    button_text = f"✅ {emoji} {name}"
                else:
                    button_text = f"{emoji} {name}"
                
                buttons.append(InlineKeyboardButton(text=button_text, callback_data=callback))
            
            # Criar teclado com botões em pares
            keyboard_rows = []
            for i in range(0, len(buttons), 2):
                row = []
                row.append(buttons[i])
                if i + 1 < len(buttons):
                    row.append(buttons[i + 1])
                keyboard_rows.append(row)
            
            # Botão para finalizar seleção
            keyboard_rows.append([InlineKeyboardButton(text="✅ Finalizar Seleção", callback_data="finish_relationship_selection")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            
            message = (
                "💞 *Com quem você deseja se relacionar?*\n\n"
                "Você pode escolher múltiplas opções. Clique em 'Finalizar Seleção' quando terminar."
            )
            
            # Se temos message_id, editar a mensagem existente, senão enviar nova
            if message_id:
                try:
                    await self.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=message,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                    self.logger.info(f"✅ Mensagem de perfis editada para usuário {user_id}")
                except Exception as edit_error:
                    self.logger.warning(f"Não foi possível editar mensagem: {edit_error}")
                    # Se não conseguir editar, enviar nova mensagem
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar seleção de perfis para relacionar: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar seleção de perfis para relacionar.")
    
    async def ask_content_creator(self, user_id: int, chat_id: int, message_id: int = None) -> None:
        """Pergunta se é criador de conteúdo."""
        try:
            self.logger.info(f"🎥 Iniciando pergunta sobre criador de conteúdo para usuário {user_id}")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Sim", callback_data="creator_yes")],
                [InlineKeyboardButton(text="❌ Não", callback_data="creator_no")]
            ])
            
            message = (
                "🎥 *Você é criador(a) de conteúdo?*"
            )
            
            # Se temos message_id, editar a mensagem anterior, senão enviar nova
            if message_id:
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                self.logger.info(f"✅ Mensagem editada para pergunta sobre criador de conteúdo para usuário {user_id}")
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                self.logger.info(f"✅ Nova mensagem enviada para pergunta sobre criador de conteúdo para usuário {user_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao perguntar sobre criador de conteúdo: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao perguntar sobre criador de conteúdo.")
    
    async def show_monetization_terms(self, user_id: int, chat_id: int) -> None:
        """Mostra os termos de monetização."""
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Aceito", callback_data="accept_monetization")],
                [InlineKeyboardButton(text="❌ Não Aceito", callback_data="reject_monetization")]
            ])
            
            message = (
                "📜 *Regras de Monetização – LiberALL*\n\n"
                "• Você pode vender conteúdos dentro do grupo.\n"
                "• Cada venda tem taxa de 20% retida pela plataforma.\n"
                "• Publicações monetizadas podem ser replicadas no Premium.\n"
                "• É proibido negociar fora do sistema oficial.\n"
                "• Você receberá automaticamente via Pix cadastrado."
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar termos de monetização: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar termos de monetização.")
    
    async def request_pix_key(self, user_id: int, chat_id: int) -> None:
        """Solicita a chave Pix."""
        try:
            message = (
                "💳 *Digite sua chave Pix*\n\n"
                "Aceitamos: *CPF*, *CNPJ*, *e-mail*, *telefone* no formato +55..., ou *chave aleatória (UUID)*.\n\n"
                "Se preferir não cadastrar agora, digite 'pular'."
            )
            
            await self.bot.send_message(
                chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao solicitar chave Pix: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao solicitar chave Pix.")
    
    async def show_group_selection(self, user_id: int, chat_id: int) -> None:
        """Mostra seleção do tipo de grupo."""
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🆓 Lite", callback_data="group_lite")],
                [InlineKeyboardButton(text="💎 Premium", callback_data="group_premium")]
            ])
            
            message = (
                "👥 *Escolha o grupo para ingressar:*\n\n"
                "🆓 *Lite* – Acesso gratuito, 5 mensagens/mês, galeria básica.\n\n"
                "💎 *Premium* – Acesso ilimitado, todos os recursos liberados."
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar seleção de grupo: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar seleção de grupo.")
    
    async def show_group_access_link(self, user_id: int, chat_id: int, group_type: str) -> None:
        """Mostra o link de acesso ao grupo.
        Gera dinamicamente um convite válido com fallback via export e envia com HTML.
        """
        try:
            from config import FREEMIUM_GROUP_ID, PREMIUM_GROUP_ID
            from utils.invite_link_helper import get_group_invite_url

            if group_type == "lite":
                group_id = FREEMIUM_GROUP_ID
                group_label = "Lite"
            else:
                group_id = PREMIUM_GROUP_ID
                group_label = "Premium"

            # Obter URL de convite válida (criar ou exportar)
            # Forçar refresh e preferir link com join request para maior confiabilidade
            group_url = await get_group_invite_url(self.bot, group_id, logger=self.logger, force_refresh=True, prefer_join_request=True)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🔗 Entrar no Grupo {group_label}", url=group_url)],
                [InlineKeyboardButton(text="♻️ Gerar novo link", callback_data=f"onboarding_refresh_invite_{group_type}")]
            ])
            message = (
                f"🔗 <b>Clique abaixo para entrar no grupo {group_label}:</b>\n\n"
                + ("🆓 <b>Grupo Lite</b> - Acesso gratuito com 5 mensagens por mês" if group_label == "Lite" else
                   "💎 <b>Grupo Premium</b> - Acesso ilimitado a todos os recursos")
            )

            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )

        except Exception as e:
            self.logger.error(f"Erro ao enviar link de acesso: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao mostrar link de acesso.")
    
    async def request_codename(self, user_id: int, chat_id: int) -> None:
        """Solicita o codinome do usuário."""
        try:
            message = (
                "🎭 <b>Escolha seu Codinome</b>\n\n"
                "Agora você precisa escolher um codinome único para usar no LiberALL.\n\n"
                "<b>Regras:</b>\n"
                "• Entre 3 e 20 caracteres\n"
                "• Apenas letras, números e underscore (_)\n"
                "• Não pode começar com número\n"
                "• Deve ser único na plataforma\n\n"
                "Digite seu codinome desejado:"
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao solicitar codinome: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao solicitar codinome.")
    
    async def complete_onboarding(self, user_id: int, chat_id: int, user_data: Dict[str, Any]) -> None:
        """Completa o processo de onboarding."""
        try:
            # Salvar usuário no banco de dados
            await self.user_service.create_user(
                user_id=user_id,
                codename=user_data.get('codename'),
                state=user_data.get('selected_state'),
                category=user_data.get('selected_category'),
                terms_accepted=user_data.get('terms_accepted', False),
                age_confirmed=user_data.get('age_confirmed', False)
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Menu Principal", callback_data="main_menu")]
            ])
            
            message = (
                f"🎉 *Bem-vindo ao LiberALL, {user_data.get('codename')}!*\n\n"
                "Seu cadastro foi concluído com sucesso!\n\n"
                "*Seus dados:*\n"
                f"• Codinome: {user_data.get('codename')}\n"
                f"• Estado: {user_data.get('selected_state')}\n"
                f"• Plano: {user_data.get('selected_category', '').title()}\n\n"
                "Agora você pode explorar todas as funcionalidades da plataforma!"
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # Log da conclusão
            self.security_service.log_user_action(user_id, 'onboarding_completed')
            
        except Exception as e:
            self.logger.error(f"Erro ao completar onboarding: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao finalizar cadastro.")
    
    async def handle_age_confirmation(self, call: CallbackQuery, user) -> None:
        """Manipula a confirmação de idade."""
        try:
            if call.data == "confirm_age":
                await self.user_service.batch_update_user_data(user.telegram_id, [
                    {'state': user_states.AWAITING_RULES_AGREEMENT}
                ])
                await self.show_rules_terms(user.telegram_id, call.message.chat.id)
            else:
                await self.bot.send_message(
                    chat_id=call.message.chat.id,
                    text="❌ Você precisa ter 18 anos ou mais para usar o LiberALL."
                )
        except Exception as e:
            self.logger.error(f"Erro ao processar confirmação de idade: {e}")
            await self.error_handler.handle_error(self.bot, user.telegram_id, "Erro ao processar confirmação de idade.")
    
    async def handle_agreement(self, call: CallbackQuery, user, agreement_type: str, next_state: str, next_method) -> None:
        """Manipula acordos de termos."""
        try:
            if call.data == "accept_terms":
                # Salvar acordo no usuário e atualizar estado em batch
                await self.user_service.batch_update_user_data(user.telegram_id, [
                    {agreement_type: True, 'state': next_state}
                ])
                await next_method(user.telegram_id, call.message.chat.id)
            else:
                await self.bot.send_message(
                    chat_id=call.message.chat.id,
                    text="❌ Você precisa aceitar os termos para continuar."
                )
        except Exception as e:
            self.logger.error(f"Erro ao processar acordo: {e}")
            await self.error_handler.handle_error(self.bot, user.telegram_id, "Erro ao processar acordo.")
    
    async def ask_for_privacy(self, user_id: int, chat_id: int) -> None:
        """Solicita aceite da política de privacidade."""
        await self.show_terms(user_id, chat_id)
    
    async def ask_for_lgpd(self, user_id: int, chat_id: int) -> None:
        """Solicita aceite dos termos LGPD."""
        await self.show_terms(user_id, chat_id)
    
    async def ask_for_category(self, user_id: int, chat_id: int) -> None:
        """Solicita seleção de categoria."""
        await self.show_category_selection(user_id, chat_id)
    
    async def handle_category_selection(self, call: CallbackQuery, user) -> None:
        """Manipula seleção de categoria com limpeza de estado."""
        try:
            category = call.data.replace("category_", "")
            user_id = user.telegram_id
            
            # Limpar estado anterior de categorias selecionadas para este usuário
            await self._clear_user_category_state(user_id)
            
            # Salvar categoria no usuário e atualizar estado em batch
            await self.user_service.batch_update_user_data(user_id, [
                {'category': category, 'state': user_states.AWAITING_LOCATION}
            ])
            
            self.logger.info(f"Categoria '{category}' selecionada para usuário {user_id}")
            await self.show_state_selection(user_id, call.message.chat.id)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar seleção de categoria: {e}")
            await self.error_handler.handle_error(self.bot, user.telegram_id, "Erro ao processar seleção de categoria.")

    async def _clear_user_category_state(self, user_id: int):
        """Limpa o estado de categorias selecionadas para um usuário específico."""
        try:
            # Limpar dados de categoria no perfil do usuário
            await self.user_service.batch_update_user_data(user_id, [
                {'profile.selected_categories': None},
                {'profile.category_selection_state': None},
                {'profile.temp_category_data': None}
            ])
            
            # Limpar estado temporário no handler se existir
            if hasattr(self.onboarding_handler, 'user_states') and user_id in self.onboarding_handler.user_states:
                user_state_data = self.onboarding_handler.user_states[user_id]
                if 'data' in user_state_data:
                    user_state_data['data'].pop('selected_categories', None)
                    user_state_data['data'].pop('category_state', None)
            
            self.logger.info(f"Estado de categoria limpo para usuário {user_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar estado de categoria para usuário {user_id}: {e}")
    
    async def handle_location_selection(self, call: CallbackQuery, user) -> None:
        """Manipula seleção de localização (estados) com otimização de batch."""
        try:
            state = call.data.replace("state_", "")
            self.logger.info(f"🏠 Processando seleção de estado: {state} para usuário {user.telegram_id}")
            
            # Batch update: salvar estado e mudar state em uma única operação
            batch_updates = [
                {"profile.state_location": state},
                {"state": user_states.AWAITING_CONTENT_CREATOR_CHOICE}
            ]
            
            await self.user_service.batch_update_user_data(user.telegram_id, batch_updates)
            self.logger.info(f"✅ Estado {state} salvo e state alterado para AWAITING_CONTENT_CREATOR_CHOICE para usuário {user.telegram_id}")
            
            # Editar a mensagem atual para a pergunta de criador de conteúdo
            await self.ask_content_creator(user.telegram_id, call.message.chat.id, call.message.message_id)
            self.logger.info(f"❓ Pergunta sobre criador de conteúdo enviada para usuário {user.telegram_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar seleção de localização: {e}")
            await self.error_handler.handle_error(self.bot, user.telegram_id, "Erro ao processar seleção de localização.")
    
    async def handle_monetization_choice(self, call: CallbackQuery, user) -> None:
        """Manipula escolha de monetização com otimização de batch."""
        try:
            # Batch update: finalizar onboarding e definir estado IDLE em uma única operação
            batch_updates = [
                {"onboarded": True},
                {"state": user_states.IDLE}
            ]
            
            await self.user_service.batch_update_user_data(user.telegram_id, batch_updates)
            self.logger.info(f"✅ Onboarding finalizado e estado alterado para IDLE para usuário {user.telegram_id}")
            
            # Enviar mensagem de conclusão
            await self.bot.send_message(
                chat_id=call.message.chat.id,
                text="🎉 Parabéns! Seu perfil foi criado com sucesso!\n\n"
                     "Agora você pode começar a usar o LiberALL. "
                     "Use /help para ver os comandos disponíveis."
            )
        except Exception as e:
            self.logger.error(f"Erro ao processar escolha de monetização: {e}")
            await self.error_handler.handle_error(self.bot, user.telegram_id, "Erro ao processar escolha de monetização.")
    
    async def handle_age_input(self, user_id: int, chat_id: int, age_text: str) -> None:
        """Manipula a entrada da idade com proteção contra loops infinitos."""
        try:
            # Criar chave única para deduplicação
            processing_key = f"age_input_{user_id}_{age_text.strip()}"
            
            # Verificar se já estamos processando esta entrada
            if hasattr(self, '_processing_age_inputs'):
                if processing_key in self._processing_age_inputs:
                    self.logger.warning(f"🔄 Entrada de idade duplicada ignorada para usuário {user_id}")
                    return
            else:
                self._processing_age_inputs = set()
            
            # Marcar como em processamento
            self._processing_age_inputs.add(processing_key)
            
            try:
                # Verificar se o usuário já está no estado AWAITING_AGE_CONFIRMATION
                user = await self.user_service.get_user(user_id)
                if user and user.state == user_states.UserStates.AWAITING_AGE_CONFIRMATION:
                    # Usuário já está aguardando confirmação, não processar novamente
                    self.logger.info(f"⚠️ Usuário {user_id} já está em AWAITING_AGE_CONFIRMATION - ignorando nova entrada")
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="⚠️ Por favor, use os botões acima para confirmar sua idade. Não é necessário enviar mensagens de texto."
                    )
                    return
                
                # Validar se é um número
                try:
                    age = int(age_text.strip())
                except ValueError:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Por favor, digite apenas números. Qual é a sua idade?"
                    )
                    return
                
                # Verificar se é maior de idade
                if age < 18:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="❌ O acesso é restrito a maiores de 18 anos. Você não poderá prosseguir."
                    )
                    # Resetar estado do usuário
                    await self.user_service.batch_update_user_data(user_id, [
                        {'state': user_states.UserStates.IDLE}
                    ])
                    return

                # Verificar se a idade já foi salva para evitar duplicatas
                if user and hasattr(user, 'profile') and hasattr(user.profile, 'age') and user.profile.age == age:
                    # Idade já foi salva, apenas mostrar confirmação
                    self.logger.info(f"⚠️ Idade {age} já estava salva para usuário {user_id}, apenas mostrando confirmação")
                else:
                    # Batch update: salvar idade e atualizar estado em uma única operação
                    batch_updates = [
                        {"profile.age": age},
                        {"state": user_states.UserStates.AWAITING_AGE_CONFIRMATION}
                    ]
                    
                    await self.user_service.batch_update_user_data(user_id, batch_updates)
                    self.logger.info(f"✅ Idade {age} salva e estado alterado para AWAITING_AGE_CONFIRMATION para usuário {user_id}")
                
                # Mostrar confirmação de idade apenas uma vez
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Confirmo que tenho 18+ anos", callback_data="confirm_age")],
                    [InlineKeyboardButton(text="❌ Tenho menos de 18 anos", callback_data="reject_age")]
                ])
                
                await self.bot.send_message(
                    chat_id,
                    text=f"📅 Você informou ter {age} anos.\n\n🔞 Confirma que tem 18 anos ou mais?",
                    reply_markup=keyboard
                )
                
            finally:
                # Remover da lista de processamento após um delay
                import asyncio
                await asyncio.sleep(2)  # Aguardar 2 segundos antes de permitir reprocessamento
                self._processing_age_inputs.discard(processing_key)
                
                # Limpar cache se ficar muito grande
                if len(self._processing_age_inputs) > 100:
                    self._processing_age_inputs.clear()
                
        except Exception as e:
            self.logger.error(f"Erro ao processar idade: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar idade.")
    
    async def handle_profile_type_selection(self, user_id: int, chat_id: int, profile_type: str) -> None:
        """Manipula a seleção do tipo de perfil com otimização de batch."""
        try:
            # Para perfil de casal, ir para seleção de perfis de relacionamento primeiro
            if profile_type == "casal":
                batch_updates = [
                    {"profile.profile_type": profile_type},
                    {"state": user_states.AWAITING_RELATIONSHIP_PROFILES}
                ]
                
                await self.user_service.batch_update_user_data(user_id, batch_updates)
                self.logger.info(f"✅ Tipo de perfil {profile_type} salvo e estado alterado para AWAITING_RELATIONSHIP_PROFILES para usuário {user_id}")
                
                # Mostrar seleção de perfis de relacionamento
                await self.show_relationship_profiles_selection(user_id, chat_id)
            else:
                # Para outros tipos de perfil, ir direto para codinome
                batch_updates = [
                    {"profile.profile_type": profile_type},
                    {"state": user_states.AWAITING_CODENAME}
                ]
                
                await self.user_service.batch_update_user_data(user_id, batch_updates)
                self.logger.info(f"✅ Tipo de perfil {profile_type} salvo e estado alterado para AWAITING_CODENAME para usuário {user_id}")
                
                # Solicitar codinome
                await self.request_codename(user_id, chat_id)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar seleção de perfil: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar seleção de perfil.")
    
    async def handle_relationship_profile_selection(self, user_id: int, chat_id: int, profile_type: str, message_id: int = None) -> None:
        """Manipula a seleção de perfis para relacionar (múltipla escolha)."""
        try:
            user_data = await self.user_service.get_user(user_id)
            if user_data:
                # Garantir que relationship_profiles existe e é uma lista
                if not hasattr(user_data.profile, 'relationship_profiles') or user_data.profile.relationship_profiles is None:
                    user_data.profile.relationship_profiles = []
                
                # Garantir que é uma lista (caso tenha sido salvo como outro tipo)
                if not isinstance(user_data.profile.relationship_profiles, list):
                    user_data.profile.relationship_profiles = []
                
                # Adicionar ou remover da lista
                if profile_type in user_data.profile.relationship_profiles:
                    user_data.profile.relationship_profiles.remove(profile_type)
                    status = "removido"
                else:
                    user_data.profile.relationship_profiles.append(profile_type)
                    status = "adicionado"
                
                # Atualizar usando batch para evitar múltiplas operações
                await self.user_service.batch_update_user_data(user_id, [
                    {'profile.relationship_profiles': user_data.profile.relationship_profiles}
                ])
                
                # CORREÇÃO: Editar a mensagem existente em vez de enviar nova
                # Isso evita o loop infinito de mensagens
                if message_id:
                    await self.show_relationship_profiles_selection(user_id, chat_id, message_id)
                else:
                    self.logger.warning(f"message_id não fornecido para edição da mensagem")
                
                self.logger.info(f"✅ Perfil {profile_type} {status} para usuário {user_id}")
                
            else:
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao salvar perfil para relacionar.")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar seleção de perfil para relacionar: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar seleção de perfil para relacionar.")
    
    async def handle_finish_relationship_selection(self, user_id: int, chat_id: int) -> None:
        """Finaliza a seleção de perfis para relacionar."""
        try:
            user_data = await self.user_service.get_user(user_id)
            if user_data:
                # Atualizar estado para próxima etapa
                await self.user_service.update_user(user_id, {
                    'state': user_states.AWAITING_LOCATION
                }, immediate=True)
                
                # Mostrar seleção de estado
                await self.show_state_selection(user_id, chat_id)
            else:
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao finalizar seleção de perfis.")
                
        except Exception as e:
            self.logger.error(f"Erro ao finalizar seleção de perfis: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao finalizar seleção de perfis.")
    
    async def handle_content_creator_choice(self, user_id: int, chat_id: int, is_creator: bool) -> None:
        """Manipula a escolha de criador de conteúdo."""
        try:
            self.logger.info(f"[DEBUG] Iniciando handle_content_creator_choice - user_id: {user_id}, is_creator: {is_creator}")
            user_data = await self.user_service.get_user(user_id)
            if user_data:
                self.logger.info(f"[DEBUG] Dados do usuário obtidos com sucesso")
                user_data.profile.is_content_creator = is_creator
                self.logger.info(f"[DEBUG] is_content_creator definido como: {is_creator}")
                
                if is_creator:
                    # Se é criador, mostrar termos de monetização
                    self.logger.info(f"[DEBUG] Usuário é criador - redirecionando para termos de monetização")
                    await self.user_service.update_user(user_id, {
                        'profile.is_content_creator': is_creator,
                        'state': user_states.AWAITING_MONETIZATION_CHOICE
                    }, immediate=True)
                    self.logger.info(f"[DEBUG] Estado alterado para AWAITING_MONETIZATION_CHOICE")
                    await self.show_monetization_terms(user_id, chat_id)
                    self.logger.info(f"[DEBUG] Termos de monetização enviados")
                else:
                    # Se não é criador, pular para seleção de grupo
                    self.logger.info(f"[DEBUG] Usuário não é criador - redirecionando para seleção de grupo")
                    await self.user_service.update_user(user_id, {
                        'profile.is_content_creator': is_creator,
                        'state': user_states.AWAITING_GROUP_CHOICE
                    }, immediate=True)
                    self.logger.info(f"[DEBUG] Estado alterado para AWAITING_GROUP_CHOICE")
                    await self.show_group_selection(user_id, chat_id)
                    self.logger.info(f"[DEBUG] Seleção de grupo enviada")
            else:
                self.logger.error(f"[DEBUG] Erro: dados do usuário não encontrados")
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao salvar escolha de criador.")
                
        except Exception as e:
            self.logger.error(f"[DEBUG] Erro ao processar escolha de criador: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar escolha de criador.")
    
    async def handle_monetization_agreement(self, user_id: int, chat_id: int, accepted: bool) -> None:
        """Manipula o acordo de monetização."""
        try:
            user_data = await self.user_service.get_user(user_id)
            if user_data:
                if accepted:
                    # Se aceitou, solicitar chave Pix
                    await self.user_service.update_user(user_id, {
                        'monetization.enabled': True,
                        'state': user_states.AWAITING_PIX_KEY
                    }, immediate=True)
                    await self.request_pix_key(user_id, chat_id)
                else:
                    # Se não aceitou, informar e pular para seleção de grupo
                    await self.user_service.update_user(user_id, {
                        'monetization.enabled': False,
                        'state': user_states.AWAITING_GROUP_CHOICE
                    }, immediate=True)
                    
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="Seu perfil foi criado sem monetização. Você pode ativar futuramente em Configurações > Monetização."
                    )
                    
                    await self.show_group_selection(user_id, chat_id)
            else:
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar acordo de monetização.")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar acordo de monetização: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar acordo de monetização.")
    
    async def handle_pix_key_input(self, user_id: int, chat_id: int, pix_key: str) -> None:
        """Manipula a entrada da chave Pix com validação e criptografia."""
        try:
            user_data = await self.user_service.get_user(user_id)
            if not user_data:
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao salvar chave Pix.")
                return

            # Preparar atualizações
            updates = {'state': user_states.AWAITING_GROUP_CHOICE}

            # Se usuário não quiser informar, apenas seguir adiante
            if pix_key.lower().strip() != 'pular':
                raw_key = pix_key.strip()
                try:
                    # Validar formato da chave PIX
                    if not self.security_service.validate_pix_key(raw_key):
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=(
                                "❌ Chave Pix inválida. Aceitamos: CPF, CNPJ, e-mail, telefone (+55...) ou chave aleatória (UUID).\n"
                                "Por favor, tente novamente ou digite 'pular' para seguir sem cadastrar."
                            )
                        )
                        # Re-solicitar a chave PIX sem alterar estado de grupo ainda
                        await self.request_pix_key(user_id, chat_id)
                        return

                    # Criptografar chave antes de salvar
                    encrypted_key = self.security_service.encrypt_sensitive_data(raw_key)
                    updates['monetization.pix_key'] = encrypted_key
                except Exception as enc_err:
                    self.logger.error(f"Falha ao validar/criptografar chave Pix: {enc_err}")
                    await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar chave Pix.")
                    return

            # Atualizar dados do usuário (compatível com serviços com/sem 'immediate')
            try:
                # Alguns serviços aceitam 'immediate', outros não; detectar dinamicamente
                if hasattr(self.user_service, 'update_user'):
                    update_fn = getattr(self.user_service, 'update_user')
                    if 'immediate' in getattr(update_fn, '__code__').co_varnames:
                        await update_fn(user_id, updates, immediate=True)
                    else:
                        await update_fn(user_id, updates)
                else:
                    # Fallback: tentar set_user_state apenas
                    await self.user_service.set_user_state(user_id, updates.get('state', user_states.AWAITING_GROUP_CHOICE))
            except Exception as upd_err:
                self.logger.error(f"Erro ao atualizar usuário com chave Pix: {upd_err}")
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao salvar chave Pix.")
                return

            # Mostrar seleção de grupo
            await self.show_group_selection(user_id, chat_id)

        except Exception as e:
            self.logger.error(f"Erro geral ao processar chave Pix: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar chave Pix.")
    
    async def handle_group_selection(self, user_id: int, chat_id: int, group_type: str) -> None:
        """Manipula a seleção do tipo de grupo."""
        try:
            user_data = await self.user_service.get_user(user_id)
            if user_data:
                await self.user_service.update_user(user_id, {
                    'profile.category': group_type,
                    'profile.onboarded': True,  # Marcar onboarding como completo
                    'state': user_states.IDLE  # Onboarding completo
                }, immediate=True)
                
                # Atualizar estado para active
                await self.user_service.set_user_state(user_id, "active")
                
                # Enviar mensagem de boas-vindas para o grupo
                await self.onboarding_handler._send_welcome_to_group(user_id)
                
                # Mostrar link de acesso
                await self.show_group_access_link(user_id, chat_id, group_type)
                
                # Mensagem de conclusão no chat privado
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Seu perfil foi criado com sucesso!\n\n"
                         "Agora você já pode interagir na comunidade. Use os botões no grupo ou fale comigo por aqui.",
                    parse_mode='Markdown'
                )
                
                # Exibir menu principal após conclusão do onboarding
                await self._show_main_menu_after_onboarding(user_id, chat_id)
                
            else:
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao finalizar cadastro.")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar seleção de grupo: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar seleção de grupo.")
    
    async def _show_main_menu_after_onboarding(self, user_id: int, chat_id: int) -> None:
        """Exibe o menu principal após a conclusão do onboarding."""
        try:
            
            # Criar teclado inline do menu principal
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Meu Perfil", callback_data="profile")],
                [InlineKeyboardButton(text="📝 Criar Post", callback_data="start_post")],
                [InlineKeyboardButton(text="❤️ Favoritos", callback_data="favorites")],
                [InlineKeyboardButton(text="⚙️ Configurações", callback_data="settings")]
            ])
            
            menu_text = (
                "🏠 <b>Menu Principal</b>\n\n"
                "Agora você pode explorar todas as funcionalidades da plataforma!\n\n"
                "Escolha uma das opções abaixo:"
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=menu_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao exibir menu após onboarding: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao exibir menu principal.")
    
    async def _send_welcome_message_to_group(self, user_data, group_type: str) -> None:
        """Envia mensagem de boas-vindas no grupo escolhido."""
        try:
            from config import FREEMIUM_GROUP_ID, PREMIUM_GROUP_ID, BOT_USERNAME
            from utils.ui_builder import build_anonymous_label
            from constants.callbacks import PostingCallbacks
            
            # Determinar o ID do grupo baseado no tipo
            if group_type == "lite":
                group_id = FREEMIUM_GROUP_ID
            else:
                group_id = PREMIUM_GROUP_ID
            
            # Obter dados do usuário para a etiqueta de anonimização
            user_dict = {
                'codename': user_data.profile.codename if hasattr(user_data.profile, 'codename') else "Novo membro",
                'category': user_data.profile.profile_type if hasattr(user_data.profile, 'profile_type') else "Indefinido",
                'state': user_data.profile.state if hasattr(user_data.profile, 'state') else "BR"
            }
            
            # Criar etiqueta de anonimização
            anonymous_label = build_anonymous_label(user_dict)
            
            # Mensagem de boas-vindas com etiqueta
            welcome_message = f"{anonymous_label}\n\nBoas vindas ao grupo mais quente do Brasil! 🔥\nAgora você pode aproveitar todas as funcionalidades disponíveis."
            
            # Criar teclado inline com botões de interação
            keyboard_rows = [
                [
                    InlineKeyboardButton(text="❤️ Match", callback_data=f"{PostingCallbacks.MATCH_POST}welcome"),
                    InlineKeyboardButton(text="🖼️ Galeria", callback_data=f"{PostingCallbacks.GALLERY_POST}welcome"),
                    InlineKeyboardButton(text="⭐ Favoritar", callback_data=f"{PostingCallbacks.FAVORITE_POST}welcome")
                ],
                [
                    InlineKeyboardButton(text="ℹ️ Informações", callback_data=f"{PostingCallbacks.INFO_POST}welcome"),
                    InlineKeyboardButton(text="💭 Comentários", callback_data=f"{PostingCallbacks.COMMENT_POST}welcome")
                ],
                [
                    InlineKeyboardButton(text="➕ Postar no Grupo", url=f"https://t.me/{BOT_USERNAME}?start=iniciar_postagem"),
                    InlineKeyboardButton(text="☰ Menu", url=f"https://t.me/{BOT_USERNAME}?start=abrir_menu")
                ]
            ]
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            
            # Enviar mensagem no grupo com teclado
            await self.bot.send_message(
                chat_id=group_id,
                text=welcome_message,
                reply_markup=keyboard
            )
            
            self.logger.info(f"Mensagem de boas-vindas enviada para o grupo {group_type} (ID: {group_id}) para o usuário {user_dict['codename']}")
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem de boas-vindas no grupo: {e}")
            # Não propagar o erro para não interromper o fluxo de onboarding
    
    async def handle_codename(self, user_id: int, chat_id: int, codename: str) -> None:
        """Manipula a entrada do codinome."""
        try:
            # Validar codinome
            if not codename or len(codename.strip()) < 3:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ O codinome deve ter pelo menos 3 caracteres. Tente novamente:"
                )
                return
            
            if len(codename.strip()) > 20:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ O codinome deve ter no máximo 20 caracteres. Tente novamente:"
                )
                return
            
            # Validar caracteres permitidos
            import re
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', codename.strip()):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ O codinome deve começar com uma letra e conter apenas letras, números e underscore (_). Tente novamente:"
                )
                return
            
            # Verificar se o codinome já existe
            existing_user = await self.user_service.get_user_by_codename(codename.strip())
            if existing_user:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Este codinome já está em uso. Escolha outro:"
                )
                return
            
            # Salvar codinome
            user_data = await self.user_service.get_user(user_id)
            if user_data:
                user_data.profile.codename = codename.strip()
                user_data.state = user_states.AWAITING_RELATIONSHIP_PROFILES
                await self.user_service.update_user(user_id, user_data.to_dict())
                
                # Mostrar seleção de perfis para relacionar
                await self.show_relationship_profiles_selection(user_id, chat_id)
            else:
                await self.error_handler.handle_error(self.bot, user_id, "Erro ao salvar codinome.")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar codinome: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar codinome.")
    
    async def handle_pix_key(self, message: Message, user) -> None:
        """Manipula entrada da chave PIX."""
        try:
            pix_key = message.text.strip()
            # Salvar chave PIX
            user.pix_key = pix_key
            await self.user_service.update_user(user.telegram_id, user.to_dict())
            
            await self.bot.send_message(
                chat_id=message.chat.id,
                text="✅ Chave PIX salva com sucesso!"
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao processar chave PIX: {e}")
            await self.error_handler.handle_error(self.bot, user.telegram_id, "Erro ao processar chave PIX.")