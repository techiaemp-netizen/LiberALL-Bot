"""Sistema robusto de tratamento de erros e logging."""

import logging
import traceback
import functools
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
# Compatível com aiogram 3.x
from services.security_service import security_service

# Configuração do logger
logger = logging.getLogger(__name__)

class ErrorSeverity:
    """Níveis de severidade de erros."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategories:
    """Categorias de erros do sistema."""
    TELEGRAM_API = "telegram_api"
    FIREBASE = "firebase"
    SECURITY = "security"
    PAYMENT = "payment"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    NETWORK = "network"
    VALIDATION = "validation"

class BotError(Exception):
    """Exceção base para erros do bot."""
    
    def __init__(self, message: str, category: str = ErrorCategories.SYSTEM, 
                 severity: str = ErrorSeverity.MEDIUM, user_id: str = None, 
                 details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.user_id = user_id
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)

class TelegramError(BotError):
    """Erros relacionados à API do Telegram."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategories.TELEGRAM_API, **kwargs)

class FirebaseError(BotError):
    """Erros relacionados ao Firebase."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategories.FIREBASE, **kwargs)

class SecurityError(BotError):
    """Erros relacionados à segurança."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategories.SECURITY, 
                        severity=ErrorSeverity.HIGH, **kwargs)

class PaymentError(BotError):
    """Erros relacionados a pagamentos."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategories.PAYMENT, 
                        severity=ErrorSeverity.HIGH, **kwargs)

class ValidationError(BotError):
    """Erros de validação de dados."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategories.VALIDATION, 
                        severity=ErrorSeverity.LOW, **kwargs)

