from nicegui import ui
import pandas as pd
import csv 

rows_constraints = None #Variable globale pour le reset du volet 2 

def display(model):
    global rows_constraints # Pour le reset du volet 2 
    # Extraction des contraintes
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

    # Fusion min + max
    rows_constraints = get_constraints_min(model) + get_constraints_max(model)

    if not rows_constraints:
        ui.label("No constraints found").classes("text-red-600")
        return

    df = pd.DataFrame(rows_constraints)


    # Fonction d’export CSV
    def export_constraints():
        filename = "constraints.csv"
        fieldnames = ["Reaction", "Lower bound", "Upper bound"]

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_constraints)

        ui.download(filename)


    # Tableau AG‑Grid 
    ui.label("Constraints table").classes("text-xl font-bold mb-2")

    ui.aggrid(
        {
            "columnDefs": [
                {"field": "Reaction"},
                {"field": "Lower bound"},
                {"field": "Upper bound"},
            ],
            "rowData": df.to_dict("records"),
            "defaultColDef": {
                "sortable": True,
                "filter": True,
                "resizable": True,
            },
            "pagination": True,
            "paginationPageSize": 20,
        },
        theme="balham",
    ).classes("w-full h-96")

    # Bouton d’export CSV
    ui.button(
        "Export constraints to CSV",
        on_click=export_constraints
    ).classes("mt-4 bg-green-600 text-white")
