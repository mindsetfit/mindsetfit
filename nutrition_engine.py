from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import pandas as pd


# ====================================================
# DATACLASS – INFORMAÇÕES DO PACIENTE
# ====================================================

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


# ====================================================
# NUTRITION ENGINE
# ====================================================

class NutritionEngine:
    """
    Motor nutricional:
    - Calcula TMB em 4 equações (Mifflin, Harris-Benedict, Owen, Cunningham)
    - Aplica fator de atividade
    - Ajusta para objetivo (emagrecimento, manutenção, ganho)
    - Gera macros diários
    - Distribui macros por refeição
    - Sugere combinações automáticas a partir da Tabela TACO
    """

    def __init__(self, df_alimentos: pd.DataFrame):
        # Normaliza colunas
        self.df_alimentos = df_alimentos.copy()
        self.df_alimentos.columns = [c.strip().lower() for c in self.df_alimentos.columns]

        # Mapeia colunas principais da TACO (nome, kcal, proteína, carbo, gordura)
        self.col_nome, self.col_kcal, self.col_prot, self.col_carb, self.col_gord = self._mapear_colunas()

        # Prepara listas de alimentos por macronutriente dominante
        self.fontes_proteina, self.fontes_carbo, self.fontes_gordura = self._preparar_listas_alimentos()

    # ------------------------------------------------
    # MAPEAMENTO DE COLUNAS
    # ------------------------------------------------
    def _mapear_colunas(self) -> Tuple[str, str, str, str, str]:
        cols = list(self.df_alimentos.columns)

        # Nome do alimento
        col_nome = next(
            (c for c in cols if any(s in c for s in ["alimento", "descr", "descricao", "descrição", "nome"])),
            cols[0]
        )

        # Energia (kcal)
        col_kcal = next(
            (c for c in cols if ("kcal" in c) or ("energia" in c)),
            None
        )

        # Proteína
        col_prot = next(
            (c for c in cols if "prot" in c),
            None
        )

        # Carboidrato
        col_carb = next(
            (c for c in cols if ("carb" in c) or ("cho" in c)),
            None
        )

        # Gordura / Lipídeos
        col_gord = next(
            (c for c in cols if ("gord" in c) or ("lip" in c)),
            None
        )

        if col_kcal is None or col_prot is None or col_carb is None or col_gord is None:
            raise ValueError(
                "Não foi possível mapear as colunas de kcal/proteína/carbo/gordura na TACO. "
                f"Colunas encontradas no CSV: {cols}"
            )

        return col_nome, col_kcal, col_prot, col_carb, col_gord

    # ------------------------------------------------
    # SEPARAÇÃO DE ALIMENTOS POR MACRO DOMINANTE
    # ------------------------------------------------
    def _preparar_listas_alimentos(self):
        df = self.df_alimentos.copy()

        # Garante que as colunas numéricas estejam em formato float
        for col in [self.col_kcal, self.col_prot, self.col_carb, self.col_gord]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=[self.col_kcal, self.col_prot, self.col_carb, self.col_gord])

        fontes_proteina = df[
            (df[self.col_prot] >= 8) &  # pelo menos 8g de proteína / 100g
            (df[self.col_prot] > df[self.col_carb]) &
            (df[self.col_prot] >= df[self.col_gord])
        ].sort_values(self.col_prot, ascending=False)

        fontes_carbo = df[
            (df[self.col_carb] >= 8) &  # pelo menos 8g de carbo / 100g
            (df[self.col_carb] > df[self.col_prot]) &
            (df[self.col_carb] >= df[self.col_gord])
        ].sort_values(self.col_carb, ascending=False)

        fontes_gordura = df[
            (df[self.col_gord] >= 5) &  # pelo menos 5g de gordura / 100g
            (df[self.col_gord] > df[self.col_prot]) &
            (df[self.col_gord] > df[self.col_carb])
        ].sort_values(self.col_gord, ascending=False)

        return fontes_proteina, fontes_carbo, fontes_gordura

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

    # ========= AJUDANTE PARA UMA COMBINAÇÃO POR REFEIÇÃO =========

    def _combo_para_refeicao(self, alvo_prot: float, alvo_carb: float, alvo_gord: float) -> str:
        """
        Gera uma sugestão de combinação de 2–3 alimentos da TACO
        tentando chegar perto dos alvos de proteína, carbo e gordura.

        Obs.: é uma aproximação simples, pensada para ser didática.
        """

        # Se não tiver listas prontas, devolve texto genérico
        if self.fontes_proteina.empty or self.fontes_carbo.empty:
            return (
                "Sugestão: combine uma fonte de proteína magra (ex.: peito de frango, ovo, iogurte), "
                "uma fonte de carboidrato complexo (ex.: arroz, aveia, batata) e uma fonte de gordura boa "
                "(ex.: azeite de oliva, castanhas), ajustando a porção para se aproximar dos macros da refeição."
            )

        # Escolhe 1 alimento de cada grupo (primeira opção das listas, que são ordenadas pela densidade)
        prot_row = self.fontes_proteina.iloc[0]
        carb_row = self.fontes_carbo.iloc[0]
        gord_row = self.fontes_gordura.iloc[0] if not self.fontes_gordura.empty else None

        nome_p = prot_row[self.col_nome]
        p_prot = float(prot_row[self.col_prot])
        p_carb = float(prot_row[self.col_carb])
        p_gord = float(prot_row[self.col_gord])

        nome_c = carb_row[self.col_nome]
        c_prot = float(carb_row[self.col_prot])
        c_carb = float(carb_row[self.col_carb])
        c_gord = float(carb_row[self.col_gord])

        if gord_row is not None:
            nome_g = gord_row[self.col_nome]
            g_prot = float(gord_row[self.col_prot])
            g_carb = float(gord_row[self.col_carb])
            g_gord = float(gord_row[self.col_gord])
        else:
            nome_g, g_prot, g_carb, g_gord = None, 0.0, 0.0, 0.0

        # Calcula gramas aproximadas
        # Proteína: 70% da proteína da refeição vindo do alimento proteico
        gr_p = 0
        if p_prot > 0:
            gr_p = round((alvo_prot * 0.7) / (p_prot / 100))

        # Carbo: 70% do carbo vindo do alimento de carbo
        gr_c = 0
        if c_carb > 0:
            gr_c = round((alvo_carb * 0.7) / (c_carb / 100))

        # Gordura: 70% da gordura vindo da fonte de gordura
        gr_g = 0
        if nome_g is not None and g_gord > 0:
            gr_g = round((alvo_gord * 0.7) / (g_gord / 100))

        # Limita gramas para evitar números muito bizarros
        def limitar_gramas(g):
            if g <= 0:
                return 0
            return max(20, min(g, 200))

        gr_p = limitar_gramas(gr_p)
        gr_c = limitar_gramas(gr_c)
        gr_g = limitar_gramas(gr_g)

        linhas = []

        if gr_p > 0:
            linhas.append(f"• **{gr_p} g** de **{nome_p}** (principal fonte de proteína)")
        if gr_c > 0:
            linhas.append(f"• **{gr_c} g** de **{nome_c}** (principal fonte de carboidrato)")
        if nome_g is not None and gr_g > 0:
            linhas.append(f"• **{gr_g} g** de **{nome_g}** (fonte de gordura boa)")

        if not linhas:
            return (
                "Sugestão: ajuste manualmente as fontes de proteína, carboidrato e gordura "
                "para se aproximar dos macros indicados nesta refeição."
            )

        texto = "\n".join(linhas)
        texto += (
            "\n\n> Ajuste fino das porções pode ser feito conforme preferência, tolerância e resposta clínica."
        )
        return texto

    # ========= RECEITAS SUGERIDAS (USANDO TACO) =========

    def sugerir_receitas(self, objetivo: str, refeicoes: List[Dict]) -> Dict[str, str]:
        """
        Gera sugestões de combinações de alimentos para cada refeição,
        usando a Tabela TACO como base e os alvos de macros da refeição.
        """
        objetivo = objetivo.lower()

        if "emagrec" in objetivo:
            foco = "redução de densidade calórica, alto teor de fibras e proteínas."
        elif "ganho" in objetivo:
            foco = "maior densidade calórica com ênfase em proteínas e carboidratos complexos."
        else:
            foco = "equilíbrio entre proteínas, carboidratos complexos e gorduras boas."

        sugestoes = {}

        for ref in refeicoes:
            nome_ref = ref["refeicao"]
            prot_ref = ref["proteina_g"]
            carb_ref = ref["carbo_g"]
            gord_ref = ref["gordura_g"]

            combo_txt = self._combo_para_refeicao(
                alvo_prot=prot_ref,
                alvo_carb=carb_ref,
                alvo_gord=gord_ref,
            )

            texto = f"""
**Meta de macros para esta refeição:**  
• Proteínas: ~{prot_ref} g  
• Carboidratos: ~{carb_ref} g  
• Gorduras: ~{gord_ref} g  

**Sugestão automática (base TACO) – foco em {foco}**

{combo_txt}
"""
            sugestoes[nome_ref] = texto

        return sugestoes

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

        # Receitas sugeridas (agora usando TACO + macros por refeição)
        receitas = self.sugerir_receitas(paciente.objetivo, refeicoes)

        return {
            "tmb_principal": round(tmb_principal),
            "tmb_equacoes": tmb_equacoes,
            "tdee": round(tdee),
            "kcal_objetivo": round(kcal_ajustada),
            "macros": macros,
            "refeicoes": refeicoes,
            "receitas": receitas,
        }


# ====================================================
# FUNÇÃO AUXILIAR – CARREGAR BANCO TACO
# ====================================================

def carregar_banco_de_dados_de_alimentos(caminho_csv: str = "taco_sample.csv") -> pd.DataFrame:
    """
    Lê um arquivo CSV com os alimentos (baseado na Tabela TACO).
    Tenta primeiro utf-8, depois latin-1. Ajuste o separador se necessário.
    """
    try:
        df = pd.read_csv(caminho_csv, sep=";", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(caminho_csv, sep=";", encoding="latin-1")
    return df
