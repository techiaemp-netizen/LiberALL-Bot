"""Constantes de callbacks para o bot."""

# Aliases para compatibilidade
PostActionsCallbacks = None
GalleryCallbacks = None
FavoritesCallbacks = None

class PostingCallbacks:
    """Callbacks relacionados a posts."""
    
    # Criação de posts
    CREATE_POST = 'create_post'
    POST_TEXT = 'post_text'
    POST_PHOTO = 'post_photo'
    POST_VIDEO = 'post_video'
    POST_AUDIO = 'post_audio'
    POST_LOCATION = 'post_location'
    POST_POLL = 'post_poll'
    POST_MONETIZED = 'post_monetized'
    
    # Tipos de post
    POST_TYPE_TEXT = 'post_type:text'
    POST_TYPE_PHOTO = 'post_type:photo'
    POST_TYPE_VIDEO = 'post_type:video'
    POST_TYPE_LOCATION = 'post_type:location'
    POST_TYPE_AUDIO = 'post_type:audio'
    POST_TYPE_POLL = 'post_type:poll'
    
    # Ações de post
    LIKE_POST = 'like_post_'
    UNLIKE_POST = 'unlike_post_'
    COMMENT_POST = 'comment_post_'
    SHARE_POST = 'share_post_'
    SAVE_POST = 'save_post_'
    REPORT_POST = 'report_post_'
    
    # Interações finais do post
    INFO_POST = 'info_post_'
    FAVORITE_POST = 'favorite_post_'
    MATCH_POST = 'match_post_'
    GALLERY_POST = 'gallery_post_'
    BACK_TO_BOT = 'back_to_bot'
    
    # Edição e ações
    EDIT_POST = 'edit_post_'
    DELETE_POST = 'delete_post_'
    POST_EDIT = 'post_edit'
    POST_PUBLISH = 'post_publish'
    POST_MONETIZE = 'post_monetize'
    POST_SCHEDULE = 'post_schedule'
    POST_ANALYTICS = 'post_analytics'

    # Aliases esperados pelos handlers
    PUBLISH = 'post_publish'
    CANCEL = 'post_cancel'
    EDIT = 'post_edit'
    DELETE = 'delete_post_'
    
    # Confirmações
    CONFIRM_POST = 'confirm_post'
    CANCEL_POST = 'cancel_post'
    
    # Ações do Preview
    POST_PUBLISH = 'post_publish'
    POST_MONETIZE = 'post_monetize'
    POST_PUBLISH_STAY = 'post_publish_stay'
    POST_CANCEL = 'post_cancel'
    
    # Visibilidade
    VISIBILITY_PUBLIC = 'visibility:public'
    VISIBILITY_MATCHES = 'visibility:matches'
    VISIBILITY_PRIVATE = 'visibility:private'
    
    # Categorias
    CATEGORY_THOUGHTS = 'category:thoughts'
    CATEGORY_MOMENTS = 'category:moments'
    CATEGORY_INTERESTS = 'category:interests'
    CATEGORY_PROFESSIONAL = 'category:professional'
    CATEGORY_EVENTS = 'category:events'
    CATEGORY_OTHER = 'category:other'

class NavigationCallbacks:
    """Callbacks de navegação."""
    
    # Menu principal
    MAIN_MENU = 'main_menu'
    BACK_TO_MAIN = 'back_to_main_menu'
    
    # Navegação geral
    BACK = 'back'
    NEXT = 'next'
    CANCEL = 'cancel'
    CONFIRM = 'confirm'
    
    # Navegação entre páginas
    NEXT_PAGE = 'next_page'
    PREV_PAGE = 'prev_page'
    FIRST_PAGE = 'first_page'
    LAST_PAGE = 'last_page'
    
    # Filtros
    FILTER_BY_DATE = 'filter_date'
    FILTER_BY_TYPE = 'filter_type'
    FILTER_BY_USER = 'filter_user'
    
    # Ordenação
    SORT_BY_DATE = 'sort_date'
    SORT_BY_POPULARITY = 'sort_popularity'
    SORT_BY_RELEVANCE = 'sort_relevance'
    
    # Seções
    PROFILE = 'profile'
    SETTINGS = 'settings'
    HELP = 'help'
    ABOUT = 'about'
    
    # Ranking
    RANKING = 'ranking'
    RANKING_REFRESH = 'ranking_refresh'
    
    # Karma
    KARMA = 'karma'
    
    # Perfil de outros usuários
    PROFILE_VIEW_OTHER = 'profile_view_other'
    
    # Funcionalidades específicas
    START_REGISTRATION = 'start_registration'
    SHOW_TERMS = 'show_terms'
    SHOW_PRIVACY = 'show_privacy'
    SHOW_HELP = 'show_help'
    SHOW_FAQ = 'show_faq'
    CONTACT_SUPPORT = 'contact_support'
    ACCEPT_TERMS_CONTINUE = 'accept_terms_continue'
    CANCEL_REGISTRATION = 'cancel_registration'

