import logging


class GroupHandler:
    """Handler simples para mensagens em grupos.

    Responde a comandos básicos como 'menu' e 'postar' enviando
    uma mensagem orientando o usuário a continuar no chat privado.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    async def handle_group_message(self, message):
        """Processa mensagens recebidas em grupos.

        - 'menu': indica como acessar o menu principal.
        - 'postar': indica como iniciar o fluxo de criação de post.
        - Demais mensagens: ignoradas.
        """
        try:
            if not getattr(message, "text", None):
                return

            text = message.text.lower().strip()

            if text == "menu":
                await self._send_hint(message.chat.id, message.from_user.first_name, "📋 Menu Completo")
            elif text == "postar":
                await self._send_hint(message.chat.id, message.from_user.first_name, "✍️ Postar Agora")
            # outras mensagens são ignoradas
        except Exception as e:
            self.logger.error(f"Erro no GroupHandler: {e}")

    async def _send_hint(self, chat_id: int, user_name: str, action_text: str):
        """Envia uma mensagem simples de orientação com texto indicado."""
        message_text = (
            f"👋 Olá {user_name}!\n\n"
            f"{action_text}\n\n"
            f"👆 Continue no chat privado usando /start e o parâmetro apropriado."
        )

        await self.bot.send_message(chat_id, message_text)