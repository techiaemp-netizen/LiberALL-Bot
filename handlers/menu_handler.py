"""
Handler para processar callbacks do menu principal.
Implementa a lógica de navegação e ações do menu principal do bot.
"""

import logging
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.user_service import UserService
from services.post_service import PostService
from services.match_service import MatchService
from utils.ui_builder import UIBuilder
from utils.error_handler import ErrorHandler
from constants.callbacks import MenuCallbacks

logger = logging.getLogger(__name__)

class MenuHandler:
    """Handler para processar callbacks do menu principal."""
    
    def __init__(self, user_service: UserService = None, post_service: PostService = None, match_service: MatchService = None, ui_builder: UIBuilder = None, error_handler: ErrorHandler = None):
        # Permitir injeção de dependências para consistência com outros handlers
        self.user_service = user_service or UserService()
        self.post_service = post_service or PostService()
        # Exigir MatchService injetado para garantir consistência com FirebaseService e simulação
        if match_service is None:
            raise ValueError("MenuHandler requer 'match_service' injetado")
        self.match_service = match_service
        self.ui_builder = ui_builder or UIBuilder()
        self.error_handler = error_handler or ErrorHandler()
    
    async def handle_menu_callback(self, update, context=None):
        """Processa callbacks do menu principal."""
        if hasattr(update, 'callback_query'):
            query = update.callback_query
        else:
            query = update
            
        callback_data = query.data
        user_id = query.from_user.id
        
        try:
            await query.answer()
            
            # Log estruturado para depuração
            logger.info(f"🏠 MENU CALLBACK: user_id={user_id}, callback={callback_data}")
            
            # Roteamento baseado no callback
            if callback_data == "main_menu":
                logger.info(f"🏠 MAIN MENU REQUEST: user_id={user_id}")
                await self._show_main_menu(query, user_id)
                
            # CALLBACKS PADRONIZADOS COM PREFIXO menu_ e menu:
            elif callback_data == MenuCallbacks.PROFILE or callback_data == "menu_profile" or callback_data == "menu:profile":
                logger.info(f"👤 PROFILE MENU REQUEST: user_id={user_id}")
                await self._show_profile(query, user_id)
                
            elif callback_data == MenuCallbacks.SETTINGS or callback_data == "settings":
                logger.info(f"⚙️ SETTINGS REQUEST: user_id={user_id}")
                await self._show_settings(query, user_id)
                
            elif callback_data == MenuCallbacks.FAVORITES or callback_data == "menu_favorites" or callback_data == "menu:favorites":
                logger.info(f"⭐ FAVORITES REQUEST: user_id={user_id}")
                await self._show_favorites(query, user_id)
                
            elif callback_data == MenuCallbacks.HELP or callback_data == "help":
                logger.info(f"❓ HELP REQUEST: user_id={user_id}")
                await self._show_help(query, user_id)
                
            elif callback_data == MenuCallbacks.CREATE_POST or callback_data == "menu_create_post" or callback_data == "start_post":
                logger.info(f"📝 CREATE POST REQUEST: user_id={user_id}")
                await self._start_create_post(query, user_id)
                
            elif callback_data == MenuCallbacks.VIEW_POSTS or callback_data == "menu_view_posts":
                logger.info(f"👀 VIEW POSTS REQUEST: user_id={user_id}")
                await self._view_posts(query, user_id)
                
            elif callback_data == MenuCallbacks.MY_MATCHES or callback_data == "menu_my_matches" or callback_data == "menu:matches":
                logger.info(f"💕 MATCHES REQUEST: user_id={user_id}")
                await self._show_matches(query, user_id)
                
            elif callback_data == MenuCallbacks.STATISTICS or callback_data == "menu_statistics":
                logger.info(f"📊 STATISTICS REQUEST: user_id={user_id}")
                await self._show_statistics(query, user_id)
                
            elif callback_data == "gallery" or callback_data == "menu:gallery":
                logger.info(f"🖼️ GALLERY REQUEST: user_id={user_id}")
                await self._show_gallery(query, user_id)
                
            # NOVOS CALLBACKS PARA AJUDA EXPANDIDA
            elif callback_data == "contact_support":
                await self._contact_support(query, user_id)
                
            elif callback_data == "show_faq":
                await self._show_faq(query, user_id)
                
            else:
                logger.warning(f"❓ UNKNOWN MENU CALLBACK: user_id={user_id}, callback={callback_data}")
                await query.answer("❌ Opção não reconhecida.", show_alert=True)
                
        except Exception as e:
            logger.error(f"💥 MENU CALLBACK ERROR: user_id={user_id}, callback={callback_data}, error={e}", exc_info=True)
            await self.error_handler.handle_callback_error(query, "Erro ao processar menu")
    
    async def _show_main_menu(self, query, user_id: int):
        """Exibe o menu principal."""
        try:
            user = await self.user_service.get_user(user_id)
            if not user:
                await query.edit_message_text("❌ Usuário não encontrado.")
                return
            
            # Construir mensagem de boas-vindas personalizada
            welcome_text = f"🏠 **Menu Principal**\n\n"
            welcome_text += f"Olá, {user.get('name', 'Usuário')}! 👋\n\n"
            welcome_text += "O que você gostaria de fazer hoje?\n\n"
            
            # Adicionar estatísticas rápidas
            stats = await self._get_user_stats(user_id)
            if stats:
                welcome_text += f"📊 **Suas estatísticas:**\n"
                welcome_text += f"• Posts criados: {stats.get('posts_count', 0)}\n"
                welcome_text += f"• Matches: {stats.get('matches_count', 0)}\n"
                welcome_text += f"• Favoritos: {stats.get('favorites_count', 0)}\n\n"
            
            keyboard = await self._get_main_menu_keyboard(user_id)
            
            await query.edit_message_text(
                welcome_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir menu principal: {e}")
            await query.edit_message_text("❌ Erro ao carregar menu principal.")
    
    async def _show_profile(self, query, user_id: int):
        """Busca e exibe os dados do perfil do utilizador conforme instruções da auditoria."""
        try:
            user_data = await self.user_service.get_user_data(user_id)
            if user_data:
                profile_text = (
                    f"👤 **O Seu Perfil**\n\n"
                    f"**Codinome:** {user_data.get('codename', 'Não definido')}\n"
                    f"**Estado:** {user_data.get('state', 'Não definido')}\n"
                    f"**Categoria:** {user_data.get('category', 'Não definida')}\n"
                    f"**Plano Atual:** {'Premium' if user_data.get('is_premium') else 'Lite'}"
                )
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✏️ Editar Perfil", callback_data="edit_profile")],
                    [InlineKeyboardButton(text="🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
                ])
                
                await query.edit_message_text(profile_text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text("Não foi possível encontrar os dados do seu perfil.")
        except Exception as e:
            logger.error(f"Erro ao exibir o perfil para {user_id}: {e}", exc_info=True)
            await query.edit_message_text("Ocorreu um erro ao buscar o seu perfil.")

    async def _show_profile_menu(self, query, user_id: int):
        """Exibe o perfil do usuário no contexto do menu (versão original)."""
        try:
            # Obter dados reais do usuário
            user_data = await self.user_service.get_user_data(user_id)
            
            if not user_data:
                text = "❌ **Erro ao carregar perfil**\n\n"
                text += "Não foi possível encontrar seus dados.\n"
                text += "Tente fazer o onboarding novamente."
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Refazer Onboarding", callback_data="restart_onboarding")],
                    [InlineKeyboardButton(text="🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
                ])
            else:
                # Construir perfil com dados reais
                name = user_data.get('name', 'Não informado')
                age = user_data.get('age', 'Não informado')
                location = user_data.get('location', 'Não informado')
                category = user_data.get('category', 'Não informado')
                interests = user_data.get('interests', [])
                bio = user_data.get('bio', 'Sem descrição')
                
                text = f"👤 **Seu Perfil**\n\n"
                text += f"**Nome:** {name}\n"
                text += f"**Idade:** {age}\n"
                text += f"**Localização:** {location}\n"
                text += f"**Categoria:** {category.title()}\n"
                
                if interests:
                    interests_text = ", ".join(interests)
                    text += f"**Interesses:** {interests_text}\n"
                
                text += f"\n**Bio:**\n{bio}\n\n"
                
                # Estatísticas básicas
                stats = await self._get_user_stats(user_id)
                text += f"**Estatísticas:**\n"
                text += f"• Posts criados: {stats.get('posts_count', 0)}\n"
                text += f"• Matches: {stats.get('matches_count', 0)}\n"
                text += f"• Favoritos: {stats.get('favorites_count', 0)}\n"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✏️ Editar Perfil", callback_data="edit_profile")],
                    [InlineKeyboardButton(text="📸 Alterar Foto", callback_data="change_photo")],
                    [InlineKeyboardButton(text="📊 Ver Estatísticas", callback_data=MenuCallbacks.STATISTICS)],
                    [InlineKeyboardButton(text="🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
                ])
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir perfil: {e}")
            await query.edit_message_text("❌ Erro ao carregar perfil.")
    
    async def _show_settings(self, query, user_id: int):
        """Exibe as configurações do usuário."""
        try:
            text = "⚙️ **Configurações**\n\n"
            text += "Personalize sua experiência no Liberall:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔔 Notificações", callback_data="settings_notifications")],
                [InlineKeyboardButton(text="🔒 Privacidade", callback_data="settings_privacy")],
                [InlineKeyboardButton(text="🎨 Tema", callback_data="settings_theme")],
                [InlineKeyboardButton(text="📍 Localização", callback_data="settings_location")],
                [InlineKeyboardButton(text="🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
            ])
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir configurações: {e}")
            await query.edit_message_text("❌ Erro ao carregar configurações.")
    
    async def _show_gallery(self, query, user_id: int):
        """Exibe a galeria de posts do usuário."""
        try:
            # Obter posts do usuário
            user_posts = await self.post_service.get_user_posts(user_id)
            
            text = "🖼️ **Sua Galeria**\n\n"
            
            if not user_posts:
                text += "Você ainda não criou nenhum post.\n"
                text += "Comece criando seu primeiro conteúdo! 🚀\n\n"
                text += "💡 **Dica:** Use o botão 'Criar Post' no menu principal."
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Criar Primeiro Post", callback_data=MenuCallbacks.CREATE_POST)],
                    [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
                ])
            else:
                text += f"Você tem **{len(user_posts)}** posts criados:\n\n"
                
                buttons = []
                for i, post in enumerate(user_posts[:5]):  # Mostrar apenas os 5 primeiros
                    post_title = post.get('title', f'Post {i+1}')[:25]
                    post_type = post.get('type', 'texto')
                    matches_count = post.get('matches_count', 0)
                    views_count = post.get('views_count', 0)
                    
                    text += f"📄 **{post_title}**\n"
                    text += f"   📱 Tipo: {post_type.title()}\n"
                    text += f"   💕 {matches_count} matches\n"
                    text += f"   👀 {views_count} visualizações\n\n"
                    
                    buttons.append([InlineKeyboardButton(
                        text=f"👀 Ver '{post_title}'",
                        callback_data=f"view_post_{post['id']}"
                    )])
                
                if len(user_posts) > 5:
                    buttons.append([InlineKeyboardButton(text="📋 Ver Todos os Posts", callback_data="view_all_user_posts")])
                
                buttons.extend([
                    [InlineKeyboardButton(text="📝 Criar Novo Post", callback_data=MenuCallbacks.CREATE_POST)],
                    [InlineKeyboardButton(text="🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
                ])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir galeria: {e}")
            await query.edit_message_text("❌ Erro ao carregar galeria.")
    
    async def _show_favorites(self, query, user_id: int):
        """Exibe os posts favoritos do usuário."""
        try:
            # Obter favoritos reais do banco de dados
            favorites = await self.post_service.get_user_favorites(user_id)
            
            if not favorites:
                text = "⭐ **Seus Favoritos**\n\n"
                text += "Você ainda não tem posts favoritos.\n"
                text += "Explore posts e adicione aos favoritos! 💫"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Explorar Posts", callback_data=MenuCallbacks.VIEW_POSTS)],
                    [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
                ])
            else:
                text = f"⭐ **Seus Favoritos** ({len(favorites)} posts)\n\n"
                
                buttons = []
                for i, post in enumerate(favorites[:5]):  # Mostrar apenas os 5 primeiros
                    post_title = post.get('title', f'Post {i+1}')[:30]
                    creator_name = post.get('creator_name', 'Anônimo')
                    text += f"📄 **{post_title}**\n"
                    text += f"   👤 Por: {creator_name}\n"
                    text += f"   📅 {post.get('created_at', 'Data não disponível')}\n\n"
                    
                    buttons.append([InlineKeyboardButton(
                        f"👀 Ver Post", 
                        callback_data=f"view_post_{post['id']}"
                    )])
                
                if len(favorites) > 5:
                    buttons.append([InlineKeyboardButton("📋 Ver Todos os Favoritos", callback_data="view_all_favorites")])
                
                buttons.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)])
                keyboard = InlineKeyboardMarkup(buttons)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir favoritos: {e}")
            await query.edit_message_text("❌ Erro ao carregar favoritos.")
    
    async def _show_help(self, query, user_id: int):
        """Exibe a ajuda completa do bot."""
        try:
            help_text = f"❓ **Central de Ajuda - LiberALL**\n\n"
            help_text += "**🚀 Como usar o LiberALL:**\n\n"
            
            help_text += "🏠 **Menu Principal**\n"
            help_text += "   • Acesse todas as funcionalidades principais\n"
            help_text += "   • Veja suas estatísticas em tempo real\n\n"
            
            help_text += "📝 **Criar Post**\n"
            help_text += "   • Compartilhe fotos, vídeos ou textos\n"
            help_text += "   • Defina preços para monetização\n"
            help_text += "   • Escolha sua audiência\n\n"
            
            help_text += "👀 **Explorar Posts**\n"
            help_text += "   • Descubra conteúdos de outros usuários\n"
            help_text += "   • Filtre por região ou categoria\n"
            help_text += "   • Interaja e faça matches\n\n"
            
            help_text += "💕 **Sistema de Matches**\n"
            help_text += "   • Conecte-se com pessoas interessantes\n"
            help_text += "   • Inicie conversas privadas\n"
            help_text += "   • Gerencie suas conexões\n\n"
            
            help_text += "⭐ **Favoritos**\n"
            help_text += "   • Salve posts que você gosta\n"
            help_text += "   • Acesse rapidamente seus conteúdos preferidos\n\n"
            
            help_text += "**💡 Dicas importantes:**\n"
            help_text += "• Mantenha seu perfil atualizado\n"
            help_text += "• Seja respeitoso nas interações\n"
            help_text += "• Use hashtags para maior alcance\n"
            help_text += "• Explore diferentes tipos de conteúdo\n\n"
            
            help_text += "**Precisa de mais ajuda?**\n"
            help_text += "Nossa equipe está sempre disponível! 💬"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contatar Suporte", callback_data="contact_support")],
                [InlineKeyboardButton("❓ Perguntas Frequentes", callback_data="show_faq")],
                [InlineKeyboardButton("📋 Guia Completo", callback_data="show_complete_guide")],
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
            ])
            
            await query.edit_message_text(
                help_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir ajuda: {e}")
            await query.edit_message_text("❌ Erro ao carregar ajuda.")
    
    async def _contact_support(self, query, user_id: int):
        """Exibe opções de contato com suporte."""
        try:
            text = "📞 **Contatar Suporte**\n\n"
            text += "Escolha a melhor forma de entrar em contato:\n\n"
            text += "**📧 Email:** suporte@liberall.com\n"
            text += "**💬 Telegram:** @LiberallSupport\n"
            text += "**📱 WhatsApp:** +55 11 99999-9999\n\n"
            text += "**⏰ Horário de atendimento:**\n"
            text += "Segunda a Sexta: 9h às 18h\n"
            text += "Sábados: 9h às 14h\n\n"
            text += "**⚡ Para emergências:**\n"
            text += "Use o botão 'Suporte Urgente' abaixo"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚨 Suporte Urgente", callback_data="urgent_support")],
                [InlineKeyboardButton("📧 Enviar Email", callback_data="send_email_support")],
                [InlineKeyboardButton("💬 Chat ao Vivo", callback_data="live_chat_support")],
                [InlineKeyboardButton("🔙 Voltar à Ajuda", callback_data=MenuCallbacks.HELP)]
            ])
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir contato de suporte: {e}")
            await query.edit_message_text("❌ Erro ao carregar opções de suporte.")
    
    async def _show_faq(self, query, user_id: int):
        """Exibe perguntas frequentes."""
        try:
            text = "❓ **Perguntas Frequentes**\n\n"
            
            text += "**🔐 Como funciona a privacidade?**\n"
            text += "Seus dados são protegidos com criptografia de ponta. Você controla quem vê seu conteúdo.\n\n"
            
            text += "**💰 Como funciona a monetização?**\n"
            text += "Defina preços para seus posts. Receba pagamentos via PIX instantaneamente.\n\n"
            
            text += "**💕 Como funcionam os matches?**\n"
            text += "Quando alguém interage com seu post, vocês podem se conectar e conversar.\n\n"
            
            text += "**📱 Posso usar em outros dispositivos?**\n"
            text += "Sim! Acesse pelo Telegram em qualquer dispositivo.\n\n"
            
            text += "**🚫 Como reportar conteúdo inadequado?**\n"
            text += "Use o botão 'Reportar' em qualquer post ou entre em contato conosco.\n\n"
            
            text += "**💳 Como recebo meus pagamentos?**\n"
            text += "Configure sua chave PIX no perfil. Pagamentos são instantâneos.\n\n"
            
            text += "**🔄 Posso editar posts publicados?**\n"
            text += "Sim, acesse 'Minha Galeria' e selecione o post para editar.\n\n"
            
            text += "**Não encontrou sua dúvida?**\n"
            text += "Entre em contato com nosso suporte!"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contatar Suporte", callback_data="contact_support")],
                [InlineKeyboardButton("📋 Mais Perguntas", callback_data="more_faq")],
                [InlineKeyboardButton("🔙 Voltar à Ajuda", callback_data=MenuCallbacks.HELP)]
            ])
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir FAQ: {e}")
            await query.edit_message_text("❌ Erro ao carregar FAQ.")
    
    async def _start_create_post(self, query, user_id: int):
        """Inicia o processo de criação de post."""
        try:
            # Verificar se o usuário pode criar posts
            user = await self.user_service.get_user(user_id)
            if not user:
                await query.edit_message_text("❌ Usuário não encontrado.")
                return
            
            # Redirecionar para o handler de postagem
            text = "📝 **Criar Novo Post**\n\n"
            text += "Vamos criar seu post! Escolha o tipo de conteúdo:\n\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📷 Post com Imagem", callback_data="post_type_image")],
                [InlineKeyboardButton("📹 Post com Vídeo", callback_data="post_type_video")],
                [InlineKeyboardButton("📝 Post Apenas Texto", callback_data="post_type_text")],
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
            ])
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao iniciar criação de post: {e}")
            await query.edit_message_text("❌ Erro ao iniciar criação de post.")
    
    async def _view_posts(self, query, user_id: int):
        """Exibe posts disponíveis para visualização."""
        try:
            # Obter posts reais do banco de dados
            recent_posts = await self.post_service.get_recent_posts(limit=5)
            
            text = "👀 **Explorar Posts**\n\n"
            
            if recent_posts:
                text += "**Posts Recentes:**\n\n"
                for post in recent_posts:
                    post_title = post.get('title', 'Sem título')[:25]
                    creator_name = post.get('creator_name', 'Anônimo')
                    text += f"📄 **{post_title}**\n"
                    text += f"   👤 {creator_name}\n"
                    text += f"   💕 {post.get('matches_count', 0)} matches\n\n"
            else:
                text += "Ainda não há posts disponíveis.\n"
                text += "Seja o primeiro a criar conteúdo! 🚀\n\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Posts em Destaque", callback_data="view_featured_posts")],
                [InlineKeyboardButton("🆕 Posts Recentes", callback_data="view_recent_posts")],
                [InlineKeyboardButton("📍 Posts da Minha Região", callback_data="view_local_posts")],
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
            ])
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir posts: {e}")
            await query.edit_message_text("❌ Erro ao carregar posts.")
    
    async def _show_matches(self, query, user_id: int):
        """Exibe os matches do usuário."""
        try:
            # Obter matches reais do banco de dados
            matches = await self.match_service.get_user_matches(user_id)
            
            if not matches:
                text = "💕 **Seus Matches**\n\n"
                text += "Você ainda não tem matches.\n"
                text += "Explore posts e faça conexões! ✨\n\n"
                text += "💡 **Dica:** Interaja com posts que te interessam para criar matches!"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Explorar Posts", callback_data=MenuCallbacks.VIEW_POSTS)],
                    [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
                ])
            else:
                text = f"💕 **Seus Matches** ({len(matches)} conexões)\n\n"
                
                buttons = []
                for i, match in enumerate(matches[:5]):  # Mostrar apenas os 5 primeiros
                    match_name = match.get('name', f'Match {i+1}')
                    post_title = match.get('post_title', 'Post sem título')[:20]
                    match_date = match.get('created_at', 'Data não disponível')
                    
                    text += f"💕 **{match_name}**\n"
                    text += f"   📄 Post: {post_title}\n"
                    text += f"   📅 Match em: {match_date}\n"
                    text += f"   💬 Status: {match.get('status', 'Ativo')}\n\n"
                    
                    buttons.append([InlineKeyboardButton(
                        f"💬 Conversar com {match_name}", 
                        callback_data=f"chat_match_{match['id']}"
                    )])
                
                if len(matches) > 5:
                    buttons.append([InlineKeyboardButton("📋 Ver Todos os Matches", callback_data="view_all_matches")])
                
                buttons.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)])
                keyboard = InlineKeyboardMarkup(buttons)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir matches: {e}")
            await query.edit_message_text("❌ Erro ao carregar matches.")
    
    async def _show_statistics(self, query, user_id: int):
        """Exibe estatísticas do usuário."""
        try:
            stats = await self._get_user_stats(user_id)
            
            text = f"📊 **Suas Estatísticas**\n\n"
            
            if stats:
                text += f"**Atividade Geral:**\n"
                text += f"• Posts criados: {stats.get('posts_count', 0)}\n"
                text += f"• Matches recebidos: {stats.get('matches_count', 0)}\n"
                text += f"• Posts favoritados: {stats.get('favorites_count', 0)}\n"
                text += f"• Visualizações totais: {stats.get('views_count', 0)}\n\n"
                
                text += f"**Esta semana:**\n"
                text += f"• Novos matches: {stats.get('weekly_matches', 0)}\n"
                text += f"• Posts criados: {stats.get('weekly_posts', 0)}\n"
                text += f"• Visualizações: {stats.get('weekly_views', 0)}\n"
            else:
                text += "Ainda não há estatísticas disponíveis.\n"
                text += "Comece a usar o bot para ver seus dados! 📈"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📈 Estatísticas Detalhadas", callback_data="detailed_stats")],
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data=MenuCallbacks.MAIN_MENU)]
            ])
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao exibir estatísticas: {e}")
            await query.edit_message_text("❌ Erro ao carregar estatísticas.")
    
    async def _get_main_menu_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Constrói o teclado do menu principal com callbacks padronizados."""
        try:
            user = await self.user_service.get_user(user_id)
            
            buttons = [
                [InlineKeyboardButton(text="📝 Criar Post", callback_data="menu_create_post")],
                [InlineKeyboardButton(text="👀 Ver Posts", callback_data="menu_view_posts")],
                [InlineKeyboardButton(text="💕 Meus Matches", callback_data="menu_my_matches")],
                [InlineKeyboardButton(text="⭐ Favoritos", callback_data="menu_favorites")],
                [
                    InlineKeyboardButton(text="👤 Perfil", callback_data="menu_profile"),
                    InlineKeyboardButton(text="🖼️ Galeria", callback_data="gallery")
                ],
                [
                    InlineKeyboardButton(text="📊 Estatísticas", callback_data="menu_statistics"),
                    InlineKeyboardButton(text="⚙️ Configurações", callback_data="settings")
                ],
                [InlineKeyboardButton(text="❓ Ajuda", callback_data="help")]
            ]
            
            return InlineKeyboardMarkup(inline_keyboard=buttons)
            
        except Exception as e:
            logger.error(f"Erro ao construir teclado do menu: {e}")
            # Retornar teclado básico em caso de erro
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Menu Principal", callback_data="main_menu")]
            ])
    
    async def _get_user_stats(self, user_id: int) -> dict:
        """Obtém estatísticas reais do usuário."""
        try:
            # Obter estatísticas reais dos serviços
            posts_count = await self.post_service.get_user_posts_count(user_id)
            matches_count = await self.match_service.get_user_matches_count(user_id)
            favorites_count = await self.post_service.get_user_favorites_count(user_id)
            
            # Estatísticas semanais
            weekly_stats = await self.post_service.get_weekly_stats(user_id)
            
            return {
                'posts_count': posts_count,
                'matches_count': matches_count,
                'favorites_count': favorites_count,
                'views_count': weekly_stats.get('total_views', 0),
                'weekly_matches': weekly_stats.get('weekly_matches', 0),
                'weekly_posts': weekly_stats.get('weekly_posts', 0),
                'weekly_views': weekly_stats.get('weekly_views', 0)
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do usuário {user_id}: {e}")
            # Retornar dados padrão em caso de erro
            return {
                'posts_count': 0,
                'matches_count': 0,
                'favorites_count': 0,
                'views_count': 0,
                'weekly_matches': 0,
                'weekly_posts': 0,
                'weekly_views': 0
            }