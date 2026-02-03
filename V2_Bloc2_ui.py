from nicegui import ui
import pandas as pd
import csv


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
    ui.label("Constraints table (editable)").classes("text-xl font-bold mb-2")

    # Boutons de filtrage uptake
    def filter_uptake():
        filtered = df[df["Reaction"].str.contains("uptake", case=False, na=False)]
        grid.options["rowData"] = filtered.to_dict("records")
        grid.update()

    def reset_filter():
        grid.options["rowData"] = df.to_dict("records")
        grid.update()

    with ui.row().classes("gap-4 mb-4"):
        ui.button("Show uptake reactions", on_click=filter_uptake).classes("bg-blue-600 text-white")
        ui.button("Show all reactions", on_click=reset_filter).classes("bg-gray-500 text-white")

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
        value=reactions[0],
        label="Choose objective reaction",
    ).classes("w-96 mb-4")

    # Résultat FBA
    result_fba = ui.column()

    def run_fba():
        result_fba.clear()

        rxn = model.reactions.get_by_id(objective_select.value)
        model.objective = rxn.flux_expression

        solution = model.optimize()

        fluxes = pd.DataFrame({
            "Reaction": [r.id for r in model.reactions if solution.fluxes[r.id] != 0],
            "Flux": [solution.fluxes[r.id] for r in model.reactions if solution.fluxes[r.id] != 0],
        })

        with result_fba:
            ui.label(f"Objective value: {solution.objective_value:.4f}").classes("font-semibold mt-2")
            ui.table(
                columns=[
                    {"name": "Reaction", "label": "Reaction", "field": "Reaction"},
                    {"name": "Flux", "label": "Flux", "field": "Flux"},
                ],
                rows=fluxes.to_dict("records"),
            ).classes("w-full")

    ui.button("Run FBA", on_click=run_fba).classes("bg-blue-600 text-white mb-4")

    result_fba
