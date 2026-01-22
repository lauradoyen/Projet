from nicegui import ui
from collections import Counter


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

    # Informations générales
    with ui.column().classes("text-lg"):
        ui.label(f"The name of the model is: {model.name}")
        ui.label(f"The number of metabolites is: {len(model.metabolites)}")
        ui.label(f"The number of reactions is: {len(model.reactions)}")
        ui.label(f"The number of genes is: {len(model.genes)}")

    # Compartiments
    Name = list(model.compartments.values())
    Id = list(model.compartments.keys())

    with ui.column().classes("mt-4 text-lg"):
        ui.label(f"The two compartments are: {Name[0]} and {Name[1]}")
        ui.label(f"The ID of the compartments are: {Id[0]} and {Id[1]}")
        ui.label(f"The number of compartments is: {len(Name)}")

    # Nombre de métabolites par compartiment
    Number_of_metabolite = [
        len([met for met in model.metabolites if met.compartment == comp_id])
        for comp_id in Id
    ]

    with ui.column().classes("mt-4 text-lg"):
        ui.label(f"The number of cytosolic metabolites is: {Number_of_metabolite[0]}")
        ui.label(f"The number of extracellular metabolites is: {Number_of_metabolite[1]}")

    # Métabolites présents dans les deux compartiments
    Meta_compte = Counter(liste_meta)
    meta_dubls = [meta for meta, count in Meta_compte.items() if count == 2]

    ui.label(f"The number of cytosolic and extracellular metabolites is: {len(meta_dubls)}").classes("mt-4 text-lg")
