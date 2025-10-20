"""Utilitários de segurança para o bot LiberALL"""

import re
import hashlib
import secrets
import base64
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging
from PIL import Image
from PIL.ExifTags import TAGS
import io
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Classe utilitária para operações de segurança"""
    
    def __init__(self):
        self.fernet = None
        fernet_key = os.getenv('FERNET_KEY')
        if fernet_key:
            try:
                self.fernet = Fernet(fernet_key.encode())
            except Exception as e:
                logger.error(f"Erro ao inicializar Fernet: {e}")
    
    def sanitize_user_data(self, data: Any) -> Any:
        """Sanitiza dados do usuário removendo conteúdo perigoso"""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {key: self.sanitize_user_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_user_data(item) for item in data]
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitiza uma string individual"""
        if not isinstance(text, str):
            return text
        
        # Remove caracteres de controle perigosos
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remove scripts e tags HTML perigosas
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        # Limita o tamanho
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return text.strip()
    
    def validate_user_input(self, data: Dict[str, Any], required_fields: List[str] = None) -> Dict[str, Any]:
        """Valida entrada do usuário"""
        if not isinstance(data, dict):
            raise ValueError("Dados devem ser um dicionário")
        
        # Verifica campos obrigatórios
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Campos obrigatórios faltando: {missing_fields}")
        
        # Sanitiza todos os dados
        sanitized_data = self.sanitize_user_data(data)
        
        # Validações específicas
        if 'user_id' in sanitized_data:
            if not self._validate_user_id(sanitized_data['user_id']):
                raise ValueError("ID de usuário inválido")
        
        if 'email' in sanitized_data:
            if not self._validate_email(sanitized_data['email']):
                raise ValueError("Email inválido")
        
        if 'age' in sanitized_data:
            if not self._validate_age(sanitized_data['age']):
                raise ValueError("Idade inválida")
        
        return sanitized_data
    
    def _validate_user_id(self, user_id: Any) -> bool:
        """Valida ID do usuário"""
        if not isinstance(user_id, (str, int)):
            return False
        
        user_id_str = str(user_id)
        return len(user_id_str) > 0 and len(user_id_str) <= 50 and user_id_str.isdigit()
    
    def _validate_email(self, email: str) -> bool:
        """Valida formato de email"""
        if not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    def _validate_age(self, age: Any) -> bool:
        """Valida idade"""
        try:
            age_int = int(age)
            return 13 <= age_int <= 120
        except (ValueError, TypeError):
            return False
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Criptografa dados sensíveis"""
        if not self.fernet:
            logger.warning("Fernet não inicializado, dados não serão criptografados")
            return data
        
        try:
            if isinstance(data, str):
                encrypted = self.fernet.encrypt(data.encode())
                return base64.urlsafe_b64encode(encrypted).decode()
            return data
        except Exception as e:
            logger.error(f"Erro ao criptografar dados: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Descriptografa dados"""
        if not self.fernet:
            logger.warning("Fernet não inicializado, dados não serão descriptografados")
            return encrypted_data
        
        try:
            if isinstance(encrypted_data, str):
                decoded = base64.urlsafe_b64decode(encrypted_data.encode())
                decrypted = self.fernet.decrypt(decoded)
                return decrypted.decode()
            return encrypted_data
        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {e}")
            return None
    
    def strip_exif(self, image_data: bytes) -> bytes:
        """Remove metadados EXIF de imagens"""
        try:
            # Abre a imagem
            image = Image.open(io.BytesIO(image_data))
            
            # Remove dados EXIF criando uma nova imagem
            clean_image = Image.new(image.mode, image.size)
            clean_image.putdata(list(image.getdata()))
            
            # Salva a imagem limpa
            output = io.BytesIO()
            format_map = {
                'JPEG': 'JPEG',
                'PNG': 'PNG',
                'WEBP': 'WEBP',
                'GIF': 'GIF'
            }
            
            image_format = format_map.get(image.format, 'JPEG')
            clean_image.save(output, format=image_format, quality=85, optimize=True)
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Erro ao remover EXIF: {e}")
            return image_data
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Gera token seguro"""
        return secrets.token_urlsafe(length)
    
    def hash_data(self, data: str, salt: str = None) -> str:
        """Gera hash seguro dos dados"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{data}{salt}"
        hash_obj = hashlib.sha256(combined.encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def verify_hash(self, data: str, hashed: str) -> bool:
        """Verifica hash dos dados"""
        try:
            salt, hash_value = hashed.split(':', 1)
            return self.hash_data(data, salt) == hashed
        except ValueError:
            return False
    
    def rate_limit_key(self, user_id: str, action: str) -> str:
        """Gera chave para rate limiting"""
        return f"rate_limit:{user_id}:{action}"
    
    def validate_file_upload(self, file_data: bytes, allowed_types: List[str] = None) -> Dict[str, Any]:
        """Valida upload de arquivo"""
        if allowed_types is None:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        
        result = {
            'valid': False,
            'file_type': None,
            'size': len(file_data),
            'errors': []
        }
        
        # Verifica tamanho
        max_size = 10 * 1024 * 1024  # 10MB
        if result['size'] > max_size:
            result['errors'].append(f"Arquivo muito grande: {result['size']} bytes (máximo: {max_size})")
        
        # Verifica tipo de arquivo
        try:
            image = Image.open(io.BytesIO(file_data))
            mime_type = f"image/{image.format.lower()}"
            result['file_type'] = mime_type
            
            if mime_type not in allowed_types:
                result['errors'].append(f"Tipo de arquivo não permitido: {mime_type}")
            
            # Verifica dimensões
            width, height = image.size
            max_dimension = 4096
            if width > max_dimension or height > max_dimension:
                result['errors'].append(f"Dimensões muito grandes: {width}x{height} (máximo: {max_dimension}x{max_dimension})")
            
        except Exception as e:
            result['errors'].append(f"Erro ao processar imagem: {e}")
        
        result['valid'] = len(result['errors']) == 0
        return result
    
    def log_security_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None):
        """Registra evento de segurança"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details or {}
        }
        
        logger.warning(f"SECURITY_EVENT: {log_data}")
    
    def check_suspicious_activity(self, user_id: str, action: str, context: Dict[str, Any] = None) -> bool:
        """Verifica atividade suspeita"""
        # Implementação básica - pode ser expandida
        suspicious_patterns = [
            'rapid_requests',
            'invalid_data_patterns',
            'unauthorized_access_attempts'
        ]
        
        if action in suspicious_patterns:
            self.log_security_event(
                'suspicious_activity',
                user_id=user_id,
                details={'action': action, 'context': context}
            )
            return True
        
        return False


# Instância global
security_utils = SecurityUtils()

# Funções de conveniência
def sanitize_user_data(data: Any) -> Any:
    """Função de conveniência para sanitizar dados"""
    return security_utils.sanitize_user_data(data)

def encrypt_data(data: str) -> Optional[str]:
    """Função de conveniência para criptografar dados"""
    return security_utils.encrypt_data(data)

def decrypt_data(encrypted_data: str) -> Optional[str]:
    """Função de conveniência para descriptografar dados"""
    return security_utils.decrypt_data(encrypted_data)

def strip_exif(image_data: bytes) -> bytes:
    """Função de conveniência para remover EXIF"""
    return security_utils.strip_exif(image_data)

def validate_user_input(data: Dict[str, Any], required_fields: List[str] = None) -> Dict[str, Any]:
    """Função de conveniência para validar entrada do usuário."""
    return security_utils.validate_user_input(data, required_fields)