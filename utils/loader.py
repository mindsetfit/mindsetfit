import pandas as pd

def load_taco_database(path: str):
    try:
        df = pd.read_csv(path)

        # Normaliza colunas
        df.columns = df.columns.str.strip().str.lower()

        # Possíveis nomes
        map_cols = {
            "kcal": ["kcal", "energia", "calorias", "energy"],
            "proteina": ["proteina", "protein", "proteínas"],
            "carbo": ["carbo", "carboidrato", "carboidratos", "carb"],
            "gordura": ["gordura", "lipideos", "gorduras", "fat"]
        }

        final_cols = {}

        for final, options in map_cols.items():
            found = [c for c in df.columns if c in options]
            if not found:
                raise KeyError(f"Coluna '{final}' não encontrada no CSV.")
            final_cols[final] = found[0]

        df = df.rename(columns=final_cols)

        return df

    except Exception as e:
        raise Exception(f"Erro ao carregar banco TACO: {e}")
