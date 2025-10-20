"""Utilitários para acesso seguro a dados de objetos e dicionários."""

import logging
from typing import Any, Optional, Union, Dict

logger = logging.getLogger(__name__)

def get_field(obj: Union[Dict[str, Any], object], name: str, default: Any = None) -> Any:
    """
    Obtém um campo de um objeto ou dicionário de forma segura.
    
    Args:
        obj: Objeto ou dicionário do qual extrair o campo
        name: Nome do campo/chave
        default: Valor padrão se o campo não existir
        
    Returns:
        Any: Valor do campo ou valor padrão
    """
    if obj is None:
        return default
    
    try:
        # Se é um dicionário, usa get()
        if isinstance(obj, dict):
            return obj.get(name, default)
        
        # Se é um objeto, usa getattr()
        return getattr(obj, name, default)
        
    except Exception as e:
        logger.warning(f"Erro ao acessar campo '{name}': {e}")
        return default

def get_nested_field(obj: Union[Dict[str, Any], object], path: str, default: Any = None, separator: str = '.') -> Any:
    """
    Obtém um campo aninhado usando notação de ponto.
    
    Args:
        obj: Objeto ou dicionário raiz
        path: Caminho para o campo (ex: 'user.profile.name')
        default: Valor padrão se o campo não existir
        separator: Separador usado no caminho
        
    Returns:
        Any: Valor do campo aninhado ou valor padrão
    """
    if obj is None or not path:
        return default
    
    try:
        current = obj
        parts = path.split(separator)
        
        for part in parts:
            if current is None:
                return default
            
            current = get_field(current, part, None)
            
            if current is None:
                return default
        
        return current
        
    except Exception as e:
        logger.warning(f"Erro ao acessar campo aninhado '{path}': {e}")
        return default

def safe_get_user_field(user: Union[Dict[str, Any], object], field: str, default: str = 'Usuário Anônimo') -> str:
    """
    Obtém um campo de usuário de forma segura, com fallback para 'Usuário Anônimo'.
    
    Args:
        user: Objeto ou dicionário do usuário
        field: Nome do campo
        default: Valor padrão
        
    Returns:
        str: Valor do campo ou valor padrão
    """
    if user is None:
        return default
    
    value = get_field(user, field, default)
    
    # Garante que retorna uma string não vazia
    if not value or (isinstance(value, str) and not value.strip()):
        return default
    
    return str(value)

def safe_get_int(obj: Union[Dict[str, Any], object], name: str, default: int = 0) -> int:
    """
    Obtém um campo inteiro de forma segura.
    
    Args:
        obj: Objeto ou dicionário
        name: Nome do campo
        default: Valor padrão
        
    Returns:
        int: Valor inteiro ou valor padrão
    """
    value = get_field(obj, name, default)
    
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Não foi possível converter '{name}' para int: {value}")
        return default

def safe_get_bool(obj: Union[Dict[str, Any], object], name: str, default: bool = False) -> bool:
    """
    Obtém um campo booleano de forma segura.
    
    Args:
        obj: Objeto ou dicionário
        name: Nome do campo
        default: Valor padrão
        
    Returns:
        bool: Valor booleano ou valor padrão
    """
    value = get_field(obj, name, default)
    
    # Converte valores comuns para bool
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ('true', '1', 'yes', 'on', 'sim'):
            return True
        elif value_lower in ('false', '0', 'no', 'off', 'não', 'nao'):
            return False
    
    try:
        return bool(value)
    except (ValueError, TypeError):
        logger.warning(f"Não foi possível converter '{name}' para bool: {value}")
        return default

def safe_get_list(obj: Union[Dict[str, Any], object], name: str, default: Optional[list] = None) -> list:
    """
    Obtém um campo lista de forma segura.
    
    Args:
        obj: Objeto ou dicionário
        name: Nome do campo
        default: Valor padrão
        
    Returns:
        list: Lista ou valor padrão
    """
    if default is None:
        default = []
    
    value = get_field(obj, name, default)
    
    if isinstance(value, list):
        return value
    
    # Tenta converter outros tipos iteráveis
    try:
        if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
            return list(value)
    except Exception:
        pass
    
    logger.warning(f"Campo '{name}' não é uma lista: {type(value)}")
    return default

def safe_get_dict(obj: Union[Dict[str, Any], object], name: str, default: Optional[dict] = None) -> dict:
    """
    Obtém um campo dicionário de forma segura.
    
    Args:
        obj: Objeto ou dicionário
        name: Nome do campo
        default: Valor padrão
        
    Returns:
        dict: Dicionário ou valor padrão
    """
    if default is None:
        default = {}
    
    value = get_field(obj, name, default)
    
    if isinstance(value, dict):
        return value
    
    logger.warning(f"Campo '{name}' não é um dicionário: {type(value)}")
    return default

def has_field(obj: Union[Dict[str, Any], object], name: str) -> bool:
    """
    Verifica se um objeto possui um campo específico.
    
    Args:
        obj: Objeto ou dicionário
        name: Nome do campo
        
    Returns:
        bool: True se o campo existe, False caso contrário
    """
    if obj is None:
        return False
    
    try:
        if isinstance(obj, dict):
            return name in obj
        else:
            return hasattr(obj, name)
    except Exception:
        return False

def get_fields_summary(obj: Union[Dict[str, Any], object]) -> Dict[str, str]:
    """
    Retorna um resumo dos campos disponíveis em um objeto.
    
    Args:
        obj: Objeto ou dicionário
        
    Returns:
        dict: Resumo dos campos e seus tipos
    """
    if obj is None:
        return {}
    
    summary = {}
    
    try:
        if isinstance(obj, dict):
            for key, value in obj.items():
                summary[key] = type(value).__name__
        else:
            for attr in dir(obj):
                if not attr.startswith('_'):
                    try:
                        value = getattr(obj, attr)
                        if not callable(value):
                            summary[attr] = type(value).__name__
                    except Exception:
                        summary[attr] = 'unknown'
    except Exception as e:
        logger.error(f"Erro ao gerar resumo de campos: {e}")
    
    return summary