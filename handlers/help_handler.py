"""Handler para comando /help do LiberALL Bot."""

import logging
from typing import Optional, Dict, Any
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
# InlineKeyboardBuilder não existe no PTB v20 - usar InlineKeyboardMarkup com lista de botões

from utils.safeget import get_field, safe_get_user_field
from services.firebase_service import firebase_service
from utils.safe_reply import safe_reply
from utils.permissions import is_admin
from services.security_service import security_service
from constants.callbacks import MenuCallbacks, SettingsCallbacks, LGPDCallbacks, NavigationCallbacks, AdminCallbacks

logger = logging.getLogger(__name__)

def register_help_handlers(bot, error_handler):
    """Registra os handlers de ajuda no bot."""
    help_handler = HelpHandler(bot)
    
    @bot.message_handler(commands=['help'])
    async def help_command(message):
        await help_handler.handle_help_command(message)

class HelpHandler:
    """Handler responsável pelo comando /help e informações de ajuda."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.security_service = security_service
        
    async def handle_help_command(self, message: Message) -> None:
        """
        Processa o comando /help.
        
        Args:
            message: Mensagem do Telegram
        """
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # Sanitizar dados do usuário
            user_input_data = {
                'telegram_id': user_id,
                'username': message.from_user.username or '',
                'first_name': message.from_user.first_name or ''
            }
            sanitized_data = self.security_service.sanitize_user_data(user_input_data)
            
            # Log de auditoria
            await self.security_service.log_user_action(
                user_id=str(user_id),
                action='help_command_accessed',
                details={'command': '/help'}
            )
            
            # Obtém dados do usuário
            user_data = await firebase_service.get_user(user_id)
            
            # Usa get_field para acessar dados de forma segura
            codinome = safe_get_user_field(user_data, 'codinome', 'Usuário Anônimo')
            is_premium = get_field(user_data, 'is_premium', False)
            posts_count = get_field(user_data, 'posts_count', 0)
            
            # Verifica se é admin
            admin_status = is_admin(user_id)
            
            # Monta mensagem de ajuda personalizada
            help_text = self._build_help_message(codinome, is_premium, posts_count, admin_status)
            
            # Cria teclado inline com opções de ajuda
            keyboard = self._create_help_keyboard(admin_status)
            
            # Envia resposta
            safe_reply(
                message,
                help_text,
                parse_mode='HTML',
                bot=self.bot
            )
            
            logger.info(f"Comando /help processado para usuário {user_id} ({codinome})")
            
        except Exception as e:
            logger.error(f"Erro ao processar comando /help: {e}")
            safe_reply(
                message,
                "❌ Ocorreu um erro ao processar sua solicitação. Tente novamente.",
                bot=self.bot
            )
    
    def _build_help_message(self, codinome: str, is_premium: bool, posts_count: int, is_admin: bool) -> str:
        """
        Constrói a mensagem de ajuda personalizada.
        
        Args:
            codinome: Nome do usuário
            is_premium: Se é usuário premium
            posts_count: Número de posts do usuário
            is_admin: Se é administrador
            
        Returns:
            str: Mensagem de ajuda formatada
        """
        premium_badge = "👑" if is_premium else ""
        admin_badge = "🛡️" if is_admin else ""
        
        help_text = f"""🤖 <b>LiberALL Bot - Ajuda</b>

👋 Olá, <b>{codinome}</b>! {premium_badge}{admin_badge}

📊 <b>Suas estatísticas:</b>
• Posts publicados: {posts_count}
• Status: {'Premium' if is_premium else 'Gratuito'}

🔧 <b>Comandos disponíveis:</b>

<b>📝 Postagem:</b>
• /start - Iniciar ou reiniciar o bot
• ➕ Postar - Criar nova postagem
• 🖼️ Ver Galeria - Visualizar suas postagens

<b>👤 Perfil:</b>
• ⚙️ Configurações - Ajustar preferências
• 📊 Estatísticas - Ver dados detalhados
• 🔄 Atualizar Perfil - Modificar informações

