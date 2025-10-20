"""Construtor de interfaces de usuário para o Telegram.

Este módulo fornece:
- Teclados inline padronizados
- Formatação de mensagens
- Componentes de UI reutilizáveis
"""

from typing import List, Dict, Any, Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.constants import EMOJIS, CATEGORIAS_USUARIO, ESTADOS_BRASIL

class UIBuilder:
    """Construtor de interfaces de usuário padronizadas."""
    
    def __init__(self):
        """Inicializa o construtor de UI."""
        self.emojis = EMOJIS
    
    def create_inline_keyboard(self, buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
        """Cria teclado inline a partir de configuração.
        
        Args:
            buttons: Lista de linhas, cada linha contém dicts com 'text' e 'callback_data'
            
        Returns:
            Teclado inline configurado
            
        Example:
            buttons = [
                [{'text': 'Opção 1', 'callback_data': 'opt1'}],
                [{'text': 'Opção 2', 'callback_data': 'opt2'}]
            ]
        """
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                keyboard_row.append(
                    InlineKeyboardButton(
                        text=button['text'],
                        callback_data=button['callback_data']
                    )
                )
            keyboard.append(keyboard_row)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    
    def create_dm_keyboard(self) -> None:
        """DMs nunca devem usar ReplyKeyboard conforme política de teclados.
        
        Returns:
            None - DMs devem usar apenas InlineKeyboardMarkup
        """
        # POLÍTICA: DMs nunca usam ReplyKeyboard, apenas InlineKeyboardMarkup
        # Use create_menu_keyboard() ou outros métodos inline para DMs
        return None
    
    def create_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Cria teclado do menu principal.
        
        Returns:
            Teclado inline do menu
        """
        buttons = [
            [{'text': f"{self.emojis['rocket']} Meus Posts", 'callback_data': 'menu_my_posts'}],
            [{'text': f"{self.emojis['heart']} Favoritos", 'callback_data': 'menu_favorites'}],
            [{'text': f"{self.emojis['money']} Monetização", 'callback_data': 'menu_monetization'}],
            [{'text': f"{self.emojis['shield']} Privacidade", 'callback_data': 'menu_privacy'}],
            [{'text': f"{self.emojis['info']} Suporte", 'callback_data': 'menu_support'}]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_post_type_keyboard(self) -> InlineKeyboardMarkup:
        """Cria teclado de seleção de tipo de post.
        
        Returns:
            Teclado inline para tipos de post
        """
        buttons = [
            [{'text': f"{self.emojis['sparkles']} Post Gratuito", 'callback_data': 'post_type_free'}],
            [{'text': f"{self.emojis['money']} Post Pago", 'callback_data': 'post_type_paid'}],
            [{'text': f"{self.emojis['fire']} Post Exclusivo", 'callback_data': 'post_type_exclusive'}]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_price_keyboard(self) -> InlineKeyboardMarkup:
        """Cria teclado de seleção de preços.
        
        Returns:
            Teclado inline com opções de preço
        """
        buttons = [
            [{'text': 'R$ 2,00', 'callback_data': 'price_200'}],
            [{'text': 'R$ 5,00', 'callback_data': 'price_500'}],
            [{'text': 'R$ 10,00', 'callback_data': 'price_1000'}],
            [{'text': 'R$ 20,00', 'callback_data': 'price_2000'}],
            [{'text': f"{self.emojis['key']} Valor Personalizado", 'callback_data': 'price_custom'}]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_confirmation_keyboard(self, confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
        """Cria teclado de confirmação.
        
        Args:
            confirm_data: Callback data para confirmação
            cancel_data: Callback data para cancelamento
            
        Returns:
            Teclado inline de confirmação
        """
        buttons = [
            [{'text': f"{self.emojis['success']} Confirmar", 'callback_data': confirm_data}],
            [{'text': f"{self.emojis['error']} Cancelar", 'callback_data': cancel_data}]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_pagination_keyboard(self, current_page: int, total_pages: int, 
                                 prefix: str = 'page') -> InlineKeyboardMarkup:
        """Cria teclado de paginação.
        
        Args:
            current_page: Página atual (1-indexed)
            total_pages: Total de páginas
            prefix: Prefixo para callback data
            
        Returns:
            Teclado inline de paginação
        """
        buttons = []
        
        # Linha de navegação
        nav_row = []
        
        # Botão anterior
        if current_page > 1:
            nav_row.append({
                'text': '◀️ Anterior',
                'callback_data': f'{prefix}_{current_page - 1}'
            })
        
        # Indicador de página
        nav_row.append({
            'text': f'{current_page}/{total_pages}',
            'callback_data': f'{prefix}_info'
        })
        
        # Botão próximo
        if current_page < total_pages:
            nav_row.append({
                'text': 'Próximo ▶️',
                'callback_data': f'{prefix}_{current_page + 1}'
            })
        
        buttons.append(nav_row)
        
        return self.create_inline_keyboard(buttons)
    
    def create_states_keyboard(self, columns: int = 2) -> InlineKeyboardMarkup:
        """Cria teclado de seleção de estados.
        
        Args:
            columns: Número de colunas no teclado
            
        Returns:
            Teclado inline com estados brasileiros
        """
        buttons = []
        states_list = list(ESTADOS_BRASIL.items())
        
        for i in range(0, len(states_list), columns):
            row = []
            for j in range(columns):
                if i + j < len(states_list):
                    code, name = states_list[i + j]
                    row.append({
                        'text': f'{code} - {name}',
                        'callback_data': f'state_{code}'
                    })
            buttons.append(row)
        
        return self.create_inline_keyboard(buttons)
    
    def create_categories_keyboard(self, columns: int = 1) -> InlineKeyboardMarkup:
        """Cria teclado de seleção de categorias.
        
        Args:
            columns: Número de colunas no teclado
            
        Returns:
            Teclado inline com categorias de usuário
        """
        buttons = []
        categories_list = list(CATEGORIAS_USUARIO.items())
        
        for i in range(0, len(categories_list), columns):
            row = []
            for j in range(columns):
                if i + j < len(categories_list):
                    code, name = categories_list[i + j]
                    row.append({
                        'text': name,
                        'callback_data': f'category_{code}'
                    })
            buttons.append(row)
        
        return self.create_inline_keyboard(buttons)
    
    def format_main_menu(self, username: str = "Usuário", karma: int = 0, 
                         total_posts: int = 0, subscription_type: str = "free") -> str:
        """Formata o menu principal do usuário.
        
        Args:
            username: Nome do usuário
            karma: Pontos de karma
            total_posts: Total de posts
            subscription_type: Tipo de assinatura
            
        Returns:
            Texto formatado do menu principal
        """
        subscription_emoji = "⭐" if subscription_type == "premium" else "🆓"
        
        return (
            f"{self.emojis['sparkles']} <b>Menu Principal</b>\n\n"
            f"👋 Olá, <b>{username}</b>!\n\n"
            f"🎯 <b>Karma:</b> {karma}\n"
            f"📝 <b>Posts:</b> {total_posts}\n"
            f"{subscription_emoji} <b>Plano:</b> {subscription_type.title()}\n\n"
            f"Escolha uma opção abaixo:"
        )
    
    def format_user_profile(self, user_data: Dict[str, Any]) -> str:
        """Formata dados do perfil do usuário.
        
        Args:
            user_data: Dados do usuário
            
        Returns:
            Texto formatado do perfil
        """
        # Verificar se é um dicionário ou objeto User
        if isinstance(user_data, dict):
            codinome = user_data.get('codinome', 'N/A')
            estado = ESTADOS_BRASIL.get(user_data.get('estado', ''), 'N/A')
            categoria = CATEGORIAS_USUARIO.get(user_data.get('categoria', ''), 'N/A')
            monetization = 'Habilitada' if user_data.get('monetization_enabled') else 'Desabilitada'
        else:
            # É um objeto User
            codinome = getattr(user_data, 'codinome', 'N/A')
            estado = ESTADOS_BRASIL.get(getattr(user_data, 'estado', ''), 'N/A')
            categoria = CATEGORIAS_USUARIO.get(getattr(user_data, 'categoria', ''), 'N/A')
            monetization = 'Habilitada' if getattr(user_data, 'monetization_enabled', False) else 'Desabilitada'
        
        return (
            f"{self.emojis['sparkles']} <b>Seu Perfil</b>\n\n"
            f"👤 <b>Codinome:</b> @{codinome}\n"
            f"📍 <b>Estado:</b> {estado}\n"
            f"🏷️ <b>Categoria:</b> {categoria}\n"
            f"💰 <b>Monetização:</b> {monetization}\n"
        )
    
    def format_post_preview(self, post_data: Dict[str, Any]) -> str:
        """Formata preview de um post.
        
        Args:
            post_data: Dados do post
            
        Returns:
            Texto formatado do preview
        """
        title = post_data.get('title', 'Sem título')
        price = post_data.get('price_cents', 0)
        is_paid = price > 0
        
        preview = f"{self.emojis['fire']} <b>{title}</b>\n\n"
        
        if is_paid:
            price_real = price / 100
            preview += f"💰 <b>Preço:</b> R$ {price_real:.2f}\n"
        else:
            preview += f"{self.emojis['sparkles']} <b>Gratuito</b>\n"
        
        # Adiciona preview do conteúdo
        content = post_data.get('content', '')
        if content:
            preview_text = content[:100] + '...' if len(content) > 100 else content
            preview += f"\n{preview_text}"
        
        return preview
    
    def format_error_message(self, error: str, details: Optional[str] = None) -> str:
        """Formata mensagem de erro.
        
        Args:
            error: Mensagem de erro principal
            details: Detalhes adicionais do erro
            
        Returns:
            Mensagem de erro formatada
        """
        message = f"{self.emojis['error']} <b>Erro</b>\n\n{error}"
        
        if details:
            message += f"\n\n<i>{details}</i>"
        
        return message
    
    def format_success_message(self, message: str, details: Optional[str] = None) -> str:
        """Formata mensagem de sucesso.
        
        Args:
            message: Mensagem de sucesso principal
            details: Detalhes adicionais
            
        Returns:
            Mensagem de sucesso formatada
        """
        formatted = f"{self.emojis['success']} <b>Sucesso!</b>\n\n{message}"
        
        if details:
            formatted += f"\n\n{details}"
        
        return formatted
    
    def format_loading_message(self, action: str) -> str:
        """Formata mensagem de carregamento.
        
        Args:
            action: Ação sendo executada
            
        Returns:
            Mensagem de carregamento formatada
        """
        return f"{self.emojis['loading']} {action}..."
    
    def create_back_button(self, callback_data: str = 'back') -> InlineKeyboardMarkup:
        """Cria botão de voltar.
        
        Args:
            callback_data: Callback data do botão
            
        Returns:
            Teclado inline com botão de voltar
        """
        buttons = [
            [{'text': '◀️ Voltar', 'callback_data': callback_data}]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def create_close_button(self, callback_data: str = 'close') -> InlineKeyboardMarkup:
        """Cria botão de fechar.
        
        Args:
            callback_data: Callback data do botão
            
        Returns:
            Teclado inline com botão de fechar
        """
        buttons = [
            [{'text': f"{self.emojis['error']} Fechar", 'callback_data': callback_data}]
        ]
        
        return self.create_inline_keyboard(buttons)
    
    def truncate_text(self, text: str, max_length: int = 100, suffix: str = '...') -> str:
        """Trunca texto se exceder o limite.
        
        Args:
            text: Texto a ser truncado
            max_length: Comprimento máximo
            suffix: Sufixo para texto truncado
            
        Returns:
            Texto truncado se necessário
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    def escape_html(self, text: str) -> str:
        """Escapa caracteres HTML em texto.
        
        Args:
            text: Texto a ser escapado
            
        Returns:
            Texto com caracteres HTML escapados
        """
        return (
            text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;')
        )