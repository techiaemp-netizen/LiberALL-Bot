"""Configurações do Bot LiberALL"""
import os
import json
from dotenv import load_dotenv
from core.env_config import env_config

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Bot
BOT_TOKEN = env_config.telegram_token
TELEGRAM_TOKEN = BOT_TOKEN  # Alias para compatibilidade
BOT_USERNAME = os.getenv('BOT_USERNAME', 'LiberALL_bot')
DEBUG = env_config.debug_mode
FIREBASE_SIMULATION = env_config.firebase_simulation
ENVIRONMENT = env_config.environment

# IDs dos grupos
FREEMIUM_GROUP_ID = int(os.getenv('FREEMIUM_GROUP_ID', '-1002620620239'))
LITE_GROUP_ID = FREEMIUM_GROUP_ID  # Alias para compatibilidade
PREMIUM_GROUP_ID = int(os.getenv('PREMIUM_GROUP_ID', '-1002680323844'))
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '123456789'))

# Configurações do Firebase
FIREBASE_DATABASE_URL = env_config.firebase_database_url
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './firebase_credentials.json')

# Configurações do Cloudinary
CLOUDINARY_CLOUD_NAME = env_config.cloudinary_cloud_name
CLOUDINARY_API_KEY = env_config.cloudinary_api_key
CLOUDINARY_API_SECRET = env_config.cloudinary_api_secret
CLOUDINARY_URL = f"cloudinary://{CLOUDINARY_API_KEY}:{CLOUDINARY_API_SECRET}@{CLOUDINARY_CLOUD_NAME}"

# Configurações do WebApp
# Temporariamente usando URL HTTPS pública para WebApp funcionar
APP_BASE_URL = os.getenv('APP_BASE_URL', 'https://httpbin.org')

# Configurações de Rede e Timeout
NETWORK_CONFIG = {
    'polling_timeout': int(os.getenv('POLLING_TIMEOUT', '60')),
    'long_polling_timeout': int(os.getenv('LONG_POLLING_TIMEOUT', '60')),
    'polling_interval': int(os.getenv('POLLING_INTERVAL', '2')),
    'max_retries': int(os.getenv('MAX_RETRIES', '5')),
    'retry_backoff_base': int(os.getenv('RETRY_BACKOFF_BASE', '30')),
    'max_retry_wait': int(os.getenv('MAX_RETRY_WAIT', '300')),
    'skip_pending': os.getenv('SKIP_PENDING', 'True').lower() == 'true'
}

# Configurações de planos
PLANS = {
    'lite': {
        'name': 'Lite',
        'price': 0.0,
        'message_limit': 5,
        'gallery_limit': 3,
        'features': ['Mensagens limitadas', 'Galeria limitada', 'Conteúdo com blur']
    },
    'premium': {
        'name': 'Premium',
        'price': 9.99,
        'message_limit': -1,  # Ilimitado
        'gallery_limit': -1,  # Ilimitado
        'features': ['Mensagens ilimitadas', 'Galeria ilimitada', 'Conteúdo sem blur', 'Match prioritário']
    },
    'diamond': {
        'name': 'Diamond',
        'price': 19.99,
        'message_limit': -1,  # Ilimitado
        'gallery_limit': -1,  # Ilimitado
        'features': ['Tudo do Premium', 'Modo invisível', 'Destaque nas postagens', 'Etiqueta 💎']
    }
}

# Configurações de monetização
MONETIZATION = {
    'platform_fee': 0.20,  # 20% para a plataforma
    'creator_percentage': 0.80,  # 80% para o criador
    'affiliate_commission': 0.20,  # 20% de comissão de afiliado
    'message_packages': {
        '10': 2.99,
        '50': 4.99,
        '100': 8.99
    }
}

# Categorias disponíveis
CATEGORIES = {
    'solteiro': {'emoji': '👨', 'name': 'Solteiro'},
    'solteira': {'emoji': '👩', 'name': 'Solteira'},
    'casal': {'emoji': '👩‍❤️‍👨', 'name': 'Casal'},
    'casal_mm': {'emoji': '👩‍❤️‍👩', 'name': 'Casal: Mulher-Mulher'},
    'casal_hh': {'emoji': '👨‍❤️‍👨', 'name': 'Casal: Homem-Homem'},
    'casal_bi': {'emoji': '💋', 'name': 'Casal BI'},
    'hotwife': {'emoji': '🔥', 'name': 'Casada Hotwife'},
    'cuckold': {'emoji': '👀', 'name': 'Cuckold'},
    'trans': {'emoji': '🏳️‍🌈', 'name': 'Trans'},
    'fluido': {'emoji': '🌊', 'name': 'Fluido(a)'},
    'intenso': {'emoji': '🔥', 'name': 'Intenso(a)'},
    'curioso': {'emoji': '❓', 'name': 'Curioso(a)'},
    'casado': {'emoji': '💍', 'name': 'Casado(a)'},
    'criador': {'emoji': '🎥', 'name': 'Criador(a) de Conteúdo'},
    'nao_binarie': {'emoji': '🌀', 'name': 'Não-binárie'},
    'poliamorista': {'emoji': '🔗', 'name': 'Poliamorista'},
    'demissexual': {'emoji': '🧠', 'name': 'Demissexual'}
}

# Estados brasileiros
BRAZILIAN_STATES = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

