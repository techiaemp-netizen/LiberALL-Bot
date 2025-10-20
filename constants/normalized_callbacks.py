"""
Callbacks normalizados seguindo o padrão: acao:alvo:identificador[:extra...]

Padrão obrigatório conforme PRD:
- Ações: match|gallery|favorite|info|comments|posting|menu|media|monetize|profile_detail|back
- Alvos: post|user|main|draft
- Identificador: sempre ID real do Firestore (nunca post_<timestamp>)

Exemplos:
- match:post:<postId>
- comments:post:<postId>
- media:next:<postId>:<index>
- posting:create:<userId>
- menu:main:<userId>
"""


class NormalizedCallbacks:
    """
    Callbacks normalizados seguindo padrão único.
    
    Formato: acao:alvo:identificador[:extra...]
    """
    
    # ========================================
    # INTERAÇÕES COM POSTS
    # ========================================
    
    @staticmethod
    def match_post(post_id: str) -> str:
        """Match em um post."""
        return f"match:post:{post_id}"
    
    @staticmethod
    def gallery_post(post_id: str) -> str:
        """Ver galeria do autor do post."""
        return f"gallery:post:{post_id}"
    
    @staticmethod
    def favorite_post(post_id: str) -> str:
        """Favoritar um post."""
        return f"favorite:post:{post_id}"
    
    @staticmethod
    def favorite_remove(post_id: str) -> str:
        """Remover post dos favoritos."""
        return f"favorite:remove:{post_id}"
    
    @staticmethod
    def info_post(post_id: str) -> str:
        """Ver informações do autor do post."""
        return f"info:post:{post_id}"
    
    @staticmethod
    def comments_post(post_id: str) -> str:
        """Ver comentários de um post."""
        return f"comments:post:{post_id}"
    
    @staticmethod
    def comments_write(post_id: str) -> str:
        """Escrever comentário em um post."""
        return f"comments:write:{post_id}"
    
    @staticmethod
    def comments_list(post_id: str, page: int = 0) -> str:
        """Listar comentários de um post."""
        return f"comments:list:{post_id}:{page}"
    
    # ========================================
    # NAVEGAÇÃO DE MÍDIA
    # ========================================
    
    @staticmethod
    def media_next(post_id: str, index: int) -> str:
        """Próxima mídia do post."""
        return f"media:next:{post_id}:{index}"
    
    @staticmethod
    def media_prev(post_id: str, index: int) -> str:
        """Mídia anterior do post."""
        return f"media:prev:{post_id}:{index}"
    
    # ========================================
    # CRIAÇÃO DE POSTS
    # ========================================
    
    @staticmethod
    def posting_create(user_id: int) -> str:
        """Iniciar criação de post."""
        return f"posting:create:{user_id}"
    
    @staticmethod
    def posting_draft(draft_id: str) -> str:
        """Continuar edição de rascunho."""
        return f"posting:draft:{draft_id}"
    
    @staticmethod
    def monetize_draft(draft_id: str) -> str:
        """Monetizar rascunho."""
        return f"monetize:draft:{draft_id}"
    
    # ========================================
    # MENU
    # ========================================
    
    @staticmethod
    def menu_main(user_id: int) -> str:
        """Menu principal."""
        return f"menu:main:{user_id}"
    
    @staticmethod
    def menu_gallery(user_id: int, page: int = 0) -> str:
        """Menu de galeria."""
        return f"menu:gallery:{user_id}:{page}"
    
    @staticmethod
    def menu_favorites(user_id: int, page: int = 0) -> str:
        """Menu de favoritos."""
        return f"menu:favorites:{user_id}:{page}"
    
    @staticmethod
    def menu_matches(user_id: int, page: int = 0) -> str:
        """Menu de matches."""
        return f"menu:matches:{user_id}:{page}"
    
    @staticmethod
    def menu_settings(user_id: int) -> str:
        """Menu de configurações."""
        return f"menu:settings:{user_id}"
    
    @staticmethod
    def menu_plan(user_id: int) -> str:
        """Menu de planos."""
        return f"menu:plan:{user_id}"
    
    # ========================================
    # PERFIL
    # ========================================
    
    @staticmethod
    def profile_detail(user_id: int) -> str:
        """Detalhar perfil do usuário."""
        return f"profile_detail:user:{user_id}"
    
    @staticmethod
    def profile_edit(user_id: int) -> str:
        """Editar perfil."""
        return f"profile:edit:{user_id}"
    
    # ========================================
    # MATCHES
    # ========================================
    
    @staticmethod
    def match_room(match_id: str) -> str:
        """Abrir sala de match."""
        return f"match:room:{match_id}"
    
    @staticmethod
    def match_close(match_id: str) -> str:
        """Fechar match."""
        return f"match:close:{match_id}"
    
    # ========================================
    # NAVEGAÇÃO GERAL
    # ========================================
    
    @staticmethod
    def back_main(context: str = "") -> str:
        """Voltar ao menu principal."""
        return f"back:main:{context}" if context else "back:main"
    
    @staticmethod
    def back_to(destination: str, context: str = "") -> str:
        """Voltar para destino específico."""
        return f"back:{destination}:{context}" if context else f"back:{destination}"


