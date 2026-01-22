from nicegui import ui
import pandas as pd
import unicodedata #permet de faire une recherche sans se préoccuper des accents


def display(model):
    # ---------- Utils ----------
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

    # ---------- DataFrame ----------
    df = pd.DataFrame({
        'Metabolite name': [m.name for m in model.metabolites],
        'Formula': [m.formula for m in model.metabolites],
        'Charge': [m.charge for m in model.metabolites],
        'Masses': [get_mass(m) for m in model.metabolites],
        'InChI': [get_inchi(m) for m in model.metabolites],
        'InChIKey': [get_inchikey(m) for m in model.metabolites],
        'SMILES': [get_smiles(m) for m in model.metabolites],

    })

    # colonne normalisée pour la recherche
    df['name_norm'] = df['Metabolite name'].apply(normalize) #colonne invisible pour la recherche partielle

    # mapping affichage ↔ recherche
    name_map = dict(zip(df['Metabolite name'], df['name_norm']))

    # Création d'un dictionnaire       {
    #               "Acétyl-CoA": "acetyl-coa",
    #               "Glucose": "glucose"
    #                }

    # ---------- UI ----------
    ui.label("Recherche de métabolites").classes('text-h5') 

    results = ui.column().classes('q-gutter-md') #conteneur de résultats


    # ---------- Affichage des métabolites sélectionnés ----------
    def show_metabolites(selected_names: list[str]):
        results.clear()

        if not selected_names:
            return

        for name in selected_names:
            row = df[df['Metabolite name'] == name].iloc[0]

            with ui.row().classes('q-gutter-lg'): 
                 # ← alignement horizontal

                # -------- CARD GAUCHE : Infos générales --------
                with ui.card().classes('w-96'):
                    ui.label(f"🧬 {row['Metabolite name']}").classes('text-h6')
                    ui.separator()
                    ui.label(f"Formula : {row['Formula']}")
                    ui.label(f"Charge : {row['Charge']}")
                    ui.label(f"Mass : {row['Masses']}")

                # -------- CARD DROITE : Représentation chimique --------
                with ui.card().classes('w-96'):
                    ui.label("⚗️ Standard chemical representation").classes('text-h6')
                    ui.separator()

                    ui.label(f"InChI : {row['InChI'] or 'Not available'}")
                    ui.label(f"InChIKey : {row['InChIKey'] or 'Not available'}")
                    ui.label(f"SMILES : {row['SMILES'] or 'Not available'}")

    # ---------- Select avec autocomplétion avancée ----------
    select = ui.select(
        options=list(name_map.keys()),
        label='Rechercher un ou plusieurs métabolites',
        multiple=True,
        on_change=lambda e: show_metabolites(e.value)
    ).props(
        'use-input clearable input-debounce=300' #Attente de 300 ms avant déclenchement : meilleure performance
    ).classes('w-96')

    # ---------- Recherche partielle insensible aux accents ----------
    def filter_options(e):
        query = normalize(e.value)
        if not query:
            select.options = list(name_map.keys())
            return

        select.options = [
            name for name, norm in name_map.items()
            if query in norm
        ]

    select.on('update:model-value', filter_options)

