"""
Serviço de Idempotência para evitar ações duplicadas.

Garante que operações críticas (favorite, match, comments:write, publish)
sejam executadas apenas uma vez dentro de uma janela de tempo (TTL).
"""
import asyncio
import logging
import time
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class IdempotencyService:
    """
    Serviço centralizado de idempotência.
    
    Usa cache em memória com TTL para evitar execuções duplicadas
    de operações críticas.
    """
    
    def __init__(self, default_ttl: int = 120):
        """
        Inicializa o serviço de idempotência.
        
        Args:
            default_ttl: Tempo de vida padrão em segundos (default: 120s)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        logger.info(f"IdempotencyService inicializado com TTL padrão de {default_ttl}s")
    
    async def start_cleanup(self):
        """Inicia tarefa de limpeza periódica do cache."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Tarefa de limpeza de cache iniciada")
    
    async def stop_cleanup(self):
        """Para a tarefa de limpeza periódica."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Tarefa de limpeza de cache parada")
    
    async def _cleanup_loop(self):
        """Loop de limpeza periódica do cache (a cada 60 segundos)."""
        while True:
            try:
                await asyncio.sleep(60)
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de limpeza: {e}")
    
    def _cleanup_expired(self):
        """Remove entradas expiradas do cache."""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry['expires_at'] <= now
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Limpeza: {len(expired_keys)} entradas expiradas removidas")
    
    def _is_duplicate(self, key: str) -> bool:
        """
        Verifica se uma chave já existe e não expirou.
        
        Args:
            key: Chave de idempotência
            
        Returns:
            True se é duplicata, False caso contrário
        """
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        now = time.time()
        
        if entry['expires_at'] <= now:
            # Expirou, remover
            del self._cache[key]
            return False
        
        return True
    
    def _store(self, key: str, result: Any, ttl: int):
        """
        Armazena resultado no cache com TTL.
        
        Args:
            key: Chave de idempotência
            result: Resultado da operação
            ttl: Tempo de vida em segundos
        """
        now = time.time()
        self._cache[key] = {
            'result': result,
            'created_at': now,
            'expires_at': now + ttl
        }
    
    async def run_once(
        self,
        key: str,
        fn: Callable,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> tuple[bool, Any]:
        """
        Executa uma função apenas uma vez dentro da janela TTL.
        
        Args:
            key: Chave única de idempotência (ex: "favorite:user123:post456")
            fn: Função a ser executada
            ttl: Tempo de vida em segundos (usa default_ttl se None)
            *args: Argumentos posicionais para fn
            **kwargs: Argumentos nomeados para fn
            
        Returns:
            Tupla (executado: bool, resultado: Any)
            - executado=True: função foi executada agora
            - executado=False: já foi executada antes (idempotência)
            - resultado: retorno da função ou resultado cacheado
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Verificar se já foi executado
        if self._is_duplicate(key):
            cached_result = self._cache[key]['result']
            logger.info(f"Idempotência: operação já executada - key={key}")
            return (False, cached_result)
        
        # Executar função
        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)
            
            # Armazenar resultado
            self._store(key, result, ttl)
            
            logger.info(f"Idempotência: operação executada e cacheada - key={key}, ttl={ttl}s")
            return (True, result)
            
        except Exception as e:
            logger.error(f"Erro ao executar operação idempotente - key={key}: {e}", exc_info=True)
            raise
    
    def check(self, key: str) -> bool:
        """
        Verifica se uma chave já existe (sem executar nada).
        
        Args:
            key: Chave de idempotência
            
        Returns:
            True se já existe e não expirou, False caso contrário
        """
        return self._is_duplicate(key)
    
    def invalidate(self, key: str):
        """
        Invalida uma chave específica do cache.
        
        Args:
            key: Chave de idempotência a invalidar
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Chave invalidada: {key}")
    
    def clear(self):
        """Limpa todo o cache."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache de idempotência limpo: {count} entradas removidas")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas
        """
        now = time.time()
        active_entries = sum(
            1 for entry in self._cache.values()
            if entry['expires_at'] > now
        )
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': len(self._cache) - active_entries,
            'default_ttl': self.default_ttl
        }


# Instância global (singleton)
_idempotency_service: Optional[IdempotencyService] = None


def get_idempotency_service(default_ttl: int = 120) -> IdempotencyService:
    """
    Retorna a instância global do serviço de idempotência.
    
    Args:
        default_ttl: TTL padrão em segundos (usado apenas na primeira chamada)
        
    Returns:
        Instância do IdempotencyService
    """
    global _idempotency_service
    
    if _idempotency_service is None:
        _idempotency_service = IdempotencyService(default_ttl)
    
    return _idempotency_service

