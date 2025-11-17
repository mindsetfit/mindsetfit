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
st.markdown("""
<style>

body {
    background-color: #0f1116;
    color: #ffffff;
}

/* Caixas */
.block-container { padding-top: 2rem; }

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

/* Inputs */
.stSelectbox, .stTextInput, .stNumberInput {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# ===========================================
# TÍTULO PREMIUM
# ===========================================
st.markdown("<h1 style='text-align:center; margin-bottom:40px;'>🧠 MINDSETFIT – Nutricionista IA Premium</h1>", unsafe_allow_html=True)

# ===========================================
# CARREGA BANCO DE DADOS
# ===========================================
foods_db = carregar_banco_de_dados_de_alimentos()

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
    nome = st.text_input("Nome")
    idade = st.number_input("Idade", 15, 100, 30)
    sexo = st.selectbox("Sexo", ["masculino", "feminino"])
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    altura = st.number_input("Altura (cm)", 120, 230, 178)
    atividade = st.selectbox("Nível de atividade", ["Sedentário", "Leve", "Moderado", "Alto", "Atleta"])
    objetivo = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde", "Performance"])
    refeicoes = st.number_input("Refeições por dia", 3, 8, 5)

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
            # Criar objeto com informações
            dados = Informações_do_Paciente(
                nome=nome,
                idade=idade,
                sexo=sexo,
                peso=peso,
                altura=altura,
                atividade=atividade,
                objetivo=objetivo,
                refeicoes=refeicoes,
            )

            engine = NutritionEngine(foods_db)
            plano = engine.gerar_plano(dados)

            st.success(f"Plano gerado para **{nome}**")
            st.write(plano)

        except Exception as e:
            st.error("❌ Ocorreu um erro ao gerar o plano.")
            st.exception(e)

    st.markdown("</div>", unsafe_allow_html=True)