class MenuCallbacks:
    """Callbacks do menu principal."""
    
    # Menu principal
    MAIN = 'main_menu'
    # Alias compatível com handlers que usam MAIN_MENU
    MAIN_MENU = 'main_menu'
    
    # Funcionalidades principais
    CREATE_POST = 'menu_create_post'
    MY_POSTS = 'menu_my_posts'
    EXPLORE = 'menu_explore'
    MATCH = 'menu_match'
    FAVORITES = 'menu_favorites'
    PROFILE = 'menu_profile'
    SETTINGS = 'menu_settings'
    MONETIZATION = 'menu_monetization'
    RANKING = 'menu_ranking'
    HELP = 'menu_help'

    # Itens adicionais usados em handlers/menu_handler.py
    # Padronizados com prefixo 'menu_'
    VIEW_POSTS = 'menu_view_posts'
    MY_MATCHES = 'menu_my_matches'
    STATISTICS = 'menu_statistics'
    
    # Submenu de perfil
    EDIT_PROFILE = 'profile_edit'
    VIEW_PROFILE = 'profile_view'
    PRIVACY_SETTINGS = 'profile_privacy'
    EDIT_PHOTOS = 'edit_photos'
    LOCATION_SETTINGS = 'location_settings'
    
    # Submenu de posts
    EXPLORE_POSTS = 'explore_posts'
    
    # Planos e monetização
    VIEW_PLANS = 'view_plans'
    
    # Submenu de configurações
    NOTIFICATIONS = 'settings_notifications'
    PRIVACY = 'settings_privacy'
    ACCOUNT = 'settings_account'
    LANGUAGE = 'settings_language'
    
    # LGPD
    LGPD_MENU = 'lgpd_menu'
    EXPORT_DATA = 'lgpd_export'
    DELETE_ACCOUNT = 'lgpd_delete'
    PRIVACY_POLICY = 'lgpd_privacy'
    
    # Consentimentos
    CONSENT_IMAGE_PROCESSING = 'consent:image_processing'
    CONSENT_MEDIA_PROCESSING = 'consent:media_processing'
    CONSENT_LOCATION_DATA = 'consent:location_data'

class MatchCallbacks:
    """Callbacks do sistema de match."""
    
    # Ações de match
    START_MATCHING = 'match_start'
    LIKE = 'match_like'
    PASS = 'match_pass'
    NEXT = 'match_next'
    SUPER_LIKE = 'match_super_like'
    
    # Descoberta
    DISCOVER_PEOPLE = 'discover_people'
    DISCOVERY_NEXT = 'discovery_next'
    VIEW_MATCHES = 'view_matches'
    VIEW_ALL_MATCHES = 'view_all_matches'
    
    # Filtros
    FILTERS = 'match_filters'
    AGE_FILTER = 'match_filter_age'
    LOCATION_FILTER = 'match_filter_location'
    INTERESTS_FILTER = 'match_filter_interests'
    MATCH_PREFERENCES = 'match_preferences'
    MATCH_DISTANCE = 'match_distance'
    MATCH_AGE_RANGE = 'match_age_range'
    MATCH_NOTIFICATIONS = 'match_notifications'
    MATCH_PRIVACY = 'match_privacy'
    MATCH_SETTINGS = 'match_settings'
    MATCH_STATS = 'match_stats'
    
    # Lista de matches
    MATCH_LIST = 'match_list'
    MATCH_CHAT = 'match_chat_'
    UNMATCH = 'match_unmatch_'

class MonetizationCallbacks:
    """Callbacks de monetização."""
    
    # Menu principal
    MONETIZATION_MENU = 'monetization_menu'
    
    # Assinaturas
    PREMIUM = 'monetization_premium'
    SUBSCRIBE_PREMIUM = 'subscribe_premium'
    SUBSCRIBE_VIP = 'subscribe_vip'
    MANAGE_SUBSCRIPTION = 'manage_subscription'
    CANCEL_SUBSCRIPTION = 'cancel_subscription'
    
    # Compras
    BUY_COINS = 'buy_coins'
    BUY_BOOST = 'buy_boost'
    BUY_SUPER_LIKE = 'buy_super_like'
    
    # Histórico
    HISTORY = 'monetization_history'
    PURCHASE_HISTORY = 'purchase_history'
    EARNINGS = 'earnings'
    
    # Recompensas
    DAILY_REWARD = 'monetization_daily_reward'
    BADGE_SHOP = 'monetization_badge_shop'
    WITHDRAW = 'monetization_withdraw'

