# Standard library
import io
import re
import contextlib
from copy import deepcopy
from typing import List, Tuple, Optional

# Third-party
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


# COBRApy
from cobra import Model
from cobra.flux_analysis import flux_variability_analysis


def sensitivities_variation_reactant_fba(
    model: Model,
    p: float = 0.5,
    reaction_id: str = None,
    verbose: bool = False,
    exclude_metabolites: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Performs local sensitivity analysis by perturbing the stoichiometric
    oefficients of reactant metabolites in a given reaction. For each
    metabolite, the function perturbs the coefficient by ±p and evaluates
    the impact on the objective function using Flux Balance Analysis (FBA).

    Parameters
    ----------
    model: cobra.Model
        COBRApy metabolic model.

    p: float, optional (default 0.5)
        Proportional change to apply to stoichiometric coefficients
        (e.g. 0.5 for ±50%).

    reaction_id: str
        ID of the reaction to perturb.

    verbose: bool, optional (default False)
        If True, display results to the console.

    exclude_metabolites: list of str, optional
        List of metabolite IDs to exclude from the analysis.

    Returns
    -------
    pd.DataFrame
        DataFrame with the following columns:
        - 'Reaction' : Reaction ID
        - 'Precursor' : Metabolite ID
        - 'FBA_result_decrease' : Growth rate after decreasing coefficient
        - 'FBA_result_increase' : Growth rate after increasing coefficient
    """

    if (
        reaction_id is None
        or reaction_id not in [rxn.id for rxn in model.reactions]
    ):
        raise ValueError(
            f"Reaction ID '{reaction_id}' not found in the model."
        )

    if exclude_metabolites is None:
        exclude_metabolites = []

    reaction = model.reactions.get_by_id(reaction_id)

    # Filter for reactants only (negative stoichiometry)
    reactants = [
        met
        for met, coeff in reaction.metabolites.items()
        if coeff < 0 and met.id not in exclude_metabolites
    ]

    results = []

    for met in reactants:
        met_id = met.id
        original_coeff = reaction.get_coefficient(met)

        # Temporary modification – decrease
        reaction.add_metabolites({met: -p * original_coeff})
        try:
            sol_dec = model.optimize()
            growth_dec = (
                sol_dec.objective_value if sol_dec.status == "optimal" else -1
            )
        finally:
            # Restore original
            reaction.add_metabolites({met: +p * original_coeff})

        # Temporary modification – increase
        reaction.add_metabolites({met: +p * original_coeff})
        try:
            sol_inc = model.optimize()
            growth_inc = (
                sol_inc.objective_value if sol_inc.status == "optimal" else -1
            )
        finally:
            # Restore original
            reaction.add_metabolites({met: -p * original_coeff})

        results.append([reaction_id, met_id, growth_dec, growth_inc])

        if verbose:
            print(f"\nPrecursor: {met_id}")
            print(f"  ↓ Coeff – Growth rate: {growth_dec:.5f}")
            print(f"  ↑ Coeff – Growth rate: {growth_inc:.5f}\n")

    df = pd.DataFrame(
        results,
        columns=[
            "Reaction", "Precursor",
            "FBA_result_decrease", "FBA_result_increase"],
    )

    return df


def sensitivities_variation_reactant_fva(
    model: Model,
    biomass_rxn_id: str,
    production_rxn_ids: List[str],
    p: float,
    exclude_metabolites: Optional[List[str]] = None,
    verbose: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform FVA before and after perturbing biomass reaction reactants
    to assess local sensitivity on production flux ranges.

    Parameters
    ----------
    model: cobra.Model
        COBRApy metabolic model

    biomass_rxn_id: str
        Biomass reaction ID

    production_rxn_ids : list of str
        List of production reaction IDs to analyse

    p: float
        Proportional change to apply to biomass reactant coefficients

    exclude_metabolites: list of str, optional (default None)
       Metabolite IDs to exclude from perturbation.

    verbose: bool, optional (default False)
        If True, display results to the console.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        - fva_reference: FVA result on the original model.
        - fva_sensitivity: FVA after perturbing biomass reaction coefficients.
    """

    if exclude_metabolites is None:
        exclude_metabolites = []

    # Compute reference FVA (no perturbation)
    fva_reference = get_fva_reference(model, production_rxn_ids, verbose)

    # Compute FVA under perturbation of biomass reaction
    fva_sensitivity = compute_fva_sensitivities(
        model=model,
        rxn_ids=production_rxn_ids,
        biomass_rxn_id=biomass_rxn_id,
        p=p,
        exclude_metabolites=exclude_metabolites,
        verbose=verbose,
    )

    return fva_reference, fva_sensitivity


def get_fva_reference(
    model: Model, rxn_ids: List[str], verbose: bool = False
) -> pd.DataFrame:
    """
    Compute FVA ranges for a set of reactions on the unperturbed model.

    Parameters
    ----------
    model : cobra.Model
        COBRApy metabolic model.

    rxn_ids : list of str
        List of reaction IDs to analyse.

    verbose : bool, optional
        If True, print computed bounds.

    Returns
    -------
    pd.DataFrame
        DataFrame with reaction ID, minimum and maximum flux values.
        Columns: ['Production', 'FVA_min', 'FVA_max']
    """

    data = []

    for rxn_id in rxn_ids:
        fva = flux_variability_analysis(
            model, reaction_list=[rxn_id], fraction_of_optimum=0.8
        )
        row = fva.loc[rxn_id]
        data.append([rxn_id, row["minimum"], row["maximum"]])

        if verbose:
            print(
                f"{rxn_id}: min = {row['minimum']:.4f},"
                f"max = {row['maximum']:.4f}")

    return pd.DataFrame(data, columns=["Production", "FVA_min", "FVA_max"])


def compute_fva_sensitivities(
    model: Model,
    rxn_ids: List[str],
    biomass_rxn_id: str,
    p: float,
    exclude_metabolites: Optional[List[str]] = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Compute FVA changes resulting from perturbations of biomass reactant
    coefficients. For each metabolite in the biomass reaction (excluding
    those in `exclude_metabolites`), the function perturbs its stoichiometric
    coefficient by ±p and evaluates the impact on the FVA range of each
    production reaction.

    Parameters
    ----------

    model: cobra.Model
        COBRApy metabolic model.

    rxn_ids: list of str
        List of reaction IDs to analyse.

    biomass_rxn_id: str
        Biomass reaction ID

    p: float
        Proportional change to apply to biomass reactant coefficients

    exclude_metabolites: list of str, optional (default None)
       Metabolite IDs to exclude from perturbation.

    verbose: bool, optional (default False)
        If True, display results to the console.

    Returns
    -------
    pd.DataFrame
        DataFrame with perturbed FVA results:
        ['Production', 'Precursor', 'FVA_min_decrease', 'FVA_max_decrease',
         'FVA_min_increase', 'FVA_max_increase']
    """

    if biomass_rxn_id not in model.reactions:
        raise ValueError(
            f"Biomass reaction ID '{biomass_rxn_id}' not found in the model."
        )

    biomass_rxn = model.reactions.get_by_id(biomass_rxn_id)

    reactants = [
        met
        for met, coeff in biomass_rxn.metabolites.items()
        if coeff < 0 and met.id not in exclude_metabolites
    ]

    results = []

    for rxn_id in rxn_ids:
        for met in reactants:
            coeff = biomass_rxn.get_coefficient(met)

            # ↓ Decrease coefficient
            biomass_rxn.add_metabolites({met: -p * coeff})
            fva_dec = flux_variability_analysis(
                model, reaction_list=[rxn_id], fraction_of_optimum=0.8
            )
            biomass_rxn.add_metabolites({met: +p * coeff})  # restore

            # ↑ Increase coefficient
            biomass_rxn.add_metabolites({met: +p * coeff})
            fva_inc = flux_variability_analysis(
                model, reaction_list=[rxn_id], fraction_of_optimum=0.8
            )
            biomass_rxn.add_metabolites({met: -p * coeff})  # restore

            min_dec, max_dec = fva_dec.loc[rxn_id][["minimum", "maximum"]]
            min_inc, max_inc = fva_inc.loc[rxn_id][["minimum", "maximum"]]

            results.append([
                rxn_id, met.id,
                min_dec, max_dec,
                min_inc, max_inc
            ])

            if verbose:
                print(
                    f"{rxn_id} | {met.id} → ↓ max: {max_dec:.4f} | "
                    f"↑ max: {max_inc:.4f}"
                )

    return pd.DataFrame(
        results,
        columns=[
            "Production",
            "Precursor",
            "FVA_min_decrease",
            "FVA_max_decrease",
            "FVA_min_increase",
            "FVA_max_increase",
        ],
    )


def variations_precursors_plot(
    df: pd.DataFrame,
    reaction: str,
    xlabel: str = "Growth rate (h⁻¹)",
    ylabel: str = "",
    value_ref: Optional[float] = None,
    min_colour: str = "#99590b",
    max_colour: str = "#20463e",
    tolerance: float = 1e-8,
    save_png: Optional[str] = None,
    save_svg: Optional[str] = None,
) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    """
    Visualise precursor variation intervals using horizontal gradient
    segments. For each precursor, this function plots the sensitivity
    nterval between decrease and increase perturbation results. Gradient
    colour segments indicate the range of response, sorted by amplitude.

    Parameters
    ----------
    df: pd.DataFrame
        Data containing results for a specific reaction, with columns:
        - 'Precursor'
        - Either 'FBA_result_decrease'/'FBA_result_increase' or
          'FVA_max_decrease'/'FVA_max_increase'

    reaction: str
        Reaction ID to filter and plot.

    xlabel: str, optional (default: "Growth rate (h⁻¹)")
        Label for the x-axis .

    ylabel: str, optional (default: empty)
        Label for the y-axis.

    value_ref: float, optional
        Reference vertical line position (e.g. unperturbed value).

    min_colour: str, optional (default "#99590b")
        Colour used for minimum values in the gradient.

    max_colour: str, optional (default "#20463e")
        Colour used for maximum values in the gradient.

    tolerance: float, optional
        Threshold below which variations are not visualised.

    save_png: str, optional
        Path to export the figure as PNG (high resolution).

    save_svg: str, optional
        Path to export the figure as SVG.

    Returns
    -------
    fig : matplotlib.figure.Figure or None
        The generated figure object (or None if skipped due to tolerance).

    ax : matplotlib.axes.Axes or None
        The corresponding axes object (or None).
    """

    if "Reaction" not in df.columns and "Production" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'Reaction' or 'Production' column."
        )

    # Filter target reaction
    if "Reaction" in df.columns:
        df = df[df["Reaction"] == reaction].copy()
    else:
        df = df[df["Production"] == reaction].copy()

    # Detect result columns
    if "FBA_result_decrease" in df.columns:
        col_min = "FBA_result_decrease"
    elif "FVA_max_decrease" in df.columns:
        col_min = "FVA_max_decrease"
    else:
        raise ValueError("No valid minimum column found.")

    if "FBA_result_increase" in df.columns:
        col_max = "FBA_result_increase"
    elif "FVA_max_increase" in df.columns:
        col_max = "FVA_max_increase"
    else:
        raise ValueError("No valid maximum column found.")

    # Check if maximum variation is above threshold
    clean_xlabel = re.sub(r"\n.*", " ", xlabel).replace("\r", " ")
    interval_sizes = (df[col_max] - df[col_min]).abs()
    max_variation = interval_sizes.max()
    if max_variation < tolerance:
        print(
            f"\n\nVariations on {clean_xlabel} are too small to be visualised"
            f" - maximum difference on the order of {max_variation:.2e}\n\n"
        )
        return None, None

    # Sort by interval size
    df["interval_size"] = (df[col_max] - df[col_min]).abs()
    df = df.sort_values("interval_size", ascending=False).copy()
    df["Precursor"] = pd.Categorical(
        df["Precursor"], categories=df["Precursor"], ordered=True
    )

    # Build segmented gradient data
    n_segments = 500
    gradient_data = []

    for _, row in df.iterrows():
        y = row["Precursor"]
        x0 = row[col_min]
        x1 = row[col_max]

        if x0 == x1:
            gradient_data.append((x0, x1, y, 0.5))
        else:
            x_vals = np.linspace(x0, x1, n_segments + 1)
            for i in range(n_segments):
                gradient_data.append(
                    (x_vals[i], x_vals[i + 1], y, i / n_segments)
                )

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "custom_gradient", [max_colour, min_colour]
    )

    for x_start, x_end, y, val in gradient_data:
        ax.plot([x_start, x_end], [y, y], color=cmap(val), linewidth=4)

    ax.scatter(df[col_min], df["Precursor"], color=max_colour, s=80, zorder=3)
    ax.scatter(df[col_max], df["Precursor"], color=min_colour, s=80, zorder=3)

    if value_ref is not None:
        ax.axvline(value_ref, color="black", linewidth=1)

    ax.set_ylabel(ylabel, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=12, fontweight="bold")
    plt.yticks(fontsize=10)
    plt.xticks(fontsize=10)
    sns.despine()

    plt.tight_layout()

    # Export
    if save_png:
        plt.savefig(save_png, dpi=300, bbox_inches="tight")
    if save_svg:
        plt.savefig(save_svg, format="svg", bbox_inches="tight")

    plt.show()

    return fig, ax
