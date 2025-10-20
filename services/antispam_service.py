"""
Serviço de Antispam para controle de taxa de ações.

Implementa rate limiting para prevenir abuso de funcionalidades:
- Comentários: 1 a cada 10s por usuário por post
- Navegação: máx. 5 cliques/s por usuário
- Match: 1 a cada 30s por alvo
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exceção lançada quando o rate limit é excedido."""
    
    def __init__(self, action: str, retry_after: float):
        self.action = action
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit excedido para ação '{action}'. "
            f"Tente novamente em {retry_after:.1f} segundos."
        )


class AntispamService:
    """
    Serviço centralizado de antispam e rate limiting.
    
    Usa algoritmo de sliding window para controle de taxa.
    """
    
    # Configurações padrão de rate limiting
    DEFAULT_LIMITS = {
        'comment': {'window': 10, 'max_hits': 1},      # 1 comentário a cada 10s
        'navigation': {'window': 1, 'max_hits': 5},    # 5 navegações por segundo
        'match': {'window': 30, 'max_hits': 1},        # 1 match a cada 30s
        'favorite': {'window': 5, 'max_hits': 1},      # 1 favorito a cada 5s
        'publish': {'window': 60, 'max_hits': 1},      # 1 publicação por minuto
        'default': {'window': 5, 'max_hits': 3}        # Padrão: 3 ações a cada 5s
    }
    
    def __init__(self, custom_limits: Optional[Dict] = None):
        """
        Inicializa o serviço de antispam.
        
        Args:
            custom_limits: Limites customizados (opcional)
        """
        self.limits = self.DEFAULT_LIMITS.copy()
        if custom_limits:
            self.limits.update(custom_limits)
        
        # Estrutura: {scope_key: deque([timestamp1, timestamp2, ...])}
        self._windows: Dict[str, deque] = defaultdict(deque)
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("AntispamService inicializado")
    
    async def start_cleanup(self):
        """Inicia tarefa de limpeza periódica."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Tarefa de limpeza de antispam iniciada")
    
    async def stop_cleanup(self):
        """Para a tarefa de limpeza periódica."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Tarefa de limpeza de antispam parada")
    
    async def _cleanup_loop(self):
        """Loop de limpeza periódica (a cada 5 minutos)."""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutos
                self._cleanup_old_windows()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de limpeza de antispam: {e}")
    
    def _cleanup_old_windows(self):
        """Remove janelas antigas que não têm mais timestamps recentes."""
        now = time.time()
        max_window = max(limit['window'] for limit in self.limits.values())
        
        keys_to_remove = []
        for key, window in self._windows.items():
            # Se a última ação foi há mais de 2x a maior janela, remover
            if window and (now - window[-1]) > (max_window * 2):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._windows[key]
        
        if keys_to_remove:
            logger.debug(f"Limpeza antispam: {len(keys_to_remove)} janelas antigas removidas")
    
    def _get_limit_config(self, action: str) -> Dict:
        """
        Retorna configuração de limite para uma ação.
        
        Args:
            action: Nome da ação
            
        Returns:
            Dicionário com 'window' e 'max_hits'
        """
        return self.limits.get(action, self.limits['default'])
    
    def _build_scope_key(self, user_id: int, action: str, scope_key: Optional[str] = None) -> str:
        """
        Constrói chave de escopo para rate limiting.
        
        Args:
            user_id: ID do usuário
            action: Ação sendo realizada
            scope_key: Chave adicional de escopo (ex: post_id)
            
        Returns:
            Chave de escopo formatada
        """
        if scope_key:
            return f"{action}:{user_id}:{scope_key}"
        return f"{action}:{user_id}"
    
    def _remove_old_timestamps(self, window: deque, cutoff_time: float):
        """
        Remove timestamps antigos da janela.
        
        Args:
            window: Deque de timestamps
            cutoff_time: Tempo de corte (timestamps antes disso são removidos)
        """
        while window and window[0] < cutoff_time:
            window.popleft()
    
    def check_and_consume(
        self,
        user_id: int,
        action: str,
        scope_key: Optional[str] = None,
        window_seconds: Optional[int] = None,
        max_hits: Optional[int] = None
    ) -> Tuple[bool, Optional[float]]:
        """
        Verifica rate limit e consome um slot se permitido.
        
        Args:
            user_id: ID do usuário
            action: Ação sendo realizada
            scope_key: Chave adicional de escopo (ex: post_id para comentários)
            window_seconds: Janela de tempo em segundos (override)
            max_hits: Máximo de hits na janela (override)
            
        Returns:
            Tupla (permitido: bool, retry_after: Optional[float])
            - permitido=True: ação permitida, slot consumido
            - permitido=False: rate limit excedido
            - retry_after: segundos até poder tentar novamente (se não permitido)
        """
        # Obter configuração
        config = self._get_limit_config(action)
        window_sec = window_seconds if window_seconds is not None else config['window']
        max_count = max_hits if max_hits is not None else config['max_hits']
        
        # Construir chave de escopo
        key = self._build_scope_key(user_id, action, scope_key)
        
        # Obter janela de timestamps
        window = self._windows[key]
        
        # Timestamp atual
        now = time.time()
        cutoff = now - window_sec
        
        # Remover timestamps antigos
        self._remove_old_timestamps(window, cutoff)
        
        # Verificar se excedeu o limite
        current_count = len(window)
        
        if current_count >= max_count:
            # Rate limit excedido
            # Calcular quando o usuário pode tentar novamente
            oldest_in_window = window[0]
            retry_after = (oldest_in_window + window_sec) - now
            
            logger.warning(
                f"Rate limit excedido: user={user_id}, action={action}, "
                f"scope={scope_key}, count={current_count}/{max_count}, "
                f"retry_after={retry_after:.1f}s"
            )
            
            return (False, retry_after)
        
        # Permitido: adicionar timestamp
        window.append(now)
        
        logger.debug(
            f"Rate limit OK: user={user_id}, action={action}, "
            f"scope={scope_key}, count={current_count + 1}/{max_count}"
        )
        
        return (True, None)
    
    def check_only(
        self,
        user_id: int,
        action: str,
        scope_key: Optional[str] = None,
        window_seconds: Optional[int] = None,
        max_hits: Optional[int] = None
    ) -> Tuple[bool, Optional[float]]:
        """
        Verifica rate limit SEM consumir um slot.
        
        Args:
            user_id: ID do usuário
            action: Ação sendo verificada
            scope_key: Chave adicional de escopo
            window_seconds: Janela de tempo em segundos (override)
            max_hits: Máximo de hits na janela (override)
            
        Returns:
            Tupla (permitido: bool, retry_after: Optional[float])
        """
        # Obter configuração
        config = self._get_limit_config(action)
        window_sec = window_seconds if window_seconds is not None else config['window']
        max_count = max_hits if max_hits is not None else config['max_hits']
        
        # Construir chave de escopo
        key = self._build_scope_key(user_id, action, scope_key)
        
        # Obter janela de timestamps
        window = self._windows[key]
        
        # Timestamp atual
        now = time.time()
        cutoff = now - window_sec
        
        # Remover timestamps antigos (temporariamente)
        temp_window = deque(ts for ts in window if ts >= cutoff)
        
        # Verificar se excedeu o limite
        current_count = len(temp_window)
        
        if current_count >= max_count:
            oldest_in_window = temp_window[0]
            retry_after = (oldest_in_window + window_sec) - now
            return (False, retry_after)
        
        return (True, None)
    
    def reset(self, user_id: int, action: str, scope_key: Optional[str] = None):
        """
        Reseta o rate limit para um usuário/ação/escopo específico.
        
        Args:
            user_id: ID do usuário
            action: Ação
            scope_key: Chave de escopo (opcional)
        """
        key = self._build_scope_key(user_id, action, scope_key)
        if key in self._windows:
            del self._windows[key]
            logger.debug(f"Rate limit resetado: {key}")
    
    def clear_all(self):
        """Limpa todos os rate limits."""
        count = len(self._windows)
        self._windows.clear()
        logger.info(f"Todos os rate limits limpos: {count} janelas removidas")
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do antispam.
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            'total_windows': len(self._windows),
            'limits_config': self.limits
        }


# Instância global (singleton)
_antispam_service: Optional[AntispamService] = None


def get_antispam_service(custom_limits: Optional[Dict] = None) -> AntispamService:
    """
    Retorna a instância global do serviço de antispam.
    
    Args:
        custom_limits: Limites customizados (usado apenas na primeira chamada)
        
    Returns:
        Instância do AntispamService
    """
    global _antispam_service
    
    if _antispam_service is None:
        _antispam_service = AntispamService(custom_limits)
    
    return _antispam_service

