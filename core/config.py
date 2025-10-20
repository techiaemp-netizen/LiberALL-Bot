"""Configurações centralizadas e gerenciamento de variáveis de ambiente."""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Configurações do bot Telegram."""
    token: str
    webhook_url: Optional[str] = None
    webhook_port: int = 8443
    debug: bool = False

@dataclass
class FirebaseConfig:
    """Configurações do Firebase."""
    credentials_path: str
    database_url: str
    storage_bucket: str

@dataclass
class SecurityConfig:
    """Configurações de segurança."""
    encryption_key: str
    jwt_secret: str
    rate_limit_per_minute: int = 30
    max_file_size_mb: int = 10

@dataclass
class PaymentConfig:
    """Configurações de pagamento."""
    pix_provider_api_key: str
    webhook_secret: str
    min_withdrawal_amount: float = 10.0
    max_withdrawal_amount: float = 1000.0

@dataclass
class NetworkConfig:
    """Configurações de rede e polling."""
    polling_timeout: int = 60
    long_polling_timeout: int = 60
    polling_interval: int = 2
    max_retries: int = 5
    retry_backoff_base: int = 30
    max_retry_wait: int = 300
    skip_pending: bool = True

class ConfigManager:
    """Gerenciador centralizado de configurações."""
    
    def __init__(self):
        self._bot_config: Optional[BotConfig] = None
        self._firebase_config: Optional[FirebaseConfig] = None
        self._security_config: Optional[SecurityConfig] = None
        self._payment_config: Optional[PaymentConfig] = None
        self._network_config: Optional[NetworkConfig] = None
        self._missing_vars: list = []
        self._required_env_vars = [
            'TELEGRAM_BOT_TOKEN',
            'FIREBASE_CREDENTIALS_PATH',
            'FIREBASE_DATABASE_URL',
            'FIREBASE_STORAGE_BUCKET',
            'ENCRYPTION_KEY',
            'JWT_SECRET',
            'PIX_PROVIDER_API_KEY',
            'WEBHOOK_SECRET'
        ]
        self._validate_required_environment()
    
    def _validate_required_environment(self) -> None:
        """Valida se todas as variáveis obrigatórias estão configuradas"""
        # Lista de variáveis obrigatórias
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'FIREBASE_PROJECT_ID', 
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL',
            'CLOUDINARY_CLOUD_NAME',
            'CLOUDINARY_API_KEY', 
            'CLOUDINARY_API_SECRET',
            'JWT_SECRET',
            'FERNET_KEY',
            'WEBHOOK_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.strip() == '' or 'your_' in value.lower():
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = (
                f"❌ Variáveis de ambiente obrigatórias não configuradas:\n\n"
                f"{'  - ' + chr(10) + '  - '.join(missing_vars)}\n\n"
                f"📋 INSTRUÇÕES:\n"
                f"1. Copie o arquivo .env.example para .env\n"
                f"2. Substitua os valores 'your_*_here' pelos valores reais\n"
                f"3. Consulte o .env.example para instruções detalhadas\n\n"
                f"🔒 SEGURANÇA: Nunca commite o arquivo .env no git!"
            )
            raise ValueError(error_msg)
    
    def validate_environment(self) -> Dict[str, bool]:
        """Valida se todas as variáveis de ambiente obrigatórias estão definidas."""
        validation_result = {}
        missing_vars = []
        
        for var in self._required_env_vars:
            value = os.getenv(var)
            is_valid = bool(value and value.strip() and value != 'your_key_here')
            validation_result[var] = is_valid
            
            if not is_valid:
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Variáveis de ambiente obrigatórias não configuradas: {missing_vars}")
            logger.error("Configure as variáveis no arquivo .env ou nas variáveis do sistema")
        
        return validation_result
    
    def get_missing_env_vars(self) -> list:
        """Retorna lista de variáveis de ambiente não configuradas."""
        validation = self.validate_environment()
        return [var for var, is_valid in validation.items() if not is_valid]
    
    @property
    def bot_config(self) -> BotConfig:
        """Configurações do bot Telegram."""
        if self._bot_config is None:
            token = self._get_required_env('TELEGRAM_BOT_TOKEN')
            webhook_url = os.getenv('WEBHOOK_URL')
            webhook_port = int(os.getenv('WEBHOOK_PORT', '8443'))
            debug = os.getenv('DEBUG', 'false').lower() == 'true'
            
            self._bot_config = BotConfig(
                token=token,
                webhook_url=webhook_url,
                webhook_port=webhook_port,
                debug=debug
            )
        
        return self._bot_config
    
    @property
    def firebase_config(self) -> FirebaseConfig:
        """Configurações do Firebase."""
        if self._firebase_config is None:
            credentials_path = self._get_required_env('FIREBASE_CREDENTIALS_PATH')
            database_url = self._get_required_env('FIREBASE_DATABASE_URL')
            storage_bucket = self._get_required_env('FIREBASE_STORAGE_BUCKET')
            
            self._firebase_config = FirebaseConfig(
                credentials_path=credentials_path,
                database_url=database_url,
                storage_bucket=storage_bucket
            )
        
        return self._firebase_config
    
    @property
    def security_config(self) -> SecurityConfig:
        """Configurações de segurança."""
        if self._security_config is None:
            encryption_key = self._get_required_env('ENCRYPTION_KEY')
            jwt_secret = self._get_required_env('JWT_SECRET')
            rate_limit = int(os.getenv('RATE_LIMIT_PER_MINUTE', '30'))
            max_file_size = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
            
            self._security_config = SecurityConfig(
                encryption_key=encryption_key,
                jwt_secret=jwt_secret,
                rate_limit_per_minute=rate_limit,
                max_file_size_mb=max_file_size
            )
        
        return self._security_config
    
    @property
    def payment_config(self) -> PaymentConfig:
        """Configurações de pagamento."""
        if self._payment_config is None:
            api_key = self._get_required_env('PIX_PROVIDER_API_KEY')
            webhook_secret = self._get_required_env('WEBHOOK_SECRET')
            min_withdrawal = float(os.getenv('MIN_WITHDRAWAL_AMOUNT', '10.0'))
            max_withdrawal = float(os.getenv('MAX_WITHDRAWAL_AMOUNT', '1000.0'))
            
            self._payment_config = PaymentConfig(
                pix_provider_api_key=api_key,
                webhook_secret=webhook_secret,
                min_withdrawal_amount=min_withdrawal,
                max_withdrawal_amount=max_withdrawal
            )
        
        return self._payment_config
    
    @property
    def network_config(self) -> NetworkConfig:
        """Configurações de rede e polling."""
        if self._network_config is None:
            polling_timeout = int(os.getenv('POLLING_TIMEOUT', '60'))
            long_polling_timeout = int(os.getenv('LONG_POLLING_TIMEOUT', '60'))
            polling_interval = int(os.getenv('POLLING_INTERVAL', '2'))
            max_retries = int(os.getenv('MAX_RETRIES', '5'))
            retry_backoff_base = int(os.getenv('RETRY_BACKOFF_BASE', '30'))
            max_retry_wait = int(os.getenv('MAX_RETRY_WAIT', '300'))
            skip_pending = os.getenv('SKIP_PENDING', 'True').lower() == 'true'
            
            self._network_config = NetworkConfig(
                polling_timeout=polling_timeout,
                long_polling_timeout=long_polling_timeout,
                polling_interval=polling_interval,
                max_retries=max_retries,
                retry_backoff_base=retry_backoff_base,
                max_retry_wait=max_retry_wait,
                skip_pending=skip_pending
            )
        
        return self._network_config
    
    def _get_required_env(self, var_name: str) -> str:
        """Obtém variável de ambiente obrigatória."""
        value = os.getenv(var_name)
        
        if not value or value.strip() == '' or value == 'your_key_here':
            self._missing_vars.append(var_name)
            raise ValueError(
                f"Variável de ambiente obrigatória não configurada: {var_name}\n"
                f"Configure no arquivo .env ou nas variáveis do sistema.\n"
                f"Consulte o arquivo .env.example para mais informações."
            )
        
        return value.strip()
    
    def _get_optional_env(self, key: str, default: str = '') -> str:
        """Obtém variável de ambiente opcional com valor padrão"""
        return os.getenv(key, default)
    
    def get_env_template(self) -> str:
        """Retorna template do arquivo .env com todas as variáveis necessárias."""
        template = """
