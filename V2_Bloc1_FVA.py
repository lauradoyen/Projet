from nicegui import ui
import pandas as pd
import csv
from cobra.flux_analysis import flux_variability_analysis
import asyncio

def display(model):

    """Extraction des contraintes"""
    original_model=model.copy()
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
    with ui.row().classes("gap-6"):
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):
            ui.label("Modify the different constraints of the model").classes("text-xl font-semibold mb-2")
            def extract_all_constraints(model):
                rows = []
                for r in model.reactions:
                    lb = None if r.lower_bound in (-1000, 0) else r.lower_bound
                    ub = None if r.upper_bound in (1000, 0) else r.upper_bound
                    rows.append({
                "Reaction": r.id,
                "Lower bound": lb if lb is not None else "",
                "Upper bound": ub if ub is not None else "",
            })
                return pd.DataFrame(rows)
            
            df = extract_all_constraints(model)

            def on_grid_edit(e):
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
            
            constraint_grid = ui.aggrid(
        {
            "columnDefs": [
                {"field": "Reaction", "editable": False},
                {"field": "Lower bound", "editable": True},
                {"field": "Upper bound", "editable": True},
            ],
            "rowData": df.to_dict("records"),
            "defaultColDef": {"sortable": True, "filter": True, "resizable": True},
            "pagination": True,
            "paginationPageSize": 20,
            "stopEditingWhenCellsLoseFocus": True,
        },
        theme="balham",
    ).classes("w-full h-96")

            constraint_grid.on("cellValueChanged", on_grid_edit)
            
            def reset_constraints():
                nonlocal df
                nonlocal model
                df = extract_all_constraints(original_model) #tableau complet
                constraint_grid.options["rowData"] = df.to_dict("records") #update 
                constraint_grid.update()
                model=original_model.copy()
                ui.notify("Constraints restored from original model", color="green")

            ui.button("Reset original constraints of the model", on_click=reset_constraints).classes(
                "mt-2 bg-gray-500 text-white")
            ui.button("Download constraints CSV", on_click=export_constraints).classes("mt-6 bg-green-600 text-white")

        # Sélection de l’objectif
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):

            default_objective=model.objective


            ui.label("Select the different parameters of the FVA ").classes("text-xl font-semibold mb-2")

            reactions = [r.id for r in model.reactions]
            
            select_objective = ui.select(options=reactions,value=reactions[0],with_input=True,label='Select the objective reaction').classes('w-64').props('use-chips')

            metabolite_select = ui.select(options=reactions, 
                multiple = True, 
                with_input=True,
                label ="Select several reactions of the model that you want to analyse with FVA").classes('w-64').props('use-chips')
            
            ui.label('Please input the fraction of optimum desired for the FVA')
            fraction_optimum = ui.slider(min=0,max=1,step=0.01, value=1)
            ui.label().bind_text_from(fraction_optimum, 'value')

        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):
            fva_grid = ui.aggrid({'columnDefs': [],'rowData': []}).style('height:200px')
            
            def clear_grid():
                fva_grid.options['rowData'] = []
                fva_grid.options['columnDefs'] = []
                fva_grid.update()

            objective_reaction=None
            df_fva=None 
            # Fonction FVA 
            async def run_fva():
                nonlocal objective_reaction
                nonlocal df_fva
                nonlocal model_copy
                ui.notify('Please wait for the calculations to be finished')
                try:
                    clear_grid()
                    model_copy=model.copy()
                    objective_reaction=model_copy.reactions.get_by_id(select_objective.value)
                    model_copy.objective =objective_reaction.flux_expression
                    if len(metabolite_select.value)==0:
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
            def result_fva():
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run before exporting", color="red")
                    return
                rows = get_constraints(model_copy)
                table_constraints = pd.DataFrame(rows)
                meta_df = pd.DataFrame({
        "Objective reaction": [objective_reaction.id],
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

            ui.label("Find the reversible reactions and reactions with a fixed flux").classes("text-xl font-semibold mb-2")
            ui.label('The reversible reactions and reactions with a fixed flux will be calculated using the current results shown for the FVA')
            zone = ui.aggrid(
    {
        "columnDefs": [
            {"field": "Reaction"},
        ],
        "rowData": [],
        "defaultColDef": {"sortable": True, "filter": True, "resizable": True},
    },
    theme="balham"
).classes("w-full h-96")    
            async def find_fixed_reactions():
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run FVA before showing these caracteristics ", color="red")
                    return 
                zone.clear()
                flux_reaction=[{
                "Reaction": r} for r in df_fva.loc[(df_fva["minimum"] == df_fva["maximum"]) & (df_fva["minimum"] != 0), "index"]]
                zone.options['rowData'] =flux_reaction
                zone.update()
                ui.notify("the results of the fixed flux reactions are available ")
            ui.button('Show fixed flux reactions',on_click=find_fixed_reactions)
            async def find_reversible_reactions():
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
            ui.button('Show reversible reactions', on_click=find_reversible_reactions)
            async def show_blocked_status():
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run FVA before showing these caracteristics ", color="red")
                    return
                zone.clear()
                blocked_reaction=[{
                "Reaction": r} for r in df_fva.loc[(df_fva["minimum"] == df_fva["maximum"]) & (df_fva["minimum"] == 0), "index"]]
                zone.options['rowData'] =blocked_reaction
                zone.update()
                ui.notify("The blocked reactions are available")
            ui.button("show blocked reactions", on_click=show_blocked_status).classes("mt-4 bg-blue-600 text-white")
            async def show_active_status():
                if fva_grid.options['rowData'] == []:
                    ui.notify("Run FVA before showing these caracteristics ", color="red")
                    return
                zone.clear()
                active_reaction = [{
                "Reaction": r} for r in df_fva.loc[df_fva["minimum"] != df_fva["maximum"], "index"]]
                zone.options['rowData'] =active_reaction
                zone.update()
                ui.notify("The active reactions are available")
            ui.button("show active reactions",on_click=show_active_status).classes("mt-4 bg-blue-600 text-white")

        