<b>🎯 Interação:</b>
• ❤️ Match - Curtir postagens
• ⭐ Favoritar - Salvar postagens
• 💭 Comentários - Interagir com posts
• ℹ️ Info - Detalhes da postagem

<b>🛡️ Privacidade:</b>
• 🔒 Configurar Privacidade - Ajustar visibilidade
• 📤 Exportar Dados - Download dos seus dados (LGPD)
• 🗑️ Excluir Conta - Remover permanentemente
"""
        
        if is_premium:
            help_text += "\n👑 <b>Recursos Premium:</b>\n"
            help_text += "• Posts ilimitados\n"
            help_text += "• Prioridade no suporte\n"
            help_text += "• Recursos exclusivos\n"
        
        if is_admin:
            help_text += "\n🛡️ <b>Comandos Admin:</b>\n"
            help_text += "• /admin - Painel administrativo\n"
            help_text += "• /stats - Estatísticas globais\n"
            help_text += "• /broadcast - Envio em massa\n"
        
        help_text += "\n💡 <b>Dica:</b> Use os botões abaixo para navegar rapidamente!"
        
        return help_text
    
    def _create_help_keyboard(self, is_admin: bool) -> InlineKeyboardMarkup:
        """
        Cria teclado inline para o comando /help.
        
        Args:
            is_admin: Se é administrador
            
        Returns:
            InlineKeyboardMarkup: Teclado com opções
        """
        keyboard = [
            # Primeira linha - Ações principais
            [
                InlineKeyboardButton(text="➕ Nova Postagem", callback_data=MenuCallbacks.CREATE_POST),
            InlineKeyboardButton(text="🖼️ Minha Galeria", callback_data=MenuCallbacks.MY_POSTS)
            ],
            # Segunda linha - Configurações
            [
                InlineKeyboardButton(text="⚙️ Configurações", callback_data=MenuCallbacks.SETTINGS),
            InlineKeyboardButton(text="📊 Estatísticas", callback_data=SettingsCallbacks.STATS)
            ],
            # Terceira linha - Privacidade
            [
                InlineKeyboardButton(text="🔒 Privacidade", callback_data=SettingsCallbacks.PRIVACY),
            InlineKeyboardButton(text="📤 Exportar Dados", callback_data=LGPDCallbacks.EXPORT)
            ],
            # Quarta linha - Suporte
            [
                InlineKeyboardButton(text="💬 Suporte", callback_data=NavigationCallbacks.CONTACT_SUPPORT),
            InlineKeyboardButton(text="📋 Termos de Uso", callback_data=LGPDCallbacks.TERMS)
            ]
        ]
        
        # Linha admin (se aplicável)
        if is_admin:
            keyboard.append([
                InlineKeyboardButton(text="🛡️ Painel Admin", callback_data=AdminCallbacks.ADMIN_PANEL)
            ])
        
        # Linha de fechamento
        keyboard.append([
             InlineKeyboardButton(text="❌ Fechar", callback_data=NavigationCallbacks.CANCEL)
         ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    async def handle_help_callback(self, callback_query) -> None:
        """
        Processa callbacks do menu de ajuda.
        
        Args:
            callback_query: Callback query do Telegram
        """
        try:
            # Verificar se o usuário é um bot
            if callback_query.from_user.is_bot:
                logger.warning(f"Bot tentou usar callback de ajuda: {callback_query.from_user.id}")
                return
                
            data = callback_query.data
            user_id = callback_query.from_user.id
            message = callback_query.message
            
            # Validar formato do callback
            if not self._is_valid_help_callback(data):
                logger.warning(f"Callback inválido recebido: '{data}' do usuário {user_id}")
                await self.bot.answer_callback_query(
                    callback_query.id, 
                    "❌ Opção inválida", 
                    show_alert=True
                )
                return
            
            # Log de auditoria
            await self.security_service.log_user_action(
                user_id=str(user_id),
                action='help_callback_processed',
                details={'callback_data': data}
            )
            
            # Responde ao callback
            await self.bot.answer_callback_query(callback_query.id)
            
            if data == NavigationCallbacks.CANCEL or data == "help_close":
                # Fecha o menu de ajuda
                await self.bot.delete_message(message.chat.id, message.message_id)
                return
            
            if data == NavigationCallbacks.BACK:
                # Volta ao menu principal de ajuda
                user_data = await firebase_service.get_user(user_id)
                codinome = safe_get_user_field(user_data, 'codinome', 'Usuário Anônimo')
                is_premium = get_field(user_data, 'is_premium', False)
                posts_count = get_field(user_data, 'posts_count', 0)
                admin_status = is_admin(user_id)
                
                help_text = self._build_help_message(codinome, is_premium, posts_count, admin_status)
                keyboard = self._create_help_keyboard(admin_status)
                
                await self.bot.edit_message_text(
                    help_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return
            
            # Processa outras opções
            response_text = self._get_help_section_text(data)
            
            if response_text:
                # Atualiza a mensagem com o conteúdo específico
                back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="⬅️ Voltar", callback_data=NavigationCallbacks.BACK),
            InlineKeyboardButton(text="❌ Fechar", callback_data=NavigationCallbacks.CANCEL)
                    ]
                ])
                
                await self.bot.edit_message_text(
                    response_text,
                    message.chat.id,
                    message.message_id,
                    reply_markup=back_keyboard,
                    parse_mode='HTML'
                )
            else:
                # Callback não reconhecido
                logger.warning(f"Seção de ajuda não encontrada: '{data}' para usuário {user_id}")
                await self.bot.answer_callback_query(
                    callback_query.id, 
                    "❌ Seção não encontrada", 
                    show_alert=True
                )
            
            logger.info(f"Callback de ajuda processado: {data} para usuário {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar callback de ajuda: {e}")
            try:
                await self.bot.answer_callback_query(
                    callback_query.id, 
                    "❌ Erro interno. Tente novamente.", 
                    show_alert=True
                )
            except:
                pass  # Evita erro duplo se callback já foi respondido
    
    def _is_valid_help_callback(self, callback_data: str) -> bool:
        """
        Valida se o callback é válido para o help handler.
        
        Args:
            callback_data: Dados do callback
            
        Returns:
            bool: True se válido, False caso contrário
        """
        if not callback_data or not isinstance(callback_data, str):
            return False
        
        # Lista de callbacks válidos para help
        valid_callbacks = {
            # Callbacks de navegação
            NavigationCallbacks.BACK,
            NavigationCallbacks.CANCEL,
            NavigationCallbacks.CONTACT_SUPPORT,
            
            # Callbacks de menu
            MenuCallbacks.CREATE_POST,
            MenuCallbacks.MY_POSTS,
            MenuCallbacks.SETTINGS,
            
            # Callbacks de configurações
            SettingsCallbacks.STATS,
            SettingsCallbacks.PRIVACY,
            
            # Callbacks LGPD
            LGPDCallbacks.EXPORT,
            LGPDCallbacks.TERMS,
            
            # Callbacks admin
            AdminCallbacks.ADMIN_PANEL,
            
            # Callbacks específicos de ajuda (legacy)
            "help_close",
            "help_new_post",
            "help_gallery",
            "help_settings",
            "help_privacy",
            "help_export",
            "help_support",
            "help_terms",
            "help_admin"
        }
        
        return callback_data in valid_callbacks
    
    def _get_help_section_text(self, section: str) -> Optional[str]:
        """
        Retorna o texto específico para cada seção de ajuda.
        
        Args:
            section: Seção solicitada
            
        Returns:
            str: Texto da seção ou None
        """
        sections = {
            "help_new_post": """📝 <b>Como criar uma nova postagem:</b>

