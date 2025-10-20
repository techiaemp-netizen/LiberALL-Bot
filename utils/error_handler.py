import logging
import traceback
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import aiogram
from services.firebase_service import FirebaseService
from core.firebase_client import firebase_client

class ErrorHandler:
    """Classe para tratamento robusto de erros e logging."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def handle_callback_error(self, query: aiogram.types.CallbackQuery, message: str = "Ocorreu um erro ao processar sua ação."):
        """Trata erros ocorridos em callbacks, notifica usuário e registra contexto."""
        try:
            user_id = str(query.from_user.id) if query and query.from_user else None
            chat_id = query.message.chat.id if query and query.message and query.message.chat else None
            callback_data = query.data if query else None
            
            # Notificar usuário de forma amigável
            if chat_id is not None:
                try:
                    await query.message.answer("😔 Ops! Algo deu errado. Tente novamente mais tarde.")
                except Exception as send_err:
                    self.logger.warning(f"Falha ao enviar mensagem de erro ao usuário {user_id}: {send_err}")
            
            # Log estruturado
            context = {
                'chat_id': chat_id,
                'user_id': user_id,
                'callback_data': callback_data,
                'message_text': query.message.text if query and query.message else None
            }
            await self.log_error(error=Exception(message), user_id=user_id, action='handle_callback_error', context=context)
        except Exception as e:
            self.logger.error(f"Erro ao tratar callback error: {e}")
        
    async def handle_error(self, bot, user_id: int, error_message: str = "Ocorreu um erro inesperado."):
        """Método para lidar com erros e enviar mensagem ao usuário."""
        try:
            await bot.send_message(user_id, error_message)
            self.logger.error(f"Error handled for user {user_id}: {error_message}")
        except Exception as e:
            self.logger.error(f"Failed to send error message to user {user_id}: {e}")
    
    async def log_error(self, 
                       error: Exception, 
                       user_id: Optional[str] = None,
                       action: Optional[str] = None,
                       context: Optional[Dict[str, Any]] = None) -> None:
        """Log detalhado de erros."""
        try:
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'user_id': user_id,
                'action': action,
                'context': context or {}
            }
            
            # Log local
            self.logger.error(f"Error in {action}: {error}", extra=error_data)
            
            # Log no Firebase para análise
            if firebase_client:
                await firebase_client.push('errors', error_data)
                
        except Exception as log_error:
            self.logger.critical(f"Failed to log error: {log_error}")
    
    # Função comentada pois foi adaptada para aiogram 3.x
        # Atualizada para compatibilidade com aiogram 3.x
    # async def handle_telegram_error(self, 
    #                                update: Update, 
    #                                context: CallbackContext,
    #                                error: Exception) -> None:
    #     """Handler específico para erros do Telegram."""
    #     try:
    #         user_id = str(update.effective_user.id) if update.effective_user else None
    #         chat_id = update.effective_chat.id if update.effective_chat else None
    #         
    #         await self.log_error(
    #             error=error,
    #             user_id=user_id,
    #             action='telegram_handler',
    #             context={
    #                 'chat_id': chat_id,
    #                 'message_text': update.message.text if update.message else None,
    #                 'callback_data': update.callback_query.data if update.callback_query else None
    #             }
    #         )
    #         
    #         # Enviar mensagem de erro amigável para o usuário
    #         if update.effective_chat:
    #             await context.bot.send_message(
    #                 chat_id=chat_id,
    #                 text="😔 Ops! Algo deu errado. Nossa equipe foi notificada e está trabalhando para resolver."
    #             )
    #             
    #     except Exception as handler_error:
    #         self.logger.critical(f"Failed to handle telegram error: {handler_error}")
    
    async def log_user_action(self, 
                             user_id: str, 
                             action: str, 
                             details: Optional[Dict[str, Any]] = None) -> None:
        """Log de ações do usuário para auditoria."""
        try:
            action_data = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'action': action,
                'details': details or {}
            }
            
            # Log local
            self.logger.info(f"User action: {user_id} - {action}", extra=action_data)
            
            # Log no Firebase
            if firebase_client:
                await firebase_client.push('user_actions', action_data)
                
        except Exception as log_error:
            self.logger.error(f"Failed to log user action: {log_error}")
    
    def validate_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validação básica de dados do usuário."""
        validated_data = {}
        
        # Validar user_id
        if 'user_id' in data and isinstance(data['user_id'], (str, int)):
            validated_data['user_id'] = str(data['user_id'])
        
        # Validar username
        if 'username' in data and isinstance(data['username'], str):
            validated_data['username'] = data['username'][:50]  # Limitar tamanho
        
        # Validar first_name
        if 'first_name' in data and isinstance(data['first_name'], str):
            validated_data['first_name'] = data['first_name'][:100]
        
        # Validar last_name
        if 'last_name' in data and isinstance(data['last_name'], str):
            validated_data['last_name'] = data['last_name'][:100]
        
        return validated_data
    
    async def safe_execute(self, 
                          func, 
                          *args, 
                          user_id: Optional[str] = None,
                          action: Optional[str] = None,
                          **kwargs) -> Any:
        """Execução segura de funções com tratamento de erro."""
        try:
            # Filtrar kwargs para remover parâmetros de controle do error_handler
            filtered_kwargs = {k: v for k, v in kwargs.items() 
                             if k not in ['error_message', 'chat_id']}
            
            if hasattr(func, '__call__'):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **filtered_kwargs)
                else:
                    return func(*args, **filtered_kwargs)
        except Exception as error:
            await self.log_error(
                error=error,
                user_id=user_id,
                action=action or func.__name__,
                context={'args': str(args), 'kwargs': str(kwargs)}
            )
            raise

