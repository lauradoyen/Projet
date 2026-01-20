from nicegui import ui, event
import cobra
import V1_Bloc1_ui
import V1_Bloc2_volet1_ui
import V1_Bloc2_volet2_ui
import V1_Bloc4_ui 
import V1_Bloc5_ui 

# Charger le modèle SBML
model = cobra.io.read_sbml_model("iPrub22.sbml")

# Interface NiceGUI : En-tête
with ui.column().classes("m-4"):
    ui.label("Penicilium Rubens Project").classes("text-3xl font-bold")

# Onglets principaux
with ui.tabs().classes('w-full') as tabs: 
    tab_accueil = ui.tab("Accueil")
    tab_identification = ui.tab("Identification des métabolites")
    tab_representation = ui.tab("Représentation chimique")
    tab_fba = ui.tab("Simulation FBA")
    tab_fva = ui.tab("FVA")

with ui.tab_panels(tabs, value=tab_accueil).classes('w-full'):
    with ui.tab_panel(tab_accueil):
        V1_Bloc1_ui.display(model)

    with ui.tab_panel(tab_identification):
        V1_Bloc2_volet1_ui.display(model) 

    with ui.tab_panel(tab_representation):
        V1_Bloc2_volet2_ui.display(model)

    with ui.tab_panel(tab_fba):
        V1_Bloc4_ui.display(model) 

    with ui.tab_panel(tab_fva):
        V1_Bloc5_ui.display(model) 

# Lancer l'application
ui.run(port=8080, reload=False)