1️⃣ Clique em ➕ <b>Postar</b> no menu principal
2️⃣ Escolha o tipo de conteúdo (texto, foto, etc.)
3️⃣ Adicione sua descrição
4️⃣ Configure a privacidade
5️⃣ Publique!

💡 <b>Dicas:</b>
• Use hashtags para maior alcance
• Adicione localização se relevante
• Revise antes de publicar""",
            
            "help_gallery": """🖼️ <b>Sua Galeria:</b>

• Visualize todas suas postagens
• Edite ou exclua posts
• Veja estatísticas de engajamento
• Gerencie comentários

🔍 Use os filtros para encontrar posts específicos!""",
            
            "help_settings": """⚙️ <b>Configurações disponíveis:</b>

🔔 <b>Notificações:</b>
• Novos matches
• Comentários
• Mensagens diretas

🎨 <b>Aparência:</b>
• Tema escuro/claro
• Idioma da interface

🔒 <b>Privacidade:</b>
• Visibilidade do perfil
• Quem pode comentar
• Filtros de conteúdo""",
            
            "help_privacy": """🔒 <b>Configurações de Privacidade:</b>

👁️ <b>Visibilidade:</b>
• Público - Todos podem ver
• Amigos - Apenas conexões
• Privado - Só você

🛡️ <b>Proteções:</b>
• Bloqueio de usuários
• Filtro de palavras
• Relatórios de abuso

