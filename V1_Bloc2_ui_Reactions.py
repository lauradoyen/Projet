from nicegui import ui
import pandas as pd
import unicodedata #permet de faire une recherche sans se préoccuper des accents
import re

def display(model):
    ui.label("Search Reactions").classes("text-2xl font-bold mb-4")

    def normalize(text: str) -> str:   #fonction clé pour la recherche
        if not isinstance(text, str):
            return '' #sécurité
        return ''.join(
            c for c in unicodedata.normalize('NFD', text) #décompose les caractères accentués , ex : é → e + ´
            if unicodedata.category(c) != 'Mn' #supprime les accents
        ).lower()
    



    #dataframe
  
    def reactionInfos(model):
        ReactionID = []
        ReactionName = []
        ReactionFormula = []
        LowerBound = []
        UpperBound = []
        ECNumbers = []
        GPRAssociations = []
        Sources = []

        for reaction in model.reactions:

            rule = reaction.gene_reaction_rule
            genes = re.findall(r'x\(([0-9]+)\)', rule)
            for gene in genes:
                rule = rule.replace(f'x({gene})', model.genes[int(gene)-1].id, 1)
                rule = rule.replace('|', 'or')
                rule = rule.replace('&', 'and')
                rule = rule.replace('( ', '(')
                rule = rule.replace(' )', ')')

            ReactionID.append(reaction.id)
            ReactionName.append(reaction.name)
            ReactionFormula.append(reaction.reaction)
            LowerBound.append(reaction.lower_bound)
            UpperBound.append(reaction.upper_bound)
            ECNumbers.append(reaction.annotation.get('ec-code', 'N/A'))
            GPRAssociations.append(rule)

            # Source
            Sources.append(reaction.notes.get('CATEGORIES', 'N/A'))

        return ReactionID, ReactionName, ReactionFormula,LowerBound, UpperBound, ECNumbers,GPRAssociations, Sources


    rReactionID, rReactionName, rReactionFormula, rLowerBound, rUpperBound, rECNumbers, rGPRAssociations, rSources = reactionInfos(model)

    # Création du DataFrame
    df = pd.DataFrame({
        'Reaction ID': rReactionID,
        'Name of the reaction': rReactionName,
        'Formula' : rReactionFormula,
        'Lower bound' : rLowerBound,
        'Upper bound' : rUpperBound,
        'Enzyme Commission Number' : rECNumbers,
        ' Gene–Protein–Reaction association' : rGPRAssociations,
        'Source of reconstruction' : rSources

    })


    # colonne normalisée pour la recherche
    df['name_norm'] = df['Reaction ID'].apply(normalize) #colonne invisible pour la recherche partielle

    # mapping affichage ↔ recherche
    name_map = dict(zip(df['Reaction ID'], df['name_norm']))


    # ---------- UI ----------
    ui.label("Recherche de réactions").classes('text-h5') 

    results = ui.column().classes('q-gutter-md') #conteneur de résultats



        # ---------- Affichage des gènes sélectionnés ----------
    def show_reactions(selected_names: list[str]):
        results.clear()

        if not selected_names:
            return

        for name in selected_names:
            row = df[df['Reaction ID'] == name].iloc[0]

            with ui.card().classes('w-96'):
                ui.label(row['Reaction ID']).classes('text-h6')
                ui.separator()
                ui.label(f"Name of the reaction: {row['Name of the reaction']}")
                ui.label(f"Formula: {row['Formula']}")
                ui.label(f"Lower bound: {row['Lower bound']}")
                ui.label(f"Upper bound: {row['Upper bound']}")
                ui.label(f"Enzyme Commission Number: {row['Enzyme Commission Number']}")
                ui.label(f"Gene–Protein–Reaction association: {row[' Gene–Protein–Reaction association']}")
                ui.label(f"Source of reconstruction: {row['Source of reconstruction']}")



    # ---------- Select avec autocomplétion avancée ----------
    select = ui.select(
        options=list(name_map.keys()),
        label='Rechercher une ou plusieurs réactions',
        multiple=True,
        on_change=lambda e: show_reactions(e.value)
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




