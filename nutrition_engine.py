import pandas as pd
import numpy as np

# ===== EQUAÇÕES DE TMB =====

def tmb_mifflin(sexo, peso, altura, idade):
    if sexo == "Masculino":
        return 10*peso + 6.25*altura - 5*idade + 5
    return 10*peso + 6.25*altura - 5*idade - 161

def tmb_harris(sexo, peso, altura, idade):
    if sexo == "Masculino":
        return 66.5 + 13.75*peso + 5.003*altura - 6.755*idade
    return 655 + 9.563*peso + 1.850*altura - 4.676*idade

def tmb_katch(peso, bf):
    massa_magra = peso * (1 - bf/100)
    return 370 + (21.6 * massa_magra)

# ===== RECOMENDAÇÃO AUTOMÁTICA =====

def sugerir_refeicoes(taco_df, kcal_alvo):
    refeicoes = taco_df.sample(4)  # simples para v1
    return refeicoes[["alimento", "kcal", "proteina", "carbo", "gordura"]]
