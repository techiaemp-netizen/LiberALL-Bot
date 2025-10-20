"""Constantes centralizadas de callback para o bot LiberALL.

Este módulo centraliza todas as constantes de callback_data utilizadas
no sistema, organizadas por funcionalidade para facilitar manutenção.
"""

from typing import Dict, Any
import json
from constants.callbacks import MenuCallbacks  # Reexporta MenuCallbacks unificado

# ===== CALLBACKS DE ONBOARDING =====
# REMOVIDO: OnboardingCallbacks movido para constants/callbacks.py para evitar duplicação
# Use: from constants.callbacks import OnboardingCallbacks

# ===== CALLBACKS DE MENU PRINCIPAL =====
# Reexporta MenuCallbacks a partir de constants/callbacks.py para evitar duplicação
# e garantir padronização dos prefixos 'menu_' e alias 'main_menu'
# Use: from constants.callbacks import MenuCallbacks

# ===== CALLBACKS DE CONFIGURAÇÕES =====
class SettingsCallbacks:
    """Callbacks das configurações"""
    MAIN = "settings_main"
    EDIT_PROFILE = "settings_edit_profile"
    PRIVACY = "settings_privacy"
    NOTIFICATIONS = "settings_notifications"
    LGPD = "settings_lgpd"
    LANGUAGE = "settings_language"
    THEME = "settings_theme"
    BLOCKED_USERS = "settings_blocked"
    
    # Edição de perfil
    EDIT_PHOTO = "edit_profile_photo"
    EDIT_BIO = "edit_profile_bio"
    EDIT_LOCATION = "edit_profile_location"
    EDIT_INTERESTS = "edit_profile_interests"
    
    # Privacidade
    PRIVACY_TOGGLE_AGE = "privacy_toggle_age"
    PRIVACY_TOGGLE_LOCATION = "privacy_toggle_location"
    PRIVACY_TOGGLE_MESSAGES = "privacy_toggle_messages"
    PRIVACY_BLOCKED_USERS = "privacy_blocked_users"
    
    # Notificações
    NOTIFICATION_TOGGLE_MATCHES = "notification_toggle_matches"
    NOTIFICATION_TOGGLE_MESSAGES = "notification_toggle_messages"
    NOTIFICATION_TOGGLE_LIKES = "notification_toggle_likes"
    NOTIFICATION_TOGGLE_POSTS = "notification_toggle_posts"

# ===== CALLBACKS DE LGPD =====
class LGPDCallbacks:
    """Callbacks relacionados à LGPD"""
    MENU = "lgpd_menu"
    EXPORT_DATA = "lgpd_export_data"
    DELETE_ACCOUNT = "lgpd_delete_account"
    CONFIRM_DELETE = "lgpd_confirm_delete"
    CONFIRM_FINAL_DELETION = "lgpd_confirm_final_deletion"
    PRIVACY_POLICY = "lgpd_privacy_policy"
    TERMS_OF_USE = "lgpd_terms_of_use"
    DATA_USAGE = "lgpd_data_usage"

# ===== CALLBACKS DE POSTAGEM =====
class PostingCallbacks:
    """Callbacks relacionados à criação de posts"""
    START = "posting_start"
    ADD_PHOTO = "posting_add_photo"
    ADD_VIDEO = "posting_add_video"
    ADD_AUDIO = "posting_add_audio"
    ADD_TEXT = "posting_add_text"
    PREVIEW = "posting_preview"
    PUBLISH = "posting_publish"
    CANCEL = "posting_cancel"
    EDIT_CAPTION = "posting_edit_caption"
    REMOVE_MEDIA = "posting_remove_media"
    
    # Tipos de post
    TYPE_FREE = "post_type_free"
    TYPE_PAID = "post_type_paid"
    TYPE_EXCLUSIVE = "post_type_exclusive"
    TYPE_PREFIX = "post_type_"

