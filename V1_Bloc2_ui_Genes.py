from nicegui import ui
import pandas as pd
import unicodedata 
import csv

def display(model):

    selected_row_df = [] # Initializes the list of selected genes

    
    # Information about genes
    ui.label("General information about the genes").classes("text-2xl font-bold mb-4")

    def gene_type_count(model):
    # Initialize gene types
        genes_types = ["Pc", "s", "t", "d", "sk", "u", "p"]

    # Create a dictionary to store the count of genes of each type
        genes_count = {gene_type: 0 for gene_type in genes_types}
        # creation of : {'Pc': 0, 's': 0, 't': 0, 'd': 0, 'sk': 0, 'u': 0, 'p': 0}
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
    
    # Get the SBO terms for each gene
    def collect_sbo_terms(model, sbo_terms):
        for gene in model.genes:
            sbo_info = gene.annotation.get('sbo', '').replace('SBO:', '')
            if sbo_info in sbo_terms:
                sbo_terms[sbo_info].append(gene.id)
        return sbo_terms

    sbo_terms = {sbo: [] for sbo in ["0000243", "0000291"]}
    #0000243 : genes
    #0000291 : empty set 
    

    sbo_terms = collect_sbo_terms(model, sbo_terms)


    
    genes_count, artificiel_genes_count = gene_type_count(model)
    total_genes = len(model.genes)

    # General information
    with ui.column().classes("text-lg"):
        ui.label(f"Total genes number in the model: {total_genes}\n\n")
        ui.label(f"Artificial genes number: {artificiel_genes_count}\n\n")
    

    with ui.column().classes("text-lg"):
        for sbo, reactions in sbo_terms.items():
            ui.label(f"{len(reactions)} reactions are annotated with SBO:{sbo}")
        ui.label(f"SBO : 0000243 : genes, SBO : 0000291 : empty set ")
        
    
    ui.separator()
        

        
    # Seach bar for the genes
    ui.label("Search Genes").classes("text-2xl font-bold mb-4")

    def normalize(text: str) -> str:  
        # Checks that the input is a string.
        if not isinstance(text, str):
            return '' # If it is not, an empty string is returned to avoid errors.
        return ''.join( #Normalizes the text by removing accents and converting it to lowercase
            c for c in unicodedata.normalize('NFD', text) # Decomposes accented characters , ex : é → e + ´
            if unicodedata.category(c) != 'Mn' # Removes accents
        ).lower() # Converts all text to lowercase
    
    data = []

    for gene in model.genes:
        data.append({
            'Gene ID': gene.id,
            'DeepLoc': gene.notes.get('DeepLoc'),
            'TMHMM': gene.notes.get('TMHMM'),
            'SignalP': gene.notes.get('SignalP'),
            'Reactions': [r.id for r in gene.reactions],
            'Count Reactions': len(gene.reactions),
            'SBO': gene.annotation.get('sbo'),
            'ncbigene': gene.annotation.get('ncbigene'),
            'ncbiprotein': gene.annotation.get('ncbiprotein'),
            'kegg.genes': gene.annotation.get('kegg.genes'),
            'uniprot': gene.annotation.get('uniprot'),
            'refseq': gene.annotation.get('refseq')
        })

    df = pd.DataFrame(data) # Dataframe which contains all key information about the gene

    # Normalized column for the research
    df['name_norm'] = df['Gene ID'].apply(normalize)

    # mapping dsiplay ↔ search
    name_map = dict(zip(df['Gene ID'], df['name_norm']))


    ui.label("Recherche de gènes").classes('text-h5') 

    results = ui.column().classes('q-gutter-md') # Results container


    # Display of information cards for the selected genes 
    def show_genes(selected_names: list[str]):
        results.clear()

        if not selected_names:
            return
 

        # Verify of the presence of the gene in the DataFrame
        row_df = df[df['Gene ID'] == selected_names] 
        if row_df.empty: 
            return
        
        row = row_df.iloc[0]

        selected_row_df.append(row_df) # Update of the list of the selected genes


        with ui.row().classes('q-gutter-lg'): 

            # CARD1 : General information
            with ui.card().classes('w-96'):
                ui.label(f"{row['Gene ID']}").classes('text-h6')
                ui.separator()
                ui.label(f"Annotation :").classes('font-semibold')
                ui.label(f"ncbigene : {row['ncbigene']}")
                ui.label(f"kegg.genes : {row['kegg.genes']}")
                ui.separator()
                ui.label(f"SBO : {row['SBO']}")
                ui.label(f"refseq : {row['refseq']}")
            
            #CARD2 : Gene product
            with ui.card().classes('w-96'):
                ui.label("Gene product").classes('text-h6')
                ui.separator()
                ui.label(f"ncbiprotein : {row['ncbiprotein']}")
                ui.label(f"uniprot : {row['uniprot']}")
                ui.separator()
                ui.label(f"DeepLoc : {row['DeepLoc']}") 
                ui.label(f"TMHMM : {row['TMHMM']}") 
                ui.label(f"SignalP : {row['SignalP']}") 

            #CARD 3 : Context in the metabolites network
            with ui.card().classes('w-96'):
                ui.label(" Context in the metabolic network").classes('text-h6')
                ui.separator()
                ui.label(f"Number of associated reactions : {row['Count Reactions']}")
                ui.label("List of associated reactions:")
                with ui.row():
                    with ui.scroll_area().classes('w-64 h-50 border'):
                        for reaction in row['Reactions']:
                            ui.label(reaction)
            
    # Function to export results to CSV  
    def export_infos_gene_csv():

        if len(selected_row_df)==0: 
            ui.notify("No Gene selected") # Inform the user of the absence of selected gene  
            return
            
        filename = "info_gene.csv"
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow(["Gene ID", "ncbigene", "kegg.genes", "SBO", "refseq", "ncbiprotein", "uniprot", "DeepLoc", "TMHMM", "SignalP", "Number of associated reactions", "List of associated reactions" ])

            for row_df in selected_row_df:
                row = row_df.iloc[0]
                writer.writerow([row["Gene ID"], row["ncbigene"], row["kegg.genes"], row ["SBO"], row ["refseq"], row ["ncbiprotein"], row ["uniprot"], row ["DeepLoc"], row ["TMHMM"],  row ["SignalP"], row ["Count Reactions"], row ["Reactions"]])

        ui.download(filename)

    # Function to export results to JSON
    def export_infos_gene_json(): 
        if len(selected_rows_df)==0 : 
            ui.notify("No Gene Selected") 
            return 
        
        row_df = selected_row_df[-1] 
        row = row_df.iloc[0] 
        
        data = { "Gene ID": row["Gene ID"], 
                "ncbigene": row["ncbigene"], 
                "kegg.genes": row["kegg.genes"], 
                "SBO": row["SBO"], "refseq": row["refseq"], 
                "ncbiprotein": row["ncbiprotein"], 
                "uniprot": row["uniprot"], 
                "DeepLoc": row["DeepLoc"], 
                "TMHMM": row["TMHMM"], 
                "SignalP": row["SignalP"], 
                "Number of associated reactions": row["Count Reactions"], 
                "List of associated reactions": row["Reactions"], } 
        
        json_str = pd.Series(data).to_json(indent=4, force_ascii=False) 
        filename = "info_gene.json" 
        with open(filename, "w", encoding="utf-8") as f: 
            f.write(json_str) 

        ui.download(filename)
    
            

    # Select component with advanced autocomplete
    select = ui.select(
        options=list(name_map.keys()),  # List of available gene IDs (displayed options)
        label='Enter gene ID',   
        multiple=False, # Only one gene can be selected              
        on_change=lambda e: show_genes(e.value) 
    ).props(
        'use-input clearable input-debounce=300' # Enables typing in the field, allows clearing,
                                                # and waits 300 ms before triggering input events
    ).classes('w-96') 

    # Accent-insensitive partial search
    def filter_options(e):
        query = normalize(e.args or "")  # Normalize the user input

        # If the search field is empty, show all options
        if not query:
            select.options = list(name_map.keys())
            return

        # Filter gene names: keep those where the normalized query
        # appears inside the normalized gene name
        select.options = [
            name for name, norm in name_map.items()
            if query in norm
        ]

    select.on('filter', filter_options)

    # Buttons to exports results
    with ui.dropdown_button('Export Gene(s) Information', auto_close=True):
        ui.item('.CSV', on_click=export_infos_gene_csv).classes("mt-4 bg-blue-600 text-white")
        ui.item('.JSON', on_click=export_infos_gene_json).classes("mt-4 bg-blue-600 text-white")