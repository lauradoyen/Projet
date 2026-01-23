from nicegui import ui
import pandas as pd
import csv

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

            objective_select = ui.select(
                options=reactions,
                value=reactions[0],
                label="Choose the objective reaction:"
            ).classes("w-full")

            def reset_objective():
                model.objective = None
                ui.notify("Objective reset to zero")

            ui.button("Reset objective", on_click=reset_objective).classes(
                "mt-2 bg-gray-500 text-white"
            )

            # Conteneur des résultats FBA
            result_container = ui.column().classes("mt-4")

            def run_fba():
                result_container.clear()

                model.objective = objective_select.value
                solution = model.optimize()

                fluxes = pd.DataFrame({
                    "Reaction": [r.id for r in model.reactions if solution.fluxes[r.id] != 0],
                    "Flux": [solution.fluxes[r.id] for r in model.reactions if solution.fluxes[r.id] != 0]

                })

                ui.label(f"Objective value: {solution.objective_value:.4f}").classes(
                    "font-semibold mt-2"
                )

                ui.aggrid(
                    {
                        "columnDefs": [
                            {"field": "Reaction"},
                            {"field": "Flux"},
                        ],
                        "rowData": fluxes.to_dict("records"),
                        "defaultColDef": {
                            "sortable": True,
                            "filter": True,
                            "resizable": True,
                        },
                        "pagination": True,
                        "paginationPageSize": 20,
                    },
                    theme="balham",
                ).classes("w-full h-80")

            ui.button("Run FBA", on_click=run_fba).classes(
                "mt-4 bg-blue-600 text-white"
            )

        
        # Tableau des contraintes
        
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-full"):

            ui.label("Constraints table").classes("text-xl font-semibold mb-2")

            ui.aggrid(
                {
                    "columnDefs": [
                        {"field": "Reaction"},
                        {"field": "Lower bound"},
                        {"field": "Upper bound"},
                    ],
                    "rowData": df_constraints.to_dict("records"),
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

    
    # BOUTON EXPORT CSV EN BAS DE PAGE
    ui.button("Download constraints CSV", on_click=export_constraints).classes("mt-6 bg-green-600 text-white")
