from dataclasses import dataclass
from typing import Optional, Dict, List
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
    - Sugere combinações automáticas usando energy_kcal_per_100g do CSV
    """

    def __init__(self, df_alimentos: pd.DataFrame):
        # Normaliza colunas
        self.df_alimentos = df_alimentos.copy()
        self.df_alimentos.columns = [str(c).strip().lower() for c in self.df_alimentos.columns]

        # Garante colunas principais do seu CSV
        if "name" not in self.df_alimentos.columns:
            raise ValueError("CSV precisa ter a coluna 'name'.")
        if "energy_kcal_per_100g" not in self.df_alimentos.columns:
            raise ValueError("CSV precisa ter a coluna 'energy_kcal_per_100g'.")

        # Converte kcal para numérico
        self.df_alimentos["energy_kcal_per_100g"] = pd.to_numeric(
            self.df_alimentos["energy_kcal_per_100g"], errors="coerce"
        )

        # Prepara listas de alimentos por grupo (carbo, proteína, gordura)
        self.fontes_proteina, self.fontes_carbo, self.fontes_gordura = self._preparar_listas_alimentos()

    # ------------------------------------------------
    # SEPARAÇÃO DE ALIMENTOS POR GRUPO
    # ------------------------------------------------
    def _preparar_listas_alimentos(self):
        df = self.df_alimentos.copy()

        # Se tiver group, usamos pra segmentar
        if "group" in df.columns:
            grupo = df["group"].astype(str).str.lower()
        else:
            grupo = pd.Series(["outro"] * len(df))

        # Proteínas: proteina_animal, proteina_vegetal, leguminosa
        fontes_proteina = df[grupo.isin(["proteina_animal", "proteina_vegetal", "leguminosa"])]

        # Carboidratos: cereal, tuberculo, fruta, leguminosa
        fontes_carbo = df[grupo.isin(["cereal", "tuberculo", "fruta", "leguminosa"])]

        # Gorduras: alimentos que contêm nuts (nozes, amendoim etc.)
        if "contains_nuts" in df.columns:
            fontes_gordura = df[df["contains_nuts"] == True]
        else:
            fontes_gordura = df.head(0)  # vazio

        # Fallback: se alguma lista estiver vazia, usa o próprio df
        if fontes_proteina.empty:
            fontes_proteina = df
        if fontes_carbo.empty:
            fontes_carbo = df
        if fontes_gordura.empty:
            fontes_gordura = df

        # Ordena por densidade energética (kcal/100g) decrescente
        fontes_proteina = fontes_proteina.sort_values("energy_kcal_per_100g", ascending=False)
        fontes_carbo = fontes_carbo.sort_values("energy_kcal_per_100g", ascending=False)
        fontes_gordura = fontes_gordura.sort_values("energy_kcal_per_100g", ascending=False)

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

    def _combo_para_refeicao(self, alvo_kcal: float, alvo_prot: float, alvo_carb: float, alvo_gord: float) -> str:
        """
        Gera uma sugestão de combinação de 2–3 alimentos da TACO
        tentando chegar perto das kcal da refeição,
        usando energy_kcal_per_100g.

        Como o CSV não tem proteína/carbo/gordura,
        as metas de macros são exibidas como alvo teórico.
        """

        # Se não tiver dados, cai para texto genérico
        if self.fontes_proteina.empty or self.fontes_carbo.empty:
            return (
                "Sugestão: combine uma fonte de proteína magra (ex.: frango peito, ovos, tilápia), "
                "uma fonte de carboidrato complexo (ex.: arroz, batata, mandioca, aveia) e uma fonte de gordura boa "
                "(ex.: amendoim, castanhas, sementes), ajustando as porções para se aproximar das calorias da refeição."
            )

        # Escolhe 1 alimento de cada grupo (primeiro da lista – mais denso energeticamente)
        prot_row = self.fontes_proteina.iloc[0]
        carb_row = self.fontes_carbo.iloc[0]
        gord_row = self.fontes_gordura.iloc[0] if not self.fontes_gordura.empty else None

        def extrair_nome_kcal(row):
            return row["name"], float(row["energy_kcal_per_100g"])

        nome_p, kcal_p_100 = extrair_nome_kcal(prot_row)
        nome_c, kcal_c_100 = extrair_nome_kcal(carb_row)

        if gord_row is not None:
            nome_g, kcal_g_100 = extrair_nome_kcal(gord_row)
        else:
            nome_g, kcal_g_100 = None, 0.0

        # Divisão aproximada de kcal por fonte
        # 60% carbo, 25% proteína, 15% gordura
        kcal_carbo = alvo_kcal * 0.6
        kcal_prot = alvo_kcal * 0.25
        kcal_gord = alvo_kcal * 0.15 if nome_g is not None else 0

        def gramas_para_kcal(kcal_alvo: float, kcal_por_100g: float) -> int:
            if kcal_por_100g <= 0:
                return 0
            g = round((kcal_alvo / kcal_por_100g) * 100)
            # limita em 20–250 g
            if g <= 0:
                return 0
            return max(20, min(g, 250))

        gr_c = gramas_para_kcal(kcal_carbo, kcal_c_100)
        gr_p = gramas_para_kcal(kcal_prot, kcal_p_100)
        gr_g = gramas_para_kcal(kcal_gord, kcal_g_100) if nome_g is not None else 0

        linhas = []
        if gr_p > 0:
            linhas.append(f"• **{gr_p} g** de **{nome_p}** (fonte principal de proteína)")
        if gr_c > 0:
            linhas.append(f"• **{gr_c} g** de **{nome_c}** (fonte principal de carboidrato)")
        if nome_g is not None and gr_g > 0:
            linhas.append(f"• **{gr_g} g** de **{nome_g}** (fonte de gordura/oleaginosas)")

        if not linhas:
            return (
                "Sugestão: ajuste manualmente as fontes de proteína, carboidrato e gordura "
                "para se aproximar das calorias indicadas nesta refeição."
            )

        texto = "\n".join(linhas)
        texto += (
            "\n\n> As metas de proteína, carboidratos e gorduras para esta refeição são aproximadas. "
            "Ajustes finos podem ser feitos conforme preferência e resposta clínica."
        )
        return texto

    # ========= RECEITAS SUGERIDAS (USANDO SEU CSV) =========

    def sugerir_receitas(self, objetivo: str, refeicoes: List[Dict]) -> Dict[str, str]:
        """
        Gera sugestões de combinações de alimentos para cada refeição,
        usando a Tabela simplificada (energy_kcal_per_100g + grupos).
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
            refe_kcal = ref["kcal"]
            prot_ref = ref["proteina_g"]
            carb_ref = ref["carbo_g"]
            gord_ref = ref["gordura_g"]

            combo_txt = self._combo_para_refeicao(
                alvo_kcal=refe_kcal,
                alvo_prot=prot_ref,
                alvo_carb=carb_ref,
                alvo_gord=gord_ref,
            )

            texto = f"""
**Meta de macros para esta refeição (alvo teórico):**  
• Proteínas: ~{prot_ref} g  
• Carboidratos: ~{carb_ref} g  
• Gorduras: ~{gord_ref} g  

**Sugestão automática (base na Tabela de alimentos) – foco em {foco}**

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

        # Receitas sugeridas (usando CSV)
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
    Lê um arquivo CSV com os alimentos.
    No seu exemplo, o separador é vírgula.
    """
    df = pd.read_csv(caminho_csv, sep=",", encoding="utf-8")
    return df