# ===== CALLBACKS DE MATCH =====
class MatchCallbacks:
    """Callbacks do sistema de match"""
    START = "match_start"
    LIST = "match_list"
    FILTERS = "match_filters"
    LIKE = "match_like"
    DISLIKE = "match_dislike"
    SUPER_LIKE = "match_super_like"
    REPORT = "match_report"
    BLOCK = "match_block"
    CHAT = "match_chat"
    VIEW_PROFILE = "match_view_profile"
    NEXT = "match_next"
    PREVIOUS = "match_previous"

# ===== CALLBACKS DE FAVORITOS =====
class FavoritesCallbacks:
    """Callbacks do sistema de favoritos"""
    LIST = "favorites_list_all"
    ADD = "favorites_add"
    REMOVE = "favorites_remove"
    VIEW = "favorites_view"
    CLEAR_ALL = "favorites_clear_all"
    CONFIRM_CLEAR = "favorites_confirm_clear"
    EXPLORE = "explore_posts"

# ===== CALLBACKS DE GALERIA =====
class GalleryCallbacks:
    """Callbacks da galeria de fotos"""
    VIEW = "gallery_view"
    NEXT = "gallery_next"
    PREVIOUS = "gallery_previous"
    ZOOM = "gallery_zoom"
    INFO = "gallery_info"
    DOWNLOAD = "gallery_download"
    REPORT = "gallery_report"
    CLOSE = "gallery_close"

# ===== CALLBACKS DE MONETIZAÇÃO =====
class MonetizationCallbacks:
    """Callbacks do sistema de monetização"""
    MENU = "monetization_menu"
    ENABLE = "monetization_enable"
    DISABLE = "monetization_disable"
    STATS = "monetization_stats"
    WITHDRAW = "monetization_withdraw"
    SETTINGS = "monetization_settings"
    PRICING = "monetization_pricing"
    CONFIRM_PREMIUM = "monetization_confirm_premium"
    CONFIRM_CONTENT = "monetization_confirm_content"
    CONFIRM_AFFILIATE = "monetization_confirm_affiliate"
    BUY_PACK = "monetization_buy_pack"
    SETUP_PIX = "monetization_setup_pix"
    CONFIRM_WITHDRAWAL = "monetization_confirm_withdrawal"
    DETAILED_REPORT = "monetization_detailed_report"
    PANEL = "monetization_panel"
    
    # Compras e assinaturas
    PURCHASES_LIST_ALL = "purchases_list_all"
    PURCHASES_RECEIPTS = "purchases_receipts"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    SUBSCRIPTION_COMPARE = "subscription_compare"
    SUBSCRIPTION_MANAGE = "subscription_manage"
    SUBSCRIPTION_INVOICES = "subscription_invoices"
    
    # Karma e ranking
    KARMA_HISTORY = "karma_history"
    KARMA_RANKING = "karma_ranking"

# ===== CALLBACKS DE NAVEGAÇÃO =====
class NavigationCallbacks:
    """Callbacks de navegação geral"""
    BACK = "back"
    BACK_TO_MAIN = "back_to_main_menu"
    BACK_TO_SETTINGS = "back_to_settings"
    BACK_TO_PROFILE = "back_to_profile"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    CLOSE = "close"
    REFRESH = "refresh"
    
    # Ajuda e suporte
    HELP_GETTING_STARTED = "help_getting_started"
    HELP_FAQ = "help_faq"
    HELP_CONTACT_SUPPORT = "help_contact_support"
    HELP_REPORT_BUG = "help_report_bug"

# ===== CALLBACKS DE POSTS =====
class PostActionsCallbacks:
    """Callbacks de ações em posts"""
    MATCH = "post_match"
    GALLERY = "post_gallery"
    INFO = "post_info"
    FAVORITE = "post_favorite"
    COMMENTS = "post_comments"
    VIA_DM = "post_via_dm"
    REPORT = "post_report"
    BLOCK_USER = "post_block_user"
    SHARE = "post_share"

