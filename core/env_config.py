import os
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

logger = logging.getLogger(__name__)

class EnvironmentConfig:
    """Classe para gerenciar configurações de ambiente obrigatórias."""
    
    # Variáveis obrigatórias
    REQUIRED_VARS = {
        'TELEGRAM_BOT_TOKEN': 'Token do bot do Telegram',
        'FIREBASE_PROJECT_ID': 'ID do projeto Firebase',
        'FIREBASE_DATABASE_URL': 'URL do banco de dados Firebase',
        'ENCRYPTION_KEY': 'Chave de criptografia para dados sensíveis',
        'JWT_SECRET': 'Chave secreta para JWT',
        'CLOUDINARY_CLOUD_NAME': 'Nome da nuvem Cloudinary',
        'CLOUDINARY_API_KEY': 'Chave da API Cloudinary',
        'CLOUDINARY_API_SECRET': 'Segredo da API Cloudinary'
    }
    
    # Variáveis opcionais com valores padrão
    OPTIONAL_VARS = {
        'DEBUG_MODE': 'False',
        'LOG_LEVEL': 'INFO',
        'FIREBASE_SIMULATION': 'False',
        'MAX_USERS_PER_QUERY': '100',
        'SESSION_TIMEOUT': '3600',
        'POLLING_TIMEOUT': '60',
        'LONG_POLLING_TIMEOUT': '60',
        'POLLING_INTERVAL': '2',
        'MAX_RETRIES': '5',
        'RETRY_BACKOFF_BASE': '30',
        'MAX_RETRY_WAIT': '300',
        'SKIP_PENDING': 'True',
        'ENVIRONMENT': 'development',
        'BOT_VERSION': '1.0.0',
        # Stripe Payment (opcional)
        'ENABLE_STRIPE': 'False',
        'STRIPE_SECRET_KEY': '',
        'STRIPE_PUBLISHABLE_KEY': '',
        'STRIPE_WEBHOOK_SECRET': '',
        # Stripe Connect (opcional)
        'ENABLE_STRIPE_CONNECT': 'False',
        'STRIPE_CONNECT_ACCOUNT_ID': ''
    }
    
    def __init__(self):
        self._config = {}
        self._load_environment()
    
    def _load_environment(self) -> None:
        """Carrega e valida variáveis de ambiente."""
        missing_vars = []
        
        # Verificar variáveis obrigatórias
        for var_name, description in self.REQUIRED_VARS.items():
            value = os.getenv(var_name)
            if not value:
                missing_vars.append(f"{var_name} ({description})")
                logger.error(f"Missing required environment variable: {var_name}")
            else:
                self._config[var_name] = value
        
        # Carregar variáveis opcionais
        for var_name, default_value in self.OPTIONAL_VARS.items():
            self._config[var_name] = os.getenv(var_name, default_value)
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.critical(error_msg)
            raise EnvironmentError(error_msg)
        
        logger.info("Environment configuration loaded successfully")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Obter valor de configuração."""
        return self._config.get(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Obter valor booleano de configuração."""
        value = self.get(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Obter valor inteiro de configuração."""
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default
    
    def validate_config(self) -> Dict[str, Any]:
        """Validar configuração atual."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validar token do Telegram
        telegram_token = self.get('TELEGRAM_BOT_TOKEN')
        if telegram_token:
            from utils.validators import validate_telegram_token
            if not validate_telegram_token(telegram_token):
                validation_result['warnings'].append('Telegram token format is invalid')
            
            # Detectar tokens de teste/desenvolvimento
            if self._is_test_telegram_token(telegram_token):
                validation_result['warnings'].append('Using test/development Telegram token - bot may not work properly')
                logger.warning("⚠️ Test Telegram token detected - switching to simulation mode")
        
        # Validar configurações do Firebase
        firebase_project_id = self.get('FIREBASE_PROJECT_ID')
        if firebase_project_id and len(firebase_project_id) < 6:
            validation_result['errors'].append('Firebase project ID seems too short')
            validation_result['valid'] = False
        
        # Validar chave de criptografia
        encryption_key = self.get('ENCRYPTION_KEY')
        if encryption_key and len(encryption_key) < 32:
            validation_result['errors'].append('Encryption key should be at least 32 characters')
            validation_result['valid'] = False
        
        return validation_result
    
    def _is_test_telegram_token(self, token: str) -> bool:
        """Detectar se o token do Telegram é de teste/desenvolvimento."""
        test_patterns = [
            'your_bot_token_here',
            'test_token',
            'fake_token',
            'development_token',
            'bot_token_placeholder',
            'replace_with_real_token'
        ]
        
        token_lower = token.lower()
        
        # Verificar padrões de teste
        for pattern in test_patterns:
            if pattern in token_lower:
                return True
        
        # Verificar se é muito curto (tokens reais têm pelo menos 45 caracteres)
        if len(token) < 30:
            return True
        
        # Verificar se contém apenas caracteres de exemplo
        if token.count('x') > 10 or token.count('0') > 10:
            return True
        
        return False
    
    def create_env_template(self) -> str:
        """Criar template de arquivo .env."""
        template_lines = [
            "# LiberALL Bot Environment Configuration",
            "# Copy this file to .env and fill in your actual values",
            "",
            "# Required Variables"
        ]
        
        for var_name, description in self.REQUIRED_VARS.items():
            template_lines.append(f"# {description}")
            template_lines.append(f"{var_name}=your_{var_name.lower()}_here")
            template_lines.append("")
        
        template_lines.append("# Optional Variables (with defaults)")
        for var_name, default_value in self.OPTIONAL_VARS.items():
            template_lines.append(f"{var_name}={default_value}")
        
        return "\n".join(template_lines)
    
    @property
    def telegram_token(self) -> str:
        """Token do bot do Telegram."""
        return self.get('TELEGRAM_BOT_TOKEN')
    
    @property
    def firebase_project_id(self) -> str:
        """ID do projeto Firebase."""
        return self.get('FIREBASE_PROJECT_ID')
    
    @property
    def firebase_private_key(self) -> str:
        """Chave privada do Firebase."""
        return self.get('FIREBASE_PRIVATE_KEY')
    
    @property
    def firebase_client_email(self) -> str:
        """Email do cliente Firebase."""
        return self.get('FIREBASE_CLIENT_EMAIL')
    
    @property
    def encryption_key(self) -> str:
        """Chave de criptografia."""
        return self.get('ENCRYPTION_KEY')
    
    @property
    def debug_mode(self) -> bool:
        """Modo de debug."""
        return self.get_bool('DEBUG_MODE')
    
    @property
    def firebase_simulation(self) -> bool:
        """Modo de simulação do Firebase."""
        return self.get_bool('FIREBASE_SIMULATION')
    
    @property
    def log_level(self) -> str:
        """Nível de log."""
        return self.get('LOG_LEVEL', 'INFO')
    
    @property
    def max_users_per_query(self) -> int:
        """Máximo de usuários por consulta."""
        return self.get_int('MAX_USERS_PER_QUERY', 100)
    
    @property
    def session_timeout(self) -> int:
        """Timeout da sessão em segundos."""
        return self.get_int('SESSION_TIMEOUT', 3600)
    
    @property
    def network_config(self):
        """Configurações de rede e polling."""
        class NetworkConfig:
            def __init__(self, env_config):
                self.polling_timeout = env_config.get_int('POLLING_TIMEOUT', 60)
                self.long_polling_timeout = env_config.get_int('LONG_POLLING_TIMEOUT', 60)
                self.polling_interval = env_config.get_int('POLLING_INTERVAL', 2)
                self.max_retries = env_config.get_int('MAX_RETRIES', 5)
                self.retry_backoff_base = env_config.get_int('RETRY_BACKOFF_BASE', 30)
                self.max_retry_wait = env_config.get_int('MAX_RETRY_WAIT', 300)
                self.skip_pending = env_config.get_bool('SKIP_PENDING', True)
        
        return NetworkConfig(self)
    
    @property
    def environment(self) -> str:
        """Ambiente de execução."""
        return self.get('ENVIRONMENT', 'development')
    
    @property
    def bot_version(self) -> str:
        """Versão do bot."""
        return self.get('BOT_VERSION', '1.0.0')
    
    @property
    def firebase_database_url(self) -> str:
        """URL do banco de dados Firebase."""
        return self.get('FIREBASE_DATABASE_URL')
    
    @property
    def jwt_secret(self) -> str:
        """Chave secreta para JWT."""
        return self.get('JWT_SECRET')
    
    @property
    def cloudinary_cloud_name(self) -> str:
        """Nome da nuvem Cloudinary."""
        return self.get('CLOUDINARY_CLOUD_NAME')
    
    @property
    def cloudinary_api_key(self) -> str:
        """Chave da API Cloudinary."""
        return self.get('CLOUDINARY_API_KEY')
    
    @property
    def cloudinary_api_secret(self) -> str:
        """Segredo da API Cloudinary."""
        return self.get('CLOUDINARY_API_SECRET')

# Instância global
try:
    env_config = EnvironmentConfig()
except EnvironmentError as e:
    logger.critical(f"Failed to load environment configuration: {e}")
    # Criar template de .env se não existir
    env_template_path = os.path.join(os.path.dirname(__file__), '..', '.env.template')
    if not os.path.exists(env_template_path):
        temp_config = EnvironmentConfig.__new__(EnvironmentConfig)
        with open(env_template_path, 'w', encoding='utf-8') as f:
            f.write(temp_config.create_env_template())
        logger.info(f"Created .env template at {env_template_path}")
    raise