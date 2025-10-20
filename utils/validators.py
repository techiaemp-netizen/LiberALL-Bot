"""Utilitários de validação para o LiberALL Bot."""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Regex para validar formato do token do Telegram
# Formato: número:string_base64_de_35_ou_mais_caracteres
TOKEN_PATTERN = re.compile(r'^\d+:[A-Za-z0-9_-]{35,}$')

def validate_telegram_token(token: str) -> bool:
    """
    Valida se o token do Telegram está no formato correto.
    
    Args:
        token: Token do bot do Telegram
        
    Returns:
        bool: True se o token é válido, False caso contrário
    """
    if not token or not isinstance(token, str):
        logger.error("Token deve ser uma string não vazia")
        return False
    
    # Remove espaços em branco
    token = token.strip()
    
    # Valida usando regex
    if not TOKEN_PATTERN.match(token):
        logger.error(f"Token inválido: formato incorreto. Esperado: número:string_base64")
        return False
    
    logger.info("Token validado com sucesso")
    return True

def validate_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    return validated_data

def validate_user_id(user_id: Any) -> bool:
    """
    Valida se o user_id é um inteiro válido.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        bool: True se válido, False caso contrário
    """
    try:
        int_user_id = int(user_id)
        return int_user_id > 0
    except (ValueError, TypeError):
        return False

def validate_chat_id(chat_id: Any) -> bool:
    """
    Valida se o chat_id é um inteiro válido.
    
    Args:
        chat_id: ID do chat
        
    Returns:
        bool: True se válido, False caso contrário
    """
    try:
        int_chat_id = int(chat_id)
        # Chat IDs podem ser negativos (grupos)
        return int_chat_id != 0
    except (ValueError, TypeError):
        return False

def validate_message_data(data: Dict[str, Any]) -> bool:
    """
    Valida dados básicos de uma mensagem.
    
    Args:
        data: Dicionário com dados da mensagem
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not isinstance(data, dict):
        return False
    
    # Campos obrigatórios
    required_fields = ['message_id', 'from', 'chat']
    
    for field in required_fields:
        if field not in data:
            logger.error(f"Campo obrigatório ausente: {field}")
            return False
    
    # Valida IDs
    if not validate_user_id(data.get('from', {}).get('id')):
        logger.error("User ID inválido na mensagem")
        return False
    
    if not validate_chat_id(data.get('chat', {}).get('id')):
        logger.error("Chat ID inválido na mensagem")
        return False
    
    return True

def sanitize_text_input(text: str, max_length: int = 4096) -> Optional[str]:
    """
    Sanitiza entrada de texto do usuário.
    
    Args:
        text: Texto a ser sanitizado
        max_length: Comprimento máximo permitido
        
    Returns:
        str: Texto sanitizado ou None se inválido
    """
    if not text or not isinstance(text, str):
        return None
    
    # Remove espaços extras
    text = text.strip()
    
    # Verifica comprimento
    if len(text) > max_length:
        logger.warning(f"Texto truncado de {len(text)} para {max_length} caracteres")
        text = text[:max_length]
    
    # Remove caracteres de controle perigosos
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text if text else None

def validate_callback_data(callback_data: str) -> bool:
    """
    Valida dados de callback de botões inline.
    
    Args:
        callback_data: Dados do callback
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not callback_data or not isinstance(callback_data, str):
        return False
    
    # Telegram limita callback_data a 64 bytes
    if len(callback_data.encode('utf-8')) > 64:
        logger.error(f"Callback data muito longo: {len(callback_data.encode('utf-8'))} bytes")
        return False
    
    return True

def validate_photo_data(photo_data: Dict[str, Any]) -> bool:
    """
    Valida dados de uma foto.
    
    Args:
        photo_data: Dados da foto
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not isinstance(photo_data, dict):
        return False
    
    required_fields = ['file_id', 'file_unique_id', 'width', 'height']
    
    for field in required_fields:
        if field not in photo_data:
            logger.error(f"Campo obrigatório ausente na foto: {field}")
            return False
    
    # Valida dimensões
    try:
        width = int(photo_data['width'])
        height = int(photo_data['height'])
        if width <= 0 or height <= 0:
            logger.error("Dimensões da foto inválidas")
            return False
    except (ValueError, TypeError):
        logger.error("Dimensões da foto não são números válidos")
        return False
    
    return True