# Configurações de karma e gamificação
KARMA_LEVELS = {
    0: {'name': 'Novato', 'emoji': '🌱'},
    100: {'name': 'Liberal', 'emoji': '🌟'},
    500: {'name': 'Veterano', 'emoji': '🏆'},
    1000: {'name': 'Lenda', 'emoji': '👑'}
}

# Emojis de reação
REACTION_EMOJIS = ['🌶️', '🔥', '🍆', '🍑', '👅']

# Configurações de match
MATCH_CONFIG = {
    'room_duration': 3600,  # 1 hora em segundos
    'queue_timeout': 300,   # 5 minutos em segundos
    'compatibility_rules': {
        'same_state': False,  # Evitar mesmo estado para diversidade
        'compatible_categories': {
            'solteiro': ['solteira', 'trans', 'fluido', 'curioso'],
            'solteira': ['solteiro', 'trans', 'fluido', 'curioso'],
            'casal': ['casal', 'solteiro', 'solteira', 'trans'],
            'trans': ['solteiro', 'solteira', 'casal', 'fluido'],
            'fluido': ['solteiro', 'solteira', 'trans', 'curioso'],
            'curioso': ['solteiro', 'solteira', 'fluido', 'intenso']
        }
    }
}

# Configurações de jobs
JOB_CONFIG = {
    'matchmaking_interval': 30,      # 30 segundos
    'cleanup_interval': 900,         # 15 minutos
    'quota_reset_cron': '0 0 1 * *'  # Todo dia 1 do mês às 00:00
}

# Mensagens padrão
MESSAGES = {
    'welcome': "🎉 Bem-vindo ao LiberALL! Um espaço seguro, anônimo e divertido para conexões liberais.",
    'age_verification': "Para continuar, confirme que você tem 18 anos ou mais. Digite sua idade:",
    'underage': "❌ Desculpe, o LiberALL é restrito a maiores de 18 anos.",
    'terms_acceptance': "📋 Você precisa aceitar nossos Termos de Uso e Política de Privacidade para continuar.",
    'monetization_blur': "💰 Adquira o conteúdo por: R$ {price:.2f}\n👉 Compre agora: {link}\n✨ Assine o Premium e acesse tudo sem limites! ✨\nMensagens e matches ilimitados por apenas R$ {premium_price:.2f}/mês.\n👉 Assine aqui: {affiliate_link}"
}

# Validação de configurações obrigatórias
def validate_config():
    """Valida se todas as configurações obrigatórias estão presentes"""
    required_vars = [
        'BOT_TOKEN',
        'FREEMIUM_GROUP_ID',
        'PREMIUM_GROUP_ID',
        'CLOUDINARY_CLOUD_NAME',
        'CLOUDINARY_API_KEY',
        'CLOUDINARY_API_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = globals().get(var)
        # Mascarar valores sensíveis nos logs
        if 'TOKEN' in var or 'SECRET' in var or 'KEY' in var:
            masked_value = f"{str(value)[:4]}...{str(value)[-4:]}" if value and len(str(value)) > 8 else "***"
            print(f"Debug: {var} = {masked_value}")
        else:
            print(f"Debug: {var} = {value}")
        if not value:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
    
    return True

class Config:
    """Classe de configuração para facilitar acesso às configurações"""
    
    def __init__(self):
        # Bot settings
        self.BOT_TOKEN = BOT_TOKEN
        self.TELEGRAM_TOKEN = TELEGRAM_TOKEN
        self.BOT_USERNAME = BOT_USERNAME
        self.DEBUG = DEBUG
        self.FIREBASE_SIMULATION = FIREBASE_SIMULATION
        
        # Group IDs
        self.FREEMIUM_GROUP_ID = FREEMIUM_GROUP_ID
        self.LITE_GROUP_ID = LITE_GROUP_ID
        self.PREMIUM_GROUP_ID = PREMIUM_GROUP_ID
        self.ADMIN_CHAT_ID = ADMIN_CHAT_ID
        
        # Firebase settings
        self.FIREBASE_DATABASE_URL = FIREBASE_DATABASE_URL
        self.GOOGLE_APPLICATION_CREDENTIALS = GOOGLE_APPLICATION_CREDENTIALS
        
        # Cloudinary settings
        self.CLOUDINARY_CLOUD_NAME = CLOUDINARY_CLOUD_NAME
        self.CLOUDINARY_API_KEY = CLOUDINARY_API_KEY
        self.CLOUDINARY_API_SECRET = CLOUDINARY_API_SECRET
        self.CLOUDINARY_URL = CLOUDINARY_URL
        
        # WebApp settings
        self.APP_BASE_URL = APP_BASE_URL
        
        # Other settings
        self.PLANS = PLANS
        self.MONETIZATION = MONETIZATION
        self.CATEGORIES = CATEGORIES
        self.BRAZILIAN_STATES = BRAZILIAN_STATES
        self.KARMA_LEVELS = KARMA_LEVELS
        self.REACTION_EMOJIS = REACTION_EMOJIS
        self.MATCH_CONFIG = MATCH_CONFIG
        self.JOB_CONFIG = JOB_CONFIG
        self.MESSAGES = MESSAGES

def get_config():
    """Retorna uma instância da configuração"""
    return Config()

# Executa validação ao importar
if __name__ != '__main__':
    validate_config()