class CallbackPatterns:
    """
    Padrões regex para roteamento de callbacks.
    
    Usado para extrair partes dos callbacks normalizados.
    """
    
    # Interações com posts
    POST_INTERACTION = r"^(match|gallery|favorite|info|comments):post:([A-Za-z0-9_-]+)$"
    
    # Navegação de mídia
    MEDIA_NAVIGATION = r"^media:(prev|next):([A-Za-z0-9_-]+):([0-9]+)$"
    
    # Criação de posts
    POSTING = r"^posting:(create|draft):([A-Za-z0-9_-]+)$"
    
    # Menu
    MENU = r"^menu:(main|gallery|favorites|matches|settings|plan):([0-9]+)(?::([0-9]+))?$"
    
    # Perfil
    PROFILE = r"^profile(_detail)?:(user|edit):([0-9]+)$"
    
    # Favoritos
    FAVORITE_REMOVE = r"^favorite:remove:([A-Za-z0-9_-]+)$"
    
    # Comentários
    COMMENTS_ACTION = r"^comments:(write|list):([A-Za-z0-9_-]+)(?::([0-9]+))?$"
    
    # Matches
    MATCH_ACTION = r"^match:(room|close):([A-Za-z0-9_-]+)$"
    
    # Navegação geral
    BACK = r"^back:(main|[a-z_]+)(?::([A-Za-z0-9=_-]+))?$"
    
    # Monetização
    MONETIZE = r"^monetize:(draft):([A-Za-z0-9_-]+)$"


class CallbackExtractor:
    """
    Utilitários para extrair partes de callbacks normalizados.
    """
    
    @staticmethod
    def extract_post_id(callback_data: str) -> str:
        """
        Extrai post_id de callbacks que seguem o padrão acao:post:<postId>.
        
        Args:
            callback_data: Callback completo
            
        Returns:
            post_id extraído
            
        Raises:
            ValueError: Se o callback não seguir o padrão esperado
        """
        parts = callback_data.split(':')
        
        if len(parts) < 3:
            raise ValueError(f"Callback inválido: {callback_data}")
        
        if parts[1] != 'post':
            raise ValueError(f"Callback não é de post: {callback_data}")
        
        return parts[2]
    
    @staticmethod
    def extract_user_id(callback_data: str) -> int:
        """
        Extrai user_id de callbacks que seguem o padrão acao:alvo:<userId>.
        
        Args:
            callback_data: Callback completo
            
        Returns:
            user_id extraído (int)
            
        Raises:
            ValueError: Se o callback não seguir o padrão esperado
        """
        parts = callback_data.split(':')
        
        if len(parts) < 3:
            raise ValueError(f"Callback inválido: {callback_data}")
        
        try:
            return int(parts[2])
        except ValueError:
            raise ValueError(f"user_id não é numérico: {callback_data}")
    
    @staticmethod
    def extract_action(callback_data: str) -> str:
        """
        Extrai a ação do callback.
        
        Args:
            callback_data: Callback completo
            
        Returns:
            Ação extraída
        """
        return callback_data.split(':')[0]
    
    @staticmethod
    def extract_target(callback_data: str) -> str:
        """
        Extrai o alvo do callback.
        
        Args:
            callback_data: Callback completo
            
        Returns:
            Alvo extraído
        """
        parts = callback_data.split(':')
        return parts[1] if len(parts) > 1 else ""
    
    @staticmethod
    def extract_parts(callback_data: str) -> dict:
        """
        Extrai todas as partes do callback.
        
        Args:
            callback_data: Callback completo
            
        Returns:
            Dicionário com partes: {action, target, identifier, extras}
        """
        parts = callback_data.split(':')
        
        return {
            'action': parts[0] if len(parts) > 0 else "",
            'target': parts[1] if len(parts) > 1 else "",
            'identifier': parts[2] if len(parts) > 2 else "",
            'extras': parts[3:] if len(parts) > 3 else []
        }


# Aliases para compatibilidade com código existente
PostCallbacks = NormalizedCallbacks
MenuCallbacks = NormalizedCallbacks
MatchCallbacks = NormalizedCallbacks

