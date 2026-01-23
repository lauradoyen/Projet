from nicegui import ui
import pandas as pd
import unicodedata #permet de faire une recherche sans se préoccuper des accents

def display(model):

    
    #INFO GENE
    ui.label("General information about the genes").classes("text-2xl font-bold mb-4")

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

    # Informations générales
    with ui.column().classes("text-lg"):
        ui.label(f"Total Genes number in the model: {total_genes}\n\n")
        ui.label(f"Artificial genes number: {artificiel_genes_count}\n\n")
        ui.label(f"Spontaneous reactions: {genes_count['s']}\n")
        ui.label(f"Transport reactions: {genes_count['t']}\n")
        ui.label(f"Demand reactions: {genes_count['d']}\n")
        ui.label(f"Sink reactions: {genes_count['sk']}\n")
        ui.label(f"Uptake reactions: {genes_count['u']}\n")
        ui.label(f"Production reactions : {genes_count['p']}\n")

    

    # Extraction of reactions and associated identifiers
    NCBI_genes = [rxn.annotation['ncbigene'] for rxn in model.genes if 'ncbigene' in rxn.annotation]
    KEGG_genes = [rxn.annotation['kegg.genes'] for rxn in model.genes if 'kegg.genes' in rxn.annotation]

    NCBI_protein = [rxn.annotation['ncbiprotein'] for rxn in model.genes if 'ncbiprotein' in rxn.annotation]
    UNIPROT = [rxn.annotation['uniprot'] for rxn in model.genes if 'uniprot' in rxn.annotation]

    # List of databases
    Database = ["NCBI_genes", 'KEGG_genes','NCBI_protein','UNIPROT']

    # Calculation of the number of annotations for each database
    Number_of_annotations = [len(db) for db in Database]

    # Display of results
    with ui.column().classes("text-lg"):
        ui.label(f"Genes :")
        ui.label(f"    {Number_of_annotations[0]} genes have a NCBI annotation of the form : {NCBI_genes[0]}")
        ui.label(f"    {Number_of_annotations[1]} genes have a KEGG annotation of the form : {KEGG_genes[0]}")

    with ui.column().classes("text-lg"):
        ui.label(f"\nGenes Products :")
        ui.label(f"    {Number_of_annotations[2]} gene products have a NCBI annotation of the form : {NCBI_protein[0]}")
        ui.label(f"    {Number_of_annotations[3]} gene products have a UNIPROT annotation of the form : {UNIPROT[0]}")

    with ui.column().classes("text-lg"):
        for sbo, reactions in sbo_terms.items():
            ui.label(f"{len(reactions)} reactions are annotated with SBO:{sbo}")
        ui.label(f"SBO : 0000243 : genes, SBO : 0000291 : empty set ")
        
    
    ui.label("   ")
        

        
    #RECHERCHES D'INFOS SUR LES GENES
    ui.label("Search Genes").classes("text-2xl font-bold mb-4")

    #MODIIFFFFFFFFF
    def normalize(text: str) -> str:   #fonction clé pour la recherche
        if not isinstance(text, str):
            return '' #sécurité
        return ''.join(
            c for c in unicodedata.normalize('NFD', text) #décompose les caractères accentués , ex : é → e + ´
            if unicodedata.category(c) != 'Mn' #supprime les accents
        ).lower()
    
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

    df = pd.DataFrame(data)

    # colonne normalisée pour la recherche
    df['name_norm'] = df['Gene ID'].apply(normalize) #colonne invisible pour la recherche partielle

    # mapping affichage ↔ recherche
    name_map = dict(zip(df['Gene ID'], df['name_norm']))


    # ---------- UI ----------
    ui.label("Recherche de gènes").classes('text-h5') 

    results = ui.column().classes('q-gutter-md') #conteneur de résultats


    # ---------- Affichage des gènes sélectionnés ----------
    def show_genes(selected_names: list[str]):
        results.clear()

        if not selected_names:
            return

        for name in selected_names:
            row = df[df['Gene ID'] == name].iloc[0]

            with ui.card().classes('w_96'):
                ui.label(f" {row['Gene ID']}").classes('text-h6')
                ui.separator()
                ui.label(f"DeepLoc : {row['DeepLoc']}") 
                ui.label(f"TMHMM : {row['TMHMM']}") 
                ui.label(f"SignalP : {row['SignalP']}") 
                ui.separator()
                ui.label(f"Number of associated reactions : {row['Count Reactions']}")
                ui.label("List of associated reactions:")
                with ui.row():
                    with ui.scroll_area().classes('w-32 h-32 border'):
                        for reaction in row['Reactions']:
                            ui.label(reaction)
                ui.separator()
                ui.label(f"SBO : {row['SBO']}")
                ui.label(f"ncbigene : {row['ncbigene']}")
                ui.label(f"ncbiprotein : {row['ncbiprotein']}")
                ui.label(f"kegg.genes : {row['kegg.genes']}")
                ui.label(f"uniprot : {row['uniprot']}")
                ui.label(f"refseq : {row['refseq']}")



    # ---------- Select avec autocomplétion avancée ----------
    select = ui.select(
        options=list(name_map.keys()),
        label='Rechercher un ou plusieurs gènes',
        multiple=True,
        on_change=lambda e: show_genes(e.value)
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

