import streamlit as st
from nutrition_engine import (
    carregar_banco_de_dados_de_alimentos,
    NutritionEngine,
    Informações_do_Paciente,
)

# ===========================================
# CONFIGURAÇÃO DE PÁGINA – DARK PREMIUM
# ===========================================
st.set_page_config(
    page_title="MindsetFit - Nutrição IA",
    layout="wide",
)

# ===========================================
# CSS PREMIUM (Dark, Minimalista, Clean)
# ===========================================
st.markdown(
    """
<style>

body {
    background-color: #0f1116;
    color: #ffffff;
}

/* Container principal */
.block-container { 
    padding-top: 2rem; 
}

/* Títulos */
h1, h2, h3, h4 {
    font-weight: 700 !important;
    letter-spacing: -1px !important;
}

/* Cards */
.card {
    background: #16181d;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0px 0px 18px rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.07);
}

/* Botão */
.stButton button {
    background: #ffffff10;
    color: white;
    border-radius: 8px;
    padding: 10px 18px;
    border: 1px solid #ffffff30;
}
.stButton button:hover {
    background: #ffffff25;
    border: 1px solid #ffffff50;
}

</style>
""",
    unsafe_allow_html=True,
)

# ===========================================
# TÍTULO PREMIUM
# ===========================================
st.markdown(
    "<h1 style='text-align:center; margin-bottom:40px;'>🧠 MINDSETFIT – Nutricionista IA Premium</h1>",
    unsafe_allow_html=True,
)

# ===========================================
# CARREGA BANCO DE DADOS
# ===========================================
foods_db = load_food_database("taco_sample.csv")

# ===========================================
# LAYOUT: FORM ESQUERDA / RESULTADO DIREITA
# ===========================================
col_form, col_result = st.columns([1, 1.6])

# --------------------------
# FORMULÁRIO – LADO ESQUERDO
# --------------------------
with col_form:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("### 📋 Dados do Paciente")

    nome = st.text_input("Nome", value="Paciente Teste")
    idade = st.number_input("Idade", 15, 100, 30)
    sexo = st.selectbox("Sexo", ["masculino", "feminino"])

    peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    altura = st.number_input("Altura (cm)", 120, 230, 178)

    atividade = st.selectbox(
        "Nível de atividade",
        ["Sedentário", "Leve", "Moderado", "Intenso"],
    )

    objetivo = st.selectbox(
        "Objetivo",
        ["Emagrecimento", "Ganho de massa muscular", "Manutenção"],
    )

    refeicoes = st.number_input("Refeições por dia", 3, 8, 5)

    # 🔹 Padrão alimentar
    pattern = st.selectbox(
        "Padrão alimentar",
        ["Onívoro", "Vegetariano", "Vegano"],
        index=0,
    )

    # 🔹 Restrições e condições de saúde
    with st.expander("⚕️ Restrições e condições de saúde"):
        is_celiac = st.checkbox("Doença celíaca / sem glúten")
        is_diabetic = st.checkbox("Diabetes")
        is_hypertensive = st.checkbox("Hipertensão")
        lactose_intolerance = st.checkbox("Intolerância à lactose")
        egg_allergy = st.checkbox("Alergia a ovo")
        nut_allergy = st.checkbox("Alergia a oleaginosas (castanhas, nozes, amendoim)")

    gerar = st.button("Gerar Plano Alimentar", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# RESULTADO – LADO DIREITO
# --------------------------
with col_result:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 🍽️ Plano Alimentar Individualizado")

    if not gerar:
        st.info("Preencha os dados ao lado e clique em **Gerar Plano Alimentar**.")
    else:
        try:
            # Criar objeto PatientInfo com os campos esperados pelo engine
            patient = PatientInfo(
                name=nome,
                age=int(idade),
                sex=sexo,
                weight_kg=float(peso),
                height_cm=float(altura),
                activity_level=atividade,
                goal=objetivo,
                meals_per_day=int(refeicoes),
                pattern=pattern,
                is_celiac=is_celiac,
                is_diabetic=is_diabetic,
                is_hypertensive=is_hypertensive,
                lactose_intolerance=lactose_intolerance,
                egg_allergy=egg_allergy,
                nut_allergy=nut_allergy,
            )

            engine = NutritionEngine(foods_db)
            plan = engine.generate_meal_plan(patient)

            st.success(f"Plano gerado para **{nome}**")

            # Resumo geral
            st.write(f"**IMC:** {plan['bmi']} – {plan['bmi_category']}")
            st.write(f"**TDEE estimado:** {plan['tdee']} kcal")
            st.write(f"**Meta calórica:** {plan['target_kcal']} kcal")

            st.markdown("---")
            st.markdown("#### 🍽️ Refeições do dia")

            for meal in plan["meals"]:
                st.markdown(f"**{meal['name']}**")
                st.write(
                    f"Alvo: {meal['kcal_target']} kcal | "
                    f"Planejado: {meal['kcal_real']} kcal"
                )

                for item in meal["items"]:
                    subs_text = ", ".join(item["substitutions"]) if item["substitutions"] else "—"
                    st.markdown(
                        f"- {item['name']} — **{item['grams']} g** "
                        f"(_~{item['kcal_total']} kcal_)  \n"
                        f"  Substituições: {subs_text}"
                    )

                st.markdown("---")

        except Exception as e:
            st.error("❌ Ocorreu um erro ao gerar o plano.")
            st.exception(e)

    st.markdown("</div>", unsafe_allow_html=True)
