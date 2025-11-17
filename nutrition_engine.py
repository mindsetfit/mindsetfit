import math
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd


# ------------ MODELOS DE DADOS ------------ #


@dataclass
class PatientInfo:
    name: str
    age: int
    sex: str  # "masculino" | "feminino"
    weight_kg: float
    height_cm: float
    activity_level: str  # "Sedentário", "Leve", "Moderado", "Intenso"
    goal: str  # "Emagrecimento", "Ganho de massa muscular", "Manutenção"
    meals_per_day: int
    pattern: str  # "Onívoro", "Vegetariano", "Vegano"
    is_celiac: bool
    is_diabetic: bool
    is_hypertensive: bool
    lactose_intolerance: bool
    egg_allergy: bool
    nut_allergy: bool


# ------------ CARREGAR BASE DE ALIMENTOS ------------ #


def load_food_database(path: str = "taco_sample.csv") -> pd.DataFrame:
    df = pd.read_csv(path)

    # Garantir colunas esperadas
    expected_cols = {
        "name",
        "preparation",
        "group",
        "energy_kcal_per_100g",
        "is_vegetarian",
        "is_vegan",
        "is_gluten_free",
        "is_ok_for_diabetes",
        "is_low_sodium",
        "contains_lactose",
        "contains_egg",
        "contains_nuts",
    }
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em taco_sample.csv: {missing}")

    # Limpar nomes de grupo para evitar variações
    df["group"] = df["group"].str.strip().str.lower()

    return df


# ------------ ENGINE NUTRICIONAL ------------ #


