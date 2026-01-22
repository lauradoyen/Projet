from nicegui import ui
import cobra
from model_utils import load_model

import V1_Bloc1_ui
import V1_Bloc2_ui_Genes
import V1_Bloc2_ui_Metabolites
import V1_Bloc2_volet2_ui
import V1_Bloc4_ui 
import V1_Bloc5_ui

# Read SBML model
model= load_model()

# -----------------------------------------------------
# Interface NiceGUI
# -----------------------------------------------------

with ui.column().classes("m-4"):
    ui.label("Mon interface NiceGUI").classes("text-3xl font-bold")
    ui.label("Bienvenue dans votre première application NiceGUI !").classes("text-lg mt-2")

    ui.label("Nom du modèle").classes("text-xl mt-4")
    ui.label(model.name).classes("text-lg")

# -----------------------------------------------------
# Onglets
# -----------------------------------------------------

with ui.tabs().classes('w-full') as tabs:
    tab_accueil = ui.tab("Accueil")
    tab_identification = ui.tab("Identification des métabolites")
    tab_representation = ui.tab("Représentation chimique des métabolites")
    tab_fba = ui.tab("Simulation FBA simple")
    tab_fva = ui.tab("FVA")

with ui.tab_panels(tabs, value=tab_accueil).classes('w-full'):

    # Onglet 1 : Accueil
    with ui.tab_panel(tab_accueil):
        V1_Bloc1_ui.display(model)

    # Onglet 2 : Identification des métabolites/gènes
    with ui.tab_panel(tab_identification):
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_metabolites = ui.tab('Métabolites')
              tab_genes = ui.tab('Gènes')

        with ui.tab_panels(internal_tabs, value=tab_metabolites).classes('w-full'):
            with ui.tab_panel(tab_metabolites):
                V1_Bloc2_ui_Metabolites.display(model)

            with ui.tab_panel(tab_genes):
                V1_Bloc2_ui_Genes.display(model)
        
    # Onglet 3 : Représentation chimique
    with ui.tab_panel(tab_representation):
        ui.label("Informations générales").classes("text-xl")
       

    # Onglet 4 : FBA simple
    with ui.tab_panel(tab_fba):
        ui.label("Informations générales").classes("text-xl")
        V1_Bloc4_ui.display(model) 

    # Onglet 5 : FVA
    with ui.tab_panel(tab_fva):
        ui.label("Informations générales").classes("text-xl")
        V1_Bloc5_ui.display(model) 
        
# ---------------------------------------------------------
# Lancer appli
# ---------------------------------------------------------
ui.run(port=8081)