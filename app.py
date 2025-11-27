import streamlit as st
import pandas as pd
from utils.loader import load_taco_database
from nutrition_engine import (
    tmb_mifflin, tmb_harris, tmb_katch, sugerir_refeicoes
)

st.set_page_config(
    page_title="MindsetFit — Sistema Nutricional",
    layout="wide"
)

# ======= CARREGAR CSS =======
with open("styles/theme.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ======= CARREGAR TACO =======
try:
    taco = load_taco_database("database/taco.csv")
except Exception as e:
    st.error(f"❌ Erro ao carregar TACO: {e}")
    st.stop()

# =========================
#          ABAS
# =========================

aba1, aba2 = st.tabs(["📋 Dados do Paciente", "📊 Resultado Final"])

# =========================
#          ABA 1
# =========================

with aba1:

    st.title("Anamnese Nutricional — MindsetFit")

    with st.container():
        st.subheader("Dados gerais")

        col1, col2, col3 = st.columns(3)
        with col1:
            sexo = st.selectbox("Sexo", ["Masculino", "Feminino"])
        with col2:
            idade = st.number_input("Idade", 10, 100, 25)
        with col3:
            altura = st.number_input("Altura (cm)", 120, 230, 175)

        col4, col5 = st.columns(2)
        with col4:
            peso = st.number_input("Peso (kg)", 30, 250, 80)
        with col5:
            bf = st.number_input("Gordura corporal (%)", 5, 50, 15)

    st.markdown("---")
    st.subheader("Equação de TMB")

    eq = st.selectbox("Escolha o método", [
        "Mifflin-St Jeor",
        "Harris-Benedict",
        "Katch-McArdle"
    ])

    if eq == "Mifflin-St Jeor":
        tmb = tmb_mifflin(sexo, peso, altura, idade)
    elif eq == "Harris-Benedict":
        tmb = tmb_harris(sexo, peso, altura, idade)
    else:
        tmb = tmb_katch(peso, bf)

    st.success(f"TMB calculada: **{tmb:.0f} kcal**")

    st.session_state["tmb"] = tmb

    st.info("➡ Vá para a aba RESULTADO FINAL para gerar o plano.")

# =========================
#          ABA 2
# =========================

with aba2:
    st.title("📊 Resultado Final")

    if "tmb" not in st.session_state:
        st.warning("⚠ Volte à primeira aba e preencha os dados.")
        st.stop()

    tmb = st.session_state["tmb"]

    st.subheader("Meta calórica")
    objetivo = st.selectbox("Objetivo", ["Emagrecimento", "Manutenção", "Ganho"])

    if objetivo == "Emagrecimento":
        kcal_final = tmb - 350
    elif objetivo == "Ganho":
        kcal_final = tmb + 300
    else:
        kcal_final = tmb

    st.success(f"Meta diária: **{kcal_final:.0f} kcal**")

    st.markdown("---")
    st.subheader("Sugestão automática de refeições (TACO)")

    refeicoes = sugerir_refeicoes(taco, kcal_final)
    st.dataframe(refeicoes)

    st.markdown("---")
    st.success("Plano gerado com sucesso! 🚀")
