from __future__ import annotations
from typing import Tuple, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)
WARN_COOLDOWN_SECONDS = 6 * 60 * 60  # 6h

def _now() -> float:
    return time.time()

def check_bot_admin_permissions(context, chat) -> Tuple[bool, Dict[str, Any]]:
    """
    Em grupos, can_post_messages costuma vir None -> considerar permitido.
    Requisitos: ser admin, poder apagar mensagens; se for fórum, poder gerenciar tópicos.
    """
    # Para compatibilidade com context.bot que tem atributo id
    bot_id = getattr(context.bot, 'id', None)
    if bot_id is None:
        # Se não tem id, tenta obter via get_me() - mas essa função não é async
        # então mantemos a lógica original para não quebrar
        bot_id = context.bot.id
    member = context.bot.get_chat_member(chat.id, bot_id)
    status = getattr(member, "status", "")
    is_admin = status in ("administrator", "creator")

    can_delete = bool(getattr(member, "can_delete_messages", False))
    raw_can_post = getattr(member, "can_post_messages", None)
    can_post = True if raw_can_post is None else bool(raw_can_post)

    is_forum = bool(getattr(chat, "is_forum", False))
    can_manage_topics = True if not is_forum else bool(getattr(member, "can_manage_topics", False))

    ok = is_admin and can_delete and can_post and can_manage_topics
    details = dict(
        is_admin=is_admin,
        can_delete=can_delete,
        can_post=can_post,
        raw_can_post=raw_can_post,
        is_forum=is_forum,
        can_manage_topics=can_manage_topics,
    )
    return ok, details

def maybe_warn_permissions(context, chat):
    """Evita spam: avisa no máximo 1x a cada 6h por chat."""
    ok, d = check_bot_admin_permissions(context, chat)
    if ok:
        return
    key = ("perm_warn_last", chat.id)
    last = context.bot_data.get(key, 0)
    if _now() - last < WARN_COOLDOWN_SECONDS:
        logger.warning("Permission warn suppressed (cooldown). chat=%s details=%s", chat.id, d)
        return
    text = (
        "🔒 *Permissões Necessárias*\n\n"
        "Para o sistema funcionar, o bot precisa de:\n"
        "• ✉️ *Enviar mensagens* (em grupos já é permitido por padrão)\n"
        "• 🗑️ *Apagar mensagens* (para renovar o menu)\n"
        + ("• 🧵 *Gerenciar tópicos* (grupo com tópicos)\n" if d.get('is_forum') else "")
        + "\nSe ainda falhar, torne o bot *Administrador* e habilite as permissões acima."
    )
    try:
        context.bot.send_message(chat.id, text, parse_mode="Markdown")
    except Exception as e:
        logger.warning("Falha ao enviar aviso de permissão: %s", e)
    context.bot_data[key] = _now()
    logger.warning("Bot lacks permissions in chat %s: %s", chat.id, d)

# Funções de compatibilidade com versão anterior
async def check_bot_admin_permissions_old(bot, chat_id):
    """Função de compatibilidade - usar check_bot_admin_permissions(context, chat) preferencialmente"""
    logger.info(f"🔍 Verificando permissões do bot no chat {chat_id}")
    try:
        # Obter informações do bot usando get_me()
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_info.id)
        status = getattr(member, "status", "")
        logger.info(f"📊 Status do bot no chat {chat_id}: {status}")
        is_admin = status in ("administrator", "creator")
        logger.info(f"✅ Bot é admin no chat {chat_id}: {is_admin}")
        return is_admin
    except Exception as e:
        logger.error(f"❌ Erro ao verificar permissões do bot no chat {chat_id}: {e}")
        return False

async def send_permission_warning(bot, chat_id):
    """Função de compatibilidade - usar maybe_warn_permissions(context, chat) preferencialmente"""
    logger.warning("Usando função de compatibilidade send_permission_warning - considere migrar")
    try:
        text = (
            "🔒 *Permissões Necessárias*\n\n"
            "Para o sistema funcionar, o bot precisa ser *Administrador* com:\n"
            "• ✉️ *Enviar mensagens*\n"
            "• 🗑️ *Apagar mensagens*\n"
            "• 🧵 *Gerenciar tópicos* (se aplicável)"
        )
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Falha ao enviar aviso de permissão: {e}")

