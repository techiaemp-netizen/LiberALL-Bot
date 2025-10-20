"""Constantes do sistema LiberALL.

Este módulo define:
- Estados brasileiros para seleção de localização
- Categorias de usuário para classificação
- Configurações de sistema
- Limites e validações
"""

# Estados brasileiros (código IBGE -> nome)
ESTADOS_BRASIL = {
    'AC': 'Acre',
    'AL': 'Alagoas', 
    'AP': 'Amapá',
    'AM': 'Amazonas',
    'BA': 'Bahia',
    'CE': 'Ceará',
    'DF': 'Distrito Federal',
    'ES': 'Espírito Santo',
    'GO': 'Goiás',
    'MA': 'Maranhão',
    'MT': 'Mato Grosso',
    'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais',
    'PA': 'Pará',
    'PB': 'Paraíba',
    'PR': 'Paraná',
    'PE': 'Pernambuco',
    'PI': 'Piauí',
    'RJ': 'Rio de Janeiro',
    'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia',
    'RR': 'Roraima',
    'SC': 'Santa Catarina',
    'SP': 'São Paulo',
    'SE': 'Sergipe',
    'TO': 'Tocantins'
}

# Categorias de usuário (código -> nome)
CATEGORIAS_USUARIO = {
    'homem_hetero': '👨 Homem Hétero',
    'mulher_hetero': '👩 Mulher Hétero',
    'homem_gay': '🏳️‍🌈 Homem Gay',
    'mulher_lesbica': '🏳️‍🌈 Mulher Lésbica',
    'homem_bi': '💜 Homem Bissexual',
    'mulher_bi': '💜 Mulher Bissexual',
    'trans_homem': '🏳️‍⚧️ Homem Trans',
    'trans_mulher': '🏳️‍⚧️ Mulher Trans',
    'nao_binario': '⚧️ Não-binário',
    'casal_hetero': '👫 Casal Hétero',
    'casal_gay': '👬 Casal Gay',
    'casal_lesbico': '👭 Casal Lésbico',
    'casal_bi': '💜 Casal Bissexual',
    'outros': '🌈 Outros'
}

# Configurações de postagem
POST_LIMITS = {
    'max_text_length': 4000,
    'max_photos_per_post': 10,
    'max_videos_per_post': 1,
    'max_file_size_mb': 50,
    'supported_image_formats': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'supported_video_formats': ['.mp4', '.mov', '.avi', '.mkv'],
    'min_price_cents': 100,  # R$ 1,00
    'max_price_cents': 50000,  # R$ 500,00
}

# Configurações de codinome
CODINOME_CONFIG = {
    'min_length': 3,
    'max_length': 20,
    'allowed_chars': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_',
    'reserved_names': [
        'admin', 'moderador', 'suporte', 'liberall', 'bot', 'sistema',
        'null', 'undefined', 'root', 'user', 'guest', 'anonymous'
    ]
}

# Configurações de segurança
SECURITY_CONFIG = {
    'rate_limit_posts_per_hour': 10,
    'rate_limit_messages_per_minute': 20,
    'max_login_attempts': 5,
    'session_timeout_hours': 24,
    'password_min_length': 8,
    'require_2fa_for_monetization': True
}

# Configurações de monetização
MONETIZATION_CONFIG = {
    'platform_fee_percentage': 20,  # 20% para a plataforma
    'creator_percentage': 80,  # 80% para o criador
    'min_payout_amount_cents': 1000,  # R$ 10,00 mínimo para saque
    'payout_processing_days': 2,  # 2 dias úteis para processar
    'supported_pix_key_types': ['cpf', 'cnpj', 'email', 'phone', 'random']
}

# Configurações de match
MATCH_CONFIG = {
    'room_expiry_hours': 24,  # Salas expiram em 24h
    'max_participants': 2,  # Máximo 2 pessoas por sala
    'cooldown_between_matches_minutes': 30,  # 30min entre matches
    'max_active_rooms_per_user': 5  # Máximo 5 salas ativas por usuário
}

# Status de posts
POST_STATUS = {
    'draft': 'Rascunho',
    'published': 'Publicado',
    'archived': 'Arquivado',
    'reported': 'Denunciado',
    'removed': 'Removido'
}

# Tipos de denúncia
REPORT_TYPES = {
    'spam': 'Spam',
    'inappropriate': 'Conteúdo Inapropriado',
    'harassment': 'Assédio',
    'fake': 'Perfil Falso',
    'underage': 'Menor de Idade',
    'violence': 'Violência',
    'hate_speech': 'Discurso de Ódio',
    'copyright': 'Violação de Direitos Autorais',
    'other': 'Outros'
}

# Configurações de cache
CACHE_CONFIG = {
    'user_profile_ttl_seconds': 3600,  # 1 hora
    'post_list_ttl_seconds': 300,  # 5 minutos
    'match_data_ttl_seconds': 1800,  # 30 minutos
    'rate_limit_ttl_seconds': 3600  # 1 hora
}

