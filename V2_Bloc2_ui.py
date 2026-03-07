from nicegui import ui
import pandas as pd
import csv
import V2_Bloc1_ui as Bloc1
import V1_Bloc2_ui_Reactions as ReacInfo

def display(model):

    # ---------- Extraction des contraintes ----------
    def extract_all_constraints(model):
        rows = []
        for r in model.reactions:
            lb = None if r.lower_bound in (-1000, 0) else r.lower_bound
            ub = None if r.upper_bound in (1000, 0) else r.upper_bound
            rows.append({"Reaction": r.id, "Lower bound": lb or "", "Upper bound": ub or ""})
        return pd.DataFrame(rows)

    df = extract_all_constraints(model)

    def apply_constraints(df):
        for _, row in df.iterrows():
            r = model.reactions.get_by_id(row["Reaction"])
            try: r.lower_bound = float(row["Lower bound"])
            except: r.lower_bound = -1000
            try: r.upper_bound = float(row["Upper bound"])
            except: r.upper_bound = 1000

    def on_grid_edit(e):
        row = e.args["data"]
        r = model.reactions.get_by_id(row["Reaction"])
        try: r.lower_bound = float(row["Lower bound"])
        except: r.lower_bound = -1000
        try: r.upper_bound = float(row["Upper bound"])
        except: r.upper_bound = 1000

    def export_constraints():
        filename = "constraints.csv"
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["Reaction","Lower bound","Upper bound"])
            writer.writeheader()
            writer.writerows(df.to_dict("records"))
        ui.download(filename)

    # ---------- Interface principale ----------
    ui.label("Model constraints and FBA").classes("text-xl font-bold mb-2")

    with ui.row().classes("gap-4"):

        # -------- Colonne gauche : contraintes --------
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):
            ui.label("Constraints table").classes("text-lg font-bold mb-2")

            def filter_uptake():
                filtered = df[df["Reaction"].str.contains("uptake", case=False, na=False)]
                grid.options["rowData"] = filtered.to_dict("records")
                grid.update()

            def reset_filter():
                grid.options["rowData"] = df.to_dict("records")
                grid.update()

            def reset_constraints():
                nonlocal df
                df = extract_all_constraints(model)
                for row in Bloc1.rows_constraints:
                    rxn = row["Reaction"]
                    df.loc[df["Reaction"]==rxn, "Lower bound"] = row["Lower bound"]
                    df.loc[df["Reaction"]==rxn, "Upper bound"] = row["Upper bound"]
                apply_constraints(df)
                grid.options["rowData"] = df.to_dict("records")
                grid.update()
                ui.notify("Constraints restored from original model", color="green")

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

        # -------- Colonne droite : FBA --------
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

            # Zone pour afficher les résultats
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
              
            # ---------- Fonctions FBA ----------
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
                    #with ui.scroll_area().classes("w-full h-80 border p-2")
                    zone_fba.options['rowData'] = last_fluxes.to_dict(orient='records')
                    zone_fba.update() 
                else:
                    ui.label("No fluxes different from zero").classes("text-red-600")

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

            # ---------- Boutons FBA visibles en haut ----------
            ui.button("Run FBA (maximize)", on_click=lambda: run_fba("max")).classes("bg-blue-600 text-white")
            ui.button("Run FBA (minimize)", on_click=lambda: run_fba("min")).classes("bg-purple-600 text-white")
            ui.button("Export FBA to CSV", on_click=export_fba).classes("bg-green-600 text-white") 