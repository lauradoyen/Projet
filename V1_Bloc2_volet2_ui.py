from nicegui import ui
import pandas as pd

def display(model):

    # -----------------------------
    # Extraction des informations
    # -----------------------------
    def name_metabolite(model):
        return [m.name for m in model.metabolites]

    def inchi(model):
        return [m.annotation.get('inchi') for m in model.metabolites]

    def inchi_key(model):
        return [m.annotation.get('inchikey') for m in model.metabolites]

    def smiles(model):
        return [m.notes.get('smiles') for m in model.metabolites]

    # Création du DataFrame
    df = pd.DataFrame({
        'Metabolite name': name_metabolite(model),
        'InChI': inchi(model),
        'InChI_key': inchi_key(model),
        'SMILES': smiles(model),
    })

    # -----------------------------
    # Interface NiceGUI
    # -----------------------------
    #ui.label("Standard chemical representation").classes("text-2xl font-bold")

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

        suggestions = filtered_df["Metabolite name"].tolist()

        with result_container:
            #ui.label("Suggestions :").classes("text-lg font-semibold")
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