class ModerationCallbacks:
    """Callbacks de moderação."""
    
    # Ações de moderação
    REPORT_CONTENT = 'report_content_'
    REPORT_USER = 'report_user_'
    BLOCK_USER = 'block_user_'
    
    # Tipos de report
    REPORT_SPAM = 'report_spam'
    REPORT_INAPPROPRIATE = 'report_inappropriate'
    REPORT_FAKE = 'report_fake'
    REPORT_HARASSMENT = 'report_harassment'
    
    # Ações do moderador
    APPROVE_CONTENT = 'mod_approve_'
    REJECT_CONTENT = 'mod_reject_'
    BAN_USER = 'mod_ban_'
    WARN_USER = 'mod_warn_'

class AdminCallbacks:
    """Callbacks administrativos."""
    
    # Menu admin
    ADMIN_MENU = 'admin_menu'
    ADMIN_PANEL = 'admin_panel'
    
    # Usuários
    ADMIN_USERS = 'admin_users'
    ADMIN_SEARCH_USER = 'admin_search_user'
    ADMIN_LIST_USERS = 'admin_list_users'
    ADMIN_BANNED_USERS = 'admin_banned_users'
    ADMIN_PREMIUM_USERS = 'admin_premium_users'
    ADMIN_USER_REPORT = 'admin_user_report'
    ADMIN_USER_SETTINGS = 'admin_user_settings'
    
    # Posts
    ADMIN_POSTS = 'admin_posts'
    ADMIN_SEARCH_POST = 'admin_search_post'
    ADMIN_RECENT_POSTS = 'admin_recent_posts'
    ADMIN_REPORTED_POSTS = 'admin_reported_posts'
    ADMIN_REMOVED_POSTS = 'admin_removed_posts'
    ADMIN_POST_REPORT = 'admin_post_report'
    ADMIN_POST_SETTINGS = 'admin_post_settings'
    
    # Denúncias
    ADMIN_REPORTS = 'admin_reports'
    ADMIN_REVIEW_REPORTS = 'admin_review_reports'
    ADMIN_REPORTS_STATS = 'admin_reports_stats'
    ADMIN_REPORTS_HISTORY = 'admin_reports_history'
    ADMIN_REPORTS_SETTINGS = 'admin_reports_settings'
    
    # Estatísticas
    ADMIN_STATS = 'admin_stats'
    ADMIN_CHARTS = 'admin_charts'
    ADMIN_TRENDS = 'admin_trends'
    ADMIN_FULL_REPORT = 'admin_full_report'
    ADMIN_EXPORT_DATA = 'admin_export_data'
    
    # Broadcast
    ADMIN_BROADCAST = 'admin_broadcast'
    ADMIN_CREATE_BROADCAST = 'admin_create_broadcast'
    ADMIN_BROADCAST_HISTORY = 'admin_broadcast_history'
    ADMIN_BROADCAST_STATS = 'admin_broadcast_stats'
    ADMIN_BROADCAST_SETTINGS = 'admin_broadcast_settings'
    ADMIN_CONFIRM_BROADCAST = 'admin_confirm_broadcast'
    
    # Manutenção
    ADMIN_MAINTENANCE = 'admin_maintenance'
    ADMIN_CLEANUP = 'admin_cleanup'
    ADMIN_BACKUP = 'admin_backup'
    ADMIN_OPTIMIZE_DB = 'admin_optimize_db'
    ADMIN_RESTART = 'admin_restart'
    ADMIN_CHECK_INTEGRITY = 'admin_check_integrity'
    ADMIN_REPAIR_DATA = 'admin_repair_data'
    
    # Logs
    ADMIN_LOGS = 'admin_logs'
    ADMIN_LOGS_ERRORS = 'admin_logs_errors'
    ADMIN_LOGS_WARNINGS = 'admin_logs_warnings'
    ADMIN_LOGS_INFO = 'admin_logs_info'
    ADMIN_LOGS_STATS = 'admin_logs_stats'
    ADMIN_EXPORT_LOGS = 'admin_export_logs'
    ADMIN_CLEAR_LOGS = 'admin_clear_logs'
    
    # Configurações
    ADMIN_SETTINGS = 'admin_settings'
    SYSTEM_CONFIG = 'admin_system_config'
    FEATURE_FLAGS = 'admin_feature_flags'

