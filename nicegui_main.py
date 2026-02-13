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
import V2_Bloc1_FVA
import tempfile

store = {'model': None}

async def uploads(e):
    print("EVENT ATTRS:", dir(e))  # vérification

    file = e.file        # premier fichier
    data = await e.file.read()        # bytes du fichier
    name = file.name

    # Sauvegarde temporaire
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.sbml')
    temp.write(data)
    temp.close()

    # Lecture du modèle
    model = cobra.io.read_sbml_model(temp.name)
    store['model'] = model

    ui.notify(f"Modèle chargé : {model.name}")

    display_container.clear()
    V1_Bloc1_ui.display(model)

with ui.tabs().classes('w-full') as tabs:
    tab_volet0 = ui.tab("Reconstruction ID card")
    tab_volet1 = ui.tab("Navigation")
    tab_volet2 = ui.tab("Model")
    tab_volet3=ui.tab("Analyses")

with ui.tab_panels(tabs, value=tab_volet0).classes('w-full'):

    # --- Onglet Home ---
    with ui.tab_panel(tab_volet0):
        ui.label("Upload the model (sbml file) you would like to work on")
        (
            ui.upload(multiple=True, max_files=1)   # ← ACTIVE LE NOUVEAU COMPOSANT
                .on_upload(uploads)
                .props("accept=.sbml,.xml")
        )
        display_container = ui.column()
        def go_to_model_info():
            model=store.get('model')
            if model is None:
                ui.notify('No model loaded yet')
            else : 
                V1_Bloc1_ui.display(model)

        ui.button(
                'Show information regarding the model',
                on_click=go_to_model_info
        )
    
    with ui.tab_panel(tab_volet1):
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_metabolites = ui.tab('Metabolites')
              tab_reactions = ui.tab('Reactions')
              tab_genes = ui.tab('Genes')
              tab_exch_reaction = ui.tab('Exchange Reactions')

        with ui.tab_panels(internal_tabs, value=tab_metabolites).classes('w-full'):
            with ui.tab_panel(tab_metabolites):
                def information_model_metabolite():
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                    else : 
                        V1_Bloc2_ui_Metabolites.display(model)
                ui.button('Show information regarding metabolites', on_click=information_model_metabolite)

            with ui.tab_panel(tab_reactions):
                def information_model_reaction():
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                    else : 
                        V1_Bloc2_ui_Reactions.display(model)
                ui.button('Show information regarding reactions', on_click=information_model_reaction)

            with ui.tab_panel(tab_genes):
                def information_model_gene():
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                    else : 
                        V1_Bloc2_ui_Genes.display(model)
                ui.button('Show information regarding genes', on_click=information_model_gene)

            with ui.tab_panel(tab_exch_reaction):
                def information_model_exchreaction():
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                    else : 
                        V1_Bloc4_ui.display(model)
                ui.button('Show information regarding exchange reactions', on_click=information_model_exchreaction)
  
    # Volet 2  : Model
    with ui.tab_panel(tab_volet2):
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_constraints = ui.tab('Original constraints')
              tab_fba = ui.tab('FBA')
              tab_fva = ui.tab('FVA')

        with ui.tab_panels(internal_tabs, value=tab_constraints).classes('w-full'):
            with ui.tab_panel(tab_constraints):
                def information_model_constraints():
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                    else : 
                        V2_Bloc1_ui.display(model)
                ui.button('Show information regarding constraints', on_click=information_model_constraints)

            with ui.tab_panel(tab_fba):
                def information_model_fba():
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                    else : 
                        V2_Bloc2_ui.display(model)
                ui.button('Show information regarding FBA', on_click=information_model_fba)
                
            with ui.tab_panel(tab_fva):
                def information_model_fva():
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                    else : 
                        V2_Bloc1_FVA.display(model)
                ui.button('Show information regarding FVA', on_click=information_model_fva)

    
<<<<<<< HEAD
    #Volet 3
    with ui.tab_panel(tab_volet3):
===):
>>>>>>> origin/main
        ui.label("TO DO")



# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

ui.run(port=8081)