# Configurações do Bot Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_PORT=8443
DEBUG=false

# Configurações do Firebase
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-project.appspot.com

# Configurações de Segurança
ENCRYPTION_KEY=your_32_character_encryption_key_here
JWT_SECRET=your_jwt_secret_key_here
RATE_LIMIT_PER_MINUTE=30
MAX_FILE_SIZE_MB=10

# Configurações de Pagamento
PIX_PROVIDER_API_KEY=your_pix_api_key_here
WEBHOOK_SECRET=your_webhook_secret_here
MIN_WITHDRAWAL_AMOUNT=10.0
MAX_WITHDRAWAL_AMOUNT=1000.0

# Stripe (Opcional)
ENABLE_STRIPE=false
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Connect (Opcional)
ENABLE_STRIPE_CONNECT=false
STRIPE_CONNECT_ACCOUNT_ID=acct_your_connect_account_id_here
"""
        return template.strip()
    
    def create_env_file_if_missing(self) -> bool:
        """Cria arquivo .env se não existir."""
        env_path = '.env'
        
        if not os.path.exists(env_path):
            try:
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(self.get_env_template())
                
                logger.info(f"Arquivo .env criado em: {os.path.abspath(env_path)}")
                logger.warning("IMPORTANTE: Configure as variáveis no arquivo .env antes de executar o bot!")
                return True
            
            except Exception as e:
                logger.error(f"Erro ao criar arquivo .env: {e}")
                return False
        
        return False
    
    def load_env_file(self) -> bool:
        """Carrega variáveis do arquivo .env."""
        env_path = '.env'
        
        if not os.path.exists(env_path):
            return False
        
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # Só define se não estiver já definida no sistema
                        if key and not os.getenv(key):
                            os.environ[key] = value
            
            logger.info("Variáveis de ambiente carregadas do arquivo .env")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo .env: {e}")
            return False
    
    def get_config_status(self) -> Dict[str, Any]:
        """Retorna status das configurações."""
        validation = self.validate_environment()
        missing_vars = self.get_missing_env_vars()
        
        return {
            'all_configured': len(missing_vars) == 0,
            'missing_variables': missing_vars,
            'validation_details': validation,
            'env_file_exists': os.path.exists('.env'),
            'total_required': len(self._required_env_vars),
            'configured_count': len(self._required_env_vars) - len(missing_vars)
        }

# Classe Config para compatibilidade com código existente
class Config:
    """Classe de configuração para compatibilidade."""
    
    def __init__(self):
        self.manager = ConfigManager()
    
    @property
    def bot_config(self):
        return self.manager.bot_config
    
    @property
    def firebase_config(self):
        return self.manager.firebase_config
    
    @property
    def security_config(self):
        return self.manager.security_config
    
    @property
    def payment_config(self):
        return self.manager.payment_config
    
    @property
    def network_config(self):
        return self.manager.network_config

# Instância global do gerenciador de configurações
config_manager = ConfigManager()

# Instância global da classe Config para compatibilidade
config = Config()

# Carrega variáveis do .env se existir
config_manager.load_env_file()

# Cria .env se não existir
config_manager.create_env_file_if_missing()