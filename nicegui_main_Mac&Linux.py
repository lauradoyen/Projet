#import libraries 

from nicegui import ui
import cobra
from model_utils import load_model
import os

#import functions from other python files

import V1_Bloc1_ui
import V1_Bloc2_ui_Genes
import V1_Bloc2_ui_Metabolites
import V1_Bloc2_ui_Reactions
import V1_Bloc4_ui
import V2_Bloc1_ui
import V2_Bloc2_FBA
import V2_Bloc3_FVA
import V3_Bloc1_ui
import V3_Bloc2_ui
import tempfile

################################IMPORT THE MODEL YOU WANT TO WORK ON 

store = {'model': None} # 

async def uploads(e):
    file = e.file        # premier fichier
    data = await e.file.read()        # bytes du fichier
    name = file.name
    file_extension = os.path.splitext(name)[1]
    # Sauvegarde temporaire
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
    temp.write(data)
    temp.close()

    # Lecture du modèle
    model = cobra.io.read_sbml_model(temp.name)
    store['model'] = model

    ui.notify(f"Modèle chargé : {model.name}")

    display_container.clear()
    V1_Bloc1_ui.display(model)

###################################

#definitions of the 4 different tabs 

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
            ui.upload(multiple=True, max_files=1)   # upload the model 
                .on_upload(uploads)
                .props("accept=.sbml,.xml") #accepted files : sbml and xml
        )
        display_container = ui.column()
        def go_to_model_info():
            button1.disable() #hide the button so that if you impatiently click on it twice, the information is still shown only once
            model=store.get('model')
            if model is None:
                ui.notify('No model loaded yet')
                button1.enable() #the button is clickable again if the model couldn't be uploaded 
            else : 
                button1.disable()
                

        button1=ui.button(
                'Show information regarding the model',
                on_click=go_to_model_info
        )
    
    with ui.tab_panel(tab_volet1): # Tab to explore the metabolites, reactions, genes, exchange reactions of the model
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_metabolites = ui.tab('Metabolites')
              tab_reactions = ui.tab('Reactions')
              tab_genes = ui.tab('Genes')
              tab_exch_reaction = ui.tab('Exchange Reactions')

        with ui.tab_panels(internal_tabs, value=tab_metabolites).classes('w-full'):
            with ui.tab_panel(tab_metabolites):
                def information_model_metabolite():
                    button2.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button2.enable()
                    else : 
                        V1_Bloc2_ui_Metabolites.display(model)
                button2=ui.button('Show information regarding metabolites', on_click=information_model_metabolite)

            with ui.tab_panel(tab_reactions):
                def information_model_reaction():
                    button3.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button3.enable()
                    else : 
                        V1_Bloc2_ui_Reactions.display(model)
                button3=ui.button('Show information regarding reactions', on_click=information_model_reaction)

            with ui.tab_panel(tab_genes):
                def information_model_gene():
                    model=store.get('model')
                    button4.disable()
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button4.enable()
                    else : 
                        V1_Bloc2_ui_Genes.display(model)
                button4=ui.button('Show information regarding genes', on_click=information_model_gene)

            with ui.tab_panel(tab_exch_reaction):
                def information_model_exchreaction():
                    button5.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button5.enable()
                    else : 
                        V1_Bloc4_ui.display(model)
                button5=ui.button('Show information regarding exchange reactions', on_click=information_model_exchreaction)
  
    # Volet 2  : Model
    with ui.tab_panel(tab_volet2):
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_constraints = ui.tab('Original constraints')
              tab_fba = ui.tab('FBA')
              tab_fva = ui.tab('FVA')

        with ui.tab_panels(internal_tabs, value=tab_constraints).classes('w-full'):
            with ui.tab_panel(tab_constraints):
                def information_model_constraints():
                    button6.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button6.enable()
                    else : 
                        V2_Bloc1_ui.display(model)
                button6=ui.button('Show information regarding constraints', on_click=information_model_constraints)

            with ui.tab_panel(tab_fba):
                def information_model_fba():
                    button7.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button7.enable()
                    else : 
                        V2_Bloc2_FBA.display(model)
                button7=ui.button('Show information regarding FBA', on_click=information_model_fba)
                
            with ui.tab_panel(tab_fva):
                def information_model_fva():
                    button8.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button8.enable()
                    else : 
                        V2_Bloc3_FVA.display(model)
                button8=ui.button('Show information regarding FVA', on_click=information_model_fva)
            

    #Volet 3
              
    with ui.tab_panel(tab_volet3):
        with ui.tabs().classes('w-full') as internal_tabs:
              tab_sensitivity_analysis_nutritional = ui.tab('Sensitivity to nutritional environment analysis')
              tab_sensitivity_analysis_nutritional_p = ui.tab('Sensitivity to nutritional environment analysis for the production of Penicillin')
        
        with ui.tab_panels(internal_tabs, value=tab_sensitivity_analysis_nutritional).classes('w-full'):
            with ui.tab_panel(tab_sensitivity_analysis_nutritional):
                def information_sensitivity():
                    button9.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button9.enable()
                    else : 
                        V3_Bloc1_ui.display(model)
                button9=ui.button('Show information regarding spaghetti plots',on_click=information_sensitivity)
            with ui.tab_panel(tab_sensitivity_analysis_nutritional_p):
                def information_sensitivity_p():
                    button10.disable()
                    model=store.get('model')
                    if model is None : 
                        ui.notify('No model loaded yet')
                        button10.enable()
                    else : 
                        V3_Bloc2_ui.display(model)
                button10=ui.button('Show information regarding spaghetti plots',on_click=information_sensitivity_p)


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

ui.run(port=8081, reload=False) #the port used to run the program is the 8081