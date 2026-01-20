from nicegui import ui
import pandas as pd

def display(model):

    #ui.label("Flux Balance Analysis (FBA)").classes("text-2xl font-bold")

    # Liste des réactions disponibles
    reactions = [r.id for r in model.reactions]

    # Sélection de la réaction objectif
    objective_select = ui.select(
        options=reactions,
        value=reactions[0],
        label="Choose the objective reaction:"
    ).classes("w-96")

    # Conteneur pour les résultats
    result_container = ui.column().classes("mt-6")

    def run_fba():
        result_container.clear()

        # Définir l'objectif
        model.objective = objective_select.value

        # Optimiser
        solution = model.optimize()

        with result_container:
            #ui.label("Optimization results").classes("text-xl font-semibold")
            #ui.label(f"Objective value: {solution.objective_value:.4f}")

            # Tableau des flux
            fluxes = pd.DataFrame({
                "Reaction": [r.id for r in model.reactions],
                "Flux": [solution.fluxes[r.id] for r in model.reactions]
            })

            ui.table.from_pandas(fluxes).classes("w-full")

    # Bouton pour lancer l’optimisation
    ui.button("Run FBA", on_click=run_fba).classes("mt-4 bg-blue-600 text-white")
