import sys 
import os 
print("PYTHON UTILISÉ :", sys.executable)
print("SCRIPT LANCÉ DEPUIS :", os.getcwd())
print(0)


from nicegui import ui, app
import cobra
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time
from cobra.flux_analysis import flux_variability_analysis

# ---------------------------------------------------------
# Charger modèle
# ---------------------------------------------------------
model = cobra.io.read_sbml_model("iPrub22.sbml")
print("Modèle :", model.name)
print("Nombre de réactions :", len(model.reactions))
print("Nombre de métabolites :", len(model.metabolites))

#Table des matières
with ui.tabs().classes('w-full') as tabs:
    tab_home=ui.tab("Home page")
    tab_reconstruction = ui.tab("Reconstruction")
    tab_model = ui.tab("Model")
    tab_analyses = ui.tab("Analyses")

with ui.tab_panels(tabs, value=tab_home).classes('w-full'):

    # -----------------------------------------------------
    # Accueil
    # -----------------------------------------------------
    with ui.tab_panel(tab_home):
        with ui.row().style("justify-content: center; align-items: center; height: 400px;"):
            ui.input("Tapez quelque chose ici").style("width: 200px; margin-left: 190px")
    with ui.tab_panel(tab_reconstruction):
        ui.label("Informations générales").classes("text-xl")
        ui.label(f"Métabolites : {len(model.metabolites)}")
        ui.label(f"Réactions : {len(model.reactions)}")
        ui.label(f"Gènes : {len(model.genes)}")
# ---------------------------------------------------------
# Lancer appli
# ---------------------------------------------------------
print(">>> Lancement de NiceGUI…") 
ui.run(port=8080, reload=False, show=True)
print(1) 
