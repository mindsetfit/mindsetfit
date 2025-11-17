import streamlit as st

from nutrition_engine import (
    load_food_database,
    NutritionEngine,
    PatientInfo,
)


# ----------------- ESTILO GLOBAL (DARK PREMIUM) ----------------- #


def inject_css():
    st.markdown(
        """
        <style>
        /* Fundo geral */
        .stApp {
            background-color: #050915;
            color: #f4f4f4;
            font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #0c111e !important;
            border-right: 1px solid #141b2f;
        }

        /* Títulos principais */
        .main-title {
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #f5f7ff;
        }

        .main-subtitle {
            font-size: 0.98rem;
            color: #d0d6f5;
            margin-top: 0.3rem;
        }

        /* Cards */
        .card {
            background: #0c111e;
            border-radius: 18px;
            padding: 18px 20px;
            border: 1px solid #141b2f;
            box-shadow: 0 18px 45px rgba(0,0,0,0.55);
            margin-bottom: 18px;
        }

        .card-header {
            font-weight: 700;
            font-size: 1.05rem;
            color: #e6ebff;
            margin-bottom: 4px;
        }

        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #9ff8c8;
            background: rgba(62, 207, 142, 0.12);
            border: 1px solid rgba(62, 207, 142, 0.4);
        }

        .kcal-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 999px;
            background: #0b1624;
            border: 1px solid #1f2b45;
            font-size: 0.72rem;
            color: #f7f9ff;
        }

        .kcal-pill span {
            color: #3ecf8e;
            font-weight: 700;
        }

        .food-line {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            padding: 4px 0;
            border-bottom: 1px dashed #1a2238;
        }

        .food-line:last-child {
            border-bottom: none;
        }

        .food-main {
            color: #f4f4ff;
        }

        .food-meta {
            color: #a1aacb;
            font-size: 0.8rem;
        }

        .subs-label {
            font-size: 0.78rem;
            color: #8f97be;
            margin-top: 4px;
        }

        .subs-badge {
            display: inline-block;
            padding: 2px 8px;
            margin: 2px 4px 0 0;
            border-radius: 999px;
            background: #050915;
            border: 1px solid #222b4a;
            font-size: 0.72rem;
            color: #d3dbff;
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #f0f4ff;
            margin-bottom: 6px;
        }

        .small-muted {
            font-size: 0.78rem;
            color: #9aa3c8;
        }

        .hydro-pill {
            padding: 6px 10px;
            border-radius: 999px;
            background: #071523;
            border: 1px solid #153554;
            font-size: 0.8rem;
            color: #e2f5ff;
            margin-right: 6px;
        }

        .hydro-pill span {
            color: #48d6ff;
            font-weight: 700;
        }

        .sleep-tip {
            font-size: 0.86rem;
            color: #d8defc;
            padding-left: 0.6rem;
        }

        .sleep-tip::before {
            content: "• ";
            color: #3ecf8e;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------- APP ----------------- #


def sidebar_inputs():
    st.sidebar.title("Dados do Paciente")

    name = st.sidebar.text_input("Nome", value="Paciente Teste")

    age = st.sidebar.number_input("Idade", 16, 90, value=30, step=1)

    sex = st.sidebar.selectbox("Sexo", ["masculino", "feminino"])

    weight = st.sidebar.number_input("Peso (kg)", 30.0, 250.0, value=80.0, step=0.5)

    height = st.sidebar.number_input("Altura (cm)", 130.0, 220.0, value=178.0, step=1.0)

    activity = st.sidebar.selectbox(
        "Nível de atividade",
        ["Sedentário", "Leve", "Moderado", "Intenso"],
        index=0,
    )

    goal = st.sidebar.selectbox(
        "Objetivo",
        ["Emagrecimento", "Ganho de massa muscular", "Manutenção"],
    )

    meals = st.sidebar.slider("Refeições por dia", 3, 6, value=4)

    pattern = st.sidebar.selectbox(
        "Padrão alimentar",
        ["Onívoro", "Vegetariano", "Vegano"],
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Restrições e condições")

    is_celiac = st.sidebar.checkbox("Doença celíaca (sem glúten)")
    is_diabetic = st.sidebar.checkbox("Diabetes (controle de carboidratos)")
    is_hypertensive = st.sidebar.checkbox("Hipertensão (baixo sódio)")
    lactose_intolerance = st.sidebar.checkbox("Intolerância à lactose")
    egg_allergy = st.sidebar.checkbox("Alergia a ovo")
    nut_allergy = st.sidebar.checkbox("Alergia a oleaginosas (castanhas, amendoim)")

    st.sidebar.markdown("---")
    generate = st.sidebar.button("✨ Gerar plano alimentar")

    patient = PatientInfo(
        name=name,
        age=age,
        sex=sex,
        weight_kg=weight,
        height_cm=height,
        activity_level=activity,
        goal=goal,
        meals_per_day=meals,
        pattern=pattern,
        is_celiac=is_celiac,
        is_diabetic=is_diabetic,
        is_hypertensive=is_hypertensive,
        lactose_intolerance=lactose_intolerance,
        egg_allergy=egg_allergy,
        nut_allergy=nut_allergy,
    )

    return patient, generate


def render_header():
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <div class="badge">MindsetFit • Nutricionista Virtual IA</div>
            <div class="main-title" style="margin-top: 10px;">
                Planejamento Alimentar Inteligente
            </div>
            <div class="main-subtitle">
                Sistema educativo de planejamento alimentar individualizado. 
                <strong>Não substitui consulta presencial com nutricionista.</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(summary: dict, patient: PatientInfo):
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">IMC</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="kcal-pill">
                <span>{summary['bmi']}</span> kg/m²
            </div>
            <div class="small-muted" style="margin-top:6px;">
                Classificação: <strong>{summary['bmi_category']}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Gasto energético</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="kcal-pill">
                <span>{summary['tdee']}</span> kcal/dia (estimado)
            </div>
            <div class="small-muted" style="margin-top:6px;">
                Baseado em Mifflin-St Jeor + nível de atividade.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Meta calórica</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="kcal-pill">
                <span>{summary['target_kcal']}</span> kcal/dia
            </div>
            <div class="small-muted" style="margin-top:6px;">
                Ajustada para objetivo de <strong>{patient.goal}</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_meal_plan(summary: dict):
    st.markdown("### Plano alimentar diário")

    for meal in summary["meals"]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card-header">{meal["name"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="kcal-pill" style="margin-bottom:8px;">
                alvo: <span>{meal['kcal_target']} kcal</span> 
                · real: {meal['kcal_real']} kcal
            </div>
            """,
            unsafe_allow_html=True,
        )

        for item in meal["items"]:
            st.markdown(
                f"""
                <div class="food-line">
                    <div class="food-main">
                        {item['name']}
                        <div class="food-meta">
                            {item['grams']} g · {item['kcal_total']} kcal
                        </div>
                    </div>
                    <div class="food-meta">
                        {item['group']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if item["substitutions"]:
                subs_html = "".join(
                    f'<span class="subs-badge">{s}</span>'
                    for s in item["substitutions"]
                )
                st.markdown(
                    f"""
                    <div class="subs-label">
                        Trocas possíveis (similar em kcal e grupo):<br/>
                        {subs_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)


def render_hydration_and_sleep(engine: NutritionEngine, patient: PatientInfo):
    col1, col2 = st.columns([1.1, 1])

    hydro = engine.calculate_hydration(patient)
    sleep = engine.sleep_hygiene_tips(patient.age)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">Hidratação diária recomendada 💧</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="hydro-pill">
                <span>{hydro['total_ml']} ml</span> por dia
            </div>
            <div class="hydro-pill">
                ~ <span>{hydro['liters']} L</span> / dia
            </div>
            <div class="hydro-pill">
                ~ <span>{hydro['cups_200']}</span> copos de 200 ml
            </div>
            <div class="small-muted" style="margin-top:6px;">
                Cálculo: {hydro['ml_per_kg']} ml/kg · 
                Ajustado conforme nível de atividade.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">Higiene do sono 😴</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="small-muted" style="margin-bottom:6px;">
                Para sua faixa etária, a recomendação geral é de 
                <strong>{sleep['recommended']}</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        for tip in sleep["tips"]:
            st.markdown(f'<div class="sleep-tip">{tip}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="MindsetFit | Nutricionista IA",
        page_icon="🥗",
        layout="wide",
    )

    inject_css()

    patient, generate = sidebar_inputs()
    render_header()

    # Carregar base e engine
    try:
        food_df = load_food_database("taco_sample.csv")
    except Exception as e:
        st.error(
            "Erro ao carregar a base de alimentos (taco_sample.csv). "
            "Verifique se o arquivo existe no repositório."
        )
        st.exception(e)
        return

    engine = NutritionEngine(food_df)

    if not generate:
        st.info(
            "Preencha os dados na barra lateral e clique em **“Gerar plano alimentar”** "
            "para visualizar o planejamento.",
        )
        return

    summary = engine.generate_meal_plan(patient)

    render_overview(summary, patient)
    render_meal_plan(summary)
    render_hydration_and_sleep(engine, patient)


if __name__ == "__main__":
    main()
