"""Serviço para remoção de metadados EXIF de imagens.

Este módulo implementa:
- Detecção de metadados EXIF
- Remoção segura de metadados
- Preservação da qualidade da imagem
- Logs de auditoria
"""

import io
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ExifTags
import piexif

logger = logging.getLogger(__name__)

class ExifService:
    """Serviço para manipulação de metadados EXIF."""
    
    def __init__(self):
        """Inicializa o serviço EXIF."""
        self.supported_formats = ['JPEG', 'JPG', 'TIFF', 'TIF']
        self.preserve_quality = True
    
    def has_exif_data(self, image_bytes: bytes) -> bool:
        """Verifica se a imagem contém dados EXIF.
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            True se contém EXIF, False caso contrário
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            exif_data = image.getexif()
            return len(exif_data) > 0
        except Exception as e:
            logger.warning(f"Erro ao verificar EXIF: {e}")
            return False
    
    def extract_exif_info(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extrai informações EXIF da imagem para auditoria.
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Dict com informações EXIF encontradas
        """
        exif_info = {
            "has_exif": False,
            "tags_found": [],
            "sensitive_data_detected": False,
            "location_data": False,
            "device_info": False
        }
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            exif_data = image.getexif()
            
            if not exif_data:
                return exif_info
            
            exif_info["has_exif"] = True
            
            # Tags sensíveis que devem ser removidas
            sensitive_tags = {
                'GPS': ['GPSInfo', 'GPS IFD'],
                'Device': ['Make', 'Model', 'Software', 'Artist', 'Copyright'],
                'Personal': ['UserComment', 'ImageDescription', 'XPComment', 'XPAuthor']
            }
            
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, f"Unknown_{tag_id}")
                exif_info["tags_found"].append(tag_name)
                
                # Verifica dados de localização
                if tag_name in ['GPSInfo'] or 'GPS' in tag_name:
                    exif_info["location_data"] = True
                    exif_info["sensitive_data_detected"] = True
                
                # Verifica informações do dispositivo
                if tag_name in sensitive_tags['Device']:
                    exif_info["device_info"] = True
                    exif_info["sensitive_data_detected"] = True
                
                # Verifica dados pessoais
                if tag_name in sensitive_tags['Personal']:
                    exif_info["sensitive_data_detected"] = True
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações EXIF: {e}")
        
        return exif_info
    
    def strip_exif_data(self, image_bytes: bytes, preserve_orientation: bool = True) -> Tuple[bytes, Dict[str, Any]]:
        """Remove todos os metadados EXIF da imagem.
        
        Args:
            image_bytes: Bytes da imagem original
            preserve_orientation: Se deve preservar orientação da imagem
            
        Returns:
            Tuple com (bytes da imagem limpa, info sobre remoção)
        """
        removal_info = {
            "original_size": len(image_bytes),
            "cleaned_size": 0,
            "exif_removed": False,
            "orientation_preserved": False,
            "format_preserved": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Abre a imagem
            image = Image.open(io.BytesIO(image_bytes))
            original_format = image.format
            
            # Extrai informações EXIF antes da remoção
            exif_info = self.extract_exif_info(image_bytes)
            
            # Preserva orientação se solicitado
            orientation = None
            if preserve_orientation and exif_info["has_exif"]:
                try:
                    exif_dict = piexif.load(image_bytes)
                    if piexif.ImageIFD.Orientation in exif_dict.get("0th", {}):
                        orientation = exif_dict["0th"][piexif.ImageIFD.Orientation]
                        removal_info["orientation_preserved"] = True
                except Exception:
                    pass
            
            # Aplica rotação baseada na orientação EXIF
            if orientation:
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
            
            # Cria nova imagem sem metadados
            clean_image = Image.new(image.mode, image.size)
            clean_image.putdata(list(image.getdata()))
            
            # Preserva paleta de cores se necessário
            if hasattr(image, 'palette') and image.palette:
                clean_image.putpalette(image.palette)
            
            # Salva a imagem limpa
            output_buffer = io.BytesIO()
            save_format = original_format if original_format in self.supported_formats else 'JPEG'
            
            # Configurações de qualidade
            save_kwargs = {}
            if save_format in ['JPEG', 'JPG']:
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
            
            clean_image.save(output_buffer, format=save_format, **save_kwargs)
            cleaned_bytes = output_buffer.getvalue()
            
            removal_info["cleaned_size"] = len(cleaned_bytes)
            removal_info["exif_removed"] = exif_info["has_exif"]
            
            # Log da remoção
            if exif_info["has_exif"]:
                logger.info(
                    "EXIF data removed from image",
                    extra={
                        "event_type": "exif_removal",
                        "original_size": removal_info["original_size"],
                        "cleaned_size": removal_info["cleaned_size"],
                        "size_reduction": removal_info["original_size"] - removal_info["cleaned_size"],
                        "sensitive_data_detected": exif_info["sensitive_data_detected"],
                        "location_data": exif_info["location_data"],
                        "device_info": exif_info["device_info"],
                        "tags_removed": len(exif_info["tags_found"]),
                        "timestamp": removal_info["timestamp"]
                    }
                )
            
            return cleaned_bytes, removal_info
            
        except Exception as e:
            logger.error(f"Erro ao remover EXIF: {e}")
            # Retorna imagem original em caso de erro
            removal_info["cleaned_size"] = len(image_bytes)
            return image_bytes, removal_info
    
    def process_image_safely(self, image_bytes: bytes, max_size_mb: int = 10) -> Tuple[bytes, Dict[str, Any]]:
        """Processa imagem de forma segura, removendo EXIF e validando tamanho.
        
        Args:
            image_bytes: Bytes da imagem
            max_size_mb: Tamanho máximo em MB
            
        Returns:
            Tuple com (bytes processados, info do processamento)
        """
        processing_info = {
            "success": False,
            "error": None,
            "size_valid": False,
            "format_supported": False,
            "exif_removed": False
        }
        
        try:
            # Valida tamanho
            size_mb = len(image_bytes) / (1024 * 1024)
            if size_mb > max_size_mb:
                processing_info["error"] = f"Imagem muito grande: {size_mb:.1f}MB (máximo: {max_size_mb}MB)"
                return image_bytes, processing_info
            
            processing_info["size_valid"] = True
            
            # Valida formato
            image = Image.open(io.BytesIO(image_bytes))
            if image.format not in self.supported_formats:
                processing_info["error"] = f"Formato não suportado: {image.format}"
                return image_bytes, processing_info
            
            processing_info["format_supported"] = True
            
            # Remove EXIF
            cleaned_bytes, removal_info = self.strip_exif_data(image_bytes)
            processing_info["exif_removed"] = removal_info["exif_removed"]
            processing_info["success"] = True
            
            return cleaned_bytes, processing_info
            
        except Exception as e:
            processing_info["error"] = str(e)
            logger.error(f"Erro no processamento seguro da imagem: {e}")
            return image_bytes, processing_info
    
    def get_image_info(self, image_bytes: bytes) -> Dict[str, Any]:
        """Obtém informações básicas da imagem.
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Dict com informações da imagem
        """
        info = {
            "format": None,
            "size": (0, 0),
            "mode": None,
            "file_size": len(image_bytes),
            "has_exif": False,
            "supported": False
        }
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            info["format"] = image.format
            info["size"] = image.size
            info["mode"] = image.mode
            info["has_exif"] = self.has_exif_data(image_bytes)
            info["supported"] = image.format in self.supported_formats
            
        except Exception as e:
            logger.error(f"Erro ao obter informações da imagem: {e}")
        
        return info

# Instância global do serviço
exif_service = ExifService()