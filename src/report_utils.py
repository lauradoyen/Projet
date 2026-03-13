"""
Utility functions for Sensitivity_analyses.ipynb (Jupyter notebook report).
"""

from datetime import datetime
from IPython.display import display, Markdown
import pandas as pd


def show_df(df, n=10):
    """
    Display the first n rows of a DataFrame with customized display options.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to display.
    n : int, optional
        Number of rows to show (default is 10).
    """
    with pd.option_context(
        "display.max_rows",
        n,
        "display.max_columns",
        None,
        "display.precision",
        3,
        "display.expand_frame_repr",
        False,
    ):
        display(df.head(n))


def print_metabolite_names(model, rxn_ids, label):
    """
    Print metabolite names for a list of reactions from a model.
    (e.g. metabolites of Uptake reactions)

    Parameters
    ----------
    model : cobra.Model
        A metabolic model containing reactions and metabolites.
    rxn_ids : list of str
        List of reaction IDs to retrieve metabolites from.
    label : str
        A label to print before the metabolite list.
    """
    print(f"\n{label}:")
    for rxn_id in rxn_ids:
        rxn = model.reactions.get_by_id(rxn_id)
        mets = [met.name for met in rxn.metabolites]
        print(f"{rxn.id:15s} | {', '.join(mets)}")


def show_report_date():
    """
    Display the current date as a Markdown header.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    display(Markdown(f"### Report generated on: `{date_str}`"))
