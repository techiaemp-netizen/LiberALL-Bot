from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class Profile:
    """Dados de perfil do usuário."""
    codename: Optional[str] = None
    age: Optional[int] = None
    age_confirmed: bool = False
    profile_type: Optional[str] = None  # Casal, Solteiro, Solteira, etc.
    relationship_profiles: List[str] = field(default_factory=list)  # Perfis para relacionar
    state_location: Optional[str] = None
    is_content_creator: bool = False
    category: Optional[str] = None  # Lite ou Premium
    interests: List[str] = field(default_factory=list)
    onboarded: bool = False

@dataclass
class Agreements:
    """Consentimentos do usuário."""
    rules_accepted: bool = False
    privacy_accepted: bool = False
    lgpd_accepted: bool = False

@dataclass
class Monetization:
    """Configurações de monetização do usuário."""
    enabled: bool = False
    pix_key: Optional[str] = None  # Armazenar criptografado
    balance: float = 0.0

@dataclass
class User:
    """Modelo principal de usuário."""
    telegram_id: int
    username: Optional[str] = None
    state: str = "IDLE"
    context_data: Dict = field(default_factory=dict)
    
    # --- CORREÇÃO PRINCIPAL AQUI ---
    # Garante que os sub-objetos sejam criados por padrão
    # quando um novo User é instanciado.
    profile: Profile = field(default_factory=Profile)
    agreements: Agreements = field(default_factory=Agreements)
    monetization: Monetization = field(default_factory=Monetization)
    
    is_premium: bool = False
    is_admin: bool = False

    @classmethod
    def from_dict(cls, data: dict):
        """Cria uma instância de User a partir de um dicionário (ex: do Firebase)."""
        # O aninhamento é tratado aqui para carregar dados existentes
        profile_data = data.get('profile', {})
        agreements_data = data.get('agreements', {})
        monetization_data = data.get('monetization', {})
        
        return cls(
            telegram_id=data.get('telegram_id'),
            username=data.get('username'),
            state=data.get('state', 'IDLE'),
            context_data=data.get('context_data', {}),
            profile=Profile(**profile_data),
            agreements=Agreements(**agreements_data),
            monetization=Monetization(**monetization_data),
            is_premium=data.get('is_premium', False),
            is_admin=data.get('is_admin', False)
        )

    def to_dict(self) -> dict:
        """Converte a instância de User para um dicionário para salvar no Firebase."""
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "state": self.state,
            "context_data": self.context_data,
            "profile": self.profile.__dict__,
            "agreements": self.agreements.__dict__,
            "monetization": self.monetization.__dict__,
            "is_premium": self.is_premium,
            "is_admin": self.is_admin
        }