class NutritionEngine:
    def __init__(self, food_df: pd.DataFrame):
        self.food_df = food_df.copy()
        # RNG fixo para gerar planos consistentes
        self.rng = np.random.default_rng(42)

    # --------- CÁLCULOS BÁSICOS --------- #

    def calculate_bmi(self, weight_kg: float, height_cm: float) -> Tuple[float, str]:
        h_m = height_kg = None  # apenas para evitar warning de IDE
        h_m = height_cm / 100
        bmi = weight_kg / (h_m**2)
        bmi = round(bmi, 1)

        if bmi < 18.5:
            cat = "Baixo peso"
        elif bmi < 25:
            cat = "Peso adequado"
        elif bmi < 30:
            cat = "Sobrepeso"
        elif bmi < 35:
            cat = "Obesidade grau I"
        elif bmi < 40:
            cat = "Obesidade grau II"
        else:
            cat = "Obesidade grau III"

        return bmi, cat

    def calculate_tdee(self, patient: PatientInfo) -> float:
        # Mifflin-St Jeor
        if patient.sex.lower() == "masculino":
            bmr = (
                10 * patient.weight_kg
                + 6.25 * patient.height_cm
                - 5 * patient.age
                + 5
            )
        else:
            bmr = (
                10 * patient.weight_kg
                + 6.25 * patient.height_cm
                - 5 * patient.age
                - 161
            )

        activity_factors = {
            "Sedentário": 1.2,
            "Leve": 1.375,
            "Moderado": 1.55,
            "Intenso": 1.725,
        }
        af = activity_factors.get(patient.activity_level, 1.4)
        tdee = bmr * af
        return tdee

    def adjust_for_goal(self, tdee: float, goal: str) -> float:
        goal = goal.lower()
        if "emagrec" in goal:
            return tdee * 0.8  # déficit ~20%
        if "ganho" in goal or "massa" in goal:
            return tdee * 1.15  # superávit ~15%
        return tdee  # manutenção

    # --------- FILTRAR POR RESTRIÇÕES --------- #

    def filter_by_restrictions(self, patient: PatientInfo) -> pd.DataFrame:
        df = self.food_df.copy()

        # padrão alimentar
        if patient.pattern == "Vegetariano":
            df = df[df["is_vegetarian"]]
        elif patient.pattern == "Vegano":
            df = df[df["is_vegan"]]

        # restrições clínicas
        if patient.is_celiac:
            df = df[df["is_gluten_free"]]
        if patient.is_diabetic:
            df = df[df["is_ok_for_diabetes"]]
        if patient.is_hypertensive:
            df = df[df["is_low_sodium"]]
        if patient.lactose_intolerance:
            df = df[~df["contains_lactose"]]
        if patient.egg_allergy:
            df = df[~df["contains_egg"]]
        if patient.nut_allergy:
            df = df[~df["contains_nuts"]]

        # fallback: se filtro ficou muito restrito, volta para base original
        if df.empty:
            df = self.food_df.copy()

        return df

    # --------- ESTRUTURA DE REFEIÇÕES --------- #

    def _meal_structure(self, meals_per_day: int) -> List[Dict[str, Any]]:
        """
        Define nomes das refeições e percentual de calorias.
        """
        if meals_per_day <= 3:
            return [
                {"name": "Café da manhã ☕", "kcal_pct": 0.25, "type": "breakfast"},
                {"name": "Almoço 🍽️", "kcal_pct": 0.40, "type": "lunch"},
                {"name": "Jantar 🌙", "kcal_pct": 0.35, "type": "dinner"},
            ]
        elif meals_per_day == 4:
            return [
                {"name": "Café da manhã ☕", "kcal_pct": 0.22, "type": "breakfast"},
                {"name": "Almoço 🍽️", "kcal_pct": 0.38, "type": "lunch"},
                {"name": "Lanche da tarde 🥙", "kcal_pct": 0.15, "type": "snack"},
                {"name": "Jantar 🌙", "kcal_pct": 0.25, "type": "dinner"},
            ]
        elif meals_per_day == 5:
            return [
                {"name": "Café da manhã ☕", "kcal_pct": 0.20, "type": "breakfast"},
                {"name": "Lanche da manhã 🥐", "kcal_pct": 0.10, "type": "snack"},
                {"name": "Almoço 🍽️", "kcal_pct": 0.35, "type": "lunch"},
                {"name": "Lanche da tarde 🥙", "kcal_pct": 0.15, "type": "snack"},
                {"name": "Jantar 🌙", "kcal_pct": 0.20, "type": "dinner"},
            ]
        else:  # 6 ou mais
            return [
                {"name": "Café da manhã ☕", "kcal_pct": 0.18, "type": "breakfast"},
                {"name": "Lanche da manhã 🥐", "kcal_pct": 0.10, "type": "snack"},
                {"name": "Almoço 🍽️", "kcal_pct": 0.32, "type": "lunch"},
                {"name": "Lanche da tarde 🥙", "kcal_pct": 0.12, "type": "snack"},
                {"name": "Jantar 🌙", "kcal_pct": 0.18, "type": "dinner"},
                {"name": "Ceia 🌜", "kcal_pct": 0.10, "type": "snack_low"},
            ]

    # --------- SELEÇÃO DE ALIMENTOS --------- #

    def _choose_item(
        self,
        df: pd.DataFrame,
        group_filter: List[str],
        kcal_target: float,
    ) -> Dict[str, Any]:
        df_group = df[df["group"].isin(group_filter)].copy()
        if df_group.empty:
            # fallback para qualquer alimento
            df_group = df.copy()

        # escolhe um alimento "aleatório"
        row = df_group.sample(1, random_state=self.rng.integers(0, 10_000)).iloc[0]

        kcal_100g = float(row["energy_kcal_per_100g"])
        if kcal_100g <= 0:
            grams = 0
        else:
            grams = kcal_target / kcal_100g * 100
            # arredondar para 5g
            grams = max(10, round(grams / 5) * 5)

        # substituições equivalentes
        subs_df = df_group.copy()
        subs_df = subs_df[subs_df["name"] != row["name"]]
        subs_df = subs_df[
            subs_df["energy_kcal_per_100g"].between(kcal_100g * 0.7, kcal_100g * 1.3)
        ]
        subs = subs_df["name"].drop_duplicates().head(5).tolist()

        return {
            "name": row["name"],
            "group": row["group"],
            "kcal_per_100g": kcal_100g,
            "grams": grams,
            "kcal_total": round(grams * kcal_100g / 100),
            "substitutions": subs,
        }

    def _build_meal(
        self,
        df_filtered: pd.DataFrame,
        meal_type: str,
        meal_kcal: float,
        pattern: str,
    ) -> Dict[str, Any]:
        """
        Constrói uma refeição com regras específicas por tipo.
        """
        # Definir percentuais por componente
        if meal_type == "breakfast":
            # carb leve + proteína leve + fruta
            comp = {
                "carb": 0.4,
                "protein": 0.3,
                "fruit": 0.3,
                "veggie": 0.0,
            }
        elif meal_type == "lunch":
            comp = {
                "carb": 0.40,
                "protein": 0.35,
                "fruit": 0.0,
                "veggie": 0.25,
            }
        elif meal_type == "dinner":
            comp = {
                "carb": 0.25,
                "protein": 0.35,
                "fruit": 0.0,
                "veggie": 0.40,
            }
        elif meal_type == "snack_low":
            comp = {
                "carb": 0.20,
                "protein": 0.30,
                "fruit": 0.50,
                "veggie": 0.0,
            }
        else:  # snack
            comp = {
                "carb": 0.25,
                "protein": 0.25,
                "fruit": 0.50,
                "veggie": 0.0,
            }

        # Grupos
        carb_groups = ["cereal", "tuberculo"]
        fruit_groups = ["fruta"]
        veggie_groups = ["hortalica", "legume", "leguminosa"]

        if pattern == "Vegano":
            protein_groups = ["proteina_vegetal", "leguminosa"]
        elif pattern == "Vegetariano":
            protein_groups = ["proteina_vegetal", "leguminosa", "proteina_animal"]
        else:
            protein_groups = ["proteina_animal", "proteina_vegetal", "leguminosa"]

        items = []

        if comp["carb"] > 0:
            items.append(
                self._choose_item(
                    df_filtered,
                    carb_groups,
                    meal_kcal * comp["carb"],
                )
            )

        if comp["protein"] > 0:
            items.append(
                self._choose_item(
                    df_filtered,
                    protein_groups,
                    meal_kcal * comp["protein"],
                )
            )

        if comp["fruit"] > 0:
            items.append(
                self._choose_item(
                    df_filtered,
                    fruit_groups,
                    meal_kcal * comp["fruit"],
                )
            )

        if comp["veggie"] > 0:
            items.append(
                self._choose_item(
                    df_filtered,
                    veggie_groups,
                    meal_kcal * comp["veggie"],
                )
            )

        # Ajuste de calorias reais da refeição
        total_kcal_real = sum(i["kcal_total"] for i in items)

        return {
            "items": items,
            "kcal_target": round(meal_kcal),
            "kcal_real": round(total_kcal_real),
        }

    # --------- PLANO ALIMENTAR COMPLETO --------- #

    def generate_meal_plan(self, patient: PatientInfo) -> Dict[str, Any]:
        tdee = self.calculate_tdee(patient)
        target_kcal = self.adjust_for_goal(tdee, patient.goal)
        bmi, bmi_cat = self.calculate_bmi(patient.weight_kg, patient.height_cm)

        structure = self._meal_structure(patient.meals_per_day)
        df_filtered = self.filter_by_restrictions(patient)

        meals_output = []
        for m in structure:
            meal_kcal = target_kcal * m["kcal_pct"]
            meal_data = self._build_meal(
                df_filtered=df_filtered,
                meal_type=m["type"],
                meal_kcal=meal_kcal,
                pattern=patient.pattern,
            )
            meal_data["name"] = m["name"]
            meals_output.append(meal_data)

        return {
            "bmi": bmi,
            "bmi_category": bmi_cat,
            "tdee": round(tdee),
            "target_kcal": round(target_kcal),
            "meals": meals_output,
        }

    # --------- HIDRATAÇÃO E SONO --------- #

    def calculate_hydration(self, patient: PatientInfo) -> Dict[str, Any]:
        # regra: sedentário = 35 ml/kg, demais = 50 ml/kg
        if patient.activity_level == "Sedentário":
            ml_per_kg = 35
        else:
            ml_per_kg = 50

        total_ml = patient.weight_kg * ml_per_kg
        liters = total_ml / 1000
        cups_200 = total_ml / 200

        return {
            "total_ml": round(total_ml),
            "liters": round(liters, 2),
            "cups_200": math.ceil(cups_200),
            "ml_per_kg": ml_per_kg,
        }

    def sleep_hygiene_tips(self, age: int) -> Dict[str, Any]:
        if age < 18:
            rec = "8–10 horas por noite"
        elif age < 65:
            rec = "7–9 horas por noite"
        else:
            rec = "7–8 horas por noite"

        tips = [
            "Evitar telas (celular, TV, computador) 60–90 minutos antes de dormir.",
            "Tentar deitar e acordar em horários semelhantes todos os dias.",
            "Evitar refeições muito pesadas nas 2–3 horas antes de dormir.",
            "Reduzir cafeína (café, energéticos, pré-treino) após o meio da tarde.",
            "Manter o quarto escuro, silencioso e com temperatura agradável.",
        ]

        return {
            "recommended": rec,
            "tips": tips,
        }
