"""
#pip install cobra optlang lxml

#import cobra

# Charger le modèle à partir d'un fichier SBML
model = cobra.io.read_sbml_model("C:/Users/lauri/OneDrive/Documents/EI2/Projet/iPrub22.sbml")

# Afficher des infos de base
print(f"Nom du modèle : {model.name}")
print(f"Nombre de métabolites : {len(model.metabolites)}")
print(f"Nombre de réactions : {len(model.reactions)}")
print(f"Nombre de gènes : {len(model.genes)}")

#Afficher des réactions
for rxn in model.reactions[:5]:
    print(rxn.id, ":", rxn.reaction)

#Calcul de flux
solution = model.optimize()
print(solution.objective_value)   # Taux de croissance ou flux cible
print(solution.fluxes.head())     # Flux de chaque réaction

#Simuler des mutations ou KO
with model:
    model.reactions.get_by_id("PFK").knock_out()
    sol = model.optimize()
    print("Croissance après knockout :", sol.objective_value)

#Tester des conditions
glucose = model.reactions.get_by_id("EX_glc__D_e")
glucose.lower_bound = -10  # Disponibilité du glucose
oxygen = model.reactions.get_by_id("EX_o2_e")
oxygen.lower_bound = -20   # Disponibilité de l’oxygène

#Analyser la variabilité des flux
from cobra.flux_analysis import flux_variability_analysis
fva_result = flux_variability_analysis(model, fraction_of_optimum=0.9)
print(fva_result.head())

#Etude des gènes
reaction = model.reactions.get_by_id("GAPD")
print(reaction.gene_reaction_rule)

#Maxminiser un métabolite
model.objective = "EX_succ_e"  # Maximiser la production de succinate
solution = model.optimize()
print("Production de succinate :", solution.objective_value)

#Visualisation
cobra.io.write_sbml_model(model, "modele_modifie.xml")




#Visualisation 2
#pip install escher
from escher import Builder
from escher_map_maker import auto_layout

import networkx as nx
from escher import Builder
import json

# Créer un graphe à partir du modèle
G = nx.DiGraph()
for r in model.reactions:
    for met in r.metabolites:
        G.add_edge(met.id, r.id)

# Calculer un layout automatique
pos = nx.spring_layout(G)  # layout de type force-directed

# Créer une structure compatible Escher
map_json = {
    "nodes": [],
    "reactions": []
}

# Ajouter les métabolites
for met_id in [n for n in G.nodes if n in model.metabolites]:
    map_json["nodes"].append({
        "id": met_id,
        "x": float(pos[met_id][0]),
        "y": float(pos[met_id][1]),
        "name": model.metabolites.get_by_id(met_id).name
    })

# Ajouter les réactions
for r in model.reactions:
    map_json["reactions"].append({
        "id": r.id,
        "metabolites": {met.id: coeff for met, coeff in r.metabolites.items()},
        "name": r.name,
        "x": float(pos[r.id][0]),
        "y": float(pos[r.id][1])
    })

# Sauvegarder le layout
with open("auto_layout.json", "w") as f:
    json.dump(map_json, f)

"""


import SBMLDiagrams, tellurium as te

r = te.loada ("C:/Users/lauri/OneDrive/Documents/EI2/Projet/iPrub22.sbml")

df = SBMLDiagrams.load(r.getSBML())

df.autolayout()

df.draw()






























