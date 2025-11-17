from dataclasses import dataclass
import pandas as pd


# 🧍‍♂️ Informações do paciente
@dataclass
class Informações_do_Paciente:
    nome: str
    idade: int
    sexo: str            # "masculino" ou "feminino"
    peso: float          # kg
    altura: float        # cm
    nivel_atividade: str
    objetivo: str        # ex: "emagrecimento", "ganho de massa", "manutenção"


# 📚 Carrega o banco de alimentos (TACO ou sua tabela)
def carregar_banco_de_dados_de_alimentos(caminho_csv: str = "banco_alimentos.csv") -> pd.DataFrame:
    """
    Lê um arquivo CSV com os alimentos e retorna um DataFrame.
    Ajuste o nome do arquivo se o seu tiver outro nome.
    """
    df = pd.read_csv(caminho_csv, sep=";")  # troque o sep se o seu csv for diferente
    df.columns = [c.strip().lower() for c in df.columns]
    return df


# 🧠 Motor de nutrição
class NutritionEngine:
    def __init__(self, df_alimentos: pd.DataFrame):
        self.df_alimentos = df_alimentos

    def calcular_tmb(self, paciente: Informações_do_Paciente) -> float:
        """Calcula TMB pela fórmula de Mifflin-St Jeor."""
        peso = paciente.peso
        altura = paciente.altura
        idade = paciente.idade

        if paciente.sexo.lower() == "masculino":
            tmb = 10 * peso + 6.25 * altura - 5 * idade + 5
        else:
            tmb = 10 * peso + 6.25 * altura - 5 * idade - 161

        return tmb

    def fator_atividade(self, nivel: str) -> float:
        mapa = {
            "sedentário": 1.2,
            "sedentario": 1.2,
            "levemente ativo": 1.375,
            "moderadamente ativo": 1.55,
            "muito ativo": 1.725,
            "extremamente ativo": 1.9,
        }
        return mapa.get(nivel.lower(), 1.2)

    def ajustar_por_objetivo(self, tdee: float, objetivo: str) -> float:
        obj = objetivo.lower()
        if "emagrec" in obj or "perda" in obj:
            return tdee * 0.8   # -20% para emagrecimento
        if "ganho" in obj or "hipertrofia" in obj:
            return tdee * 1.1   # +10% para ganho de massa
        return tdee            # manutenção

    def gerar_macros(self, kcal_dia: float) -> dict:
        # distribuição simples de macros
        prot_kcal = kcal_dia * 0.30
        carb_kcal = kcal_dia * 0.45
        gord_kcal = kcal_dia * 0.25

        return {
            "kcal": round(kcal_dia),
            "proteina_g": round(prot_kcal / 4),
            "carbo_g": round(carb_kcal / 4),
            "gordura_g": round(gord_kcal / 9),
        }

    def gerar_plano(self, paciente: Informações_do_Paciente) -> dict:
        """Retorna um dicionário com TMB, TDEE, kcal alvo e macros."""
        tmb = self.calcular_tmb(paciente)
        tdee = tmb * self.fator_atividade(paciente.nivel_atividade)
        kcal_ajustada = self.ajustar_por_objetivo(tdee, paciente.objetivo)
        macros = self.gerar_macros(kcal_ajustada)

        return {
            "tmb": round(tmb),
            "tdee": round(tdee),
            "kcal_objetivo": round(kcal_ajustada),
            "macros": macros,
        }