class SettingsCallbacks:
    """Callbacks de configurações."""
    
    # Menu principal
    SETTINGS_MENU = 'settings_menu'
    
    # Perfil
    EDIT_PROFILE = 'settings_edit_profile'
    CHANGE_PHOTO = 'settings_change_photo'
    EDIT_BIO = 'settings_edit_bio'
    EDIT_INTERESTS = 'settings_edit_interests'
    
    # Privacidade
    PRIVACY = 'settings_privacy'
    BLOCK_LIST = 'settings_block_list'
    VISIBILITY = 'settings_visibility'
    
    # Notificações
    NOTIFICATIONS = 'settings_notifications'
    PUSH_NOTIFICATIONS = 'settings_push_notifications'
    EMAIL_NOTIFICATIONS = 'settings_email_notifications'
    
    # Conta
    ACCOUNT = 'settings_account'
    CHANGE_PASSWORD = 'settings_change_password'
    DELETE_ACCOUNT = 'settings_delete_account'
    
    # Configurações específicas
    PIX = 'settings_pix'
    DATA = 'settings_data'
    STATS = 'settings_stats'
    APPEARANCE = 'settings_appearance'
    
    # Idioma
    LANGUAGE = 'settings_language'
    LANGUAGE_PT = 'settings_language_pt'
    LANGUAGE_EN = 'settings_language_en'
    LANGUAGE_ES = 'settings_language_es'

class FavoritesCallbacks:
    """Callbacks de favoritos."""
    
    # Menu principal
    FAVORITES_MENU = 'favorites_menu'
    
    # Ações
    ADD_FAVORITE = 'favorites_add_'
    REMOVE_FAVORITE = 'favorites_remove_'
    VIEW_FAVORITE = 'favorites_view_'
    
    # Categorias
    POSTS = 'favorites_posts'
    USERS = 'favorites_users'
    CONTENT = 'favorites_content'
    
    # Navegação
    NEXT_PAGE = 'favorites_next_page'
    PREV_PAGE = 'favorites_prev_page'
    
    # Ações específicas
    CLEAR = 'favorites_clear'

class LGPDCallbacks:
    """Callbacks relacionados à LGPD."""
    
    # Menu principal
    MENU = 'lgpd_menu'
    
    # Exportação de dados
    EXPORT = 'lgpd_export_data'
    EXPORT_CONFIRM = 'lgpd_export_confirm'
    DOWNLOAD_DATA = 'lgpd_download_data'
    
    # Exclusão de conta
    DELETE = 'lgpd_delete_account'
    DELETE_CONFIRM = 'lgpd_delete_confirm'
    DELETE_FINAL = 'lgpd_delete_final'
    
    # Política de privacidade
    PRIVACY = 'lgpd_privacy_policy'
    TERMS = 'lgpd_terms_of_service'
    
    # Consentimentos
    CONSENT_MENU = 'lgpd_consent_menu'
    REVOKE_CONSENT = 'lgpd_revoke_consent'
    UPDATE_CONSENT = 'lgpd_update_consent'

class OnboardingCallbacks:
    """Callbacks do processo de onboarding."""
    
    # Início do processo
    START = 'onboarding_start'
    RESTART = 'onboarding_restart'
    
    # Termos LGPD
    ACCEPT_TERMS = 'onboarding_accept_terms'
    REJECT_TERMS = 'onboarding_reject_terms'
    
    # Seleção de estado
    STATE_PREFIX = 'onboarding_state_'
    
    # Seleção de categoria
    CATEGORY_PREFIX = 'onboarding_category_'
    
    # Navegação
    SKIP = 'onboarding_skip'
    BACK = 'onboarding_back'
    CONTINUE = 'onboarding_continue'
    
    # Finalização
    COMPLETE = 'onboarding_complete'
    CANCEL = 'onboarding_cancel'
    
    # Confirmação de idade
    CONFIRM_AGE = 'onboarding_confirm_age'
    REJECT_AGE = 'onboarding_reject_age'
    
    # Seleção de gênero
    GENDER_MALE = 'onboarding_gender_male'
    GENDER_FEMALE = 'onboarding_gender_female'
    GENDER_OTHER = 'onboarding_gender_other'
    GENDER_PREFER_NOT_SAY = 'onboarding_gender_prefer_not_say'