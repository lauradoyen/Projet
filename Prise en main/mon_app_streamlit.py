import streamlit as st
import pandas as pd
import numpy as np
import cobra
#python -m venv ~/venv_streamlit (créer un nouvel environnement)
#venv_streamlit\Scripts\activate.bat (active l'environnement)
#pip install cobra streamlit pandas numpy
#streamlit run "C:\Users\lauri\OneDrive\Documents\EI2\Projet\mon_app_streamlit.py"

#controle C pour sortir de Streamlit une fois que c'est lancé

# Charger le modèle à partir d'un fichier SBML
model = cobra.io.read_sbml_model("/Users/lauri/OneDrive/Documents/EI2/Projet/iPrub22.sbml")

st.title("Mon interface Streamlit")
st.write("Bienvenue dans votre première application Streamlit !")
#Modele
st.subheader("Nom du modèle")
st.write(model.name)

#Faire des onglets
onglets = st.tabs(["Accueil", "Liste des réactions", "Liste des métabolites","Simulation FBA simple"])
with onglets[0]:
    st.header("Bloc 1")
    st.write("Contenu du premier bloc")
    st.title("Mon interface Streamlit")
    st.write("Bienvenue dans votre première application Streamlit !")
    st.write(f"Nom du modèle : {model.name}")
    st.write(f"Nombre de métabolites : {len(model.metabolites)}")
    st.write(f"Nombre de réactions : {len(model.reactions)}")
    st.write(f"Nombre de gènes : {len(model.genes)}")


with onglets[1]:
    st.title("Liste des réactions")
    reactions = pd.DataFrame({
    "ID": [r.id for r in model.reactions],
    "Nom": [r.name for r in model.reactions],
    "Formule": [r.reaction for r in model.reactions],
    "Flux min": [r.lower_bound for r in model.reactions],
    "Flux max": [r.upper_bound for r in model.reactions]
})
    st.dataframe(reactions)

with onglets[2]:
    st.subheader("Liste des métabolites")
    metabolites = pd.DataFrame({
    "ID": [m.id for m in model.metabolites],
    "Nom": [m.name for m in model.metabolites],
    "Formule": [m.formula for m in model.metabolites]
})
    st.dataframe(metabolites)

with onglets[3]:
    st.title("Simulation FBA")
    solution = model.optimize()
    st.write(f"Objectif : {solution.objective_value}")
    fluxes = pd.DataFrame({
    "Réaction": [r.id for r in model.reactions],
    "Flux": [solution.fluxes[r.id] for r in model.reactions]
})
    st.dataframe(fluxes)

#Entrée utilisateur
#nom = st.text_input("Ton nom :")
#if st.button("Saluer"):
    #st.write(f"Bonjour {nom} ! 👋")

#Curseur et calcul simple
    #age = st.slider("Ton âge :", 0, 100, 25)
    #st.write(f"En 10 ans, tu auras {age + 10} ans.")

# Affichage d'un tableau
    #st.subheader("Exemple de tableau")
    #data = pd.DataFrame(
    #np.random.randn(5, 3),
    #columns=["A", "B", "C"])
    #st.dataframe(data)

# Graphique simple
    #st.subheader("Graphique interactif")
    #st.line_chart(data)

#

import Flux_Analysis
