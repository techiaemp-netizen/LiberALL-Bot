"""Safe reply utility for handling Telegram responses with aiogram.

This module provides a safe way to send replies that works with both
regular messages and callback queries, with proper error handling.
Compatible with aiogram 3.x.
"""

import logging
from typing import Optional, Union
from aiogram import Bot
from aiogram.types import Message, CallbackQuery


async def safe_reply(
    message_or_query: Union[Message, CallbackQuery], 
    text: str, 
    parse_mode: Optional[str] = None, 
    bot: Optional[Bot] = None
) -> bool:
    """
    Envia uma resposta de forma segura usando aiogram.
    
    Args:
        message_or_query: Message ou CallbackQuery do aiogram
        text: Texto da resposta
        parse_mode: Modo de parsing (HTML, Markdown, etc.)
        bot: Instância do Bot (opcional, usa o bot da mensagem se não fornecido)
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    logger = logging.getLogger('LiberALL')
    
    try:
        if isinstance(message_or_query, CallbackQuery):
            # Para callback queries, responder primeiro e depois enviar mensagem
            await message_or_query.answer()
            if message_or_query.message:
                await message_or_query.message.answer(text, parse_mode=parse_mode)
                logger.info("Resposta enviada com sucesso via CallbackQuery")
                return True
        elif isinstance(message_or_query, Message):
            # Para mensagens normais, usar reply
            await message_or_query.reply(text, parse_mode=parse_mode)
            logger.info("Resposta enviada com sucesso via Message.reply")
            return True
        else:
            logger.error(f"Tipo de mensagem não suportado: {type(message_or_query)}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao enviar resposta: {e}")
        return False