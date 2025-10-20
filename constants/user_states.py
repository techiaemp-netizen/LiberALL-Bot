"""Constantes de estados do usuário."""

class UserStates:
    """Estados possíveis do usuário no sistema."""
    
    # Estados básicos
    IDLE = 'idle'
    ACTIVE = 'active'
    ONBOARDING = 'onboarding'
    MENU = 'menu'
    
    # Estados específicos do onboarding (fluxo revisado)
    AWAITING_AGE_INPUT = 'awaiting_age_input'
    AWAITING_RULES_AGREEMENT = 'awaiting_rules_agreement'
    AWAITING_TERMS_AGREEMENT = 'awaiting_terms_agreement'
    AWAITING_LGPD_AGREEMENT = 'awaiting_lgpd_agreement'
    AWAITING_PROFILE_TYPE = 'awaiting_profile_type'
    AWAITING_CODENAME = 'awaiting_codename'
    AWAITING_RELATIONSHIP_PROFILES = 'awaiting_relationship_profiles'
    AWAITING_LOCATION = 'awaiting_location'
    AWAITING_CONTENT_CREATOR_CHOICE = 'awaiting_content_creator_choice'
    AWAITING_MONETIZATION_CHOICE = 'awaiting_monetization_choice'
    AWAITING_PIX_KEY = 'awaiting_pix_key'
    AWAITING_GROUP_CHOICE = 'awaiting_group_choice'
    
    # Estados antigos mantidos para compatibilidade
    AWAITING_GENDER = 'awaiting_gender'
    AWAITING_AGE = 'awaiting_age'
    AWAITING_AGE_CONFIRMATION = 'awaiting_age_confirmation'
    AWAITING_PRIVACY_AGREEMENT = 'awaiting_privacy_agreement'
    AWAITING_CATEGORY = 'awaiting_category'
    AWAITING_BIO = 'awaiting_bio'
    AWAITING_INTERESTS = 'awaiting_interests'
    AWAITING_PHOTOS = 'awaiting_photos'
    WAITING_POST_CONFIRMATION = 'waiting_post_confirmation'
    
    # Estados de postagem
    POSTING = 'posting'
    POSTING_CONTENT = 'posting_content'
    POSTING_TYPE_SELECTION = 'posting_type_selection'
    POSTING_REVIEW = 'posting_review'
    CREATING_POST_CAPTION = 'creating_post_caption'
    AWAITING_POST_MEDIA = 'awaiting_post_media'
    AWAITING_POST_CONFIRMATION = 'awaiting_post_confirmation'
    AWAITING_POST_CONTENT = 'awaiting_post_content'
    AWAITING_POST_ACTION = 'awaiting_post_action'
    
    # Estados de configuração
    SETTINGS = 'settings'
    PROFILE_EDIT = 'profile_edit'
    PRIVACY_SETTINGS = 'privacy_settings'
    
    # Estados de match
    MATCHING = 'matching'
    MATCH_FILTERS = 'match_filters'
    MATCH_CONVERSATION = 'match_conversation'
    
    # Estados de monetização
    MONETIZATION = 'monetization'
    AWAITING_MONETIZATION_VALUE = 'awaiting_monetization_value'
    PAYMENT_PROCESSING = 'payment_processing'
    SUBSCRIPTION_MANAGEMENT = 'subscription_management'
    
    # Estados de comentários
    AWAITING_COMMENT = 'awaiting_comment'
    COMMENTING = 'commenting'
    
    # Estados de moderação
    MODERATION_REVIEW = 'moderation_review'
    CONTENT_FLAGGED = 'content_flagged'
    
    # Estados de erro
    ERROR = 'error'
    SUSPENDED = 'suspended'
    BANNED = 'banned'
    
    @classmethod
    def get_all_states(cls) -> list:
        """Retorna todos os estados disponíveis."""
        return [
            cls.IDLE, cls.ACTIVE, cls.ONBOARDING, cls.MENU,
            # Novos estados do fluxo revisado
            cls.AWAITING_AGE_INPUT, cls.AWAITING_RULES_AGREEMENT, cls.AWAITING_TERMS_AGREEMENT,
            cls.AWAITING_LGPD_AGREEMENT, cls.AWAITING_PROFILE_TYPE, cls.AWAITING_CODENAME,
            cls.AWAITING_RELATIONSHIP_PROFILES, cls.AWAITING_LOCATION, cls.AWAITING_CONTENT_CREATOR_CHOICE,
            cls.AWAITING_MONETIZATION_CHOICE, cls.AWAITING_PIX_KEY, cls.AWAITING_GROUP_CHOICE,
            # Estados antigos mantidos para compatibilidade
            cls.AWAITING_GENDER, cls.AWAITING_AGE, cls.AWAITING_AGE_CONFIRMATION, 
            cls.AWAITING_PRIVACY_AGREEMENT, cls.AWAITING_CATEGORY, cls.AWAITING_BIO, cls.AWAITING_INTERESTS, 
            cls.AWAITING_PHOTOS, cls.WAITING_POST_CONFIRMATION,
            cls.POSTING, cls.POSTING_CONTENT, cls.POSTING_TYPE_SELECTION, cls.POSTING_REVIEW,
            cls.CREATING_POST_CAPTION, cls.AWAITING_POST_MEDIA, cls.AWAITING_POST_CONFIRMATION,
            cls.AWAITING_POST_CONTENT, cls.AWAITING_POST_ACTION,
            cls.SETTINGS, cls.PROFILE_EDIT, cls.PRIVACY_SETTINGS,
            cls.MATCHING, cls.MATCH_FILTERS, cls.MATCH_CONVERSATION,
            cls.MONETIZATION, cls.AWAITING_MONETIZATION_VALUE, cls.PAYMENT_PROCESSING, cls.SUBSCRIPTION_MANAGEMENT,
            cls.AWAITING_COMMENT, cls.COMMENTING,
            cls.MODERATION_REVIEW, cls.CONTENT_FLAGGED,
            cls.ERROR, cls.SUSPENDED, cls.BANNED
        ]
    
    @classmethod
    def is_valid_state(cls, state: str) -> bool:
        """Verifica se um estado é válido."""
        return state in cls.get_all_states()