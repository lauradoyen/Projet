from nicegui import ui
import pandas as pd

def display(model):

    # Extraction des contraintes
    def extract_constraints():
        rows = []
        for r in model.reactions:
            lb = r.lower_bound if r.lower_bound not in (-1000, 0) else None
            ub = r.upper_bound if r.upper_bound not in (1000, 0) else None
            rows.append({"Reaction": r.id, "Lower bound": lb, "Upper bound": ub})
        return pd.DataFrame(rows)

    df_constraints = extract_constraints()

    # Mise à jour du modèle COBRA
    def update_bound(rxn_id, col, value):

        # retirer les valeurs non float
        try:
            val = float(value)
        except:
            val = None

        r = model.reactions.get_by_id(rxn_id)

        if col == "Lower bound":
            r.lower_bound = val if val is not None else -1000
            df_constraints.loc[df_constraints["Reaction"] == rxn_id, "Lower bound"] = val

        if col == "Upper bound":
            r.upper_bound = val if val is not None else 1000
            df_constraints.loc[df_constraints["Reaction"] == rxn_id, "Upper bound"] = val

        ui.notify(f"{col} updated for {rxn_id}")

   
    # Export CSV
    def export_constraints():
        filename = "constraints.csv"
        df_constraints.to_csv(filename, index=False)
        ui.download(filename)

    
    # Interface 
    with ui.tabs() as tabs:
        tab1 = ui.tab("Biomass maximisation")
        tab2 = ui.tab("FBA")

    with ui.tab_panels(tabs, value=tab1).classes("w-full"):
        
        # ONGLET 1 : BIOMASSE
       
        with ui.tab_panel(tab1):

            ui.label("Biomass maximisation").classes("text-2xl font-bold mb-4")

            with ui.row().classes("gap-6"):

                # Colonne gauche : FBA biomasse
                with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):

                    result_container1 = ui.column().classes("mt-4")

                    def run_fba_biomass():
                        result_container1.clear()

                        rxn = model.reactions.get("Exchange_Biomass")
                        model.objective = rxn.flux_expression

                        solution = model.optimize()

                        fluxes = pd.DataFrame({
                            "Reaction": [r.id for r in model.reactions if solution.fluxes[r.id] != 0],
                            "Flux": [solution.fluxes[r.id] for r in model.reactions if solution.fluxes[r.id] != 0],
                        })

                        ui.label(
                            f"Objective value: {solution.objective_value:.4f}"
                        ).classes("font-semibold mt-2")

                        ui.table(
                            columns=["Reaction", "Flux"],
                            rows=fluxes.to_dict("records")
                        ).classes("w-full")

                    ui.button(
                        "Run FBA Biomass",
                        on_click=run_fba_biomass
                    ).classes("mt-4 bg-blue-600 text-white")

                # Colonne droite : contraintes 
                with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-full"):

                    ui.label("Constraints (editable)").classes("text-xl font-semibold mb-2")

                    # En-têtes
                    with ui.row().classes("font-bold border-b pb-2"):
                        ui.label("Reaction").classes("w-1/3")
                        ui.label("Lower bound").classes("w-1/3")
                        ui.label("Upper bound").classes("w-1/3")

                    # Lignes du tableau
                    for _, row in df_constraints.iterrows():

                        # Toujours un float pour NiceGUI
                        lb_display = float(row["Lower bound"]) if row["Lower bound"] is not None else 0.0
                        ub_display = float(row["Upper bound"]) if row["Upper bound"] is not None else 0.0

                        with ui.row().classes("items-center py-1"):
                            ui.label(row["Reaction"]).classes("w-1/3")

                            ui.number(
                                value=lb_display,
                                format="%.6f",      # format valide obligatoire
                                step=0.1,
                                on_change=lambda e, rxn=row["Reaction"]: update_bound(
                                    rxn, "Lower bound", e.value
                                )
                            ).classes("w-1/3")

                            ui.number(
                                value=ub_display,
                                format="%.6f",      # format valide obligatoire
                                step=0.1,
                                on_change=lambda e, rxn=row["Reaction"]: update_bound(
                                    rxn, "Upper bound", e.value
                                )
                            ).classes("w-1/3")


            ui.button(
                "Download constraints CSV",
                on_click=export_constraints
            ).classes("mt-6 bg-green-600 text-white")


        # ONGLET 2 : FBA GÉNÉRIQUE
        
        with ui.tab_panel(tab2):

            ui.label("FBA").classes("text-2xl font-bold mb-4")

            with ui.row().classes("gap-6"):

                # Colonne gauche : choix objectif + FBA
                with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-96"):

                    ui.label("Objective selection").classes("text-xl font-semibold mb-2")

                    reactions = [r.id for r in model.reactions]

                    objective_select = ui.select(
                        options=reactions,
                        value=reactions[0],
                        label="Choose the objective reaction:"
                    ).classes("w-full")

                    result_container2 = ui.column().classes("mt-4")

                    def run_fba_other():
                        result_container2.clear()

                        rxn = model.reactions.get(objective_select.value)
                        model.objective = rxn.flux_expression

                        solution = model.optimize()

                        fluxes = pd.DataFrame({
                            "Reaction": [r.id for r in model.reactions if solution.fluxes[r.id] != 0],
                            "Flux": [solution.fluxes[r.id] for r in model.reactions if solution.fluxes[r.id] != 0],
                        })

                        ui.label(
                            f"Objective value: {solution.objective_value:.4f}"
                        ).classes("font-semibold mt-2")

                        ui.table(
                            columns=["Reaction", "Flux"],
                            rows=fluxes.to_dict("records")
                        ).classes("w-full")

                    ui.button(
                        "Run FBA",
                        on_click=run_fba_other
                    ).classes("mt-4 bg-blue-600 text-white")

                # Colonne droite : contraintes 
                with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-full"):

                    ui.label("Constraints (editable)").classes("text-xl font-semibold mb-2")

                    with ui.row().classes("font-bold border-b pb-2"):
                        ui.label("Reaction").classes("w-1/3")
                        ui.label("Lower bound").classes("w-1/3")
                        ui.label("Upper bound").classes("w-1/3")

                    for _, row in df_constraints.iterrows():

                        # Toujours un float pour NiceGUI
                        lb_display = float(row["Lower bound"]) if row["Lower bound"] is not None else 0.0
                        ub_display = float(row["Upper bound"]) if row["Upper bound"] is not None else 0.0

                        with ui.row().classes("items-center py-1"):
                            ui.label(row["Reaction"]).classes("w-1/3")

                            ui.number(
                                value=lb_display,
                                format="%.6f",      # format valide obligatoire
                                step=0.1,
                                on_change=lambda e, rxn=row["Reaction"]: update_bound(
                                    rxn, "Lower bound", e.value
                                )
                            ).classes("w-1/3")

                            ui.number(
                                value=ub_display,
                                format="%.6f",      # format valide obligatoire
                                step=0.1,
                                on_change=lambda e, rxn=row["Reaction"]: update_bound(
                                    rxn, "Upper bound", e.value
                                )
                            ).classes("w-1/3")


            ui.button(
                "Download constraints CSV",
                on_click=export_constraints
            ).classes("mt-6 bg-green-600 text-white")
