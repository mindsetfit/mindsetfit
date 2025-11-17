import streamlit as st
import pandas as pd
from nutrition_engine import (
    carregar_banco_de_dados_de_alimentos,
    NutritionEngine,
    Informações_do_Paciente,
)

# ======================================
# CONFIGURAÇÃO DE PÁGINA – DARK PREMIUM
# ======================================
st.set_page_config(
    page_title="MindsetFit – Nutrição IA",
    layout="wide",
)

# ======================================
# CARREGAMENTO DO BANCO DE DADOS
# ======================================
@st.cache_data
def carregar_engine():
    try:
        df_alimentos = carregar_banco_de_dados_de_alimentos("taco_sample.csv")
        engine = NutritionEngine(df_alimentos)
        return engine, df_alimentos, None
    except Exception as e:
        return None, None, str(e)


engine, df_alimentos, erro_db = carregar_engine()

if erro_db:
    st.error(f"Erro ao carregar banco de alimentos: {erro_db}")
    st.stop()

# ======================================
# CSS PREMIUM (Dark, Minimalista, Clean)
# ======================================
st.markdown(
    """
    <style>
    body {
        background-color: #0f1116;
        color: #ffffff;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
    }

    .sub-title {
        font-size: 1.0rem;
        color: #b0b3c1;
    }

    .card {
        background: #151821;
        border-radius: 18px;
        padding: 1.5rem 1.8rem;
        border: 1px solid #262a36;
        box-shadow: 0 14px 35px rgba(0,0,0,0.45);
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        color: #ffffff;
    }

    .hint-text {
        font-size: 0.9rem;
        color: #9ca0b3;
    }

    .metric-box {
        background: #11131b;
        border-radius: 14px;
        padding: 0.8rem 1rem;
        border: 1px solid #232738;
        text-align: center;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #a1a7c2;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .metric-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
    }

    .tag {
        display: inline-block;
        padding: 0.12rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        border: 1px solid #2b3042;
        color: #c3c7dd;
        margin-right: 0.3rem;
        margin-bottom: 0.2rem;
        background: #141722;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================
# CABEÇALHO
# ======================================
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem;">
        <span style="font-size:2.1rem;">🧠</span>
        <div>
            <div class="main-title">MINDSETFIT – Nutricionista IA Premium</div>
            <div class="sub-title">Planejamento alimentar inteligente, 100% individualizado para seu paciente.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")  # espaçamento

# ======================================
# LAYOUT PRINCIPAL (2 COLUNAS)
# ======================================
col_form, col_result = st.columns([1.1, 1.2])

# -------- COLUNA ESQUERDA: FORMULÁRIO --------
with col_form:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 Dados do Paciente</div>', unsafe_allow_html=True)

    nome = st.text_input("Nome", value="Paciente Teste")

    idade = st.number_input("Idade", min_value=10, max_value=100, value=30, step=1)

    sexo = st.selectbox("Sexo", options=["masculino", "feminino"], index=0)

    peso = st.number_input("Peso (kg)", min_value=30.0, max_value=250.0, value=80.0, step=0.5, format="%.2f")

    altura = st.number_input("Altura (cm)", min_value=120.0, max_value=220.0, value=178.0, step=1.0, format="%.0f")

    nivel_atividade = st.selectbox(
        "Nível de atividade",
        options=[
            "Sedentário",
            "Levemente ativo",
            "Moderadamente ativo",
            "Muito ativo",
            "Extremamente ativo",
        ],
        index=0,
    )

    objetivo = st.selectbox(
        "Objetivo principal",
        options=[
            "Emagrecimento",
            "Manutenção",
            "Ganho de massa",
        ],
        index=0,
    )

    st.markdown(
        '<p class="hint-text">Preencha os dados acima e clique em <b>Gerar Plano Alimentar</b> para calcular TMB, TDEE, kcal alvo e macronutrientes.</p>',
        unsafe_allow_html=True,
    )

    gerar = st.button("🚀 Gerar Plano Alimentar", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------- COLUNA DIREITA: RESULTADOS --------
with col_result:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🍽️ Plano Alimentar Individualizado</div>', unsafe_allow_html=True)

    if not gerar:
        st.markdown(
            '<p class="hint-text">Preencha os dados ao lado e clique no botão para visualizar o plano nutricional sugerido pela IA.</p>',
            unsafe_allow_html=True,
        )
    else:
        # Cria o objeto paciente
        paciente = Informações_do_Paciente(
            nome=nome,
            idade=int(idade),
            sexo=sexo,
            peso=float(peso),
            altura=float(altura),
            nivel_atividade=nivel_atividade,
            objetivo=objetivo,
        )

        # Gera os resultados principais
        resultado = engine.gerar_plano(paciente)
        macros = resultado["macros"]

        # --- Cards de métricas principais ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">TMB</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{resultado["tmb"]} kcal</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with m2:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">TDEE</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{resultado["tdee"]} kcal</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with m3:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">KCAL OBJETIVO</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{resultado["kcal_objetivo"]} kcal</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown("#### Distribuição de Macronutrientes (estimada)")

        df_macros = pd.DataFrame(
            [
                {
                    "Macronutriente": "Proteínas",
                    "Quantidade (g)": macros["proteina_g"],
                    "% Kcal aprox.": 30,
                },
                {
                    "Macronutriente": "Carboidratos",
                    "Quantidade (g)": macros["carbo_g"],
                    "% Kcal aprox.": 45,
                },
                {
                    "Macronutriente": "Gorduras",
                    "Quantidade (g)": macros["gordura_g"],
                    "% Kcal aprox.": 25,
                },
            ]
        )

        st.dataframe(
            df_macros,
            use_container_width=True,
            hide_index=True,
        )

        st.write("")

        st.markdown("#### Contexto do Paciente")
        tags = [
            f"Idade: {paciente.idade} anos",
            f"Sexo: {paciente.sexo.capitalize()}",
            f"Peso: {paciente.peso:.1f} kg",
            f"Altura: {paciente.altura:.0f} cm",
            f"Atividade: {paciente.nivel_atividade}",
            f"Objetivo: {paciente.objetivo}",
        ]
        tags_html = "".join([f'<span class="tag">{t}</span>' for t in tags])
        st.markdown(tags_html, unsafe_allow_html=True)

        st.write("")
        st.markdown(
            '<p class="hint-text">A partir desses dados, você pode montar o cardápio detalhado no seu padrão profissional (refeições, horários, substituições etc.), usando o banco TACO como base.</p>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)