# Configurações de logs
LOG_CONFIG = {
    'retention_days': 90,  # Manter logs por 90 dias
    'sensitive_fields': ['pix_key', 'email', 'phone', 'ip_address'],
    'audit_events': [
        'user_registration',
        'lgpd_consent',
        'post_creation',
        'payment_processed',
        'data_export',
        'data_deletion',
        'login_attempt',
        'password_change'
    ]
}

# Mensagens do sistema
SYSTEM_MESSAGES = {
    'welcome': (
        "🎉 Bem-vindo ao LiberALL!\n\n"
        "Uma plataforma segura e anônima para conexões autênticas.\n\n"
        "Para começar, precisamos configurar seu perfil."
    ),
    'maintenance': (
        "🔧 Sistema em manutenção\n\n"
        "Voltaremos em breve! Obrigado pela paciência."
    ),
    'terms_updated': (
        "📋 Nossos termos foram atualizados\n\n"
        "Por favor, revise e aceite os novos termos para continuar usando a plataforma."
    ),
    'account_suspended': (
        "⚠️ Conta suspensa\n\n"
        "Sua conta foi suspensa por violação dos termos de uso. "
        "Entre em contato com o suporte para mais informações."
    ),
    'error_generic': (
        "❌ Ocorreu um erro interno\n\n"
        "Tente novamente em alguns instantes. Se o problema persistir, "
        "entre em contato com o suporte."
    )
}

# Emojis do sistema
EMOJIS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'loading': '⏳',
    'money': '💰',
    'heart': '❤️',
    'fire': '🔥',
    'star': '⭐',
    'lock': '🔒',
    'unlock': '🔓',
    'key': '🔑',
    'shield': '🛡️',
    'rocket': '🚀',
    'sparkles': '✨',
    'wave': '👋',
    'help': '❓',
    'check': '✅',
    'question': '❓',
    'post': '📝',
    'menu': '☰',
    'profile': '👤',
    'match': '💕',
    'favorites': '⭐',
    'subscription': '💎',
    'lgpd': '🔐',
    'check': '✅',
    'x': '❌'
}

# Textos dos teclados
KEYBOARD_TEXTS = {
    'post_button': '➕ Postar',
    'menu_button': '☰ Menu',
    'profile_button': '👤 Perfil',
    'matches_button': '💕 Matches',
    'favorites_button': '⭐ Favoritos',
    'settings_button': '⚙️ Configurações',
    'help_button': '❓ Ajuda',
    'back_button': '⬅️ Voltar',
    'cancel_button': '❌ Cancelar',
    'confirm_button': '✅ Confirmar',
    'skip_button': '⏭️ Pular',
    'next_button': '➡️ Próximo',
    'previous_button': '⬅️ Anterior',
    'edit_button': '✏️ Editar',
    'delete_button': '🗑️ Excluir',
    'share_button': '📤 Compartilhar',
    'report_button': '🚨 Denunciar'
}

# Textos dos botões inline
INLINE_TEXTS = {
    'match_button': '💕 Match',
    'gallery_button': '🖼️ Galeria',
    'favorite_button': '⭐ Favoritar',
    'info_button': 'ℹ️ Info',
    'comments_button': '💬 Comentários',
    'buy_button': '💰 Comprar',
    'subscribe_button': '💎 Assinar',
    'like_button': '👍 Curtir',
    'dislike_button': '👎 Não Curtir'
}

# Opções do menu principal
MENU_OPTIONS = {
    'profile': '👤 Meu Perfil',
    'my_posts': '📝 Meus Posts',
    'match': '💕 Match',
    'favorites': '⭐ Favoritos',
    'purchases': '🛒 Compras',
    'subscription': '💎 Assinatura',
    'karma': '🎯 Karma',
    'ranking': '🏆 Ranking',
    'settings': '⚙️ Configurações',
    'help': '❓ Ajuda'
}

# Estados do usuário
USER_STATES = {
    'idle': 'idle',
    'posting': 'posting',
    'editing_profile': 'editing_profile',
    'onboarding': 'onboarding',
    'matching': 'matching',
    'in_room': 'in_room',
    'purchasing': 'purchasing',
    'settings': 'settings'
}

# Emojis adicionais para UI
EMOJIS.update({
    'posts': '📝',
    'purchases': '🛒',
    'karma': '🎯',
    'ranking': '🏆',
    'settings': '⚙️',
    'edit': '✏️',
    'privacy': '🔒',
    'notifications': '🔔',
    'download': '📥',
    'delete': '🗑️',
    'back': '⬅️',
    'document': '📄'
})

# URLs e links
SYSTEM_URLS = {
    'support_username': '@liberall_suporte',
    'terms_url': 'https://liberall.com/termos',
    'privacy_url': 'https://liberall.com/privacidade',
    'help_url': 'https://liberall.com/ajuda',
    'website': 'https://liberall.com'
}