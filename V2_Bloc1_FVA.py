from nicegui import ui
import pandas as pd
import csv
from cobra.flux_analysis import flux_variability_analysis
import threading

def display(model):
    """Extraction des contraintes"""
    def get_constraints_min(model):
        return [{"Reaction": r.id, "Lower bound": r.lower_bound, "Upper bound": ""}
            for r in model.reactions if r.lower_bound > -1000 and r.lower_bound != 0]

    def get_constraints_max(model):
        return [{"Reaction": r.id, "Lower bound": "", "Upper bound": r.upper_bound}
            for r in model.reactions if r.upper_bound < 1000 and r.upper_bound != 0]

    rows = get_constraints_min(model) + get_constraints_max(model)
    df_constraints = pd.DataFrame(rows)

    """Fonction d’export CSV"""
    def export_constraints():
        filename = "constraints.csv"
        fieldnames = ["Reaction", "Lower bound", "Upper bound"]

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        ui.download(filename)

    # Interface 
    with ui.row().classes("gap-6"):

        # Sélection de l’objectif
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):

            ui.label("Objective selection").classes("text-xl font-semibold mb-2")

            reactions = [r.id for r in model.reactions]
            
            metabolite_select = ui.select(options=reactions, 
                multiple = True, 
                with_input=True,
                label ="Select several reactions of the model that you want to analyse with FVA").classes('w-64').props('use-chips')
            
            ui.label('Please input the fraction of optimum desired for the FVA')
            fraction_optimum = ui.slider(min=0,max=1,step=0.01, value=1)
            ui.label().bind_text_from(fraction_optimum, 'value')

            def reset_objective():
                model.objective = None
                fraction_optimum.value=1
                ui.notify("Objective reset to zero")

            ui.button("Reset objective", on_click=reset_objective).classes(
                "mt-2 bg-gray-500 text-white"
            )

            grid = ui.aggrid([]).classes('max-h-40')

            # Fonction FVA dans un thread pour éviter blocage
            def run_fva():
                solution = flux_variability_analysis(model,metabolite_select.options,fraction_of_optimum=fraction_optimum.value)
                # Mise à jour des données dans AgGrid
                grid.data = solution.to_dict(orient='records') 

            ui.button("Run FVA", on_click=run_fva).classes("mt-4 bg-blue-600 text-white")

    # BOUTON EXPORT CSV EN BAS DE PAGE
    ui.button("Download constraints CSV", on_click=export_constraints).classes("mt-6 bg-green-600 text-white")

