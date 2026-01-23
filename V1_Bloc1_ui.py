from nicegui import ui
from collections import Counter
import pandas as pd 


def display(model):

    ui.label("ID card of the model").classes("text-2xl font-bold mb-4")

    def split_metabolite_info(metabolites):
        liste_meta = []
        liste_comp = []
        for metabolite in metabolites:
            id_parts = metabolite.id.split('_')
            name = '_'.join(id_parts[0:-1])
            compartment = id_parts[-1]
            liste_meta.append(name)
            liste_comp.append(compartment)
        return liste_meta, liste_comp

    metabolites = model.metabolites
    liste_meta, liste_comp = split_metabolite_info(metabolites)

    # Compartiments
    Name = list(model.compartments.values())
    Id = list(model.compartments.keys())

    # Nombre de métabolites par compartiment
    Number_of_metabolites = [len([met for met in model.metabolites 
            if met.compartment == comp_id]) for comp_id in Id]

    # Nombre de dead-ends (impliqués dans une seule réaction)
    def find_dead_end_metabolites(model): 
        dead_ends = [] 
        for m in model.metabolites: 
            if len(m.reactions) == 1: 
                dead_ends.append(m.id) 
        return dead_ends
    
    Dead_ends = find_dead_end_metabolites(model) 


    with ui.row().classes("gap-6"): #Visualisation en colonnes

        # Informations générales
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-80"):
            ui.label(f"Number of metabolites: {len(model.metabolites)}")
            ui.label(f"Number of reactions: {len(model.reactions)}")
            ui.label(f"Number of genes: {len(model.genes)}")

        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-80"):
            ui.label(f"Number of compartments: {len(Name)}")
            ui.label("List of compartments:").classes("font-semibold")
            for i in range(len(Name)):
                ui.label(f" * Number of {Name[i]} metabolites: {Number_of_metabolites[i]}") 
            ui.label(f"Number of dead-ends: {len(Dead_ends)}")
        
