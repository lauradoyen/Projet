from nicegui import ui
import pandas as pd
import unicodedata #permet de faire une recherche sans se préoccuper des accents
import csv

def display(model):

    selected_row_df = [] #initalise la liste de gènes sélectionnés

    
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


    # Affichage des gènes sélectionnés 
    def show_genes(selected_names: list[str]):
        results.clear()

        if not selected_names:
            return
 

        # Vérifier que le gène existe dans le DataFrame 
        row_df = df[df['Gene ID'] == selected_names] 
        if row_df.empty: 
            return # évite l'erreur iloc[0] 
        
        row = row_df.iloc[0]

        selected_row_df.append(row_df) #màj de la liste de gènes sélectionnés


        with ui.row().classes('q-gutter-lg'): 
            # ← alignement horizontal

            # CARD1 : Infos générales
            with ui.card().classes('w-96'):
                ui.label(f"{row['Gene ID']}").classes('text-h6')
                ui.separator()
                ui.label(f"Annotation :").classes('font-semibold')
                ui.label(f"ncbigene : {row['ncbigene']}")
                ui.label(f"kegg.genes : {row['kegg.genes']}")
                ui.separator()
                ui.label(f"SBO : {row['SBO']}")
                ui.label(f"refseq : {row['refseq']}")
            
            #CARD2 : Produit génique
            with ui.card().classes('w-96'):
                ui.label("Gene product").classes('text-h6')
                ui.separator()
                ui.label(f"ncbiprotein : {row['ncbiprotein']}")
                ui.label(f"uniprot : {row['uniprot']}")
                ui.separator()
                ui.label(f"DeepLoc : {row['DeepLoc']}") 
                ui.label(f"TMHMM : {row['TMHMM']}") 
                ui.label(f"SignalP : {row['SignalP']}") 

            #CARD 3 : Contexte dans le réseau métabolique
            with ui.card().classes('w-96'):
                ui.label(" Context in the metabolic network").classes('text-h6')
                ui.separator()
                ui.label(f"Number of associated reactions : {row['Count Reactions']}")
                ui.label("List of associated reactions:")
                with ui.row():
                    with ui.scroll_area().classes('w-64 h-50 border'):
                        for reaction in row['Reactions']:
                            ui.label(reaction)
            
    #export csv   
    def export_infos_gene_csv():

        if len(selected_row_df)==0: 
            ui.notify("No Gene selected") 
            return
            
        filename = "info_gene.csv"
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # En‑têtes
            writer.writerow(["Gene ID", "ncbigene", "kegg.genes", "SBO", "refseq", "ncbiprotein", "uniprot", "DeepLoc", "TMHMM", "SignalP", "Number of associated reactions", "List of associated reactions" ])

            # Infos
            for row_df in selected_row_df:
                row = row_df.iloc[0]
                writer.writerow([row["Gene ID"], row["ncbigene"], row["kegg.genes"], row ["SBO"], row ["refseq"], row ["ncbiprotein"], row ["uniprot"], row ["DeepLoc"], row ["TMHMM"],  row ["SignalP"], row ["Count Reactions"], row ["Reactions"]])

        ui.download(filename)

    #export json
    def export_infos_gene_json(): 
        if len(selected_rows_df)==0 : 
            ui.notify("No Gene Selected") 
            return 
        
        row_df = selected_row_df[-1] 
        row = row_df.iloc[0] 
        
        # Construire un dictionnaire propre 
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
        
        # Convertir en JSON formaté 
        json_str = pd.Series(data).to_json(indent=4, force_ascii=False) 
        filename = "info_gene.json" 
        with open(filename, "w", encoding="utf-8") as f: 
            f.write(json_str) 

        ui.download(filename)
    
            


    # Select avec autocomplétion avancée 
    select = ui.select(
        options=list(name_map.keys()),
        label='Enter gene ID',
        multiple=False,
        on_change=lambda e: show_genes(e.value)
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

    with ui.dropdown_button('Export Gene(s) Information', auto_close=True):
        ui.item('.CSV', on_click=export_infos_gene_csv).classes("mt-4 bg-blue-600 text-white")
        ui.item('.JSON', on_click=export_infos_gene_json).classes("mt-4 bg-blue-600 text-white")