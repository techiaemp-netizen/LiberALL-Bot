"""Exceções personalizadas para o sistema."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseCustomException(Exception):
    """Classe base para exceções personalizadas."""
    
    def __init__(self, message: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.user_id = user_id
        self.details = details or {}
        super().__init__(self.message)
        
        # Log automático da exceção
        self._log_exception()
    
    def _log_exception(self):
        """Registra a exceção no log."""
        log_data = {
            'exception_type': self.__class__.__name__,
            'message': self.message,
            'user_id': self.user_id,
            'details': self.details
        }
        logger.error(f"Exception raised: {log_data}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a exceção para dicionário."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'user_id': self.user_id,
            'details': self.details
        }

class ValidationError(BaseCustomException):
    """Erro de validação de dados."""
    pass

class SecurityError(BaseCustomException):
    """Erro de segurança."""
    pass

class AuthenticationError(BaseCustomException):
    """Erro de autenticação."""
    pass

class AuthorizationError(BaseCustomException):
    """Erro de autorização."""
    pass

class RateLimitError(BaseCustomException):
    """Erro de limite de taxa."""
    pass

class DatabaseError(BaseCustomException):
    """Erro de banco de dados."""
    pass

class ExternalServiceError(BaseCustomException):
    """Erro de serviço externo."""
    pass

class ContentModerationError(BaseCustomException):
    """Erro de moderação de conteúdo."""
    pass

class PaymentError(BaseCustomException):
    """Erro de pagamento."""
    pass

class ConfigurationError(BaseCustomException):
    """Erro de configuração."""
    pass

class FileProcessingError(BaseCustomException):
    """Erro de processamento de arquivo."""
    pass

class NetworkError(BaseCustomException):
    """Erro de rede."""
    pass

class BusinessLogicError(BaseCustomException):
    """Erro de lógica de negócio."""
    pass

class UserNotFoundError(BaseCustomException):
    """Usuário não encontrado."""
    pass

class ContentNotFoundError(BaseCustomException):
    """Conteúdo não encontrado."""
    pass

class DuplicateError(BaseCustomException):
    """Erro de duplicação."""
    pass

class PermissionDeniedError(BaseCustomException):
    """Permissão negada."""
    pass

class MaintenanceModeError(BaseCustomException):
    """Sistema em manutenção."""
    pass

class FeatureDisabledError(BaseCustomException):
    """Funcionalidade desabilitada."""
    pass

# Mapeamento de códigos de erro para exceções
ERROR_CODE_MAP = {
    'VALIDATION_ERROR': ValidationError,
    'SECURITY_ERROR': SecurityError,
    'AUTH_ERROR': AuthenticationError,
    'AUTHZ_ERROR': AuthorizationError,
    'RATE_LIMIT': RateLimitError,
    'DB_ERROR': DatabaseError,
    'EXTERNAL_SERVICE': ExternalServiceError,
    'CONTENT_MODERATION': ContentModerationError,
    'PAYMENT_ERROR': PaymentError,
    'CONFIG_ERROR': ConfigurationError,
    'FILE_ERROR': FileProcessingError,
    'NETWORK_ERROR': NetworkError,
    'BUSINESS_ERROR': BusinessLogicError,
    'USER_NOT_FOUND': UserNotFoundError,
    'CONTENT_NOT_FOUND': ContentNotFoundError,
    'DUPLICATE_ERROR': DuplicateError,
    'PERMISSION_DENIED': PermissionDeniedError,
    'MAINTENANCE_MODE': MaintenanceModeError,
    'FEATURE_DISABLED': FeatureDisabledError
}

def create_exception_from_code(error_code: str, message: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> BaseCustomException:
    """Cria uma exceção baseada no código de erro."""
    exception_class = ERROR_CODE_MAP.get(error_code, BaseCustomException)
    return exception_class(message, user_id, details)

def handle_exception(exception: Exception, user_id: Optional[str] = None, context: Optional[str] = None) -> BaseCustomException:
    """Converte exceções padrão em exceções personalizadas."""
    details = {'original_exception': str(exception), 'context': context}
    
    if isinstance(exception, BaseCustomException):
        return exception
    elif isinstance(exception, ValueError):
        return ValidationError(str(exception), user_id, details)
    elif isinstance(exception, PermissionError):
        return PermissionDeniedError(str(exception), user_id, details)
    elif isinstance(exception, FileNotFoundError):
        return ContentNotFoundError(str(exception), user_id, details)
    elif isinstance(exception, ConnectionError):
        return NetworkError(str(exception), user_id, details)
    else:
        return BaseCustomException(str(exception), user_id, details)