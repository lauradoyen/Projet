#import the libraries 

from nicegui import ui
import pandas as pd
import csv
from cobra.flux_analysis import flux_variability_analysis
import asyncio

def display(model):

    """Extraction des contraintes"""
    original_model=model.copy() #save informations to restore contraints and keep in mind the objective function of the original model 
    model_copy=model.copy()
    def get_constraints(model):
        return [{"Reaction": r.id, "Lower bound": r.lower_bound, "Upper bound": r.upper_bound} for r in model.reactions]

    """Fonction d’export CSV"""
    def export_constraints():
        filename = "constraints.csv"
        fieldnames = ["Reaction", "Lower bound", "Upper bound"]
        rows = get_constraints(model)

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        ui.download(filename)


    # Interface 
    with ui.row().classes("gap-6"): #the 2nd block is right next to the 1rst one and not below it  
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"): #create boxes where you can write text 
            ui.label("Modify the different constraints of the model").classes("text-xl font-semibold mb-2")
            def extract_all_constraints(model): # extract the constraints of the model and changes the values to display 
                rows = []
                for r in model.reactions:
                    lb = None if r.lower_bound in (-1000, 0) else r.lower_bound #we treat +/- 1000 as an infinity bound
                    ub = None if r.upper_bound in (1000, 0) else r.upper_bound
                    rows.append({
                "Reaction": r.id,
                "Lower bound": lb if lb is not None else "",
                "Upper bound": ub if ub is not None else "",
            })
                return pd.DataFrame(rows)
            
            df = extract_all_constraints(model) #constraints that will be shown in the constraint_grid

            def on_grid_edit(e): #allows you to modify in the table the constraints of the model 
                row = e.args["data"]
                rxn_id = row["Reaction"]
                r = model.reactions.get_by_id(rxn_id)

                # LB
                lb = row["Lower bound"]
                try:
                    r.lower_bound = float(lb)
                except:
                    r.lower_bound = -1000

                # UB
                ub = row["Upper bound"]
                try:
                    r.upper_bound = float(ub)
                except:
                    r.upper_bound = 1000
            
            constraint_grid = ui.aggrid( #define the grid where the constraints will be shown 
        {
            "columnDefs": [
                {"field": "Reaction", "editable": False}, # cannot change the name of the reaction 
                {"field": "Lower bound", "editable": True}, #possibility to change the lower bound 
                {"field": "Upper bound", "editable": True}, #possibility to change the upper bound 
            ],
            "rowData": df.to_dict("records"), 
            "defaultColDef": {"sortable": True, "filter": True, "resizable": True},
            "pagination": True,
            "paginationPageSize": 20,
            "stopEditingWhenCellsLoseFocus": True,
        },
        theme="balham",
    ).classes("w-full h-96")

            constraint_grid.on("cellValueChanged", on_grid_edit) #call to on_grid_edit to be able to modify the constraints directly in the table 
            
            def reset_constraints(): 
                nonlocal df #allows you to modify variables defined outside of the function 
                nonlocal model
                df = extract_all_constraints(original_model) #reset the constraints with original_model
                constraint_grid.options["rowData"] = df.to_dict("records") 
                constraint_grid.update() # udates the constraints that the user sees on the interface
                model=original_model.copy()
                ui.notify("Constraints restored from original model", color="green")

            ui.button("Reset original constraints of the model", on_click=reset_constraints).classes(
                "mt-2 bg-gray-500 text-white")
            ui.button("Download constraints CSV", on_click=export_constraints).classes("mt-6 bg-green-600 text-white")

        # Sélection de l’objectif
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):

            #default_objective=model.objective.expression.args[0].id #store the default objective function of the model 

            ui.label("Select the different parameters of the FVA ").classes("text-xl font-semibold mb-2")

            reactions = [r.id for r in model.reactions]
            
            select_objective = ui.select(options=reactions,with_input=True,label='Select the objective reaction').classes('w-64').props('use-chips') #select the objective function of the model. 

            metabolite_select = ui.select(options=reactions, #reactions whose FVA fluxes you want 
                multiple = True, 
                with_input=True,
                label ="Select several reactions of the model that you want to analyse with FVA").classes('w-64').props('use-chips')
            
            ui.label('Please input the fraction of optimum desired for the FVA')
            fraction_optimum = ui.slider(min=0,max=1,step=0.01, value=1) #slider to choose the fraction of optimum desired, by default, it's 1
            ui.label().bind_text_from(fraction_optimum, 'value') #shows the fraction of optimum as you move the cursor

        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):
            fva_grid = ui.aggrid( #grid where fva results are shown 
        {
            "columnDefs": [],
            "rowData": [] ,
            "defaultColDef": {"sortable": True, "filter": True, "resizable": True},
            "pagination": True,
            "paginationPageSize": 20,
            "stopEditingWhenCellsLoseFocus": True,
        },
        theme="balham",
    ).classes("w-full h-96")
            
            def clear_grid(): #resets a grid 
                fva_grid.options['rowData'] = []
                fva_grid.options['columnDefs'] = []
                fva_grid.update()

            objective_reaction = None
            df_fva = None 

            # Function FVA 

            async def run_fva(): #use of asyncio so that the FVA runs asynchrononously since it can take a lot of time 
                nonlocal objective_reaction #modify objective_reaction, function defined outside of run_fva
                nonlocal df_fva
                nonlocal model_copy
                ui.notify('Please wait for the calculations to be finished')
                try:
                    clear_grid()
                    model_copy=model.copy()
                    objective_reaction=model_copy.reactions.get_by_id(select_objective.value)
                    model_copy.objective =objective_reaction.flux_expression
                    if len(metabolite_select.value)==0: #if no reactions have been selected, we show the results of the FVA for all the reactions of the model, else only those selected 
                        solution = await asyncio.to_thread(flux_variability_analysis,model_copy,fraction_of_optimum=fraction_optimum.value,)
                    else : 
                        solution = await asyncio.to_thread(flux_variability_analysis,model_copy,reaction_list=metabolite_select.value,fraction_of_optimum=fraction_optimum.value,)
                    df_fva = solution.reset_index()
                    fva_grid.options['columnDefs'] = [{'headerName': col, 'field': col} for col in df_fva.columns]
                    fva_grid.options['rowData'] = df_fva.to_dict(orient='records')
                    fva_grid.update()
                    ui.notify("The results are available ")
                except Exception as err:
                    ui.notify(f"Error: {err}", color='red')
            def result_fva(): #export results from the fva 
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run before exporting", color="red")
                    return
                rows = get_constraints(model_copy) #show constraints of the model 
                table_constraints = pd.DataFrame(rows)
                meta_df = pd.DataFrame({
        "Objective reaction": [objective_reaction.id], #shown objective reaction and fraction of optimum for the FVA that was run
        "Fraction of optimum": [fraction_optimum.value]
    })
                with open("fva_results.csv", "w", newline="", encoding="utf-8") as f:
                    f.write("Summary\n")
                    meta_df.to_csv(f, index=False)
                    f.write("\nFVA Results\n")
                    df_fva.to_csv(f, index=False)
                    f.write("\nConstraints\n")
                    table_constraints.to_csv(f, index=False)
                ui.download("fva_results.csv")
            ui.button("Run FVA", on_click=run_fva).classes("mt-4 bg-blue-600 text-white")
            ui.button("export FVA results", on_click=result_fva).classes("mt-4 bg-blue-600 text-white")
        

        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):
            ui.label("Find the blocked/active/fixed flux/reversible reactions").classes("text-xl font-semibold mb-2")
            ui.label('They will be calculated using the current results shown for the FVA')
            with ui.card():
                number_reaction=ui.label("") # zone to show the number of blocked/active/fixed flux/reversible reactions depending on the button that the user clicks on 
            zone = ui.aggrid( #grid to show the blocked/active/fixed flux/reversible reactions depending on the button that the user clicks on
    {
        "columnDefs": [
            {"field": "Reaction"},
        ],
        "rowData": [],
        "defaultColDef": {"sortable": True, "filter": True, "resizable": True},
    },
    theme="balham"
).classes("w-full h-96")    
            async def find_fixed_reactions(): #find fixed flux reactions
                if fva_grid.options['rowData'] == []: #ensure one FVA has been run 
                    ui.notify("Run FVA before showing these caracteristics ", color="red")
                    return 
                zone.clear()
                flux_reaction=[{
                "Reaction": r} for r in df_fva.loc[(df_fva["minimum"] == df_fva["maximum"]) & (df_fva["minimum"] != 0), "index"]]
                zone.options['rowData'] =flux_reaction
                zone.update()
                ui.notify("the results of the fixed flux reactions are available ")
                number_reaction.set_text(f"There are {len(flux_reaction)} fixed flux reactions") #show the number of fixed flux reactions 
            ui.button('Show fixed flux reactions',on_click=find_fixed_reactions)
            async def find_reversible_reactions(): #show all reversible reactions 
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run FVA before showing these caracteristics ", color="red")
                    return
                zone.clear()
                reversible_reaction = [
    {"Reaction": r}
    for r in df_fva.loc[df_fva["minimum"] * df_fva["maximum"] < 0, "index"]
]
                zone.options['rowData'] =reversible_reaction
                zone.update()
                ui.notify("The reversible reactions are available")
                number_reaction.set_text(f"There are {len(reversible_reaction)} reversible reactions")
            ui.button('Show reversible reactions', on_click=find_reversible_reactions)
            async def show_blocked_status(): #show all blocked reactions 
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run FVA before showing these caracteristics ", color="red")
                    return
                zone.clear()
                blocked_reaction=[{
                "Reaction": r} for r in df_fva.loc[(df_fva["minimum"] == df_fva["maximum"]) & (df_fva["minimum"] == 0), "index"]]
                zone.options['rowData'] =blocked_reaction
                zone.update()
                ui.notify("The blocked reactions are available")
                number_reaction.set_text(f"There are {len(blocked_reaction)} blocked reactions")
            ui.button("show blocked reactions", on_click=show_blocked_status).classes("mt-4 bg-blue-600 text-white")
            async def show_active_status(): #show all the active reactions 
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run FVA before showing these caracteristics ", color="red")
                    return
                zone.clear()
                active_reaction = [{
                "Reaction": r} for r in df_fva.loc[(df_fva["minimum"] != df_fva["maximum"]) | ((df_fva["minimum"] !=0) & (df_fva["minimum"]==df_fva["maximum"])  ), "index"]]
                zone.options['rowData'] =active_reaction
                zone.update()
                ui.notify("The active reactions are available")
                number_reaction.set_text(f"There are {len(active_reaction)} active reactions")
            ui.button("show active reactions",on_click=show_active_status).classes("mt-4 bg-blue-600 text-white")    