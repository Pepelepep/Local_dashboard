import os

def load_query(filename):
    """Charge un fichier .gql brut depuis le dossier gql/"""
    path = os.path.join(os.path.dirname(__file__), "gql", filename)
    with open(path, "r") as f:
        return f.read()