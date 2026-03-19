from nicegui import ui
import pandas as pd
import unicodedata 
import re
import csv

def display(model):

    selected_row_df = [] # Initializes the list of selected reactions

    #Information about the reactions
    ui.label("General information about the reactions").classes("text-2xl font-bold mb-4")

    def gene_type_count(model):
    # Initialize gene types
        genes_types = ["Pc", "s", "t", "d", "sk", "u", "p"]

    # Create a dictionary to store the count of genes of each type
        genes_count = {gene_type: 0 for gene_type in genes_types}
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


    # General information
    with ui.column().classes("text-lg"):
        ui.label(f"Spontaneous reactions: {genes_count['s']}\n")
        ui.label(f"Transport reactions: {genes_count['t']}\n")
        ui.label(f"Demand reactions: {genes_count['d']}\n")
        ui.label(f"Sink reactions: {genes_count['sk']}\n")
        ui.label(f"Uptake reactions: {genes_count['u']}\n")
        ui.label(f"Production reactions : {genes_count['p']}\n")

 
    def normalize(text: str) -> str:  
        # Checks that the input is a string.
        if not isinstance(text, str):
            return '' # If it is not, an empty string is returned to avoid errors.
        return ''.join( #Normalizes the text by removing accents and converting it to lowercase
            c for c in unicodedata.normalize('NFD', text) # Decomposes accented characters , ex : é → e + ´
            if unicodedata.category(c) != 'Mn' # Removes accents
        ).lower() # Converts all text to lowercase
    
    
    # Retrieve information about the reactions
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
            Sources.append(reaction.notes.get('CATEGORIES', 'N/A'))

        return ReactionID, ReactionName, ReactionFormula,LowerBound, UpperBound, ECNumbers,GPRAssociations, Sources

    rReactionID, rReactionName, rReactionFormula, rLowerBound, rUpperBound, rECNumbers, rGPRAssociations, rSources = reactionInfos(model)


    # Retrieve database information
    def get_data_reaction(rxn):
        if isinstance(rxn.annotation, dict):
            return rxn.annotation.get('database')
        return None
    
    # Retrieve SBO annotation
    def get_sbo_reaction(rxn):
        if isinstance(rxn.annotation, dict):
            return rxn.annotation.get('sbo')
        return None


    # DataFrame containing reaction information
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


    # Normalized column for the research by ID
    df['name_norm'] = df['Reaction ID'].apply(normalize) #colonne invisible pour la recherche partielle

    # mapping display ↔ search
    name_map = dict(zip(df['Reaction ID'], df['name_norm']))


    ui.separator()
    ui.label("Search Reactions").classes("text-2xl font-bold mb-4")

    results = ui.column().classes('q-gutter-md')



    # Display of information cards for the selected reactions 
    def show_reactions(selected_names: list[str]):
        results.clear()

        if not selected_names:
            return
        
        # Retrieve the reaction row from the DataFrame
        row_df = df[df['Reaction ID'] == selected_names] 
        if row_df.empty: 
            return #

        row = row_df.iloc[0]

        selected_row_df.append(row_df) # Update of the list of selected reactions

        with ui.row().classes('q-gutter-lg'): 

            # CARD1 : Identification
            with ui.card().classes('w-96'):
                ui.label(row['Reaction ID']).classes('text-h6')
                ui.separator()
                ui.label(f"Name of the reaction: {row['Name of the reaction']}")
                ui.label(f"Formula: {row['Formula']}")
            
            # CARD2 : Properties
            with ui.card().classes('w-96'):
                ui.label("Properties").classes('text-h6')
                ui.separator()
                ui.label(f"Gene–Protein–Reaction association: {row['Gene–Protein–Reaction association']}")
                ui.label(f"Lower bound: {row['Lower bound']}")
                ui.label(f"Upper bound: {row['Upper bound']}")
            
            # CARD3 : References
            with ui.card().classes('w-96'):
                ui.label("References and interoperability").classes('text-h6')
                ui.separator()
                ui.label(f"Database: {row['Database'] or 'Not available'}")
                ui.label(f"Enzyme Commission Number: {row['Enzyme Commission Number']}")
                ui.label(f"SBO: {row['SBO'] or 'Not available'}")
                ui.label(f"Source of reconstruction: {row['Source of reconstruction']}")
            
    # Function to export results to CSV            
    def export_infos_reaction_csv(): 
        if len(selected_row_df)==0: 
            ui.notify("No Metabolite selected") 
            return
        

        filename = "info_reaction.csv" 
        with open(filename, "w", newline="", encoding="utf-8") as file: 
            writer = csv.writer(file) 
            
            writer.writerow([ "Reaction ID", "Name of the reaction", "Formula", "Lower bound", "Upper bound", "Enzyme Commission Number", "Gene–Protein–Reaction association", "Source of reconstruction", "Database", "SBO" ]) 
            
            for row_df in selected_row_df:
                row = row_df.iloc[0]
                writer.writerow([ row["Reaction ID"], row["Name of the reaction"], row["Formula"], row["Lower bound"], row["Upper bound"], row["Enzyme Commission Number"], row["Gene–Protein–Reaction association"], row["Source of reconstruction"], row["Database"], row["SBO"] ]) 
        ui.download(filename)

    # Function to export results to JSON
    def export_infos_reaction_json(): 
        if len(selected_row_df)==0: 
            ui.notify("No Reaction selected") 
            return 
        
        row_df = selected_row_df[-1] 
            
        row = row_df.iloc[0] 
        data = { "Reaction ID": row["Reaction ID"], 
                "Name of the reaction": row["Name of the reaction"], 
                "Formula": row["Formula"], 
                "Lower bound": row["Lower bound"], 
                "Upper bound": row["Upper bound"], 
                "Enzyme Commission Number": row["Enzyme Commission Number"], 
                "Gene–Protein–Reaction association": row["Gene–Protein–Reaction association"], 
                "Source of reconstruction": row["Source of reconstruction"], 
                "Database": row["Database"], "SBO": row["SBO"], } 
        
        json_str = pd.Series(data).to_json(indent=4, force_ascii=False) 
        filename = "info_reaction.json" 
        with open(filename, "w", encoding="utf-8") as f: 
            f.write(json_str) 
        ui.download(filename)


    # Select component with advanced autocomplete
    select = ui.select(
        options=list(name_map.keys()), # List of displayed options
        label='Enter reaction ID',
        multiple=False, # Only one reaction can be selected
        on_change=lambda e: show_reactions(e.value)
    ).props(
        'use-input clearable input-debounce=300' # Enables typing in the field, allows clearing,
                                                # and waits 300 ms before triggering input events
    ).classes('w-96')


    # Accent-insensitive partial search
    def filter_options(e):
        query = normalize(e.args or "") # Normalize the user input
        
        # If the search field is empty, show all options
        if not query:
            select.options = list(name_map.keys())
            return

        select.options = [
            name for name, norm in name_map.items()
            if query in norm
        ]

    select.on('filter', filter_options)

    # Buttons to exports results
    with ui.dropdown_button('Export Reaction(s) Information', auto_close=True):
        ui.item('.CSV', on_click=export_infos_reaction_csv).classes("mt-4 bg-blue-600 text-white")
        ui.item('.JSON', on_click=export_infos_reaction_json).classes("mt-4 bg-blue-600 text-white")


def get_reaction_type(model, reaction_id):
    """Retourne le type de réaction (sink, transport, demand, sk, uptake, production)"""

    reaction = model.reactions.get_by_id(reaction_id)

    # Concatène les IDs des gènes associés
    gene_id = "".join([g.id.replace("gp_", "") for g in reaction.genes]).lower()

    # Dictionnaire de correspondance
    mapping = {
        "s": "sink",
        "t": "transport",
        "d": "demand",
        "sk": "sk",
        "u": "uptake",
        "p": "production",
    }

    # On teste d'abord les types longs (sk)
    if "sk" in gene_id:
        return "sk"

    # Puis les types simples
    for key, label in mapping.items():
        if key in gene_id:
            return label

    return ""