class ErrorHandler:
    """Manipulador centralizado de erros."""
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = []
        self.max_last_errors = 100
    
    async def handle_error(self, error: Exception, update = None, 
                          context = None, 
                          user_message: str = None) -> bool:
        """Manipula erros de forma centralizada."""
        try:
            # Extrai informações do erro
            error_info = self._extract_error_info(error, update, context)
            
            # Registra o erro
            await self._log_error(error_info)
            
            # Notifica o usuário se apropriado
            if update and context:
                await self._notify_user(error_info, update, context, user_message)
            
            # Verifica se precisa de ação administrativa
            await self._check_admin_notification(error_info)
            
            return True
            
        except Exception as e:
            # Erro ao manipular erro - log crítico
            logger.critical(f"Erro crítico no manipulador de erros: {e}")
            logger.critical(f"Erro original: {error}")
            return False
    
    def _extract_error_info(self, error: Exception, update = None, 
                           context = None) -> Dict[str, Any]:
        """Extrai informações detalhadas do erro."""
        error_info = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
        }
        
        # Informações específicas do BotError
        if isinstance(error, BotError):
            error_info.update({
                'category': error.category,
                'severity': error.severity,
                'user_id': error.user_id,
                'details': error.details
            })
        else:
            # Categoriza erros padrão
            error_info.update({
                'category': self._categorize_error(error),
                'severity': self._assess_severity(error),
                'user_id': None,
                'details': {}
            })
        
        # Informações do update
        if update:
            try:
                error_info['user_id'] = error_info['user_id'] or str(update.effective_user.id)
                error_info['chat_id'] = str(update.effective_chat.id)
                error_info['message_id'] = getattr(update.message, 'message_id', None)
                error_info['update_type'] = self._get_update_type(update)
            except Exception:
                pass  # Ignora erros ao extrair informações do update
        
        # Informações do contexto
        if context:
            try:
                error_info['bot_data'] = str(context.bot_data) if context.bot_data else None
                error_info['user_data'] = str(context.user_data) if context.user_data else None
            except Exception:
                pass  # Ignora erros ao extrair informações do contexto
        
        return error_info
    
    async def log_error(
        self,
        error: Exception,
        update = None,
        context = None,
        user_id: int = None,
        additional_info: Dict[str, Any] = None
    ) -> None:
        """Registra o erro nos logs."""
        # Extrai informações do erro se não fornecidas
        if isinstance(error, dict):
            error_info = error
        else:
            error_info = self._extract_error_info(error, update, context)
            if user_id:
                error_info['user_id'] = str(user_id)
            if additional_info:
                error_info['details'].update(additional_info)
        
        await self._log_error(error_info)
    
    async def _log_error(self, error_info: Dict[str, Any]) -> None:
        """Registra o erro nos logs."""
        severity = error_info.get('severity', ErrorSeverity.MEDIUM)
        category = error_info.get('category', ErrorCategories.SYSTEM)
        
        # Incrementa contador de erros
        error_key = f"{category}_{error_info['error_type']}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Adiciona à lista de erros recentes
        self.last_errors.append(error_info)
        if len(self.last_errors) > self.max_last_errors:
            self.last_errors.pop(0)
        
        # Log estruturado
        log_data = {
            'event_type': 'error_occurred',
            'error_category': category,
            'error_severity': severity,
            'error_type': error_info['error_type'],
            'user_id': error_info.get('user_id'),
            'chat_id': error_info.get('chat_id'),
            'error_count': self.error_counts[error_key],
            'timestamp': error_info['timestamp']
        }
        
        # Escolhe nível de log baseado na severidade
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(error_info['error_message'], extra=log_data)
        elif severity == ErrorSeverity.HIGH:
            logger.error(error_info['error_message'], extra=log_data)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(error_info['error_message'], extra=log_data)
        else:
            logger.info(error_info['error_message'], extra=log_data)
        
        # Log de auditoria para erros de segurança
        if category == ErrorCategories.SECURITY and error_info.get('user_id'):
            await security_service.log_user_action(
                user_id=error_info['user_id'],
                action="security_error",
                details={
                    'error_type': error_info['error_type'],
                    'severity': severity
                }
            )
    
    async def _notify_user(self, error_info: Dict[str, Any], update, 
                          context, 
                          custom_message: str = None) -> None:
        """Notifica o usuário sobre o erro."""
        try:
            severity = error_info.get('severity', ErrorSeverity.MEDIUM)
            category = error_info.get('category', ErrorCategories.SYSTEM)
            
            # Mensagem personalizada ou padrão
            if custom_message:
                message = custom_message
            else:
                message = self._get_user_error_message(category, severity)
            
            # Envia mensagem apenas para erros que o usuário deve saber
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] or \
               category in [ErrorCategories.USER_INPUT, ErrorCategories.VALIDATION]:
                
                if update.callback_query:
                    await update.callback_query.answer(message, show_alert=True)
                elif update.message:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=message,
                        parse_mode='HTML'
                    )
        
        except Exception as e:
            logger.error(f"Erro ao notificar usuário: {e}")
    
    async def _check_admin_notification(self, error_info: Dict[str, Any]) -> None:
        """Verifica se administradores devem ser notificados."""
        severity = error_info.get('severity', ErrorSeverity.MEDIUM)
        category = error_info.get('category', ErrorCategories.SYSTEM)
        error_type = error_info['error_type']
        
        # Critérios para notificação administrativa
        should_notify = (
            severity == ErrorSeverity.CRITICAL or
            category == ErrorCategories.SECURITY or
            category == ErrorCategories.PAYMENT or
            self.error_counts.get(f"{category}_{error_type}", 0) > 10  # Muitos erros do mesmo tipo
        )
        
        if should_notify:
            # TODO: Implementar notificação para administradores
            logger.critical(
                f"NOTIFICAÇÃO ADMIN NECESSÁRIA: {error_info['error_message']}",
                extra={'admin_notification': True}
            )
    
    def _categorize_error(self, error: Exception) -> str:
        """Categoriza erros padrão."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if 'telegram' in error_message or 'bot' in error_message:
            return ErrorCategories.TELEGRAM_API
        elif 'firebase' in error_message or 'database' in error_message:
            return ErrorCategories.FIREBASE
        elif 'network' in error_message or 'connection' in error_message:
            return ErrorCategories.NETWORK
        elif 'validation' in error_message or 'invalid' in error_message:
            return ErrorCategories.VALIDATION
        else:
            return ErrorCategories.SYSTEM
    
    def _assess_severity(self, error: Exception) -> str:
        """Avalia severidade de erros padrão."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Erros críticos
        if error_type in ['SystemExit', 'KeyboardInterrupt', 'MemoryError']:
            return ErrorSeverity.CRITICAL
        
        # Erros de alta severidade
        if 'permission' in error_message or 'unauthorized' in error_message:
            return ErrorSeverity.HIGH
        
        # Erros de validação são geralmente baixa severidade
        if error_type in ['ValueError', 'TypeError'] and 'validation' in error_message:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _get_update_type(self, update) -> str:
        """Identifica o tipo de update."""
        if update.message:
            return 'message'
        elif update.callback_query:
            return 'callback_query'
        elif update.inline_query:
            return 'inline_query'
        else:
            return 'unknown'
    
    def _get_user_error_message(self, category: str, severity: str) -> str:
        """Gera mensagem de erro apropriada para o usuário."""
        if category == ErrorCategories.VALIDATION:
            return "❌ <b>Dados inválidos</b>\n\nVerifique as informações e tente novamente."
        
        elif category == ErrorCategories.SECURITY:
            return "🔒 <b>Erro de segurança</b>\n\nSua ação foi bloqueada por motivos de segurança."
        
        elif category == ErrorCategories.PAYMENT:
            return "💳 <b>Erro no pagamento</b>\n\nTente novamente ou entre em contato com o suporte."
        
        elif severity == ErrorSeverity.CRITICAL:
            return "🚨 <b>Erro crítico</b>\n\nO sistema está temporariamente indisponível. Tente novamente em alguns minutos."
        
        else:
            return "⚠️ <b>Algo deu errado</b>\n\nTente novamente em alguns instantes."
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de erros."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts_by_type': self.error_counts.copy(),
            'recent_errors_count': len(self.last_errors),
            'last_error_time': self.last_errors[-1]['timestamp'] if self.last_errors else None
        }

# Instância global do manipulador de erros
error_handler = ErrorHandler()

# Decorator para tratamento automático de erros
def handle_errors(user_message: str = None, category: str = None, severity: str = None):
    """Decorator para tratamento automático de erros em funções."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Tenta extrair update e context dos argumentos
                update = None
                context = None
                
                for arg in args:
                    if hasattr(arg, 'message') or hasattr(arg, 'callback_query'):  # Update-like object
                        update = arg
                    elif hasattr(arg, 'bot'):  # Context-like object
                        context = arg
                
                # Cria BotError se categoria/severidade especificadas
                if category or severity:
                    error = BotError(
                        str(e),
                        category=category or ErrorCategories.SYSTEM,
                        severity=severity or ErrorSeverity.MEDIUM
                    )
                else:
                    error = e
                
                await error_handler.handle_error(error, update, context, user_message)
                return None
        
        return wrapper
    return decorator

# Decorator específico para handlers do Telegram
def telegram_handler(user_message: str = None):
    """Decorator específico para handlers do Telegram."""
    return handle_errors(
        user_message=user_message,
        category=ErrorCategories.TELEGRAM_API,
        severity=ErrorSeverity.MEDIUM
    )