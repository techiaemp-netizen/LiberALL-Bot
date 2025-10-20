import asyncio
import logging
import random
import time
from typing import Any, Optional

import aiohttp
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

class TelegramClientError(Exception):
    """Exceção customizada para erros do cliente Telegram"""
    pass

class RobustTelegramClient:
    """
    Wrapper robusto para aiogram Bot com retry logic, timeouts e tratamento de erros de conectividade
    """
    
    def __init__(self, token: str, max_retries: int = 3, base_delay: float = 1.0):
        """Inicializa o cliente robusto do Telegram."""
        self.token = token
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger(__name__)
        
        # Métricas de conectividade
        self.connection_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'last_success_time': None,
            'last_failure_time': None,
            'consecutive_failures': 0,
            'fallback_activations': 0
        }
        
        # Inicializa o bot primeiro
        self.bot = Bot(token)
        
        # Configura timeout personalizado
        self.bot.request_timeout = 30
        
        # Cria sessão personalizada com configurações otimizadas
        timeout = aiohttp.ClientTimeout(
            total=45,  # Timeout total
            connect=10,  # Timeout de conexão
            sock_read=20  # Timeout de leitura
        )
        
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60
        )
        
        session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )
        
        # Atribui a sessão ao bot se a propriedade existir
        if hasattr(self.bot, '_session'):
            self.bot._session = session
        
        self.logger.info(f"🔧 RobustTelegramClient inicializado com max_retries={max_retries}")
        self._log_connection_info()
    
    def _log_connection_info(self):
        """Registra informações detalhadas sobre a conexão."""
        stats = self.connection_stats
        success_rate = (stats['successful_requests'] / max(stats['total_requests'], 1)) * 100
        
        self.logger.info(f"📊 Estatísticas de conectividade:")
        self.logger.info(f"   • Total de requisições: {stats['total_requests']}")
        self.logger.info(f"   • Taxa de sucesso: {success_rate:.1f}%")
        self.logger.info(f"   • Tentativas de retry: {stats['retry_attempts']}")
        self.logger.info(f"   • Falhas consecutivas: {stats['consecutive_failures']}")
        self.logger.info(f"   • Ativações de fallback: {stats['fallback_activations']}")
        
        if stats['last_success_time']:
            time_since_success = time.time() - stats['last_success_time']
            self.logger.info(f"   • Último sucesso: {time_since_success:.1f}s atrás")
    
    async def _test_connectivity(self):
        """Testa a conectividade básica com a API do Telegram."""
        start_time = time.time()
        try:
            self.connection_stats['total_requests'] += 1
            await self.get_me()
            
            # Atualiza estatísticas de sucesso
            self.connection_stats['successful_requests'] += 1
            self.connection_stats['last_success_time'] = time.time()
            self.connection_stats['consecutive_failures'] = 0
            
            response_time = (time.time() - start_time) * 1000
            self.logger.debug(f"✅ Teste de conectividade bem-sucedido ({response_time:.0f}ms)")
        except Exception as e:
            # Atualiza estatísticas de falha
            self.connection_stats['failed_requests'] += 1
            self.connection_stats['last_failure_time'] = time.time()
            self.connection_stats['consecutive_failures'] += 1
            
            response_time = (time.time() - start_time) * 1000
            self.logger.warning(f"⚠️ Falha no teste de conectividade ({response_time:.0f}ms): {e}")
            raise
    
    async def _activate_fallback_mode(self):
        """Ativa modo de fallback com configurações mais conservadoras."""
        self.connection_stats['fallback_activations'] += 1
        
        self.logger.warning("🔧 Ativando modo fallback...")
        self.logger.warning(f"   • Tentativa de fallback #{self.connection_stats['fallback_activations']}")
        self.logger.warning(f"   • Falhas consecutivas: {self.connection_stats['consecutive_failures']}")
        
        # Recria a sessão com configurações mais conservadoras
        if hasattr(self.bot, '_session') and self.bot._session:
            await self.bot._session.close()
            self.logger.debug("🔒 Sessão anterior fechada")
        
        # Configurações de fallback mais conservadoras
        fallback_timeout = aiohttp.ClientTimeout(
            total=60,  # Timeout total maior
            connect=15,  # Timeout de conexão maior
            sock_read=30  # Timeout de leitura maior
        )
        
        connector = aiohttp.TCPConnector(
            limit=10,  # Menos conexões simultâneas
            limit_per_host=5,
            ttl_dns_cache=600,
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        fallback_session = aiohttp.ClientSession(
            timeout=fallback_timeout,
            connector=connector
        )
        
        if hasattr(self.bot, '_session'):
            self.bot._session = fallback_session
        
        self.logger.info("✅ Modo fallback ativado com configurações conservadoras")
        self.logger.info(f"   • Timeout total: 60s, conexão: 15s, leitura: 30s")
        self.logger.info(f"   • Limite de conexões: 10 (5 por host)")
        
        # Log das estatísticas atuais
        self._log_connection_info()
    
    async def close(self):
        """Fecha a sessão HTTP personalizada."""
        if hasattr(self.bot, '_session') and self.bot._session:
            await self.bot._session.close()
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calcular delay exponencial com jitter"""
        max_delay = 30.0  # Define max_delay aqui
        delay = min(self.base_delay * (2 ** attempt), max_delay)
        # Adicionar jitter para evitar thundering herd
        jitter = delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
        return max(0.1, delay + jitter)
    
    async def _retry_request(self, func, *args, **kwargs):
        """Executa uma função com retry automático."""
        last_exception = None
        func_name = getattr(func, '__name__', str(func))
        
        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            try:
                self.connection_stats['total_requests'] += 1
                result = await func(*args, **kwargs)
                
                # Atualiza estatísticas de sucesso
                self.connection_stats['successful_requests'] += 1
                self.connection_stats['last_success_time'] = time.time()
                self.connection_stats['consecutive_failures'] = 0
                
                response_time = (time.time() - start_time) * 1000
                if attempt > 0:
                    self.logger.info(f"✅ {func_name} bem-sucedido após {attempt + 1} tentativas ({response_time:.0f}ms)")
                else:
                    self.logger.debug(f"✅ {func_name} bem-sucedido ({response_time:.0f}ms)")
                
                return result
                
            except Exception as e:
                last_exception = e
                response_time = (time.time() - start_time) * 1000
                
                # Atualiza estatísticas de falha
                self.connection_stats['failed_requests'] += 1
                self.connection_stats['last_failure_time'] = time.time()
                self.connection_stats['consecutive_failures'] += 1
                
                if not self._is_retryable_error(e):
                    self.logger.error(f"❌ Erro não recuperável em {func_name} ({response_time:.0f}ms): {e}")
                    raise
                
                if attempt < self.max_retries:
                    self.connection_stats['retry_attempts'] += 1
                    delay = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"⚠️ {func_name} - Tentativa {attempt + 1}/{self.max_retries + 1} falhou ({response_time:.0f}ms): {e}. "
                        f"Tentando novamente em {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"❌ {func_name} - Todas as {self.max_retries + 1} tentativas falharam ({response_time:.0f}ms). "
                        f"Último erro: {e}"
                    )
                    # Log estatísticas quando todas as tentativas falham
                    self._log_connection_info()
        
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Verificar se o erro é passível de retry"""
        retryable_errors = (
            aiohttp.ClientError,
            aiohttp.ServerTimeoutError,
            aiohttp.ClientConnectorError,
            aiohttp.ClientOSError,
            asyncio.TimeoutError,
            ConnectionError,
            OSError
        )
        
        if isinstance(error, retryable_errors):
            return True
        
        if isinstance(error, TelegramAPIError):
            # Retry apenas para erros temporários do Telegram
            retryable_codes = [429, 500, 502, 503, 504]
            return any(str(code) in str(error) for code in retryable_codes)
        
        return False
    
    def with_retry(self, method_name: str = None):
        """Decorator para adicionar retry logic a métodos"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await self._retry_request(func, *args, **kwargs)
            return wrapper
        return decorator
    
    @property
    def send_message(self):
        """Wrapper para send_message com retry"""
        @self.with_retry("send_message")
        async def _send_message(*args, **kwargs):
            return await self.bot.send_message(*args, **kwargs)
        return _send_message
    
    @property
    def edit_message_text(self):
        """Wrapper para edit_message_text com retry"""
        @self.with_retry("edit_message_text")
        async def _edit_message_text(*args, **kwargs):
            return await self.bot.edit_message_text(*args, **kwargs)
        return _edit_message_text
    
    @property
    def edit_message_reply_markup(self):
        """Wrapper para edit_message_reply_markup com retry"""
        @self.with_retry("edit_message_reply_markup")
        async def _edit_message_reply_markup(*args, **kwargs):
            return await self.bot.edit_message_reply_markup(*args, **kwargs)
        return _edit_message_reply_markup
    
    @property
    def answer_callback_query(self):
        """Wrapper para answer_callback_query com retry"""
        @self.with_retry("answer_callback_query")
        async def _answer_callback_query(*args, **kwargs):
            return await self.bot.answer_callback_query(*args, **kwargs)
        return _answer_callback_query
    
    @property
    def get_me(self):
        """Wrapper para get_me com retry"""
        @self.with_retry("get_me")
        async def _get_me(*args, **kwargs):
            return await self.bot.get_me(*args, **kwargs)
        return _get_me
    
    @property
    def get_chat_member(self):
        """Wrapper para get_chat_member com retry"""
        @self.with_retry("get_chat_member")
        async def _get_chat_member(*args, **kwargs):
            return await self.bot.get_chat_member(*args, **kwargs)
        return _get_chat_member
    
    @property
    def reply_to(self):
        """Wrapper para reply_to com retry"""
        @self.with_retry("reply_to")
        async def _reply_to(*args, **kwargs):
            return await self.bot.reply_to(*args, **kwargs)
        return _reply_to
    
    async def polling_with_retry(self, non_stop: bool = True, timeout: int = 20):
        """Inicia o polling com retry automático em caso de falhas."""
        self.logger.info("🚀 Iniciando polling robusto...")
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while True:
            try:
                # Testa conectividade antes de iniciar polling
                await self._test_connectivity()
                
                await self.bot.polling(non_stop=non_stop, timeout=timeout)
                consecutive_failures = 0  # Reset contador em caso de sucesso
                break  # Se chegou aqui, o polling terminou normalmente
            except Exception as e:
                consecutive_failures += 1
                self.logger.error(f"❌ Erro no polling (tentativa {consecutive_failures}): {e}")
                
                if not non_stop:
                    raise
                
                # Implementa fallback progressivo
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.critical("🚨 Muitas falhas consecutivas. Ativando modo fallback...")
                    await self._activate_fallback_mode()
                    consecutive_failures = 0
                
                # Aguarda progressivamente mais tempo entre tentativas
                wait_time = min(5 * consecutive_failures, 60)
                self.logger.info(f"🔄 Tentando reconectar em {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
    
    def __getattr__(self, name):
        """Proxy para métodos não explicitamente wrappados"""
        if hasattr(self.bot, name):
            attr = getattr(self.bot, name)
            if callable(attr):
                return self.with_retry(name)(attr)
            return attr
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    # Métodos de handler que precisam ser expostos diretamente
    def message_handler(self, *args, **kwargs):
        return self.bot.message_handler(*args, **kwargs)
    
    def callback_query_handler(self, *args, **kwargs):
        return self.bot.callback_query_handler(*args, **kwargs)
    
    def register_message_handler(self, *args, **kwargs):
        return self.bot.register_message_handler(*args, **kwargs)
    
    def register_callback_query_handler(self, *args, **kwargs):
        return self.bot.register_callback_query_handler(*args, **kwargs)