# ===== UTILITÁRIOS =====
def encode_callback_data(prefix: str, data: Dict[str, Any] = None) -> str:
    """Codifica dados de callback de forma segura.
    
    Args:
        prefix: Prefixo do callback
        data: Dados adicionais (opcional)
        
    Returns:
        String de callback_data codificada
    """
    if data:
        # Limitar tamanho para respeitar limite do Telegram (64 bytes)
        encoded = json.dumps(data, separators=(',', ':'))
        callback_data = f"{prefix}:{encoded}"
        
        # Verificar limite de 64 bytes
        if len(callback_data.encode('utf-8')) > 64:
            # Usar apenas o prefixo se os dados forem muito grandes
            return prefix
        
        return callback_data
    
    return prefix

def decode_callback_data(callback_data: str) -> tuple[str, Dict[str, Any]]:
    """Decodifica dados de callback.
    
    Args:
        callback_data: String de callback_data
        
    Returns:
        Tupla com (prefix, data)
    """
    if ':' in callback_data:
        prefix, encoded_data = callback_data.split(':', 1)
        try:
            data = json.loads(encoded_data)
            return prefix, data
        except json.JSONDecodeError:
            return prefix, {}
    
    return callback_data, {}

def is_callback_for(callback_data: str, prefix: str) -> bool:
    """Verifica se o callback pertence ao prefixo especificado.
    
    Args:
        callback_data: String de callback_data
        prefix: Prefixo a verificar
        
    Returns:
        True se o callback pertence ao prefixo
    """
    decoded_prefix, _ = decode_callback_data(callback_data)
    return decoded_prefix == prefix or callback_data.startswith(f"{prefix}_")

def get_callback_action(callback_data: str) -> str:
    """Extrai a ação do callback_data.
    
    Args:
        callback_data: String de callback_data
        
    Returns:
        Ação extraída do callback
    """
    prefix, data = decode_callback_data(callback_data)
    
    if data and 'action' in data:
        return data['action']
    
    # Fallback para callbacks simples
    if '_' in callback_data:
        parts = callback_data.split('_')
        if len(parts) > 1:
            return '_'.join(parts[1:])
    
    return callback_data

# ===== MAPEAMENTO DE CALLBACKS =====
CALLBACK_HANDLERS = {
    # Onboarding
    'onboarding_': 'onboarding_handler',
    'confirm_age': 'onboarding_handler',
    'reject_age': 'onboarding_handler',
    'accept_terms': 'onboarding_handler',
    'reject_terms': 'onboarding_handler',
    'state_': 'onboarding_handler',
    'category_': 'onboarding_handler',
    'gender_': 'onboarding_handler',
    'orientation_': 'onboarding_handler',
    'status_': 'onboarding_handler',
    
    # Menu principal
    'menu_': 'menu_handler',
    'main_menu': 'menu_handler',  # alias explícito para o menu principal
    
    # Configurações
    'settings_': 'settings_handler',
    
    # LGPD
    'lgpd_': 'lgpd_handler',
    
    # Postagem
    'posting_': 'posting_handler',
    
    # Match
    'match_': 'match_handler',
    
    # Favoritos
    'favorites_': 'favorites_handler',
    
    # Galeria
    'gallery_': 'gallery_handler',
    
    # Monetização
    'monetization_': 'monetization_handler',
    
    # Posts
    'post_': 'post_actions_handler',
    
    # Navegação
    'back': 'navigation_handler',
    'cancel': 'navigation_handler',
    'confirm': 'navigation_handler',
}

def get_handler_for_callback(callback_data: str) -> str:
    """Retorna o handler apropriado para um callback.
    
    Args:
        callback_data: String de callback_data
        
    Returns:
        Nome do handler responsável
    """
    for prefix, handler in CALLBACK_HANDLERS.items():
        if callback_data.startswith(prefix) or callback_data == prefix.rstrip('_'):
            return handler
    
    return 'default_handler'