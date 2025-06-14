from enum import Enum

class BasicEnum(str, Enum):
    """
    Enum de base pour les autres enums.
    Utilisé pour la sérialisation et la désérialisation des valeurs d'enum.
    """
    @classmethod
    def get_possiblevalue(cls):
        """
        Retourne une liste des valeurs de l'enum.
        """
        return [val.value for val in cls]
    
    @classmethod
    def is_valid(cls, value):
        """
        Vérifie si une valeur donnée est valide pour cet enum.
        """
        for val in cls:
            if val.value.upper() == value.upper():
                return val
        return None
