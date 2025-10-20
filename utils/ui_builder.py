# Em um novo ficheiro: utils/ui_builder.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from constants.callbacks import PostingCallbacks  # Certifique-se que os callbacks estão definidos
from config import BOT_USERNAME

class UIBuilder:
    """Classe para construir interfaces de usuário do bot."""
    
    @staticmethod
    def build_anonymous_label(user_data) -> str:
        """Constrói a etiqueta de anonimização do autor do post."""
        # Trabalha com dicionário de dados do usuário
        if isinstance(user_data, dict):
            profile = user_data.get('profile', {})
            codename = profile.get('codename', 'Anónimo')
            category = profile.get('category', 'Indefinido')
            state = profile.get('state_location', 'BR')
        else:
            # Fallback para objeto User (compatibilidade)
            codename = getattr(user_data.profile, 'codename', None) or 'Anónimo'
            category = getattr(user_data.profile, 'category', None) or 'Indefinido'
            state = getattr(user_data.profile, 'state_location', None) or 'BR'
        return f"👤 {codename} · {category} · {state}"
    
    @staticmethod
    def create_post_interaction_keyboard(post_id: str, user_id: int = None, is_matched: bool = False, is_favorited: bool = False, comment_count: int = 0) -> InlineKeyboardMarkup:
        """Cria o teclado inline completo para uma postagem no grupo."""
        # Definir textos dos botões baseado no estado
        match_text = "💖 Matched" if is_matched else "❤️ Match"
        favorite_text = "⭐ Favoritado" if is_favorited else "⭐ Favoritar"
        
        keyboard_rows = [
            [
                InlineKeyboardButton(text=match_text, callback_data=f"match:post:{post_id}"),
                InlineKeyboardButton(text="🖼️ Ver Galeria", callback_data=f"gallery:post:{post_id}"),
                InlineKeyboardButton(text=favorite_text, callback_data=f"favorite:post:{post_id}")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Info", callback_data=f"info:post:{post_id}"),
                InlineKeyboardButton(text=f"💭 Comentários ({comment_count})", callback_data=f"comments:post:{post_id}")
            ],
            [
                InlineKeyboardButton(text="➕ Postar na Comunidade", callback_data="posting:create"),
                InlineKeyboardButton(text="☰ Acessar Menu", callback_data="menu:main")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    @staticmethod
    def create_post_preview_keyboard(draft_id: str) -> InlineKeyboardMarkup:
        """Cria o teclado de pré-visualização do post com opções de ação usando draft_id."""
        keyboard_rows = [
            [
                InlineKeyboardButton(text="✅ Publicar", callback_data=f"post_publish:{draft_id}"),
                InlineKeyboardButton(text="💲 Monetizar", callback_data=f"post_monetize:{draft_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Cancelar", callback_data=f"post_cancel:{draft_id}")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    @staticmethod
    def create_control_panel_keyboard(bot_username: str) -> InlineKeyboardMarkup:
        """Cria o teclado de controle anônimo para o grupo."""
        post_url = f"https://t.me/{bot_username}?start=iniciar_postagem"
        menu_url = f"https://t.me/{bot_username}?start=abrir_menu"
        
        keyboard_rows = [
            [
                InlineKeyboardButton(text="➕ Postar na Comunidade", url=post_url),
                InlineKeyboardButton(text="☰ Acessar Menu", url=menu_url)
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    @staticmethod
    def create_welcome_keyboard(user_id: int, bot_username: str) -> InlineKeyboardMarkup:
        """Cria o teclado inline completo para a mensagem de boas-vindas de um novo membro."""
        
        # URLs para os botões de ação principais
        post_url = f"https://t.me/{bot_username}?start=iniciar_postagem"
        menu_url = f"https://t.me/{bot_username}?start=abrir_menu"

        # Criar o teclado com linhas organizadas usando callbacks padronizados
        keyboard_rows = [
            # Primeira fila de botões de interação
            [
                InlineKeyboardButton(text="❤️ Match", callback_data=f"{PostingCallbacks.MATCH_POST}welcome:{user_id}"),
                InlineKeyboardButton(text="🖼️ Ver Galeria", callback_data=f"{PostingCallbacks.GALLERY_POST}welcome:{user_id}"),
                InlineKeyboardButton(text="⭐ Favoritar", callback_data=f"{PostingCallbacks.FAVORITE_POST}welcome:{user_id}")
            ],
            # Segunda fila de botões de interação
            [
                InlineKeyboardButton(text="ℹ️ Info", callback_data=f"{PostingCallbacks.INFO_POST}welcome:{user_id}"),
                InlineKeyboardButton(text="💭 Comentários (0)", callback_data=f"{PostingCallbacks.COMMENT_POST}welcome:{user_id}")
            ],
            # Terceira fila com botões de URL
            [
                InlineKeyboardButton(text="➕ Postar na Comunidade", url=post_url),
                InlineKeyboardButton(text="☰ Acessar Menu", url=menu_url)
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
"""
Wrappers para compatibilidade retroativa
"""

def build_anonymous_label(user_data) -> str:
    """Wrapper: mantém compatibilidade chamando a versão na classe."""
    return UIBuilder.build_anonymous_label(user_data)

def create_post_interaction_keyboard(post_id: str, user_id: int = None, is_matched: bool = False, is_favorited: bool = False, comment_count: int = 0) -> InlineKeyboardMarkup:
    """Wrapper: mantém compatibilidade chamando a versão na classe."""
    return UIBuilder.create_post_interaction_keyboard(post_id, user_id, is_matched, is_favorited, comment_count)

def create_control_panel_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    """Wrapper: mantém compatibilidade chamando a versão na classe."""
    return UIBuilder.create_control_panel_keyboard(bot_username)

def create_post_preview_keyboard(draft_id: str) -> InlineKeyboardMarkup:
    """Wrapper: mantém compatibilidade chamando a versão na classe com draft_id."""
    return UIBuilder.create_post_preview_keyboard(draft_id)

def create_welcome_keyboard(user_id: int, bot_username: str) -> InlineKeyboardMarkup:
    """Cria o teclado inline completo para a mensagem de boas-vindas de um novo membro."""
    
    # URLs para os botões de ação principais
    post_url = f"https://t.me/{bot_username}?start=iniciar_postagem"
    menu_url = f"https://t.me/{bot_username}?start=abrir_menu"

    # Criar o teclado com linhas organizadas usando callbacks padronizados
    keyboard_rows = [
        # Primeira fila de botões de interação
        [
            InlineKeyboardButton(text="❤️ Match", callback_data=f"{PostingCallbacks.MATCH_POST}welcome:{user_id}"),
            InlineKeyboardButton(text="🖼️ Ver Galeria", callback_data=f"{PostingCallbacks.GALLERY_POST}welcome:{user_id}"),
            InlineKeyboardButton(text="⭐ Favoritar", callback_data=f"{PostingCallbacks.FAVORITE_POST}welcome:{user_id}")
        ],
        # Segunda fila de botões de interação
        [
            InlineKeyboardButton(text="ℹ️ Info", callback_data=f"{PostingCallbacks.INFO_POST}welcome:{user_id}"),
            InlineKeyboardButton(text="💭 Comentários (0)", callback_data=f"{PostingCallbacks.COMMENT_POST}welcome:{user_id}")
        ],
        # Terceira fila com botões de URL
        [
            InlineKeyboardButton(text="➕ Postar na Comunidade", url=post_url),
            InlineKeyboardButton(text="☰ Acessar Menu", url=menu_url)
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)