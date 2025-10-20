"""Serviço de processamento e upload de mídia.

Este módulo implementa:
- Download de arquivos do Telegram
- Processamento de imagens com blur para usuários freemium
- Upload para Cloudinary
- Suporte para imagens e vídeos
"""

import logging
import io
import time
from typing import Optional, Dict, Any
from PIL import Image, ImageFilter
import cloudinary
import cloudinary.uploader
from moviepy.editor import VideoFileClip

from services.user_service import UserService
from services.monetization_service import MonetizationService
import config

logger = logging.getLogger(__name__)

class MediaService:
    """Serviço para processamento e upload de mídia."""
    
    def __init__(self, user_service: UserService, monetization_service: MonetizationService, bot_instance):
        """Inicializa o serviço de mídia."""
        self.user_service = user_service
        self.monetization_service = monetization_service
        self.bot = bot_instance
        
        # Configurar Cloudinary
        cloudinary.config(
            cloud_name=config.CLOUDINARY_CLOUD_NAME,
            api_key=config.CLOUDINARY_API_KEY,
            api_secret=config.CLOUDINARY_API_SECRET
        )
        
        logger.info("MediaService inicializado com Cloudinary")
    
    async def process_and_upload_media(self, file_id: str, user_id: int, media_type: str = 'photo') -> Dict[str, Any]:
        """Processa e faz upload de mídia.
        
        Args:
            file_id: ID do arquivo no Telegram
            user_id: ID do usuário
            media_type: Tipo de mídia ('photo' ou 'video')
            
        Returns:
            Dict com URL da mídia e informações adicionais
        """
        try:
            # 1. Baixar arquivo do Telegram
            file_info = await self.bot.get_file(file_id)
            downloaded_file = await self.bot.download_file(file_info.file_path)
            
            # Converter BytesIO para bytes se necessário
            if isinstance(downloaded_file, io.BytesIO):
                downloaded_file = downloaded_file.getvalue()
            elif hasattr(downloaded_file, 'read'):
                # Se tem método read, ler o conteúdo
                downloaded_file = downloaded_file.read()
            elif isinstance(downloaded_file, bytes):
                # Já está em bytes, não precisa converter
                pass
            elif isinstance(downloaded_file, str):
                # Se for string, converter para bytes
                downloaded_file = downloaded_file.encode('utf-8')
            else:
                # Tentar converter para bytes como último recurso
                try:
                    downloaded_file = bytes(downloaded_file)
                except (TypeError, ValueError) as e:
                    logger.error(f"Erro ao converter arquivo para bytes: {e}")
                    raise ValueError(f"Não foi possível converter arquivo para bytes: {type(downloaded_file)}")
            
            # 2. Verificar status premium do usuário
            user = await self.user_service.get_user_profile(user_id)
            user_data = user.to_dict() if user else None
            is_premium = self.monetization_service.is_premium_user(user_data)
            
            # 3. Processar mídia baseado no tipo
            if media_type == 'photo':
                return await self._process_image(downloaded_file, user_id, is_premium)
            elif media_type == 'video':
                return await self._process_video(downloaded_file, user_id, is_premium)
            else:
                raise ValueError(f"Tipo de mídia não suportado: {media_type}")
                
        except Exception as e:
            logger.error(f"Erro ao processar mídia para usuário {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None
            }
    
    async def _process_image(self, image_bytes: bytes, user_id: int, is_premium: bool) -> Dict[str, Any]:
        """Processa imagem com blur condicional.
        
        Args:
            image_bytes: Bytes da imagem
            user_id: ID do usuário
            is_premium: Se o usuário é premium
            
        Returns:
            Dict com resultado do processamento
        """
        try:
            # Abrir imagem
            img = Image.open(io.BytesIO(image_bytes))
            
            # Converter para RGB se necessário
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Aplicar blur se não for premium
            if not is_premium:
                logger.info(f"Aplicando blur para usuário freemium {user_id}")
                img = img.filter(ImageFilter.GaussianBlur(radius=15))
                
                # Adicionar marca d'água de blur
                # TODO: Implementar marca d'água "Desbloqueie com Premium"
            
            # Converter para bytes
            output_buffer = io.BytesIO()
            img.save(output_buffer, format='JPEG', quality=85, optimize=True)
            output_buffer.seek(0)
            
            # Upload para Cloudinary
            upload_result = cloudinary.uploader.upload(
                output_buffer.getvalue(),
                folder="user_posts",
                public_id=f"user_{user_id}_{int(time.time())}",
                resource_type="image",
                format="jpg",
                transformation=[
                    {'width': 1080, 'height': 1080, 'crop': 'limit'},
                    {'quality': 'auto:good'}
                ]
            )
            
            logger.info(f"Imagem processada e enviada para Cloudinary: {upload_result.get('public_id')}")
            
            return {
                'success': True,
                'url': upload_result.get('secure_url'),
                'public_id': upload_result.get('public_id'),
                'media_type': 'image',
                'is_blurred': not is_premium,
                'width': upload_result.get('width'),
                'height': upload_result.get('height')
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None
            }
    
    async def _process_video(self, video_bytes: bytes, user_id: int, is_premium: bool) -> Dict[str, Any]:
        """Processa vídeo com blur condicional.
        
        Args:
            video_bytes: Bytes do vídeo
            user_id: ID do usuário
            is_premium: Se o usuário é premium
            
        Returns:
            Dict com resultado do processamento
        """
        try:
            # Salvar temporariamente para processamento
            temp_input_path = f"/tmp/input_{user_id}_{int(time.time())}.mp4"
            temp_output_path = f"/tmp/output_{user_id}_{int(time.time())}.mp4"
            
            with open(temp_input_path, 'wb') as f:
                f.write(video_bytes)
            
            # Carregar vídeo
            video = VideoFileClip(temp_input_path)
            
            # Aplicar blur se não for premium
            if not is_premium:
                logger.info(f"Aplicando blur em vídeo para usuário freemium {user_id}")
                # Aplicar filtro de blur no vídeo
                video = video.fx(lambda clip: clip.resize(0.3).resize(video.size))
                
                # TODO: Adicionar marca d'água "Desbloqueie com Premium"
            
            # Redimensionar e otimizar
            video = video.resize(height=720)  # Máximo 720p
            
            # Salvar vídeo processado
            video.write_videofile(
                temp_output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Upload para Cloudinary
            upload_result = cloudinary.uploader.upload(
                temp_output_path,
                folder="user_posts",
                public_id=f"user_{user_id}_video_{int(time.time())}",
                resource_type="video",
                format="mp4"
            )
            
            # Limpar arquivos temporários
            import os
            try:
                os.remove(temp_input_path)
                os.remove(temp_output_path)
            except:
                pass
            
            video.close()
            
            logger.info(f"Vídeo processado e enviado para Cloudinary: {upload_result.get('public_id')}")
            
            return {
                'success': True,
                'url': upload_result.get('secure_url'),
                'public_id': upload_result.get('public_id'),
                'media_type': 'video',
                'is_blurred': not is_premium,
                'duration': upload_result.get('duration'),
                'width': upload_result.get('width'),
                'height': upload_result.get('height')
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar vídeo: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None
            }
    
    async def delete_media(self, public_id: str) -> bool:
        """Remove mídia do Cloudinary.
        
        Args:
            public_id: ID público da mídia no Cloudinary
            
        Returns:
            True se removido com sucesso
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            logger.error(f"Erro ao remover mídia {public_id}: {e}")
            return False
    
    async def get_media_info(self, public_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de uma mídia.
        
        Args:
            public_id: ID público da mídia no Cloudinary
            
        Returns:
            Dict com informações da mídia ou None se não encontrada
        """
        try:
            result = cloudinary.api.resource(public_id)
            return {
                'public_id': result.get('public_id'),
                'url': result.get('secure_url'),
                'format': result.get('format'),
                'width': result.get('width'),
                'height': result.get('height'),
                'bytes': result.get('bytes'),
                'created_at': result.get('created_at')
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações da mídia {public_id}: {e}")
            return None
    
    def generate_thumbnail_url(self, public_id: str, width: int = 300, height: int = 300) -> str:
        """Gera URL de thumbnail para uma mídia.
        
        Args:
            public_id: ID público da mídia
            width: Largura do thumbnail
            height: Altura do thumbnail
            
        Returns:
            URL do thumbnail
        """
        return cloudinary.CloudinaryImage(public_id).build_url(
            width=width,
            height=height,
            crop="fill",
            quality="auto:good",
            format="jpg"
        )
    
    def is_premium_user(self, user_data: Dict[str, Any]) -> bool:
        """Verifica se usuário é premium.
        
        Args:
            user_data: Dados do usuário
            
        Returns:
            True se for premium
        """
        if not user_data:
            return False
        
        plan_type = user_data.get('plan_type', 'free')
        return plan_type in ['premium', 'diamond']

# Instância global do serviço (será inicializada no main.py)
media_service = None

def initialize_media_service(user_service: UserService, monetization_service: MonetizationService, bot_instance):
    """Inicializa o serviço de mídia global."""
    global media_service
    media_service = MediaService(user_service, monetization_service, bot_instance)
    return media_service