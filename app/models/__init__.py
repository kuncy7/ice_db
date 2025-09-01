# Importuj Base z pliku database, aby modele mogły z niego dziedziczyć
from ..database import Base

# Importuj wszystkie swoje modele, aby były dostępne w jednym miejscu
from .models import Organization, User, UserSession
