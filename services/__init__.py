"""Módulo de serviços do LiberALL.

Este módulo exporta todos os serviços principais da aplicação.
"""

from .firebase_service import FirebaseService
from .security_service import SecurityService, security_service
from .user_service import UserService
from .post_service import PostService
from .match_service import MatchService
from .monetization_service import MonetizationService
from .atomic_persistence import AtomicPersistence

# Criar instâncias dos serviços (sem inicializar MonetizationService ainda)
firebase_service = FirebaseService()
# monetization_service será inicializado após Firebase estar pronto
post_service = None  # Será inicializado no main.py
match_service = None  # Será inicializado no main.py
atomic_persistence = AtomicPersistence()
user_service = None  # Será inicializado no main.py
from .atomic_persistence import get_atomic_user_data, get_post_data
from .exif_service import ExifService

# Alias para compatibilidade
atomic_service = atomic_persistence

__all__ = [
    'firebase_service',
    'SecurityService',
    'security_service',
    'UserService',
    'PostService',
    'MatchService',
    'MonetizationService',
    'AtomicPersistence',
    'atomic_persistence',
    'atomic_service',
    'get_atomic_user_data',
    'get_post_data',
    'ExifService'
]