📊 Seus dados são protegidos conforme LGPD!""",
            
            "help_export": """📤 <b>Exportação de Dados (LGPD):</b>

📋 <b>O que é incluído:</b>
• Perfil e configurações
• Todas as postagens
• Histórico de interações
• Dados de uso

⏱️ <b>Processo:</b>
1. Solicitação processada
2. Arquivo gerado (até 48h)
3. Link enviado por DM
4. Download disponível por 7 dias

🔒 Arquivo protegido por senha!""",
            
            "help_support": """💬 <b>Suporte ao Usuário:</b>

📞 <b>Canais de contato:</b>
• Chat interno do bot
• Email: suporte@liberall.com
• Telegram: @LiberAllSupport

⏰ <b>Horário de atendimento:</b>
• Segunda a Sexta: 9h às 18h
• Sábado: 9h às 14h
• Domingo: Emergências apenas

🚀 Usuários Premium têm prioridade!""",
            
            "help_terms": """📋 <b>Termos de Uso - Resumo:</b>

✅ <b>Permitido:</b>
• Conteúdo original e criativo
• Interações respeitosas
• Compartilhamento responsável

❌ <b>Proibido:</b>
• Spam ou conteúdo malicioso
• Violação de direitos autorais
• Assédio ou discriminação

⚖️ <b>Consequências:</b>
• Advertência → Suspensão → Banimento

📄 Leia os termos completos em: /terms""",
            
            "help_admin": """🛡️ <b>Painel Administrativo:</b>

📊 <b>Estatísticas:</b>
• Usuários ativos
• Posts por dia
• Relatórios de abuso

🔧 <b>Ferramentas:</b>
• Moderação de conteúdo
• Gestão de usuários
• Configurações globais

📢 <b>Comunicação:</b>
• Broadcast para usuários
• Notificações do sistema
• Alertas de manutenção"""
        }
        
        return sections.get(section)
    
    def register_handlers(self) -> None:
        """
        Registra os handlers no bot.
        """
        # Comando /help
        self.bot.message_handler(commands=['help'])(self.handle_help_command)
        
        # Callbacks de ajuda
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith('help_')
        )(self.handle_help_callback)
        
        logger.info("Handlers de ajuda registrados com sucesso")

def create_help_handler(bot: Bot) -> HelpHandler:
    """
    Factory function para criar e configurar o HelpHandler.
    
    Args:
        bot: Instância do Bot
        
    Returns:
        HelpHandler: Handler configurado
    """
    handler = HelpHandler(bot)
    handler.register_handlers()
    return handler