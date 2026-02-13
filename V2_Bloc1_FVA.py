from nicegui import ui
import pandas as pd
import threading
from cobra.flux_analysis import flux_variability_analysis

# -----------------------------
# Fonction FVA (thread-safe)
# -----------------------------
def run_fva(model, reactions=None, frac=1.0):
    model_copy = model.copy()
    model_copy.solver = "glpk"
    return flux_variability_analysis(
        model_copy,
        reaction_list=reactions,
        fraction_of_optimum=frac
    )

# -----------------------------
# Interface NiceGUI
# -----------------------------
def display(model):

    #ui.label("Flux Variability Analysis (FVA)").classes("text-2xl font-bold")

    reactions = [r.id for r in model.reactions]

    selected_reactions = ui.select(
        options=reactions,
        multiple=True,
        label="Select reactions for FVA (leave empty for all):"
    ).classes("w-96")

    frac_slider = ui.slider(
        min=0.5,
        max=1.0,
        value=1.0,
        step=0.05
    ).classes("w-96")

    #ui.label("Fraction of optimum (tolerance around the objective)").classes("text-sm text-gray-600")

    result_container = ui.column().classes("mt-6")

    # Variables pour le thread
    state = {"thread": None, "result": None, "running": False}

    def start_fva():
        result_container.clear()
        result_container.label("FVA calculation running… please wait").classes("text-blue-600")

        state["running"] = True
        state["result"] = None

        def worker():
            try:
                fva_result = run_fva(
                    model,
                    selected_reactions.value or None,
                    frac_slider.value
                )
                state["result"] = fva_result
            except Exception as e:
                state["result"] = e
            finally:
                state["running"] = False

        state["thread"] = threading.Thread(target=worker)
        state["thread"].start()

    def check_status():
        if state["running"]:
            ui.timer(0.5, check_status, once=True)
        else:
            result_container.clear()

            if isinstance(state["result"], Exception):
                result_container.label(f"FVA failed: {state['result']}").classes("text-red-600")
                return

            fva_df = pd.DataFrame(state["result"])
            fva_df.reset_index(inplace=True)
            fva_df.rename(
                columns={"index": "Reaction", "minimum": "Flux min", "maximum": "Flux max"},
                inplace=True
            )

            result_container.label("FVA results").classes("text-xl font-semibold")
            ui.table.from_pandas(fva_df).classes("w-full")

    ui.button("Run FVA", on_click=lambda: (start_fva(), ui.timer(0.5, check_status, once=True))).classes(
        "mt-4 bg-blue-600 text-white"