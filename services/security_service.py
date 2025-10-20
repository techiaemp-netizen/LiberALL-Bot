"""Serviço de segurança e conformidade LGPD.

Este módulo implementa:
- Logs de consentimento LGPD
- Remoção de metadados EXIF
- Criptografia de dados sensíveis
- Auditoria de ações sensíveis
"""

import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import os
from PIL import Image
from PIL.ExifTags import TAGS
import io

logger = logging.getLogger(__name__)

class SecurityService:
    """Serviço de segurança e conformidade LGPD."""
    
    def __init__(self):
        """Inicializa o serviço de segurança."""
        # Chave de criptografia (deve ser armazenada de forma segura)
        encryption_key = os.getenv('FERNET_KEY')
        if not encryption_key:
            # Gera uma nova chave se não existir (apenas para desenvolvimento)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("Chave de criptografia gerada automaticamente. Configure FERNET_KEY em produção.")
        
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def sanitize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza dados do usuário removendo campos perigosos e validando tipos.
        
        Args:
            user_data: Dados brutos do usuário
            
        Returns:
            Dict com dados sanitizados
        """
        if not isinstance(user_data, dict):
            raise ValueError("user_data deve ser um dicionário")
        
        sanitized = {}
        
        # Campos permitidos e suas validações
        allowed_fields = {
            'telegram_id': (int, str),
            'username': (str, type(None)),
            'first_name': (str, type(None)),
            'last_name': (str, type(None)),
            'language_code': (str, type(None)),
            'age': (int, type(None)),
            'gender': (str, type(None)),
            'bio': (str, type(None)),
            'state': (str, type(None)),
            'category': (str, type(None)),
            'lgpd_consent': bool,
            'onboarding_state': (str, type(None)),
            'onboarding_completed': bool,
            'plan_type': (str, type(None)),
            'is_active': bool,
            'created_at': (str, type(None)),
            'updated_at': (str, type(None))
        }
        
        for field, value in user_data.items():
            if field in allowed_fields:
                expected_type = allowed_fields[field]
                
                # Tratamento especial para telegram_id
                if field == 'telegram_id':
                    if isinstance(value, str):
                        try:
                            value = int(value)
                        except ValueError:
                            logger.error(f"Falha ao converter telegram_id '{value}' para int")
                            continue
                
                # Verificar tipo
                if isinstance(expected_type, tuple):
                    if isinstance(value, expected_type):
                        # Aplicar limitações de tamanho para strings
                        if isinstance(value, str):
                            value = value[:500]  # Limitar strings a 500 caracteres
                            # Remover caracteres potencialmente perigosos
                            value = ''.join(c for c in value if c.isprintable() or c.isspace())
                        
                        sanitized[field] = value
                else:
                    if isinstance(value, expected_type):
                        # Aplicar limitações de tamanho para strings
                        if isinstance(value, str):
                            value = value[:500]  # Limitar strings a 500 caracteres
                            # Remover caracteres potencialmente perigosos
                            value = ''.join(c for c in value if c.isprintable() or c.isspace())
                        
                        sanitized[field] = value
        
        # Verificar se telegram_id está presente
        if 'telegram_id' not in sanitized:
            raise ValueError("telegram_id é obrigatório")
        
        return sanitized
    
    def log_lgpd_consent(self, user_id: int, telegram_id: int, ip_address: str = "unknown") -> Dict[str, Any]:
        """Registra consentimento LGPD do usuário.
        
        Args:
            user_id: ID interno do usuário
            telegram_id: ID do Telegram
            ip_address: Endereço IP do usuário
            
        Returns:
            Dict com dados do consentimento registrado
        """
        consent_data = {
            "version": "1.0",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip_address,
            "user_agent": "Telegram Bot",
            "consent_type": "explicit",
            "terms_version": "2025-01-09",
            "privacy_policy_version": "2025-01-09"
        }
        
        # Log estruturado para auditoria
        logger.info(
            "LGPD consent registered",
            extra={
                "event_type": "lgpd_consent",
                "user_id": user_id,
                "telegram_id": telegram_id,
                "consent_data": consent_data,
                "timestamp": consent_data["accepted_at"]
            }
        )
        
        return consent_data
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Criptografa dados sensíveis como chaves Pix.
        
        Args:
            data: Dados a serem criptografados
            
        Returns:
            String criptografada em base64
        """
        if not data:
            return ""
        
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Erro ao criptografar dados: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis.
        
        Args:
            encrypted_data: Dados criptografados em base64
            
        Returns:
            String descriptografada
        """
        if not encrypted_data:
            return ""
        
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {e}")
            raise
    
    def strip_exif_data(self, image_bytes: bytes) -> bytes:
        """Remove metadados EXIF de imagens.
        
        Args:
            image_bytes: Bytes da imagem original
            
        Returns:
            Bytes da imagem sem metadados EXIF
        """
        try:
            # Abre a imagem
            image = Image.open(io.BytesIO(image_bytes))
            
            # Log dos metadados encontrados (para auditoria)
            exif_data = image.getexif()
            if exif_data:
                exif_info = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_info[tag] = str(value)[:100]  # Limita tamanho para log
                
                logger.info(
                    "EXIF data stripped",
                    extra={
                        "event_type": "exif_strip",
                        "exif_tags_found": list(exif_info.keys()),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            
            # Remove todos os metadados EXIF
            clean_image = Image.new(image.mode, image.size)
            clean_image.putdata(list(image.getdata()))
            
            # Salva a imagem limpa
            output_buffer = io.BytesIO()
            clean_image.save(output_buffer, format=image.format or 'JPEG')
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao remover EXIF: {e}")
            # Retorna imagem original se houver erro
            return image_bytes
    
    def log_sensitive_action(self, action: str, user_id: int, details: Dict[str, Any] = None):
        """Registra ações sensíveis para auditoria.
        
        Args:
            action: Tipo da ação (ex: 'data_export', 'data_deletion', 'payment')
            user_id: ID do usuário
            details: Detalhes adicionais da ação
        """
        log_data = {
            "event_type": "sensitive_action",
            "action": action,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        }
        
        logger.info(
            f"Sensitive action: {action}",
            extra=log_data
        )
    
    def validate_pix_key(self, pix_key: str) -> bool:
        """Valida formato de chave Pix.
        
        Args:
            pix_key: Chave Pix a ser validada
            
        Returns:
            True se válida, False caso contrário
        """
        if not pix_key:
            return False
        
        pix_key = pix_key.strip()
        
        # CPF (11 dígitos)
        if pix_key.replace('.', '').replace('-', '').isdigit() and len(pix_key.replace('.', '').replace('-', '')) == 11:
            return True
        
        # CNPJ (14 dígitos)
        if pix_key.replace('.', '').replace('-', '').replace('/', '').isdigit() and len(pix_key.replace('.', '').replace('-', '').replace('/', '')) == 14:
            return True
        
        # Email
        if '@' in pix_key and '.' in pix_key.split('@')[1]:
            return True
        
        # Telefone (formato +5511999999999)
        if pix_key.startswith('+55') and len(pix_key) >= 13:
            return True
        
        # Chave aleatória (UUID)
        if len(pix_key) == 36 and pix_key.count('-') == 4:
            return True
        
        return False
    
    def hash_user_data(self, data: str) -> str:
        """Gera hash de dados do usuário para anonimização.
        
        Args:
            data: Dados a serem hasheados
            
        Returns:
            Hash SHA-256 dos dados
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_data_retention_policy(self) -> Dict[str, int]:
        """Retorna política de retenção de dados em dias.
        
        Returns:
            Dict com tipos de dados e tempo de retenção
        """
        return {
            "user_posts": 365 * 2,  # 2 anos
            "payment_data": 365 * 5,  # 5 anos (obrigatório fiscal)
            "consent_logs": 365 * 5,  # 5 anos (LGPD)
            "audit_logs": 365 * 3,  # 3 anos
            "inactive_users": 365 * 1,  # 1 ano sem atividade
        }
    
    def anonymize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonimiza dados do usuário para exportação.
        
        Args:
            user_data: Dados originais do usuário
            
        Returns:
            Dados anonimizados
        """
        anonymized = user_data.copy()
        
        # Remove dados identificáveis
        sensitive_fields = ['telegram_id', 'pix_key_encrypted', 'ip_address']
        for field in sensitive_fields:
            if field in anonymized:
                if field == 'telegram_id':
                    anonymized[field] = self.hash_user_data(str(anonymized[field]))
                else:
                    anonymized[field] = "[REDACTED]"
        
        return anonymized
    
    async def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """Registra ação do usuário para auditoria.
        
        Args:
            user_id: ID do usuário
            action: Tipo da ação realizada
            details: Detalhes adicionais da ação
        """
        log_data = {
            "event_type": "user_action",
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        }
        
        logger.info(
            f"User action: {action}",
            extra=log_data
        )
    


# Instância global do serviço
security_service = SecurityService()