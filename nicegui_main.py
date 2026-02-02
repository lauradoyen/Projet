from nicegui import ui
import cobra
from model_utils import load_model
#print("VERSION NICEGUI =", nicegui._version_) 

import V1_Bloc1_ui
import V1_Bloc2_ui_Genes
import V1_Bloc2_ui_Metabolites
import V1_Bloc2_ui_Reactions
import V1_Bloc4_ui
import V2_Bloc1_ui
import V2_Bloc2_ui



# Read SBML model
model= load_model()

# Interface NiceGUI
with ui.column().classes("m-4"):
    ui.label("Projet BIOSTIC").classes("text-3xl font-bold")
    ui.label(f"Modele {model.name}").classes("text-xl mt-4")

with ui.tabs().classes('w-full') as tabs:
    tab_voletO = ui.tab("Reconstruction ID card")
    tab_volet1 = ui.tab("Navigation")
    tab_volet2 = ui.tab("Model")
    Tab_volet3=ui.tab("Analyses")

with ui.tab_panels(tabs, value=tab_voletO).classes('w-full'):

    # Volet 1 Bloc1
    with ui.tab_panel(tab_voletO):
        V1_Bloc1_ui.display(model)

    # Volet 1  Bloc 2, 3, 4: Identification des métabolites/réactions/gènes
    with ui.tab_panel(tab_volet1):
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_metabolites = ui.tab('Metabolites')
              tab_reactions = ui.tab('Reactions')
              tab_genes = ui.tab('Genes')
              tab_exch_reaction = ui.tab('Exchange Reactions')

        with ui.tab_panels(internal_tabs, value=tab_metabolites).classes('w-full'):
            with ui.tab_panel(tab_metabolites):
                V1_Bloc2_ui_Metabolites.display(model)

            with ui.tab_panel(tab_reactions):
                V1_Bloc2_ui_Reactions.display(model)

            with ui.tab_panel(tab_genes):
                V1_Bloc2_ui_Genes.display(model)

            with ui.tab_panel(tab_exch_reaction):
                V1_Bloc4_ui.display(model)
  
    # Volet 2  : Model
    with ui.tab_panel(tab_volet2):
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_constraints = ui.tab('Constraints')
              tab_fba = ui.tab('FBA')

        with ui.tab_panels(internal_tabs, value=tab_constraints).classes('w-full'):
            with ui.tab_panel(tab_constraints):
                V2_Bloc1_ui.display(model)

            with ui.tab_panel(tab_fba):
                V2_Bloc2_ui.display(model)
    
    #Volet 3
    with ui.tab_panel(Tab_volet3):
        ui.label("TO DO")

                

        
# Lancer appli
ui.run(port=8081)