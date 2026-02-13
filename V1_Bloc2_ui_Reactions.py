from nicegui import ui
import pandas as pd
import unicodedata #permet de faire une recherche sans se préoccuper des accents
import re

def display(model):


    #INFO REACTIONS
    ui.label("General information about the reactions").classes("text-2xl font-bold mb-4")

    def gene_type_count(model):
    # Initialize gene types
        genes_types = ["Pc", "s", "t", "d", "sk", "u", "p"]

    # Create a dictionary to store the count of genes of each type
        genes_count = {gene_type: 0 for gene_type in genes_types}
        # création de : {'Pc': 0, 's': 0, 't': 0, 'd': 0, 'sk': 0, 'u': 0, 'p': 0}
        artificial_genes_count = 0

        for gene in model.genes:
        # Remove the 'gp_' prefix from the gene id
            gene_id = gene.id.replace('gp_', '')

        # Increment the count if the gene name contains the gene type
            for gene_type in genes_types:
                if gene_type in gene_id:
                    genes_count[gene_type] += 1

        # Count the number of times the characters ‘s’, ‘t’, ‘d’, ‘u’, or ‘p’ appear in the gene name
            artificial_genes_count += sum(gene_id.count(char) for char in ['s', 't', 'd', 'u', 'p'])

        return genes_count, artificial_genes_count
    
    genes_count, artificiel_genes_count = gene_type_count(model)
    total_genes = len(model.genes)



    # Informations générales
    with ui.column().classes("text-lg"):
        ui.label(f"Spontaneous reactions: {genes_count['s']}\n")
        ui.label(f"Transport reactions: {genes_count['t']}\n")
        ui.label(f"Demand reactions: {genes_count['d']}\n")
        ui.label(f"Sink reactions: {genes_count['sk']}\n")
        ui.label(f"Uptake reactions: {genes_count['u']}\n")
        ui.label(f"Production reactions : {genes_count['p']}\n")

 

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

    def get_data_reaction(rxn):
        if isinstance(rxn.annotation, dict):
            return rxn.annotation.get('database')
        return None
    
    def get_sbo_reaction(rxn):
        if isinstance(rxn.annotation, dict):
            return rxn.annotation.get('sbo')
        return None



    # Création du DataFrame
    df = pd.DataFrame({
        'Reaction ID': rReactionID,
        'Name of the reaction': rReactionName,
        'Formula' : rReactionFormula,
        'Lower bound' : rLowerBound,
        'Upper bound' : rUpperBound,
        'Enzyme Commission Number' : rECNumbers,
        'Gene–Protein–Reaction association' : rGPRAssociations,
        'Source of reconstruction' : rSources,
        'Database' : [get_data_reaction(rxn) for rxn in model.reactions],
        'SBO' : [get_sbo_reaction(rxn) for rxn in model.reactions]
        

    })


    # colonne normalisée pour la recherche
    df['name_norm'] = df['Reaction ID'].apply(normalize) #colonne invisible pour la recherche partielle

    # mapping affichage ↔ recherche
    name_map = dict(zip(df['Reaction ID'], df['name_norm']))


    # ---------- UI ----------
    ui.label("   ")
    ui.label("Search Reactions").classes("text-2xl font-bold mb-4")

    results = ui.column().classes('q-gutter-md') #conteneur de résultats



        # ---------- Affichage des réactions sélectionnées ----------
    def show_reactions(selected_names: list[str]):
        results.clear()

        if not selected_names:
            return
        
        # Vérifier que le gène existe dans le DataFrame 
        row_df = df[df['Reaction ID'] == selected_names] 
        if row_df.empty: 
            return # évite l'erreur iloc[0] 

        row = row_df.iloc[0]

        with ui.row().classes('q-gutter-lg'): 
                # ← alignement horizontal

            # CARD1 : Identification et définition
            with ui.card().classes('w-96'):
                ui.label(row['Reaction ID']).classes('text-h6')
                ui.separator()
                ui.label(f"Name of the reaction: {row['Name of the reaction']}")
                ui.label(f"Formula: {row['Formula']}")
            
            # CARD2 : Propriétés associées
            with ui.card().classes('w-96'):
                ui.label("Properties").classes('text-h6')
                ui.separator()
                ui.label(f"Gene–Protein–Reaction association: {row['Gene–Protein–Reaction association']}")
                ui.label(f"Lower bound: {row['Lower bound']}")
                ui.label(f"Upper bound: {row['Upper bound']}")
            
            # CARD3 : Références et interopérabilités
            with ui.card().classes('w-96'):
                ui.label("References and interoperability").classes('text-h6')
                ui.separator()
                ui.label(f"Database: {row['Database'] or 'Not available'}")
                ui.label(f"Enzyme Commission Number: {row['Enzyme Commission Number']}")
                ui.label(f"SBO: {row['SBO'] or 'Not available'}")
                ui.label(f"Source of reconstruction: {row['Source of reconstruction']}")
            
                



    # Select avec autocomplétion avancée 
    select = ui.select(
        options=list(name_map.keys()),
        label='Enter reaction ID',
        multiple=False,
        on_change=lambda e: show_reactions(e.value)
    ).props(
        'use-input clearable input-debounce=300' #Attente de 300 ms avant déclenchement : meilleure performance
    ).classes('w-96')


    # Recherche partielle insensible aux accents
    def filter_options(e):
        query = normalize(e.args or "")
        if not query:
            select.options = list(name_map.keys())
            return

        select.options = [
            name for name, norm in name_map.items()
            if query in norm
        ]

    select.on('filter', filter_options)




