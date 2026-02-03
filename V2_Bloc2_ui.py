from nicegui import ui
import pandas as pd
import csv


def display(model):

    # ==========================================================
    # Extraction des contraintes (min + max)
    # ==========================================================
    def get_constraints_min(model):
        return [
            {"Reaction": r.id, "Lower bound": r.lower_bound, "Upper bound": ""}
            for r in model.reactions
            if r.lower_bound > -1000 and r.lower_bound != 0
        ]

    def get_constraints_max(model):
        return [
            {"Reaction": r.id, "Lower bound": "", "Upper bound": r.upper_bound}
            for r in model.reactions
            if r.upper_bound < 1000 and r.upper_bound != 0
        ]

    rows = get_constraints_min(model) + get_constraints_max(model)

    if not rows:
        ui.label("No constraints found").classes("text-red-600")
        return

    df = pd.DataFrame(rows)

    # ==========================================================
    # Mise à jour du modèle COBRA quand AG‑Grid change
    # ==========================================================
    def on_grid_edit(e):
        """e contient la ligne modifiée"""
        row = e.args["data"]
        rxn_id = row["Reaction"]

        r = model.reactions.get_by_id(rxn_id)

        # Lower bound
        lb = row["Lower bound"]
        try:
            lb = float(lb)
            r.lower_bound = lb
        except:
            r.lower_bound = -1000

        # Upper bound
        ub = row["Upper bound"]
        try:
            ub = float(ub)
            r.upper_bound = ub
        except:
            r.upper_bound = 1000

    # ==========================================================
    # Export CSV
    # ==========================================================
    def export_constraints():
        filename = "constraints.csv"
        fieldnames = ["Reaction", "Lower bound", "Upper bound"]

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        ui.download(filename)

    # ==========================================================
    # Interface : Tableau AG‑Grid
    # ==========================================================
    ui.label("Constraints table").classes("text-xl font-bold mb-2")

    grid = ui.aggrid(
        {
            "columnDefs": [
                {"field": "Reaction", "editable": False},
                {"field": "Lower bound", "editable": True},
                {"field": "Upper bound", "editable": True},
            ],
            "rowData": df.to_dict("records"),
            "defaultColDef": {
                "sortable": True,
                "filter": True,
                "resizable": True,
            },
            "pagination": True,
            "paginationPageSize": 20,
            "stopEditingWhenCellsLoseFocus": True,
        },
        theme="balham",
    ).classes("w-full h-96")

    grid.on("cellValueChanged", on_grid_edit)

    ui.button(
        "Export constraints to CSV",
        on_click=export_constraints
    ).classes("mt-4 bg-green-600 text-white")

    ui.separator().classes("my-6")

    # ==========================================================
    # Sélection de la réaction à optimiser
    # ==========================================================
    ui.label("FBA objective selection").classes("text-xl font-bold mb-2")

    reactions = [r.id for r in model.reactions]

    objective_select = ui.select(
        options=reactions,
        value=reactions[0],
        label="Choose objective reaction"
    ).classes("w-96 mb-4")

    # ==========================================================
    # Résultat FBA
    # ==========================================================
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
    rows=fluxes.to_dict("records")
)


    ui.button(
        "Run FBA",
        on_click=run_fba
    ).classes("bg-blue-600 text-white mb-4")

    result_fba
