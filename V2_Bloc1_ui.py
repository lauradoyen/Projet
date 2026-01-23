from nicegui import ui
import pandas as pd
import csv 

def display(model):

    # -----------------------------
    # 1) Définir les fonctions AVANT l'UI
    # -----------------------------
    def get_constraints_min(model):
        return [
            {"Reaction": r.id, "Lower bound": r.lower_bound}
            for r in model.reactions
            if r.lower_bound > -1000 and r.lower_bound != 0
        ]

    def get_constraints_max(model):
        return [
            {"Reaction": r.id, "Upper bound": r.upper_bound}
            for r in model.reactions
            if r.upper_bound < 1000 and r.upper_bound != 0
        ]

    def export_constraints():
        rows = []

        # Fusionner les contraintes min/max
        for c in get_constraints_min(model):
            rows.append({"Reaction": c["Reaction"], "Lower bound": c["Lower bound"], "Upper bound": ""})

        for c in get_constraints_max(model):
            rows.append({"Reaction": c["Reaction"], "Lower bound": "", "Upper bound": c["Upper bound"]})

        if not rows:
            ui.notify("No constraints to export", color="red")
            return

        filename = "constraints.csv"
        fieldnames = ["Reaction", "Lower bound", "Upper bound"]

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        ui.download(filename)

    # -----------------------------
    # 2) Interface graphique
    # -----------------------------
    with ui.row().classes("gap-6"):

        # Bloc 1 : Objective
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-80"):
            ui.label("Objective Value for biomass").classes("font-semibold")
            solution = model.optimize()
            ui.label(solution.objective_value)

        # Bloc 2 : Lower bounds
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-80"):
            ui.label("Constraints on lower bounds").classes("font-semibold")
            for c in get_constraints_min(model):
                ui.label(f"{c['Reaction']} : {round(c['Lower bound'])}")

        # Bloc 3 : Upper bounds
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-80"):
            ui.label("Constraints on upper bounds").classes("font-semibold")
            for c in get_constraints_max(model):
                ui.label(f"{c['Reaction']} : {round(c['Upper bound'])}")

    # Bouton d’export
    ui.button("Export constraints to CSV", on_click=export_constraints).classes(
        "mt-4 bg-green-600 text-white"
    )
