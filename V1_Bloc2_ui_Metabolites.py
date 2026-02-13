from nicegui import ui
import pandas as pd
import unicodedata #permet de faire une recherche sans se préoccuper des accents
import io
import csv

def display(model):

    selected_rows_df = [] #initalise la liste de métabolites selectionnés

    def normalize(text: str) -> str:   #fonction clé pour la recherche
        if not isinstance(text, str):
            return '' #sécurité
        return ''.join(
            c for c in unicodedata.normalize('NFD', text) #décompose les caractères accentués , ex : é → e + ´
            if unicodedata.category(c) != 'Mn' #supprime les accents
        ).lower()
     
    # résultat : "Acétyl-CoA" → "acetyl-coa"

    def get_mass(m):  #sinon erreur 'str' object has no attribute 'get'
        if isinstance(m.notes, dict):
            return m.notes.get('mass')
        return None
    
    def get_inchi(m):
        if isinstance(m.annotation, dict):
            return m.annotation.get('inchi')
        return None

    def get_inchikey(m):
        if isinstance(m.annotation, dict):
            return m.annotation.get('inchikey')
        return None

    def get_smiles(m):
        if isinstance(m.notes, dict):
            return m.notes.get('smiles')
        return None
    
    def get_data_met(m):
        if isinstance(m.annotation, dict):
            return m.annotation.get('database')
        return None
    
    def get_sbo_met(m):
        if isinstance(m.annotation, dict):
            return m.annotation.get('sbo')
        return None
    


    # ---------- DataFrame ----------
    df = pd.DataFrame({
        'Metabolite ID' : [m.id for m in model.metabolites],
        'Metabolite name': [m.name for m in model.metabolites],
        'Formula': [m.formula for m in model.metabolites],
        'Charge': [m.charge for m in model.metabolites],
        'Masses': [get_mass(m) for m in model.metabolites],
        'InChI': [get_inchi(m) for m in model.metabolites],
        'InChIKey': [get_inchikey(m) for m in model.metabolites],
        'SMILES': [get_smiles(m) for m in model.metabolites],
        'Database' : [get_data_met(m) for m in model.metabolites],
        'SBO' : [get_sbo_met(m) for m in model.metabolites],
        'Reactions': [[r.id for r in m.reactions] for m in model.metabolites],
        'Count Reactions': [len(m.reactions) for m in model.metabolites],
        'Compartment' : [m.compartment for m in model.metabolites]

    })

    # colonne normalisée pour la recherche
    df['name_norm'] = df['Metabolite name'].apply(normalize) #colonne invisible pour la recherche partielle

    # mapping affichage ↔ recherche
    name_map = dict(zip(df['Metabolite name'], df['name_norm']))

    # Création d'un dictionnaire       {
    #               "Acétyl-CoA": "acetyl-coa",
    #               "Glucose": "glucose"
    #                }

    #pour la recherche par l'ID :
    df['ID_norm'] = df['Metabolite ID'].apply(normalize) #colonne invisible pour la recherche partielle

    # mapping affichage ↔ recherche
    ID_map = dict(zip(df['Metabolite ID'], df['ID_norm']))

    search_mode = {'value': 'name'} # 'name' ou 'id'

    #fonctions pour changer le mode : 
    def set_search_by_name(): 
        search_mode['value'] = 'name' 
        select.options = list(name_map.keys()) 
        select.label = "Enter metabolite name" 
        select.update() 
    
    def set_search_by_id(): 
        search_mode['value'] = 'id' 
        select.options = list(ID_map.keys()) 
        select.label = "Enter metabolite ID" 
        select.update()

    ui.label("Search Metabolites").classes("text-2xl font-bold mb-4") 

    with ui.button_group():
        ui.button('Search by Name', on_click=set_search_by_name)
        ui.button('Search by ID', on_click=set_search_by_id)

    results = ui.column().classes('q-gutter-md') #conteneur de résultats


    # Affichage des métabolites sélectionnés
    def show_metabolites_byname(selected_name: str):
        results.clear()

        if not selected_name:
            return

        # Vérifier que le gène existe dans le DataFrame 
        row_df = df[df['Metabolite name'] == selected_name] 
        if row_df.empty: 
            return # évite l'erreur iloc[0] 

        row = row_df.iloc[0]

        selected_rows_df.append(row_df) #màj de la liste des métabolites selectionnés


        with ui.row().classes('q-gutter-lg'): 

            # CARD1 : Infos générales
            with ui.card().classes('w-96'):
                ui.label(f"{row['Metabolite name']}").classes('text-h6')
                ui.separator()
                ui.label(f"Metabolite ID : {row['Metabolite ID']}")
                ui.label(f"Formula : {row['Formula']}")
                ui.label(f"Charge : {row['Charge']}")
                ui.label(f"Mass : {row['Masses']}")

            # CARD2 : Représentation chimique
            with ui.card().classes('w-96'):
                ui.label("Standard chemical representation").classes('text-h6')
                ui.separator()
                ui.label(f"InChI : {row['InChI'] or 'Not available'}")
                ui.label(f"InChIKey : {row['InChIKey'] or 'Not available'}")
                ui.label(f"SMILES : {row['SMILES'] or 'Not available'}")
            
            #CARD3 : Références
            with ui.card().classes('w-96'):
                ui.label(" References and interoperability").classes('text-h6')
                ui.separator()
                ui.label(f"Database : {row['Database'] or 'Not available'}")
                ui.label(f"SBO : {row['SBO'] or 'Not available'}")
            
            #CARD 4 : Contexte dans le réseau métabolique
            with ui.card().classes('w-96'):
                ui.label(" Context in the metabolic network").classes('text-h6')
                ui.separator()
                ui.label(f"Number of associated reactions : {row['Count Reactions']}")
                ui.label("List of associated reactions:")
                with ui.row():
                    with ui.scroll_area().classes('w-64 h-50 border'):
                        for reaction in row['Reactions']:
                            ui.label(reaction)
                ui.separator()
                ui.label(f"Compartment : {row['Compartment']}")


    # pour la recherche par ID : 
    def show_metabolites_byid(selected_id: str):
        results.clear()

        if not selected_id:
            return

        # Vérifier que le gène existe dans le DataFrame 
        row_df = df[df['Metabolite ID'] == selected_id] 
        if row_df.empty: 
            return # évite l'erreur iloc[0] 

        row = row_df.iloc[0]

        show_metabolites_byname(row['Metabolite name'])


    #export csv   
    def export_infos_met_csv():

        if len(selected_rows_df)==0: 
            ui.notify("No Metabolite selected") 
            return
        
        
        filename = "info_metabolite.csv"
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # En‑têtes
            writer.writerow(["Metabolite ID", "Formula", "Charge", "Mass", "InChI", "InChIKey", "SMILES", "Database", "SBO", "Reactions", "Count Reactions", "Compartment" ])

            # Infos
            for row_df in selected_rows_df:
                row = row_df.iloc[0]
                writer.writerow([row["Metabolite ID"], row["Formula"], row["Charge"], row ["Masses"], row ["InChI"], row ["InChIKey"], row ["SMILES"], row ["Database"], row ["SBO"],  row ["Reactions"], row ["Count Reactions"], row ["Compartment"]])

            ui.download(filename)

    #export json
    def export_infos_met_json(): 
        if len(selected_rows_df)==0: 
            ui.notify("No Metabolite selected") 
            return 
        
        row_df = selected_rows_df[-1] 
            
        row = row_df.iloc[0] 
        
        # Conversion en dictionnaire simple 
        data = { "Metabolite ID": row["Metabolite ID"], 
                "Metabolite name": row["Metabolite name"], 
                "Formula": row["Formula"], 
                "Charge": row["Charge"], 
                "Mass": row["Masses"], 
                "InChI": row["InChI"], 
                "InChIKey": row["InChIKey"], 
                "SMILES": row["SMILES"], 
                "Database": row["Database"], 
                "SBO": row["SBO"], 
                "Reactions": row["Reactions"], 
                "Count Reactions": row["Count Reactions"], 
                "Compartment": row["Compartment"], } 
        
        # Export JSON 
        json_str = pd.Series(data).to_json(indent=4, force_ascii=False) 
        filename = "info_metabolite.json" 
        with open(filename, "w", encoding="utf-8") as f: 
            f.write(json_str) 
        
        ui.download(filename)


    def on_select_change(e):
        if search_mode['value'] == 'name': 
            show_metabolites_byname(e.value) 
        else: 
            show_metabolites_byid(e.value)
    
    #  Select avec autocomplétion avancée 
    select = ui.select(
        options=list(name_map.keys()),
        label='Enter metabolite name',
        multiple=False,
        on_change=on_select_change
    ).props(
        'use-input clearable input-debounce=300' #Attente de 300 ms avant déclenchement : meilleure performance
    ).classes('w-96')

    # Recherche partielle insensible aux accents
    def filter_options(e):
        query = normalize(e.args or "")

        if search_mode['value'] == 'name': 
            mapping = name_map 
        else: 
            mapping = ID_map

        if not query:
            select.options = list(mapping.keys())
            return

        select.options = [
            key for key, norm in mapping.items()
            if query in norm
        ]

    select.on("filter", filter_options)

     
    with ui.dropdown_button('Export Metabolite(s) Information', auto_close=True):
        ui.item('.CSV', on_click=export_infos_met_csv).classes("mt-4 bg-blue-600 text-white")
        ui.item('.JSON', on_click=export_infos_met_json).classes("mt-4 bg-blue-600 text-white")
