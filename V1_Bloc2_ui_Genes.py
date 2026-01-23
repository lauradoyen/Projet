from nicegui import ui
import pandas as pd
import cobra
import cobra.util

def display(model):

    ui.label("ID card of the model").classes("text-2xl font-bold mb-4")

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
  
