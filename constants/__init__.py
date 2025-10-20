"""Inicialização do módulo constants."""

# Importar e expor as constantes de user_states
from .user_states import UserStates

# Expor as constantes diretamente no módulo user_states
import sys
from . import user_states as _user_states_module

# Adicionar todas as constantes da classe UserStates ao módulo user_states
for attr_name in dir(UserStates):
    if not attr_name.startswith('_') and attr_name.isupper():
        setattr(_user_states_module, attr_name, getattr(UserStates, attr_name))