def error_handler_decorator(handler_name: str):
    """Decorator para tratamento automático de erros em handlers."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                # Assumindo que o handler tem acesso ao error_handler
                if hasattr(self, 'error_handler'):
                    user_id = None
                    # Tentar extrair user_id dos argumentos
                    for arg in args:
                        if hasattr(arg, 'effective_user') and arg.effective_user:
                            user_id = str(arg.effective_user.id)
                            break
                        elif hasattr(arg, 'from_user') and arg.from_user:
                            user_id = str(arg.from_user.id)
                            break
                    
                    await self.error_handler.log_error(
                        error=e,
                        user_id=user_id,
                        action=handler_name,
                        context={'handler': handler_name, 'args': str(args)[:200]}
                    )
                else:
                    self.logger.error(f"Erro em {handler_name}: {e}", exc_info=e)
                
                # Re-raise para permitir tratamento específico se necessário
                raise
        return wrapper
    return decorator

def log_action(action: str, level: str = "INFO"):
    """Decorator para log automático de ações."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            user_id = None
            # Tentar extrair user_id dos argumentos
            for arg in args:
                if hasattr(arg, 'effective_user') and arg.effective_user:
                    user_id = str(arg.effective_user.id)
                    break
                elif hasattr(arg, 'from_user') and arg.from_user:
                    user_id = str(arg.from_user.id)
                    break
            
            # Log início da ação
            if level.upper() == "DEBUG":
                logging.debug(f"Iniciando {action} para usuário {user_id}")
            else:
                logging.info(f"Iniciando {action} para usuário {user_id}")
            
            try:
                # Executar função sem await desnecessário
                await func(self, *args, **kwargs)
                
                # Log sucesso
                if level.upper() == "DEBUG":
                    logging.debug(f"Concluído {action} para usuário {user_id}")
                else:
                    logging.info(f"Concluído {action} para usuário {user_id}")
                
                # Não retornar nada para evitar problemas com await
                return None
                
            except Exception as e:
                logging.error(f"Erro em {action} para usuário {user_id}: {e}")
                raise
                
        return wrapper
    return decorator

# Instância global
error_handler = ErrorHandler()