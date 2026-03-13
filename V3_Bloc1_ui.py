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
from src.Sensitivity_to_variation_reactant import *

import gurobipy as gp
cobra.Configuration().solver = "gurobi"


def display(model):
    import gurobipy as gp
    cobra.Configuration().solver = "gurobi"

    # Liste des uptakes disponibles
    uptake_list = list(model.medium.keys())

    ui.label("Select uptakes to analyse").classes("text-xl font-bold")

    select_uptakes = ui.select(
        options=uptake_list,
        label="Choose one or more uptakes",
        multiple=True,
        with_input=True
    ).classes("w-96").props('use-chips')

    analysis_results = {"df": None, "selected": None}


    

    
    def run_analysis():

        selected = select_uptakes.value #selected = ['...', '...', ...]

        if not selected:
            ui.notify("Select at least one uptake.", color="red")
            return

        # Analyse uniquement sur les uptakes choisis
        dfs = []
        for uptake in selected:

            df = perform_robustness_analysis(
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

    # Fonctions
    def single_uptake (): 

        plots_single_container.clear()

        df = analysis_results["df"]
        selected = analysis_results["selected"]

        if df is None:
            ui.notify("Run the analysis first.", color="red")
            return
        
        with plots_single_container:
            print("SELECTED:", selected)
    
            for uptake in selected:

                df_u = df[df["Uptake"] == uptake]

                xlabel = f"{uptake}\n(mmol·gDW⁻¹·h⁻¹)"

                fig, ax = robustness_analysis_plot(
                    data=df_u,
                    xlabel=xlabel,
                    ylabel="Growth rate\n(h⁻¹)",
                    filter_uptakes=[uptake],
                    experimental_value=0.20,
                    point_intersection=True,
                    legend=True
                )

                with ui.pyplot() as p:
                    p.fig = fig



    def multiple_uptakes (): 

        plots_multi_container.clear()

        df = analysis_results["df"]
        selected = analysis_results["selected"]

        if df is None:
            ui.notify("Run the analysis first.", color="red")
            return

        with plots_multi_container:

            ui.label("Select uptake to highlight").classes("text-xl font-bold")

            select_highlighted_uptake = ui.select(
                options=selected,
                label="Choose one uptake",
            ).classes("w-96")

            plot_area = ui.column()

            def plot_multiple() : 

                plot_area.clear()
            
                fig, ax = robustness_analysis_plot(
                    data=df,
                    xlabel="Uptake flux\n(mmol·gDW⁻¹·h⁻¹)",
                    ylabel="Growth rate\n(h⁻¹)",
                    filter_uptakes=selected,
                    highlight=select_highlighted_uptake.value,
                    experimental_value=0.20,
                    point_intersection=True,
                    legend=True
                )
                
                
                with ui.pyplot() as p:
                    p.fig = fig
                print("FIG TYPE:", type(fig))

            ui.button("Generate plot", on_click=plot_multiple).classes("mt-4 bg-blue-600 text-white")

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

    ui.button("Run analysis", on_click=run_analysis)
    ui.label("Once you clicked on the button Run analysis please wait until the anaLysis is completed")