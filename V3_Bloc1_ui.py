from nicegui import ui
import pandas as pd
import cobra
import numpy as np
import io
import matplotlib.pyplot as plt
import matplotlib

print(matplotlib.get_backend())

from src.report_utils import *
from src.Sensitivity_to_nutritional_environment import *

import gurobipy as gp
cobra.Configuration().solver = "gurobi"

def display(model):

    # Definition of an exchange reaction
    def is_exchange_reaction(rxn):
        return len(rxn.metabolites) == 1
    
    # Get the unique associated metabolite of the exchange reaction
    def get_associated_metabolite(rxn):
        return list(rxn.metabolites.keys())[0].id
    

    uptake_data = []
    uptake_list=[]

    for rxn in model.reactions: # Collects only the uptake reactions and stores their ID and metabolite
        if not is_exchange_reaction(rxn):
            continue

        if "uptake" not in rxn.id.lower():
            continue

        data = {
            "Reaction ID": rxn.id,
            "Associated metabolite": get_associated_metabolite(rxn),
        }

        
        uptake_list.append(rxn.id)
        uptake_data.append(data)

    # Dataframe which links exchange reaction with its unique metabolite
    df_uptake = pd.DataFrame(uptake_data)

    
    with ui.row().classes("gap-4"):
        # Left column
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-270"):

            ui.label("Select uptakes to analyse").classes("text-xl font-bold")
            # Enables the user to choose the uptake(s) to study
            select_uptakes = ui.select(
                options=uptake_list,
                label="Choose one or more uptakes",
                multiple=True,
                with_input=True
            ).classes("w-96").props('use-chips')

            ui.label("Choose experimental growth rate to display on plots (h⁻¹)").classes("text-xl font-bold")
            # Enables the user to choose the experimental growth rate, default number : 0.20
            experimental_input = ui.number(
            label="Experimental growth rate",
            value=0.20,
            min=0,
            step=0.01,
            format="%.2f"
        ).classes("w-40")

        
            analysis_results = {"df": None, "selected": None}


            async def run_analysis():

                print(">>> ANALYSE START")

                selected = select_uptakes.value # Selected is a list of strings
                if not selected:
                    ui.notify("Select at least one uptake.", color="red") # Inform the user if no uptake is selected
                    return
                
                print("selected:", selected)#
                    
                def worker():
                
                    dfs = []
                    for uptake in selected: # Analyse only on the chosen uptakes


                        df = perform_robustness_analysis( # Performs a robustness analysis on a set of uptake reactions by
                                                          # evaluating the impact of their flux range on the objective function
                            model=model,
                            uptake_rxns=[uptake],
                            obj_rxn="Biomass_rxn",
                            value_ub=20,
                            change_bounds=True,
                            n_points=50
                        )
                        dfs.append(df)

        df = pd.concat(dfs, ignore_index=True)

        analysis_results["df"] = df
        analysis_results["selected"] = selected

        ui.notify("Analysis completed.", color="green")

                ui.notify("Sensitivity analysis completed.", color="green") # Inform the user when the calculation is finished

            # Function to diplay all curves in different graphs
            def single_uptake (): 

        plots_single_container.clear()

        df = analysis_results["df"]
        selected = analysis_results["selected"]

                if df is None:
                    ui.notify("Run the analysis first.", color="red") # Inform the user if the analysis has not run
                    return
                
                with plots_single_container:
                    print("SELECTED:", selected)
            
                    for uptake in selected:

                df_u = df[df["Uptake"] == uptake]

                xlabel = f"{uptake}\n(mmol·gDW⁻¹·h⁻¹)"

                        fig, ax = robustness_analysis_plot( # Plot the relationship between uptake fluxes and growth rate from robustness analysis
                            data=df_u,
                            xlabel=xlabel,
                            ylabel="Growth rate\n(h⁻¹)",
                            filter_uptakes=[uptake],
                            experimental_value=experimental_input.value,
                            point_intersection=True,
                            legend=True
                        )

                        with ui.pyplot() as p:
                            p.fig = fig # Display the graph


            # Function to diplay all curves in one single graph
            def multiple_uptakes (): 

                plots_multi_container.clear() 

        df = analysis_results["df"]
        selected = analysis_results["selected"]

                if df is None:
                    ui.notify("Run the analysis first.", color="red") # Inform the user if the analysis has not run
                    return

        with plots_multi_container:

            ui.label("Select uptake to highlight").classes("text-xl font-bold")

                    select_highlighted_uptake = ui.select( # Enables the user to select the uptake to highlight
                        options=selected,
                        label="Choose one uptake",
                    ).classes("w-96")

            plot_area = ui.column()

            def plot_multiple() : 

                        plot_area.clear()
                    
                        fig, ax = robustness_analysis_plot( # Plot the relationship between uptake fluxes and growth rate from robustness analysis
                            data=df,
                            xlabel="Uptake flux\n(mmol·gDW⁻¹·h⁻¹)",
                            ylabel="Growth rate\n(h⁻¹)",
                            filter_uptakes=selected,
                            highlight=select_highlighted_uptake.value,
                            experimental_value=experimental_input.value,
                            point_intersection=True,
                            legend=True
                        )
                        
                        
                        with ui.pyplot() as p:
                            p.fig = fig # Display the graphs

                    ui.button("Generate plot", on_click=plot_multiple).classes("mt-4 bg-blue-600 text-white") 

            # Button to run the analysis
            ui.button("Run analysis", on_click=run_analysis)
            ui.label("Once you clicked on the button Run analysis please wait until the analysis is completed")

            # Sub-tabs for choosing how to display graphs
            with ui.tabs() as tabs:
                tab1 = ui.tab("One uptake per graph")
                tab2 = ui.tab("Multiple uptakes")

            with ui.tab_panels(tabs):
                with ui.tab_panel(tab1):
                    ui.button("Show graphs", on_click=single_uptake)
                    plots_single_container = ui.column()

                with ui.tab_panel(tab2):
                    ui.button("Prepare plot", on_click=multiple_uptakes)
                    plots_multi_container = ui.column()
    

        # Left column
        with ui.column().classes("bg-gray-100 p-4 rounded-lg shadow-md w-130"):

            ui.label("Uptake ID ⭤  Associated metabolite").classes("text-xl font-bold mt-6")

            # Display the table of the pairs of exchange reaction and associated metabolite
            ui.aggrid({
                "columnDefs": [
                    {"headerName": "Reaction ID", "field": "Reaction ID", "filter": True},
                    {"headerName": "Associated metabolite", "field": "Associated metabolite", "filter": True},
                ],
                "rowData": df_uptake.to_dict("records"),
                "defaultColDef": {
                    "resizable": True,
                    "sortable": True,
                    "floatingFilter": True,
                },
            }).classes("w-full h-96")

            
            
