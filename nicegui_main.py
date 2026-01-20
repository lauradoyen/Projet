from nicegui import ui, event
import cobra

import V1_Bloc1_ui

# Path to the SBML file
iPrub22_path = "C:/Users/laura/Desktop/EI2/PROENC/Projet_BIOSTIC_2025_2026/Model/iPrub22.sbml"

# Read SBML model
model= cobra.io.read_sbml_model(iPrub22_path)

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

    # Onglet 2 : Identification des métabolites
    with ui.tab_panel(tab_identification):
        ui.label("Identification des métabolites").classes("text-xl")
        
    # Onglet 3 : Représentation chimique
    with ui.tab_panel(tab_representation):
        ui.label("Informations générales").classes("text-xl")
       

    # Onglet 4 : FBA simple
    with ui.tab_panel(tab_fba):
        ui.label("Informations générales").classes("text-xl")

    # Onglet 5 : FVA
    with ui.tab_panel(tab_fva):
        ui.label("Informations générales").classes("text-xl")
        
# ---------------------------------------------------------
# Lancer appli
# ---------------------------------------------------------
ui.run(port=8080, reload=False)

