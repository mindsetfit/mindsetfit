from dataclasses import dataclass
from typing import Optional, Dict, List
import pandas as pd


@dataclass
class Informações_do_Paciente:
    nome: str
    idade: int
    sexo: str            # "masculino" ou "feminino"
    peso: float          # kg
    altura: float        # cm
    nivel_atividade: str
    objetivo: str        # "Emagrecimento", "Manutenção", "Ganho de massa"
    gordura_corporal: Optional[float] = None  # % (opcional)


class NutritionEngine:
    """
    Motor nutricional:
    - Calcula TMB em 4 equações (Mifflin, Harris-Benedict, Owen, Cunningham)
    - Aplica fator de atividade
    - Ajusta para objetivo (emagrecimento, manutenção, ganho)
    - Gera macros diários
    - Distribui macros por refeição
    - Sugere receitas baseadas em alimentos presentes na TACO
    """

    def __init__(self, df_alimentos: pd.DataFrame):
        self.df_alimentos = df_alimentos
        self.df_alimentos.columns = [c.strip().lower() for c in df_alimentos.columns]

    # ========= EQUAÇÕES DE TMB =========

    def _tmb_mifflin(self, p: Informações_do_Paciente) -> float:
        """Mifflin-St Jeor (kcal/dia)."""
        if p.sexo.lower() == "masculino":
            return 10 * p.peso + 6.25 * p.altura - 5 * p.idade + 5
        else:
            return 10 * p.peso + 6.25 * p.altura - 5 * p.idade - 161

    def _tmb_harris_benedict(self, p: Informações_do_Paciente) -> float:
        """Harris-Benedict revisada (kcal/dia)."""
        if p.sexo.lower() == "masculino":
            return 88.362 + 13.397 * p.peso + 4.799 * p.altura - 5.677 * p.idade
        else:
            return 447.593 + 9.247 * p.peso + 3.098 * p.altura - 4.330 * p.idade

    def _tmb_owen(self, p: Informações_do_Paciente) -> float:
        """Owen (kcal/dia)."""
        if p.sexo.lower() == "masculino":
            return 879 + 10.2 * p.peso
        else:
            return 795 + 7.18 * p.peso

    def _tmb_cunningham(self, p: Informações_do_Paciente) -> float:
        """Cunningham (kcal/dia) – usa massa magra se disponível."""
        if p.gordura_corporal is None:
            # se não tiver % gordura, aproxima por Mifflin mesmo
            return self._tmb_mifflin(p)
        massa_magra = p.peso * (1 - p.gordura_corporal / 100.0)
        return 500 + 22 * massa_magra

    def calcular_tmb_equacao(self, p: Informações_do_Paciente, equacao: str) -> float:
        equacao = equacao.lower()
        if equacao == "mifflin":
            return self._tmb_mifflin(p)
        if equacao == "harris-benedict":
            return self._tmb_harris_benedict(p)
        if equacao == "owen":
            return self._tmb_owen(p)
        if equacao == "cunningham":
            return self._tmb_cunningham(p)
        # padrão: Mifflin
        return self._tmb_mifflin(p)

    def calcular_tmb_todas_equacoes(self, p: Informações_do_Paciente) -> Dict[str, float]:
        return {
            "Mifflin-St Jeor": round(self._tmb_mifflin(p)),
            "Harris-Benedict": round(self._tmb_harris_benedict(p)),
            "Owen": round(self._tmb_owen(p)),
            "Cunningham": round(self._tmb_cunningham(p)),
        }

    # ========= FATOR DE ATIVIDADE =========

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

    # ========= AJUSTE POR OBJETIVO =========

    def ajustar_por_objetivo(self, tdee: float, objetivo: str) -> float:
        obj = objetivo.lower()
        if "emagrec" in obj or "perda" in obj:
            return tdee * 0.8   # -20% para emagrecimento
        if "ganho" in obj or "hipertrofia" in obj:
            return tdee * 1.1   # +10% para ganho de massa
        return tdee            # manutenção

    # ========= MACROS DIÁRIOS =========

    def gerar_macros(self, kcal_dia: float) -> Dict[str, float]:
        prot_kcal = kcal_dia * 0.30
        carb_kcal = kcal_dia * 0.45
        gord_kcal = kcal_dia * 0.25

        return {
            "kcal": round(kcal_dia),
            "proteina_g": round(prot_kcal / 4),
            "carbo_g": round(carb_kcal / 4),
            "gordura_g": round(gord_kcal / 9),
        }

    # ========= DISTRIBUIÇÃO POR REFEIÇÃO =========

    def distribuir_por_refeicao(self, macros: Dict[str, float]) -> List[Dict]:
        esquema = [
            ("Café da manhã", 0.20),
            ("Lanche da manhã", 0.10),
            ("Almoço", 0.30),
            ("Lanche da tarde", 0.10),
            ("Jantar", 0.20),
            ("Ceia", 0.10),
        ]
        refeicoes = []
        for nome, frac in esquema:
            refeicoes.append(
                {
                    "refeicao": nome,
                    "fracao": frac,
                    "kcal": round(macros["kcal"] * frac),
                    "proteina_g": round(macros["proteina_g"] * frac),
                    "carbo_g": round(macros["carbo_g"] * frac),
                    "gordura_g": round(macros["gordura_g"] * frac),
                }
            )
        return refeicoes

    # ========= RECEITAS SUGERIDAS (base TACO) =========

    def sugerir_receitas(self, objetivo: str) -> Dict[str, str]:
        """
        Sugestões didáticas. Todos os alimentos existem na Tabela TACO
        (ex.: ovo de galinha, pão integral, banana, arroz branco cozido,
        feijão carioca, peito de frango, azeite de oliva, etc.).
        """
        objetivo = objetivo.lower()

        if "emagrec" in objetivo:
            foco = "redução de densidade calórica, alto teor de fibras e proteínas."
        elif "ganho" in objetivo:
            foco = "maior densidade calórica com ênfase em proteínas e carboidratos complexos."
        else:
            foco = "equilíbrio entre proteínas, carboidratos complexos e gorduras boas."

        receitas = {
            "Café da manhã": f"""
• Omelete de 2 ovos inteiros + clara extra com espinafre refogado (ovo de galinha, espinafre – TACO)  
• 1 fatia de pão integral (pão de forma integral – TACO)  
• 1 porção de fruta (banana-prata ou maçã – TACO)  

Modo de preparo:
1. Bater os ovos, adicionar o espinafre picado e temperos naturais (sal, pimenta, cheiro-verde).  
2. Grelhar em frigideira antiaderente com mínimo de óleo.  
3. Servir com o pão integral levemente aquecido e a fruta in natura.
Foco: {foco}
""",
            "Lanche da manhã": """
• Iogurte natural desnatado (TACO)  
• 1 colher de sopa de aveia em flocos (TACO)  
• 1 porção pequena de fruta (mamão papaya ou morango – TACO)  

Modo de preparo:
1. Misturar o iogurte com a aveia.  
2. Servir com a fruta picada por cima.
""",
            "Almoço": """
• Arroz branco ou integral cozido (arroz branco/ integral cozido – TACO)  
• Feijão carioca cozido (TACO)  
• Peito de frango grelhado (TACO) ou carne magra  
• Salada crua variada (alface, tomate, cenoura ralada – TACO)  
• 1 fio de azeite de oliva extra virgem (TACO)  

Modo de preparo:
1. Cozinhar o arroz e o feijão conforme o hábito, com pouco óleo.  
2. Grelhar o peito de frango em frigideira antiaderente com temperos naturais.  
3. Montar o prato com metade do espaço para salada, 1/4 para arroz + feijão e 1/4 para a proteína.
""",
            "Lanche da tarde": """
• Castanhas (castanha de caju ou do Pará – TACO)  
• 1 fruta (pera, maçã ou tangerina – TACO)  

Modo de preparo:
1. Consumir as castanhas in natura.  
2. Comer a fruta inteira, de preferência com casca quando possível.
""",
            "Jantar": """
• Omelete de claras com legumes (clara de ovo, abobrinha, cebola, pimentão – TACO)  
• Salada verde variada  
• Fonte leve de carboidrato se necessário (mandioca cozida, batata-doce – TACO)  

Modo de preparo:
1. Refogar os legumes com mínimo de óleo.  
2. Adicionar as claras batidas e cozinhar em fogo baixo.  
3. Servir com salada e, se houver treino à noite, adicionar uma porção pequena de carboidrato.
""",
            "Ceia": """
• Leite desnatado ou bebida vegetal sem açúcar (TACO)  
• 1 porção pequena de oleaginosas OU 1 colher de sopa de pasta de amendoim 100% (TACO)  

Modo de preparo:
1. Aquecer levemente a bebida, se desejar.  
2. Consumir junto com as oleaginosas ou pasta de amendoim.
""",
        }
        return receitas

    # ========= PLANO COMPLETO =========

    def gerar_plano(self, paciente: Informações_do_Paciente, equacao_principal: str = "mifflin") -> Dict:
        # TMB principal + outras equações
        tmb_principal = self.calcular_tmb_equacao(paciente, equacao_principal)
        tmb_equacoes = self.calcular_tmb_todas_equacoes(paciente)

        # TDEE + ajuste para objetivo
        fator = self.fator_atividade(paciente.nivel_atividade)
        tdee = tmb_principal * fator
        kcal_ajustada = self.ajustar_por_objetivo(tdee, paciente.objetivo)

        # Macros diários
        macros = self.gerar_macros(kcal_ajustada)

        # Distribuição por refeição
        refeicoes = self.distribuir_por_refeicao(macros)

        # Receitas sugeridas
        receitas = self.sugerir_receitas(paciente.objetivo)

        return {
            "tmb_principal": round(tmb_principal),
            "tmb_equacoes": tmb_equacoes,
            "tdee": round(tdee),
            "kcal_objetivo": round(kcal_ajustada),
            "macros": macros,
            "refeicoes": refeicoes,
            "receitas": receitas,
        }
        

def carregar_banco_de_dados_de_alimentos(caminho_csv: str = "taco_sample.csv") -> pd.DataFrame:
    """
    Lê um arquivo CSV com os alimentos (baseado na Tabela TACO).
    Ajuste o separador ou nome do arquivo, se necessário.
    """
    df = pd.read_csv(caminho_csv, sep=";")
    return df
