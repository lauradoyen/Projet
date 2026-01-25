from nicegui import ui
import pandas as pd


def display(model):
    def is_exchange_reaction(rxn):
    # Une réaction d’échange a un seul métabolite
        return len(rxn.metabolites) == 1


    def reaction_nature(rxn):
        if rxn.lower_bound < 0 and rxn.upper_bound == 0:
            return "Uptake"
        elif rxn.lower_bound == 0 and rxn.upper_bound > 0:
            return "Production"
        elif rxn.lower_bound < 0 and rxn.upper_bound > 0:
            return "Uptake & Production"
        else:
            return "Blocked"


    def get_associated_metabolite(rxn):
        # unique métabolite de la réaction d’échange
        return list(rxn.metabolites.keys())[0].id

    exchange_data = []

    for rxn in model.reactions:
        if not is_exchange_reaction(rxn):
            continue

        exchange_data.append({
            'Reaction ID': rxn.id,
            'Nature': reaction_nature(rxn),
            'Associated metabolite': get_associated_metabolite(rxn),
            'Lower bound': rxn.lower_bound,
            'Upper bound': rxn.upper_bound,
        })

    df_exchange = pd.DataFrame(exchange_data)

    ui.separator()
    ui.label("Exchange reactions (uptake & production)").classes("text-2xl font-bold mb-4")

    ui.aggrid({
        "columnDefs": [
            {"headerName": "Reaction ID", "field": "Reaction ID", "filter": True},
            {"headerName": "Nature", "field": "Nature", "filter": True},
            {"headerName": "Associated metabolite", "field": "Associated metabolite", "filter": True},
            {"headerName": "Lower bound", "field": "Lower bound"},
            {"headerName": "Upper bound", "field": "Upper bound"},
        ],
        "rowData": df_exchange.to_dict("records"),
        "defaultColDef": {
            "resizable": True,
            "sortable": True,
            "floatingFilter": True,
        },
    }).classes("w-full h-96")