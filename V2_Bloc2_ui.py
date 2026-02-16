from nicegui import ui
import pandas as pd
import csv
import V2_Bloc1_ui  as Bloc1 #contraintes du modèle d'origine
import V1_Bloc2_ui_Reactions as ReacInfo


def display(model):

    # Extraction des contraintes 
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

    #Appliquer les contraintes du modèle originel 
    def apply_constraints(df):
        for _, row in df.iterrows():
            r = model.reactions.get_by_id(row["Reaction"])

            lb = row["Lower bound"]
            ub = row["Upper bound"]

            try:
                r.lower_bound = float(lb)
            except:
                r.lower_bound = -1000

            try:
                r.upper_bound = float(ub)
            except:
                r.upper_bound = 1000



    # Mise à jour du modèle
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

    # Export CSV
    def export_constraints():
        filename = "constraints.csv"
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["Reaction", "Lower bound", "Upper bound"])
            writer.writeheader()
            writer.writerows(df.to_dict("records"))
        ui.download(filename)

    # Interface 
    ui.label("Constraints table").classes("text-xl font-bold mb-2")

    # Boutons de filtrage uptake
    def filter_uptake():
        filtered = df[df["Reaction"].str.contains("uptake", case=False, na=False)]
        grid.options["rowData"] = filtered.to_dict("records")
        grid.update()

    def reset_filter():
        grid.options["rowData"] = df.to_dict("records")
        grid.update()

    def reset_constraints():
        nonlocal df
        df = extract_all_constraints(model) #tableau complet
        for row in Bloc1.rows_constraints: #réactions originelles 
            rxn = row["Reaction"]
            df.loc[df["Reaction"] == rxn, "Lower bound"] = row["Lower bound"]
            df.loc[df["Reaction"] == rxn, "Upper bound"] = row["Upper bound"]
        apply_constraints(df) #appliquer au modèle 

        grid.options["rowData"] = df.to_dict("records") #update 
        grid.update()

        ui.notify("Constraints restored from original model", color="green")

    with ui.row().classes("gap-4 mb-4"):
        ui.button("Show uptake reactions", on_click=filter_uptake).classes("bg-blue-600 text-white")
        ui.button("Show all reactions", on_click=reset_filter).classes("bg-gray-500 text-white")
        ui.button("Reset constraints from original model", on_click=reset_constraints).classes("bg-red-600 text-white mb-4")

    grid = ui.aggrid(
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

    grid.on("cellValueChanged", on_grid_edit)

    ui.button("Export constraints to CSV", on_click=export_constraints).classes("mt-4 bg-green-600 text-white")
    ui.separator().classes("my-6")

    # Sélection de la réaction à optimiser
    ui.label("FBA objective selection").classes("text-xl font-bold mb-2")

    reactions = [r.id for r in model.reactions]

    objective_select = ui.select(
        options=reactions,
        value="Biomass_rxn" if "Biomass_rxn" in reactions else reactions[0],
        label="Choose objective reaction",
    ).classes("w-96 mb-4")

    # Résultat FBA
    result_fba = ui.column()
    last_fluxes = None
    last_objective_value = None

    model.solver = "gurobi"
    
    def run_fba(mode):
        nonlocal last_fluxes, last_objective_value
        result_fba.clear()

        rxn = model.reactions.get_by_id(objective_select.value)
        model.objective = rxn.flux_expression

        # mode = "max" ou "min" 
        sense = "maximize" if mode == "max" else "minimize" 
        solution = model.optimize(objective_sense=sense)

        # Stockage
        last_objective_value = solution.objective_value
        last_fluxes = pd.DataFrame({
            "Reaction": [r.id for r in model.reactions if solution.fluxes[r.id] != 0],
            "Flux": [solution.fluxes[r.id] for r in model.reactions if solution.fluxes[r.id] != 0],
            "Type": [ReacInfo.get_reaction_type(model, r.id) for r in model.reactions if solution.fluxes[r.id] != 0],
        })

        # Affichage
        with result_fba:
            with ui.scroll_area().classes('w-180 h-100 border'):
                ui.label(f"Objective value: {last_objective_value:.4f}").classes("font-semibold mt-2")
                ui.table(
                    columns=[
                        {"name": "Reaction", "label": "Reaction", "field": "Reaction"},
                        {"name": "Flux", "label": "Flux", "field": "Flux"},
                        {"name": "Type", "label": "Type", "field": "Type"},
                    ],
                    rows=last_fluxes.to_dict("records"),
                ).classes("w-full")


    def export_fba():
        if last_fluxes is None or last_fluxes.empty:
            ui.notify("Run FBA before exporting", color="red")
            return

        filename = "fba.csv"
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Ligne 1 : objective value
            writer.writerow(["Objective value", last_objective_value])

            # Ligne vide
            writer.writerow([])

            # En‑têtes
            writer.writerow(["Reaction", "Flux", "Type"])

            # Flux
            for row in last_fluxes.to_dict("records"):
                writer.writerow([row["Reaction"], row["Flux"], row["Type"]])

        ui.download(filename)

    with ui.row().classes("gap-4 mb-4"):
        ui.button("Run FBA (maximize)", on_click=lambda: run_fba("max")).classes("bg-blue-600 text-white mb-2")
        ui.button("Run FBA (minimize)", on_click=lambda: run_fba("min")).classes("bg-purple-600 text-white mb-4")
        ui.button("Export FBA to CSV", on_click=export_fba).classes("bg-green-600 text-white mb-4")

    result_fba