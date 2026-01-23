from nicegui import ui
import pandas as pd

def display(model):
    # Extraction des informations
    def name_metabolite(model):
        return [m.name for m in model.metabolites]

    def formula(model):
        return [m.formula for m in model.metabolites]

    def charge(model):
        return [m.charge for m in model.metabolites]

    def masse(model):
        return [m.notes.get('mass') for m in model.metabolites]

    # Création du DataFrame
    df = pd.DataFrame({
        'Metabolite name': name_metabolite(model),
        'Formula': formula(model),
        'Charge': charge(model),
        'Masses': masse(model),
    })

    # Interface NiceGUI
    ui.label("Identification and chemical structure of metabolites").classes("text-2xl font-bold")

    query_input = ui.input("Enter the name of the metabolite :").classes("w-80")

    result_container = ui.column().classes("mt-4")

    def update_results():
        result_container.clear()

        query = query_input.value

        if not query:
            return

        bool_df = df["Metabolite name"].str.contains(query, case=False)
        filtered_df = df[bool_df]

        if filtered_df.empty:
            result_container.label("No result found").classes("text-red-600")
            return

        # Liste des suggestions
        suggestions = filtered_df["Metabolite name"].tolist()

        with result_container:
            ui.label("Suggestions :").classes("text-lg font-semibold")
            select = ui.select(options=suggestions, value=suggestions[0]).classes("w-80")

            selected_container = ui.column().classes("mt-4")

            def update_selected():
                selected_name = select.value
                selected_df = filtered_df[filtered_df["Metabolite name"] == selected_name]

                selected_container.clear()
                #selected_container.label("Selected metabolite :").classes("text-lg font-semibold")
                ui.table.from_pandas(selected_df).classes("w-full")

            select.on("update:model-value", lambda e: update_selected())
            update_selected()

    query_input.on("update:model-value", lambda e: update_results())