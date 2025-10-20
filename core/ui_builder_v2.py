"""
UI Builder V2 - Teclados combinados e renderização de posts.

Implementa teclados que combinam navegação + ações sem sobrescrever.
Suporta dois modos de renderização:
- carousel: 1 mensagem com primeira mídia + navegação inline
- album+panel: álbum sem teclado + painel separado com teclado
"""
import os
from typing import List, Dict, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from constants.normalized_callbacks import NormalizedCallbacks

# Configuração do modo de renderização
POST_RENDER_MODE = os.getenv('POST_RENDER_MODE', 'carousel')  # carousel | album+panel


class UIBuilderV2:
    """
    Construtor de interfaces com teclados combinados.
    
    Garante que navegação e ações sempre apareçam juntas,
    sem sobrescrita.
    """
    
    def __init__(self, bot_username: str):
        """
        Inicializa o UI Builder.
        
        Args:
            bot_username: Username do bot (para deep links)
        """
        self.bot_username = bot_username
    
    def create_media_nav_keyboard(
        self,
        post_id: str,
        current_index: int,
        total_media: int
    ) -> List[List[InlineKeyboardButton]]:
        """
        Cria linha de navegação de mídia (◀️ X/Y ▶️).
        
        Args:
            post_id: ID do post
            current_index: Índice atual (0-based)
            total_media: Total de mídias
            
        Returns:
            Lista com uma linha de botões de navegação
        """
        if total_media <= 1:
            return []
        
        buttons = []
        
        # Botão anterior
        if current_index > 0:
            buttons.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=NormalizedCallbacks.media_prev(post_id, current_index)
                )
            )
        
        # Indicador de posição (não clicável)
        buttons.append(
            InlineKeyboardButton(
                text=f"{current_index + 1}/{total_media}",
                callback_data="noop"
            )
        )
        
        # Botão próximo
        if current_index < total_media - 1:
            buttons.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=NormalizedCallbacks.media_next(post_id, current_index)
                )
            )
        
        return [buttons] if buttons else []
    
    def create_post_actions_keyboard(
        self,
        post_id: str,
        counts: Dict[str, int],
        viewer_user_id: int
    ) -> List[List[InlineKeyboardButton]]:
        """
        Cria teclado de ações do post.
        
        Args:
            post_id: ID do post
            counts: Contadores {comments, favorites, matches}
            viewer_user_id: ID do usuário visualizando
            
        Returns:
            Lista de linhas de botões
        """
        comments_count = counts.get('comments', 0)
        favorites_count = counts.get('favorites', 0)
        matches_count = counts.get('matches', 0)
        
        # Linha 1: Match, Galeria, Favoritar
        row1 = [
            InlineKeyboardButton(
                text="❤️ Match",
                callback_data=NormalizedCallbacks.match_post(post_id)
            ),
            InlineKeyboardButton(
                text="🖼️ Ver Galeria",
                callback_data=NormalizedCallbacks.gallery_post(post_id)
            ),
            InlineKeyboardButton(
                text="⭐ Favoritar",
                callback_data=NormalizedCallbacks.favorite_post(post_id)
            )
        ]
        
        # Linha 2: Info, Comentários (com contador)
        row2 = [
            InlineKeyboardButton(
                text="ℹ️ Info",
                callback_data=NormalizedCallbacks.info_post(post_id)
            ),
            InlineKeyboardButton(
                text=f"💭 Comentários ({comments_count})",
                callback_data=NormalizedCallbacks.comments_post(post_id)
            )
        ]
        
        # Linha 3: Postar, Menu
        row3 = [
            InlineKeyboardButton(
                text="➕ Postar na Comunidade",
                callback_data=NormalizedCallbacks.posting_create(viewer_user_id)
            ),
            InlineKeyboardButton(
                text="☰ Acessar Menu",
                callback_data=NormalizedCallbacks.menu_main(viewer_user_id)
            )
        ]
        
        return [row1, row2, row3]
    
    def create_combined_keyboard(
        self,
        post_id: str,
        counts: Dict[str, int],
        viewer_user_id: int,
        current_index: int = 0,
        total_media: int = 1
    ) -> InlineKeyboardMarkup:
        """
        Cria teclado combinado: navegação + ações.
        
        Args:
            post_id: ID do post
            counts: Contadores
            viewer_user_id: ID do usuário visualizando
            current_index: Índice atual da mídia
            total_media: Total de mídias
            
        Returns:
            InlineKeyboardMarkup completo
        """
        # Linha de navegação (se houver múltiplas mídias)
        nav_rows = self.create_media_nav_keyboard(post_id, current_index, total_media)
        
        # Linhas de ações
        action_rows = self.create_post_actions_keyboard(post_id, counts, viewer_user_id)
        
        # Combinar: navegação primeiro, depois ações
        all_rows = nav_rows + action_rows
        
        return InlineKeyboardMarkup(inline_keyboard=all_rows)
    
    def create_control_panel_keyboard(self) -> InlineKeyboardMarkup:
        """
        Cria painel de controle para grupos (deep links).
        
        Returns:
            InlineKeyboardMarkup com deep links
        """
        buttons = [
            [
                InlineKeyboardButton(
                    text="💬",
                    url=f"https://t.me/{self.bot_username}?start=postar"
                ),
                InlineKeyboardButton(
                    text="📎",
                    url=f"https://t.me/{self.bot_username}?start=postar_midia"
                ),
                InlineKeyboardButton(
                    text="🔊",
                    url=f"https://t.me/{self.bot_username}?start=postar_audio"
                ),
                InlineKeyboardButton(
                    text="☰",
                    url=f"https://t.me/{self.bot_username}?start=perfil"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def create_monetization_teaser_keyboard(
        self,
        post_id: str,
        price: float,
        creator_affiliate_link: str,
        premium_price: float = 9.99
    ) -> InlineKeyboardMarkup:
        """
        Cria teclado para teaser de conteúdo monetizado no Lite.
        
        Args:
            post_id: ID do post
            price: Preço do conteúdo
            creator_affiliate_link: Link de afiliado do criador
            premium_price: Preço do plano Premium
            
        Returns:
            InlineKeyboardMarkup com CTAs
        """
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"💰 Comprar por R$ {price:.2f}",
                    url=creator_affiliate_link
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"✨ Assinar Premium - R$ {premium_price:.2f}/mês",
                    url=f"https://t.me/{self.bot_username}?start=subscribe_premium"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def create_comments_keyboard(
        self,
        post_id: str,
        has_more: bool = False,
        page: int = 0
    ) -> InlineKeyboardMarkup:
        """
        Cria teclado para visualização de comentários.
        
        Args:
            post_id: ID do post
            has_more: Se há mais comentários
            page: Página atual
            
        Returns:
            InlineKeyboardMarkup
        """
        buttons = []
        
        # Botão para escrever comentário
        buttons.append([
            InlineKeyboardButton(
                text="✍️ Escrever Comentário",
                callback_data=NormalizedCallbacks.comments_write(post_id)
            )
        ])
        
        # Navegação de páginas (se houver mais)
        if has_more:
            buttons.append([
                InlineKeyboardButton(
                    text="📄 Carregar Mais",
                    callback_data=NormalizedCallbacks.comments_list(post_id, page + 1)
                )
            ])
        
        # Botão fechar
        buttons.append([
            InlineKeyboardButton(
                text="❌ Fechar",
                callback_data="close_comments"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def create_gallery_keyboard(
        self,
        user_id: int,
        posts: List[str],
        page: int = 0,
        has_more: bool = False
    ) -> InlineKeyboardMarkup:
        """
        Cria teclado para galeria de posts de um usuário.
        
        Args:
            user_id: ID do usuário
            posts: Lista de IDs de posts
            page: Página atual
            has_more: Se há mais posts
            
        Returns:
            InlineKeyboardMarkup
        """
        buttons = []
        
        # Botões de posts (até 5 por página)
        for i, post_id in enumerate(posts[:5], 1):
            buttons.append([
                InlineKeyboardButton(
                    text=f"📸 Post {i}",
                    callback_data=f"view:post:{post_id}"
                )
            ])
        
        # Navegação
        nav_row = []
        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀️ Anterior",
                    callback_data=NormalizedCallbacks.menu_gallery(user_id, page - 1)
                )
            )
        if has_more:
            nav_row.append(
                InlineKeyboardButton(
                    text="Próxima ▶️",
                    callback_data=NormalizedCallbacks.menu_gallery(user_id, page + 1)
                )
            )
        
        if nav_row:
            buttons.append(nav_row)
        
        # Voltar
        buttons.append([
            InlineKeyboardButton(
                text="🔙 Voltar",
                callback_data=NormalizedCallbacks.back_main()
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def create_main_menu_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """
        Cria teclado do menu principal.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            InlineKeyboardMarkup
        """
        buttons = [
            [
                InlineKeyboardButton(
                    text="➕ Postar",
                    callback_data=NormalizedCallbacks.posting_create(user_id)
                )
            ],
            [
                InlineKeyboardButton(
                    text="🖼️ Minha Galeria",
                    callback_data=NormalizedCallbacks.menu_gallery(user_id)
                ),
                InlineKeyboardButton(
                    text="⭐ Favoritos",
                    callback_data=NormalizedCallbacks.menu_favorites(user_id)
                )
            ],
            [
                InlineKeyboardButton(
                    text="❤️ Meus Matches",
                    callback_data=NormalizedCallbacks.menu_matches(user_id)
                ),
                InlineKeyboardButton(
                    text="⚙️ Configurações",
                    callback_data=NormalizedCallbacks.menu_settings(user_id)
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Plano",
                    callback_data=NormalizedCallbacks.menu_plan(user_id)
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Detalhar meu Perfil",
                    callback_data=NormalizedCallbacks.profile_detail(user_id)
                )
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)


# Função auxiliar para criar instância
def create_ui_builder(bot_username: str) -> UIBuilderV2:
    """
    Cria instância do UI Builder V2.
    
    Args:
        bot_username: Username do bot
        
    Returns:
        Instância do UIBuilderV2
    """
    return UIBuilderV2(bot_username)