def is_admin(user_id: int, chat_id: int, bot) -> bool:
    """Verifica se o usuário é administrador do chat."""
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Erro ao verificar se usuário {user_id} é admin: {e}")
        return False

async def check_bot_permissions_in_group(bot, chat_id: int) -> bool:
    """Verifica se o bot tem permissões adequadas no grupo."""
    try:
        bot_info = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id, bot_info.id)
        logger.info(f"🤖 Bot {bot_info.username} status no grupo {chat_id}: {bot_member.status}")
        
        if bot_member.status == 'left':
            logger.error(f"❌ Bot não está no grupo {chat_id}")
            return False
        elif bot_member.status == 'kicked':
            logger.error(f"❌ Bot foi removido do grupo {chat_id}")
            return False
        elif bot_member.status in ['administrator', 'member']:
            logger.info(f"✅ Bot tem acesso ao grupo {chat_id}")
            return True
        else:
            logger.warning(f"⚠️ Status desconhecido do bot no grupo {chat_id}: {bot_member.status}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar permissões do bot no grupo {chat_id}: {e}")
        return False

async def is_group_admin(bot, chat_id: int, user_id: int) -> bool:
    """Verifica se o usuário é administrador do grupo (versão assíncrona)."""
    try:
        logger.info(f"🔍 Verificando se usuário {user_id} é admin do grupo {chat_id}")
        
        # Constante para o ID do GroupAnonymousBot
        GROUP_ANONYMOUS_BOT_ID = 1087968824
        
        # Verifica se é o GroupAnonymousBot (admin anônimo)
        if user_id == GROUP_ANONYMOUS_BOT_ID:
            logger.info(f"🎭 Detectado GroupAnonymousBot - Admin enviando comando de forma anônima")
            
            # Verifica se o bot tem permissões no grupo
            bot_has_access = await check_bot_permissions_in_group(bot, chat_id)
            if not bot_has_access:
                logger.error(f"❌ Bot não tem acesso adequado ao grupo {chat_id}")
                return False
            
            # Se chegou até aqui, é um admin anônimo em um grupo onde o bot tem acesso
            logger.info(f"✅ GroupAnonymousBot detectado - Tratando como admin válido")
            logger.info(f"💡 Apenas administradores podem enviar mensagens anônimas em grupos")
            return True
        
        # Primeiro, vamos verificar se o bot tem permissões para acessar informações do grupo
        bot_has_access = await check_bot_permissions_in_group(bot, chat_id)
        if not bot_has_access:
            logger.error(f"❌ Bot não tem acesso adequado ao grupo {chat_id}")
            return False
        
        # Agora verifica o usuário
        member = await bot.get_chat_member(chat_id, user_id)
        logger.info(f"📊 Status do usuário {user_id}: {member.status}")
        
        # Log adicional para debug
        if hasattr(member, 'user'):
            logger.info(f"👤 Dados do usuário: ID={member.user.id}, Username={getattr(member.user, 'username', 'N/A')}")
        
        # Se o status for 'left', pode ser um problema de cache do Telegram
        if member.status == 'left':
            logger.warning(f"⚠️ Usuário {user_id} aparece como 'left' no grupo {chat_id}. Isso pode ser um problema de cache do Telegram.")
            logger.info(f"💡 Sugestão: Verifique se o usuário realmente está no grupo e se o bot tem permissões adequadas.")
            return False
        
        is_admin = member.status in ['administrator', 'creator']
        logger.info(f"✅ Usuário {user_id} é admin: {is_admin}")
        return is_admin
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar se usuário {user_id} é admin do grupo {chat_id}: {e}")
        logger.error(f"🔧 Tipo do erro: {type(e).__name__}")
        return False