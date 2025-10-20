import logging
import asyncio
import aiohttp
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatInviteLink

# Cache para links de convite válidos
_invite_cache = {}
_cache_duration = timedelta(minutes=5)  # Reduzido para 5 minutos para evitar links expirados

async def get_group_invite_url(bot: Bot, chat_id: int, logger: Optional[logging.Logger] = None, max_retries: int = 3, force_refresh: bool = False, prefer_join_request: bool = False) -> str:
    """Return a valid invite URL for a group.

    Tries multiple strategies to get a working invite link:
    1. Check cache for recent valid link (with validation)
    2. Export the primary invite link (most reliable)
    3. Create a new permanent invite link
    4. Create a temporary invite link (24h)
    5. Fallback to t.me link if possible
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info(f"🔗 Iniciando obtenção de link de convite para chat {chat_id}")
    
    # Verificar cache primeiro e validar o link
    cache_key = f"invite_{chat_id}"
    # Se solicitado, ignorar cache e forçar criação de novo link
    if force_refresh and cache_key in _invite_cache:
        logger.debug(f"♻️ Force refresh ativo: removendo link do cache para {chat_id}")
        try:
            del _invite_cache[cache_key]
        except Exception:
            _invite_cache.pop(cache_key, None)
    if cache_key in _invite_cache:
        cached_link, cached_time = _invite_cache[cache_key]
        cache_age = datetime.now() - cached_time
        logger.debug(f"📋 Link encontrado no cache (idade: {cache_age.total_seconds():.1f}s)")
        
        if cache_age < _cache_duration:
            logger.debug(f"🔍 Validando link do cache: {cached_link}")
            if await validate_invite_link(bot, cached_link, logger):
                logger.info(f"✅ Usando link válido do cache para chat {chat_id}")
                return cached_link
            else:
                logger.warning(f"❌ Link do cache inválido, removendo: {cached_link}")
            del _invite_cache[cache_key]
        else:
            logger.debug(f"⏰ Link do cache expirado, removendo")
            del _invite_cache[cache_key]

    # Se preferir join request, tentar primeiro criar link com pedido de aprovação
    if prefer_join_request:
        for attempt in range(max_retries):
            try:
                logger.debug(f"🔄 Tentativa {attempt + 1}/{max_retries}: Criando link com join request (preferência) para chat {chat_id}")
                invite: ChatInviteLink = await bot.create_chat_invite_link(
                    chat_id=chat_id,
                    name=f"LiberALL Bot - Join Request {datetime.now().strftime('%H:%M')}",
                    creates_join_request=True
                )
                link = invite.invite_link

                _invite_cache[cache_key] = (link, datetime.now())
                logger.info(f"✅ Link com join request (preferência) criado para chat {chat_id}: {link}")

                try:
                    logger.debug(f"🔍 Validando link com join request (preferência): {link}")
                    await validate_invite_link(bot, link, logger)
                except Exception as validation_error:
                    logger.warning(f"⚠️ Erro na validação do link com join request (preferência), mas continuando: {validation_error}")

                return link
            except Exception as e:
                logger.warning(f"❌ Falha ao criar link com join request (preferência) na tentativa {attempt + 1} para chat {chat_id}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

    # Preferir link público do grupo se houver username (link não expira)
    try:
        logger.debug(f"🔄 Verificando se o chat {chat_id} possui username público")
        chat = await bot.get_chat(chat_id)
        if getattr(chat, 'username', None):
            link = f"https://t.me/{chat.username}"
            _invite_cache[cache_key] = (link, datetime.now())
            logger.info(f"✅ Link público t.me preferido para chat {chat_id}: {link}")
            try:
                logger.debug(f"🔍 Validando link t.me preferido: {link}")
                await validate_invite_link(bot, link, logger)
            except Exception as validation_error:
                logger.warning(f"⚠️ Erro na validação do link t.me preferido, mas continuando: {validation_error}")
            return link
    except Exception as e:
        logger.warning(f"❌ Falha ao obter username público do chat {chat_id}: {e}")
    
    # Se force_refresh, priorizar criação de link novo em vez de exportar principal
    if force_refresh:
        for attempt in range(max_retries):
            try:
                logger.debug(f"🔄 Tentativa {attempt + 1}/{max_retries}: Criando link permanente (force) para chat {chat_id}")
                invite: ChatInviteLink = await bot.create_chat_invite_link(
                    chat_id=chat_id,
                    name=f"LiberALL Bot - Link Permanente {datetime.now().strftime('%H:%M')}"
                )
                link = invite.invite_link

                _invite_cache[cache_key] = (link, datetime.now())
                logger.info(f"✅ Link permanente criado (force) para chat {chat_id}: {link}")

                try:
                    logger.debug(f"🔍 Validando link permanente (force): {link}")
                    await validate_invite_link(bot, link, logger)
                except Exception as validation_error:
                    logger.warning(f"⚠️ Erro na validação do link permanente (force), mas continuando: {validation_error}")

                return link
            except Exception as e:
                logger.warning(f"❌ Falha ao criar link permanente (force) na tentativa {attempt + 1} para chat {chat_id}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

    # Estratégia 1 (preferida): Criar link permanente único para evitar rotacionar o link principal
    for attempt in range(max_retries):
        try:
            logger.debug(f"🔄 Tentativa {attempt + 1}/{max_retries}: Criando link permanente preferencial para chat {chat_id}")
            invite: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"LiberALL Bot - Link Permanente {datetime.now().strftime('%H:%M')}"
            )
            link = invite.invite_link

            # Salvar no cache imediatamente
            _invite_cache[cache_key] = (link, datetime.now())
            logger.info(f"✅ Link permanente preferencial criado para chat {chat_id}: {link}")

            # Tentar validar, mas não falhar se a validação der problema
            try:
                logger.debug(f"🔍 Validando link permanente preferencial: {link}")
                await validate_invite_link(bot, link, logger)
            except Exception as validation_error:
                logger.warning(f"⚠️ Erro na validação do link permanente preferencial, mas continuando: {validation_error}")

            return link
        except Exception as e:
            logger.warning(f"❌ Falha ao criar link permanente preferencial na tentativa {attempt + 1} para chat {chat_id}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)

    # Estratégia 2: Criar link com join request (pedido de aprovação) como fallback
    for attempt in range(max_retries):
        try:
            logger.debug(f"🔄 Tentativa {attempt + 1}/{max_retries}: Criando link com join request para chat {chat_id}")
            invite: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"LiberALL Bot - Join Request {datetime.now().strftime('%H:%M')}",
                creates_join_request=True
            )
            link = invite.invite_link

            _invite_cache[cache_key] = (link, datetime.now())
            logger.info(f"✅ Link com join request criado para chat {chat_id}: {link}")

            try:
                logger.debug(f"🔍 Validando link com join request: {link}")
                await validate_invite_link(bot, link, logger)
            except Exception as validation_error:
                logger.warning(f"⚠️ Erro na validação do link com join request, mas continuando: {validation_error}")

            return link
        except Exception as e:
            logger.warning(f"❌ Falha ao criar link com join request na tentativa {attempt + 1} para chat {chat_id}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)

    # Estratégia 3: Exportar link principal do chat (pode invalidar links anteriores se usado com frequência)
    for attempt in range(max_retries):
        try:
            logger.debug(f"🔄 Tentativa {attempt + 1}/{max_retries}: Exportando link principal para chat {chat_id}")
            url: str = await bot.export_chat_invite_link(chat_id)
            
            # Salvar no cache imediatamente após obter o link
            _invite_cache[cache_key] = (url, datetime.now())
            logger.info(f"✅ Link principal exportado para chat {chat_id}: {url}")
            
            # Tentar validar, mas não falhar se a validação der problema
            try:
                logger.debug(f"🔍 Validando link exportado: {url}")
                await validate_invite_link(bot, url, logger)
            except Exception as validation_error:
                logger.warning(f"⚠️ Erro na validação do link, mas continuando: {validation_error}")
            
            return url
                
        except Exception as e:
            logger.warning(f"❌ Falha ao exportar link principal na tentativa {attempt + 1} para chat {chat_id}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Reduzido para 1 segundo
    
    # Estratégia 4: Tentar criar link permanente (fallback)
    for attempt in range(max_retries):
        try:
            logger.debug(f"🔄 Tentativa {attempt + 1}/{max_retries}: Criando link permanente para chat {chat_id}")
            # Revogar links expirados conhecidos (se o bot tiver permissões)
            try:
                # Se houver link em cache, tentar revogar antes de criar novo para evitar conflito
                cache_key = f"invite_{chat_id}"
                if cache_key in _invite_cache:
                    cached_link, _ = _invite_cache[cache_key]
                    logger.debug(f"🗑️ Revogando link em cache antes de criar novo: {cached_link}")
                    # Não há método direto para revogar por URL, então ignoramos silenciosamente
            except Exception as revoke_err:
                logger.debug(f"⚠️ Falha ao tentar revogar link em cache: {revoke_err}")
            invite: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"LiberALL Bot - Link Permanente {datetime.now().strftime('%H:%M')}"
            )
            link = invite.invite_link
            
            # Salvar no cache imediatamente
            _invite_cache[cache_key] = (link, datetime.now())
            logger.info(f"✅ Link permanente criado para chat {chat_id}: {link}")
            
            # Tentar validar, mas não falhar se a validação der problema
            try:
                logger.debug(f"🔍 Validando link permanente: {link}")
                await validate_invite_link(bot, link, logger)
            except Exception as validation_error:
                logger.warning(f"⚠️ Erro na validação do link permanente, mas continuando: {validation_error}")
            
            return link
                
        except Exception as e:
            logger.warning(f"❌ Falha ao criar link permanente na tentativa {attempt + 1} para chat {chat_id}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Reduzido para 1 segundo
    
    # Estratégia 3: Tentar criar link temporário (24h)
    for attempt in range(max_retries):
        try:
            logger.debug(f"🔄 Tentativa {attempt + 1}/{max_retries}: Criando link temporário para chat {chat_id}")
            # Usar UTC para evitar expiração incorreta por diferença de fuso horário
            expire_date = datetime.now(timezone.utc) + timedelta(hours=24)
            invite: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"LiberALL Bot - Link 24h {datetime.now().strftime('%H:%M')}",
                expire_date=expire_date
            )
            link = invite.invite_link
            
            # Salvar no cache imediatamente
            _invite_cache[cache_key] = (link, datetime.now())
            logger.info(f"✅ Link temporário (24h) criado para chat {chat_id}: {link}")
            
            # Tentar validar, mas não falhar se a validação der problema
            try:
                logger.debug(f"🔍 Validando link temporário: {link}")
                await validate_invite_link(bot, link, logger)
            except Exception as validation_error:
                logger.warning(f"⚠️ Erro na validação do link temporário, mas continuando: {validation_error}")
            
            return link
                
        except Exception as e:
            logger.warning(f"❌ Falha ao criar link temporário na tentativa {attempt + 1} para chat {chat_id}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Reduzido para 1 segundo
    
    
    # Se todas as estratégias falharam
    error_msg = f"❌ Não foi possível obter nenhum link de convite válido para chat {chat_id} após {max_retries} tentativas"
    logger.error(error_msg)
    raise Exception(error_msg)

async def validate_invite_link(bot: Bot, invite_link: str, logger: Optional[logging.Logger] = None) -> bool:
    """Valida se um link de convite ainda está ativo fazendo uma requisição HTTP."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Validação básica de formato
        if not invite_link.startswith(('https://t.me/', 'https://telegram.me/')):
            logger.warning(f"Link com formato inválido: {invite_link}")
            return False
        
        # Teste real fazendo uma requisição HEAD para verificar se o link existe
        # Reduzindo timeout para 3 segundos para evitar bloqueios longos
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.head(invite_link, allow_redirects=True) as response:
                    # Links válidos do Telegram geralmente retornam 200 ou 302
                    is_valid = response.status in [200, 302]
                    if is_valid:
                        logger.debug(f"✅ Link validado com sucesso: {invite_link} (status: {response.status})")
                    else:
                        logger.warning(f"❌ Link inválido: {invite_link} (status: {response.status})")
                    return is_valid
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Timeout ao validar link: {invite_link}")
                # Em caso de timeout, assumir que o link é válido para não bloquear o fluxo
                logger.info(f"🔄 Assumindo link válido devido ao timeout: {invite_link}")
                return True
            except Exception as e:
                logger.warning(f"❌ Erro na requisição HTTP para validar link {invite_link}: {e}")
                # Em caso de erro de rede, assumir que o link é válido
                logger.info(f"🔄 Assumindo link válido devido ao erro de rede: {invite_link}")
                return True
                
    except Exception as e:
        logger.warning(f"❌ Erro geral ao validar link {invite_link}: {e}")
        # Em caso de erro geral, assumir que o link é válido
        logger.info(f"🔄 Assumindo link válido devido ao erro geral: {invite_link}")
        return True

def clear_invite_cache():
    """Limpa o cache de links de convite."""
    global _invite_cache
    _invite_cache.clear()