from dataclasses import dataclass
from typing import List, Literal, Dict, Any
import math
import pandas as pd

ActivityLevel = Literal["sedentary", "light", "moderate", "high"]
Goal = Literal["fat_loss", "muscle_gain"]
DietaryPattern = Literal["omnivore", "vegetarian", "vegan"]

Restriction = Literal[
    "celiac",
    "diabetes",
    "hypertension",
    "lactose_intolerance",
    "egg_allergy",
    "nut_allergy"
]

@dataclass
class UserInput:
    name: str
    age: int
    sex: Literal["male", "female"]
    weight_kg: float
    height_cm: float
    activity_level: ActivityLevel
    goal: Goal
    meals_per_day: int
    dietary_pattern: DietaryPattern
    restrictions: List[Restriction]
    dislikes: List[str]

def load_food_database(csv_path: str) -> List[Dict[str, Any]]:
    df = pd.read_csv(csv_path)
    records = df.to_dict(orient="records")
    return records

def calc_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)

def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Abaixo do peso"
    elif bmi < 25:
        return "Peso adequado"
    elif bmi < 30:
        return "Sobrepeso"
    elif bmi < 35:
        return "Obesidade grau I"
    elif bmi < 40:
        return "Obesidade grau II"
    else:
        return "Obesidade grau III"

def estimate_tdee(user: UserInput) -> float:
    if user.sex == "male":
        bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age + 5
    else:
        bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age - 161

    activity_factor_map = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "high": 1.725
    }
    tdee = bmr * activity_factor_map[user.activity_level]

    if user.goal == "fat_loss":
        tdee *= 0.8
    elif user.goal == "muscle_gain":
        tdee *= 1.1

    return round(tdee)

def macro_split(user: UserInput, total_kcal: float) -> Dict[str, float]:
    if user.goal == "fat_loss":
        protein_kcal = total_kcal * 0.30
        fat_kcal = total_kcal * 0.25
        carb_kcal = total_kcal * 0.45
    else:
        protein_kcal = total_kcal * 0.25
        fat_kcal = total_kcal * 0.25
        carb_kcal = total_kcal * 0.50

    return {
        "protein_g": round(protein_kcal / 4, 1),
        "carb_g": round(carb_kcal / 4, 1),
        "fat_g": round(fat_kcal / 9, 1),
    }

def water_intake_ml(user: UserInput) -> int:
    if user.activity_level == "sedentary":
        return int(user.weight_kg * 35)
    else:
        return int(user.weight_kg * 50)

def food_allowed_for_user(food: Dict[str, Any], user: UserInput) -> bool:
    name_lower = str(food.get("name", "")).lower()

    for d in user.dislikes:
        if d.lower() in name_lower:
            return False

    if user.dietary_pattern == "vegetarian" and not bool(food.get("is_vegetarian", True)):
        return False
    if user.dietary_pattern == "vegan" and not bool(food.get("is_vegan", True)):
        return False

    if "celiac" in user.restrictions and not bool(food.get("is_gluten_free", True)):
        return False
    if "diabetes" in user.restrictions and not bool(food.get("is_ok_for_diabetes", True)):
        return False
    if "hypertension" in user.restrictions and not bool(food.get("is_low_sodium", True)):
        return False
    if "lactose_intolerance" in user.restrictions and bool(food.get("contains_lactose", False)):
        return False
    if "egg_allergy" in user.restrictions and bool(food.get("contains_egg", False)):
        return False
    if "nut_allergy" in user.restrictions and bool(food.get("contains_nuts", False)):
        return False

    return True

def get_filtered_foods(user: UserInput, foods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [f for f in foods if food_allowed_for_user(f, user)]

def build_meal_plan(user: UserInput, foods: List[Dict[str, Any]]) -> Dict[str, Any]:
    bmi = calc_bmi(user.weight_kg, user.height_cm)
    bmi_class = classify_bmi(bmi)
    total_kcal = estimate_tdee(user)
    macros = macro_split(user, total_kcal)
    water_ml = water_intake_ml(user)

    foods = get_filtered_foods(user, foods)

    fruits = [f for f in foods if f.get("group") == "fruta"]
    veggies = [f for f in foods if f.get("group") in ("hortalica", "legume")]
    proteins = [f for f in foods if "proteina" in str(f.get("group", ""))]
    carbs = [f for f in foods if f.get("group") in ("cereal", "tuberculo")]

    meals = []
    per_meal_kcal = total_kcal / user.meals_per_day if user.meals_per_day > 0 else total_kcal

    def pick_and_calc_portion(food_list, target_kcal, index):
        if not food_list or target_kcal <= 0:
            return None
        food = food_list[index % len(food_list)]
        energy = float(food.get("energy_kcal_per_100g", 0) or 0)
        if energy <= 0:
            return None
        grams = (target_kcal / energy) * 100
        return {
            "name": food.get("name", ""),
            "preparation": food.get("preparation", ""),
            "grams": int(grams),
            "kcal": round(energy * grams / 100),
        }

    for i in range(user.meals_per_day):
        meal_target = per_meal_kcal
        carb_kcal = meal_target * 0.4
        protein_kcal = meal_target * 0.3
        fruit_kcal = meal_target * 0.15
        veggie_kcal = meal_target * 0.15

        carb_item = pick_and_calc_portion(carbs, carb_kcal, i)
        protein_item = pick_and_calc_portion(proteins, protein_kcal, i)
        fruit_item = pick_and_calc_portion(fruits, fruit_kcal, i)
        veggie_item = pick_and_calc_portion(veggies, veggie_kcal, i)

        items = [x for x in [carb_item, protein_item, fruit_item, veggie_item] if x]

        meals.append({
            "name": f"Refeição {i+1}",
            "target_kcal": round(meal_target),
            "items": items,
        })

    hydration_block = {
        "target_ml": water_ml,
        "guidance": [
            "Distribua a ingestão de água ao longo do dia.",
            "Use garrafa marcada para acompanhar o volume diário.",
            "Observe a cor da urina: quanto mais clara, melhor a hidratação."
        ]
    }

    sleep_hygiene_block = {
        "title": "Higiene do Sono",
        "guidance": [
            "Mantenha horários fixos para dormir e acordar.",
            "Evite telas e luz azul pelo menos 1 hora antes de dormir.",
            "Reduza cafeína após o meio da tarde.",
            "Crie um ritual relaxante pré-sono (leitura leve, respiração, alongamento).",
            "Prefira ambiente escuro, silencioso e fresco para dormir."
        ]
    }

    education_block = {
        "title": "Educação Alimentar",
        "points": [
            "Priorize alimentos in natura e minimamente processados.",
            "Inclua frutas, legumes e hortaliças em todas as refeições principais.",
            "Coma devagar, mastigando bem, respeitando sinais de fome e saciedade.",
            "Evite dietas extremas sem acompanhamento profissional."
        ]
    }

    return {
        "user": {
            "name": user.name,
            "bmi": bmi,
            "bmi_classification": bmi_class,
            "total_kcal": total_kcal,
            "macros": macros,
        },
        "hydration": hydration_block,
        "sleep_hygiene": sleep_hygiene_block,
        "education": education_block,
        "meals": meals,
    }