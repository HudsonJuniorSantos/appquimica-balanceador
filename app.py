import streamlit as st
import re
import pandas as pd
import sympy as sp
import plotly.express as px
from collections import defaultdict

st.set_page_config(page_title="Balanceador Químico", layout="centered")

st.title("⚗️ Balanceador de Equações Químicas Inorgânicas")
st.write("Digite uma equação ou envie um arquivo `.txt` com várias.")

def extrair_elementos(composto):
    elementos = re.findall(r'([A-Z][a-z]?)(\d*)', composto)
    return {el: int(qtd) if qtd else 1 for el, qtd in elementos}

def contar_elementos(expressao):
    partes = re.findall(r'(\d*)([A-Za-z0-9()]+)', expressao)
    contagem = defaultdict(int)
    for multiplicador, composto in partes:
        fator = int(multiplicador) if multiplicador else 1
        elementos = extrair_elementos(composto)
        for el, qtd in elementos.items():
            contagem[el] += qtd * fator
    return dict(contagem)

def balancear_equacao(equacao):
    try:
        lados = re.split(r"->|→|=", equacao)
        reagentes = [r.strip() for r in lados[0].split("+")]
        produtos = [p.strip() for p in lados[1].split("+")]

        todos = reagentes + produtos
        elementos = sorted(set(el for composto in todos for el in extrair_elementos(composto)))
        matriz = []

        for el in elementos:
            linha = []
            for comp in reagentes:
                linha.append(extrair_elementos(comp).get(el, 0))
            for comp in produtos:
                linha.append(-extrair_elementos(comp).get(el, 0))
            matriz.append(linha)

        A = sp.Matrix(matriz)
        sol = A.nullspace()[0]
        coeficientes = sp.lcm([term.q for term in sol]) * sol
        coeficientes = [abs(int(c)) for c in coeficientes]

        reagente_fmt = " + ".join(f"{coef} {comp}" for coef, comp in zip(coeficientes[:len(reagentes)], reagentes))
        produto_fmt = " + ".join(f"{coef} {comp}" for coef, comp in zip(coeficientes[len(reagentes):], produtos))

        return f"{reagente_fmt} → {produto_fmt}"
    except:
        return "❌ Erro ao balancear. Verifique a equação."

def verificar_balanceamento(eq_bal):
    if "→" not in eq_bal:
        return False
    reagentes, produtos = eq_bal.split("→")
    lado1 = contar_elementos(reagentes)
    lado2 = contar_elementos(produtos)
    return lado1 == lado2, lado1, lado2

def plotar_elementos(dic, titulo):
    df = pd.DataFrame(dic.items(), columns=["Elemento", "Quantidade"])
    fig = px.bar(df, x="Elemento", y="Quantidade", text="Quantidade", title=titulo)
    st.plotly_chart(fig, use_container_width=True)

# Entrada manual
eq_input = st.text_input("📥 Digite a equação (ex: Al + Ag2SO4 -> Al2(SO4)3 + Ag):")

# Upload .txt
uploaded = st.file_uploader("Ou envie um arquivo .txt com equações", type="txt")
equacoes = []

if eq_input:
    equacoes.append(eq_input)

if uploaded:
    texto = uploaded.read().decode("utf-8")
    linhas = texto.strip().splitlines()
    equacoes += [l.strip() for l in linhas if l.strip()]

# Processar
resultados = []
for eq in equacoes:
    eq_bal = balancear_equacao(eq)
    status, lado1, lado2 = verificar_balanceamento(eq_bal)
    resultados.append({
        "Original": eq,
        "Balanceada": eq_bal,
        "Status": "✅ Balanceada" if status else "❌ Incorreta"
    })

    if eq == eq_input and status:
        col1, col2 = st.columns(2)
        with col1: plotar_elementos(lado1, "Reagentes")
        with col2: plotar_elementos(lado2, "Produtos")

# Mostrar
if resultados:
    df = pd.DataFrame(resultados)
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📤 Baixar como CSV", csv, "equacoes_balanceadas.csv", "text/csv")
