import streamlit as st
from nutrition_engine import UserInput, load_food_database, build_meal_plan

st.set_page_config(page_title="Nutricionista Virtual IA", layout="wide")

st.title("Nutricionista Virtual IA")
st.write("Sistema educativo de planejamento alimentar individualizado. Não substitui consulta com nutricionista.")

with st.sidebar:
    st.header("Dados do Paciente")

    name = st.text_input("Nome", "Paciente Teste")
    age = st.number_input("Idade", min_value=10, max_value=100, value=30)
    sex = st.selectbox("Sexo", options=[("Masculino", "male"), ("Feminino", "female")], format_func=lambda x: x[0])[1]

    weight_kg = st.number_input("Peso (kg)", min_value=30.0, max_value=250.0, value=80.0, step=0.5)
    height_cm = st.number_input("Altura (cm)", min_value=130.0, max_value=220.0, value=178.0, step=0.5)

    activity_map = {
        "Sedentário": "sedentary",
        "Levemente ativo": "light",
        "Moderadamente ativo": "moderate",
        "Muito ativo": "high",
    }
    activity_label = st.selectbox("Nível de atividade", list(activity_map.keys()))
    activity_level = activity_map[activity_label]

    goal_map = {
        "Emagrecimento": "fat_loss",
        "Ganho de massa muscular": "muscle_gain",
    }
    goal_label = st.selectbox("Objetivo", list(goal_map.keys()))
    goal = goal_map[goal_label]

    meals_per_day = st.number_input("Refeições por dia", min_value=3, max_value=8, value=5)

    diet_pattern_map = {
        "Onívoro": "omnivore",
        "Vegetariano": "vegetarian",
        "Vegano": "vegan",
    }
    diet_label = st.selectbox("Padrão alimentar", list(diet_pattern_map.keys()))
    dietary_pattern = diet_pattern_map[diet_label]

    restrictions_options = {
        "Celíaco (sem glúten)": "celiac",
        "Diabetes": "diabetes",
        "Hipertensão": "hypertension",
        "Intolerância à lactose": "lactose_intolerance",
        "Alergia a ovo": "egg_allergy",
        "Alergia a castanhas/nozes": "nut_allergy",
    }
    selected_restrictions_labels = st.multiselect("Restrições e condições", list(restrictions_options.keys()))
    restrictions = [restrictions_options[l] for l in selected_restrictions_labels]

    dislikes_text = st.text_input("Alimentos que não gosta (separe por vírgula)", "")
    dislikes = [x.strip() for x in dislikes_text.split(",") if x.strip()]

    generate = st.button("Gerar plano alimentar")

foods = load_food_database("taco_sample.csv")

if generate:
    user = UserInput(
        name=name,
        age=int(age),
        sex=sex,
        weight_kg=float(weight_kg),
        height_cm=float(height_cm),
        activity_level=activity_level,
        goal=goal,
        meals_per_day=int(meals_per_day),
        dietary_pattern=dietary_pattern,
        restrictions=restrictions,
        dislikes=dislikes,
    )

    plan = build_meal_plan(user, foods)

    st.subheader("Resumo do Paciente")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("IMC", plan["user"]["bmi"], help=plan["user"]["bmi_classification"])
    with col2:
        st.metric("Kcal diárias estimadas", plan["user"]["total_kcal"])
    with col3:
        macros = plan["user"]["macros"]
        st.write(f"Proteínas: **{macros['protein_g']} g**")
        st.write(f"Carboidratos: **{macros['carb_g']} g**")
        st.write(f"Gorduras: **{macros['fat_g']} g**")

    st.subheader("Hidratação")
    st.write(f"Meta diária de água: **{plan['hydration']['target_ml']} ml**")
    for g in plan["hydration"]["guidance"]:
        st.write(f"- {g}")

    st.subheader(plan["education"]["title"])
    for p in plan["education"]["points"]:
        st.write(f"- {p}")

    st.subheader(plan["sleep_hygiene"]["title"])
    for p in plan["sleep_hygiene"]["guidance"]:
        st.write(f"- {p}")

    st.subheader("Plano de Refeições")
    for meal in plan["meals"]:
        st.markdown(f"### {meal['name']} (alvo ~ {meal['target_kcal']} kcal)")
        for item in meal["items"]:
            st.write(
                f"- {item['name']} ({item['preparation']}): **{item['grams']} g** (~{item['kcal']} kcal)"
            )

    st.info("Este plano é educativo e não substitui o acompanhamento individualizado com nutricionista.")
else:
    st.info("Preencha os dados na barra lateral e clique em **Gerar plano alimentar**.")