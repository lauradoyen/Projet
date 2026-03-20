from nicegui import ui
import pandas as pd
import csv
import V2_Bloc1_ui as Bloc1
import V1_Bloc2_ui_Reactions as ReacInfo

def display(model):

    # Constraints extraction 
    def extract_all_constraints(model):
        rows = []
        for r in model.reactions:
            lb = 0 if r.lower_bound is None else r.lower_bound 
            ub = 0 if r.upper_bound is None else r.upper_bound
            rows.append({"Reaction": r.id, "Lower bound": lb, "Upper bound": ub})
        return pd.DataFrame(rows)

    df = extract_all_constraints(model)

    # Functions to apply constraints modifications from the grid to the model
    def apply_constraints(df):
        for _, row in df.iterrows():
            r = model.reactions.get_by_id(row["Reaction"])
            r.lower_bound = float(row["Lower bound"])
            r.upper_bound = float(row["Upper bound"])

    def on_grid_edit(e):
        row = e.args["data"]
        r = model.reactions.get_by_id(row["Reaction"])
        r.lower_bound = float(row["Lower bound"])
        r.upper_bound = float(row["Upper bound"])

    # Function to export constraints to CSV   
    def get_constraints(model):
        return [{"Reaction": r.id, "Lower bound": r.lower_bound, "Upper bound": r.upper_bound} for r in model.reactions]
    
    def export_constraints():
        filename = "constraints.csv"
        fieldnames = ["Reaction", "Lower bound", "Upper bound"]
        rows = get_constraints(model)

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        ui.download(filename)

    """Extraction of the constraints"""
    original_model=model.copy() #save informations to restore contraints and keep in mind the objective function of the original model 
    def get_constraints(model):
        return [{"Reaction": r.id, "Lower bound": r.lower_bound, "Upper bound": r.upper_bound} for r in model.reactions]
    
    # Title of the page
    ui.label("Model constraints and FBA").classes("text-xl font-bold mb-2")

    with ui.row().classes("gap-4"):

        # Left column : constraints table
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):
            ui.label("Constraints table").classes("text-lg font-bold mb-2")

            # Filter to show only uptake reactions (assuming they contain "uptake" in their ID or name)
            def filter_uptake():
                filtered = df[df["Reaction"].str.contains("uptake", case=False, na=False)]
                grid.options["rowData"] = filtered.to_dict("records")
                grid.update()

            # Reset filter to show all reactions
            def reset_filter():
                grid.options["rowData"] = df.to_dict("records")
                grid.update()

            
            # Reset constraints to original model values
            def reset_constraints(): 
                nonlocal df #allows you to modify variables defined outside of the function 
                nonlocal model 
                df = extract_all_constraints(original_model) #reset the constraints with original_model
                grid.options["rowData"] = df.to_dict("records") 
                grid.update() # updates the constraints that the user sees on the interface
                model=original_model.copy()
                ui.notify("Constraints restored from original model", color="green")

            # Buttons to filter and reset constraints
            with ui.row().classes("gap-2 mb-2"):
                ui.button("Show uptake reactions", on_click=filter_uptake).classes("bg-blue-600 text-white")
                ui.button("Show all reactions", on_click=reset_filter).classes("bg-gray-500 text-white")
                ui.button("Reset original constraints", on_click=reset_constraints).classes("bg-red-600 text-white")

            grid = ui.aggrid(
                {"columnDefs":[
                    {"field":"Reaction","editable":False},
                    {"field":"Lower bound","editable":True},
                    {"field":"Upper bound","editable":True}],
                 "rowData":df.to_dict("records"),
                 "defaultColDef":{"sortable":True,"filter":True,"resizable":True},
                 "pagination":True,"paginationPageSize":20,
                 "stopEditingWhenCellsLoseFocus":True},
                theme="balham"
            ).classes("w-full h-96")
            grid.on("cellValueChanged", on_grid_edit)
            ui.button("Export constraints to CSV", on_click=export_constraints).classes("mt-2 bg-green-600 text-white")


        # Right column : FBA results and objective selection
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):

            ui.label("FBA objective selection").classes("text-lg font-bold mb-2")
            reactions = [r.id for r in model.reactions]
            objective_select = ui.select(
                options=reactions,
                value="Biomass_rxn" if "Biomass_rxn" in reactions else reactions[0],
                label="Choose objective reaction"
            ).classes("w-80 mb-2")

            last_fluxes = None
            last_objective_value = None
            objective_label = ui.label("").classes("font-semibold mt-2")

            # Data grid to display FBA results
            zone_fba = ui.aggrid(
    {
        "columnDefs": [
            {"field": "Reaction"},
            {"field": "Flux"},
            {"field": "Type"},
        ],
        "rowData": [],
        "defaultColDef": {"sortable": True, "filter": True, "resizable": True},
    },
    theme="balham"
).classes("w-full h-96")
            def clear_grid():
                zone_fba.options['rowData'] = []
                zone_fba.update()
              
            # Function to run FBA and display results
            def run_fba(mode):
                nonlocal last_fluxes, last_objective_value
                nonlocal objective_label
                clear_grid()
                rxn = model.reactions.get_by_id(objective_select.value)
                model.objective = rxn.flux_expression
                sense = "maximize" if mode=="max" else "minimize"
                solution = model.optimize(objective_sense=sense)
                if solution.status != 'optimal':
                    ui.notify(f"FBA failed: {solution.status}", color="red")
                    return
                last_objective_value = solution.objective_value
                last_fluxes = pd.DataFrame({
                    "Reaction":[r.id for r in model.reactions if abs(solution.fluxes[r.id])>1e-12],
                    "Flux":[solution.fluxes[r.id] for r in model.reactions if abs(solution.fluxes[r.id])>1e-12],
                    "Type":[ReacInfo.get_reaction_type(model,r.id) for r in model.reactions if abs(solution.fluxes[r.id])>1e-12]
                })
                objective_label.text = f"Objective value: {last_objective_value:.4f}"
                if not last_fluxes.empty:
                    zone_fba.options['rowData'] = last_fluxes.to_dict(orient='records')
                    zone_fba.update() 
                else:
                    ui.label("No fluxes different from zero").classes("text-red-600")

            # Function to export FBA results to CSV
            def export_fba():
                if last_fluxes is None or last_fluxes.empty:
                    ui.notify("Run FBA before exporting", color="red")
                    return
                filename="fba.csv"
                with open(filename,"w",newline="",encoding="utf-8") as file:
                    writer=csv.writer(file)
                    writer.writerow(["Objective value", last_objective_value])
                    writer.writerow([])
                    writer.writerow(["Reaction","Flux","Type"])
                    for row in last_fluxes.to_dict("records"):
                        writer.writerow([row["Reaction"],row["Flux"],row["Type"]])
                ui.download(filename)    

            # Buttons to run FBA and export results
            ui.button("Run FBA (maximize)", on_click=lambda: run_fba("max")).classes("bg-blue-600 text-white")
            ui.button("Run FBA (minimize)", on_click=lambda: run_fba("min")).classes("bg-purple-600 text-white")
            ui.button("Export FBA to CSV", on_click=export_fba).classes("bg-green-600 text-white") 