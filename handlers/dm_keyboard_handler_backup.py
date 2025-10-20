# ARQUIVO REMOVIDO - Consolidado em dm_keyboard_handler.py
# Este arquivo foi removido para eliminar duplicações
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"✅ DMKeyboardHandler inicializado (ID da instância: {id(self)})")

    async def handle_menu_button(self, message: Message):
        """Processa clique no botão Menu"""
        user_id = message.from_user.id
        self.logger.info(f"Menu solicitado pelo usuário {user_id}")
        
        try:
            # Verificar se usuário existe
            user = await self.user_service.get_user(user_id)
            if not user:
                await self.bot.send_message(user_id, "Usuário não encontrado. Use /start para começar.")
                return
            
            # Criar teclado do menu
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Postar", callback_data="menu_post")],
                [InlineKeyboardButton(text="⚙️ Configurações", callback_data="menu_settings")],
                [InlineKeyboardButton(text="❤️ Favoritos", callback_data="menu_favorites")],
                [InlineKeyboardButton(text="🔍 Buscar", callback_data="menu_search")]
            ])
            
            await self.bot.send_message(
                user_id,
                "🏠 **Menu Principal**\n\nEscolha uma opção:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao processar menu para usuário {user_id}: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao carregar menu.")

    async def handle_post_button(self, message: Message):
        """Processa clique no botão Postar"""
        user_id = message.from_user.id
        self.logger.info(f"Postagem solicitada pelo usuário {user_id}")
        
        try:
            await self.bot.send_message(
                user_id,
                "📝 **Criar Post**\n\nFuncionalidade em desenvolvimento...",
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error(f"Erro ao processar postagem para usuário {user_id}: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao iniciar postagem.")

    async def handle_callback(self, call: CallbackQuery):
        """Processa callbacks do teclado DM"""
        user_id = call.from_user.id
        callback_data = call.data
        
        # Verificar se o usuário é um bot - bots não podem usar callbacks
        if call.from_user.is_bot:
            self.logger.warning(f"Bot {user_id} tentou usar callback - ignorando")
            return
        
        self.logger.info(f"Callback recebido: {callback_data} do usuário {user_id}")
        
        try:
            if callback_data == "menu_post":
                await self.handle_post_button(call.message)
            elif callback_data == "menu_settings":
                await self.bot.send_message(user_id, "⚙️ Configurações em desenvolvimento...")
            elif callback_data == "menu_favorites":
                await self.bot.send_message(user_id, "❤️ Favoritos em desenvolvimento...")
            elif callback_data == "menu_search":
                await self.bot.send_message(user_id, "🔍 Busca em desenvolvimento...")
            elif callback_data == PostingCallbacks.POST_PUBLISH:
                await self._handle_post_publish(call)
            elif callback_data == PostingCallbacks.POST_CANCEL:
                await self._handle_post_cancel(call)
            elif callback_data == PostingCallbacks.POST_MONETIZE:
                await self._handle_post_monetize(call)
            elif callback_data == PostingCallbacks.POST_PUBLISH_STAY:
                await self._handle_post_publish_stay(call)
            # Callbacks de interação final dos posts
            elif callback_data.startswith(PostingCallbacks.FAVORITE_POST):
                await self._handle_favorite_post(call)
            elif callback_data.startswith(PostingCallbacks.MATCH_POST):
                await self._handle_match_post(call)
            elif callback_data.startswith(PostingCallbacks.GALLERY_POST):
                await self._handle_gallery_post(call)
            elif callback_data.startswith(PostingCallbacks.COMMENT_POST):
                await self._handle_comment_post(call)
            else:
                await self.bot.send_message(user_id, "Opção não reconhecida.")
                
            await self.bot.answer_callback_query(call.id)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar callback {callback_data} para usuário {user_id}: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar ação.")

    async def _handle_post_publish(self, call: CallbackQuery):
        """Processa clique no botão Postar"""
        user_id = call.from_user.id
        
        try:
            # Obter dados do post do estado do usuário
            user_state = await self.user_service.get_user_state(user_id)
            if not user_state or user_state.get('state') != user_states.WAITING_POST_CONFIRMATION:
                await self.bot.edit_message_text(
                    "❌ Sessão expirada. Inicie um novo post.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                return
            
            post_content = user_state.get('post_content')
            if not post_content:
                await self.bot.edit_message_text(
                    "❌ Conteúdo do post não encontrado. Inicie um novo post.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                return
            
            # Publicar no grupo freemium
            await self._publish_post_to_groups(post_content, user_id)
            
            # Atualizar mensagem de confirmação
            await self.bot.edit_message_text(
                "✅ **Seu post foi publicado com sucesso!**\n\n"
                "📢 Sua mensagem foi enviada anonimamente para o grupo.\n"
                "🎉 Obrigado por contribuir com a comunidade!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='Markdown'
            )
            
            # Limpar estado do usuário
            await self.user_service.clear_user_state(user_id)
            
        except Exception as e:
            self.logger.error(f"Erro ao cancelar post do usuário {user_id}: {e}")
            await self.bot.edit_message_text(
                "❌ Erro ao cancelar post.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

    async def _handle_favorite_post(self, call: CallbackQuery):
        """Processa clique no botão Favoritar"""
        user_id = call.from_user.id
        post_id = call.data.replace(PostingCallbacks.FAVORITE_POST, "")
        
        try:
            # Aqui você pode implementar a lógica de favoritar
            # Por exemplo, salvar no banco de dados, etc.
            
            await self.bot.answer_callback_query(
                call.id,
                "⭐ Post adicionado aos favoritos!",
                show_alert=True
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao favoritar post {post_id} para usuário {user_id}: {e}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Erro ao favoritar post.",
                show_alert=True
            )

    async def _handle_match_post(self, call: CallbackQuery):
        """Processa clique no botão Match"""
        user_id = call.from_user.id
        post_id = call.data.replace(PostingCallbacks.MATCH_POST, "")
        
        try:
            # Aqui você pode implementar a lógica de match
            # Por exemplo, conectar usuários, etc.
            
            await self.bot.answer_callback_query(
                call.id,
                "💕 Match realizado! Verifique suas mensagens.",
                show_alert=True
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao fazer match com post {post_id} para usuário {user_id}: {e}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Erro ao realizar match.",
                show_alert=True
            )

    async def _handle_gallery_post(self, call: CallbackQuery):
        """Processa clique no botão Galeria"""
        user_id = call.from_user.id
        post_id = call.data.replace(PostingCallbacks.GALLERY_POST, "")
        
        try:
            # Aqui você pode implementar a lógica de galeria
            # Por exemplo, mostrar mais fotos do usuário, etc.
            
            await self.bot.answer_callback_query(
                call.id,
                "🖼️ Abrindo galeria...",
                show_alert=False
            )
            
            # Enviar mensagem com galeria (exemplo)
            await self.bot.send_message(
                user_id,
                "🖼️ **Galeria do Post**\n\nEm breve você poderá ver mais conteúdos relacionados!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao abrir galeria do post {post_id} para usuário {user_id}: {e}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Erro ao abrir galeria.",
                show_alert=True
            )

    async def _handle_comment_post(self, call: CallbackQuery):
        """Processa clique no botão Comentar"""
        user_id = call.from_user.id
        post_id = call.data.replace(PostingCallbacks.COMMENT_POST, "")
        
        try:
            # Aqui você pode implementar a lógica de comentários
            # Por exemplo, abrir interface de comentários, etc.
            
            await self.bot.answer_callback_query(
                call.id,
                "💬 Abrindo comentários...",
                show_alert=False
            )
            
            # Enviar mensagem para comentar (exemplo)
            await self.bot.send_message(
                user_id,
                "💬 **Comentários**\n\nEm breve você poderá comentar nos posts!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao abrir comentários do post {post_id} para usuário {user_id}: {e}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Erro ao abrir comentários.",
                show_alert=True
            )

    async def _handle_post_cancel(self, call: CallbackQuery):
        """Processa clique no botão Cancelar"""
        user_id = call.from_user.id
        
        try:
            # Atualizar mensagem
            await self.bot.edit_message_text(
                "❌ **Criação de post cancelada.**\n\n"
                "Você pode criar um novo post a qualquer momento usando o menu.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='Markdown'
            )
            
            # Limpar estado do usuário
            await self.user_service.clear_user_state(user_id)
            
        except Exception as e:
            self.logger.error(f"Erro ao cancelar post do usuário {user_id}: {e}")

    async def _handle_post_monetize(self, call: CallbackQuery):
        """Processa clique no botão Monetizar"""
        user_id = call.from_user.id
        
        try:
            # Define o estado do usuário para aguardar o valor de monetização
            await self.user_service.set_user_state(user_id, user_states.AWAITING_MONETIZATION_VALUE)
            
            # Edita a mensagem de preview para pedir o valor
            await self.bot.edit_message_caption(
                caption="💰 **Monetização**\n\n"
                        "Qual o valor (em R$) que você deseja atribuir a este post?\n"
                        "Exemplo: 10.50\n\n"
                        "Digite apenas o valor numérico:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None,  # Remove os botões antigos
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao processar monetização do usuário {user_id}: {e}")
            await self.error_handler.handle_error(self.bot, user_id, "Erro ao processar monetização.")

    async def _handle_post_publish_stay(self, call: CallbackQuery):
        """Processa clique no botão Postar e Ficar"""
        user_id = call.from_user.id
        
        try:
            await self.bot.edit_message_text(
                "📌 **Postar e Ficar**\n\n"
                "Funcionalidade em desenvolvimento...\n"
                "Em breve você poderá postar e permanecer no grupo!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao processar postar e ficar do usuário {user_id}: {e}")

    async def _publish_post_to_groups(self, post_content: dict, user_id: int):
        """Publica o conteúdo nos grupos apropriados"""
        self.logger.info(f"Publicando post do usuário {user_id} no grupo freemium.")
        
        caption = f"<b>Post Anônimo:</b>\n\n{post_content.get('caption', '') or post_content.get('text', '')}"
        
        try:
            # Por enquanto, vamos publicar tudo no grupo Freemium
            if post_content["type"] == "photo":
                await self.bot.send_photo(self.freemium_group_id, post_content["file_id"], caption=caption, parse_mode='HTML')
            elif post_content["type"] == "video":
                await self.bot.send_video(self.freemium_group_id, post_content["file_id"], caption=caption, parse_mode='HTML')
            elif post_content["type"] == "text":
                await self.bot.send_message(self.freemium_group_id, caption, parse_mode='HTML')
        except Exception as e:
            self.logger.error(f"Falha ao publicar post para o usuário {user_id}: {e}", exc_info=True)
            raise
