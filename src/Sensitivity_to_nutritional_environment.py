# Standard library
import io
import math
import contextlib
import textwrap

# Third-party
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from tqdm import tqdm
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
from scipy.interpolate import interp1d
from adjustText import adjust_text

# COBRApy
from cobra import Model
from cobra.util.solver import linear_reaction_coefficients


def robustness_analysis(
    model: Model,
    control_rxn: str,
    n_points: int = 20,
    obj_rxn: str = None,
    obj_type: str = "max",
) -> pd.DataFrame:
    """
    Reproduces the COBRA Toolbox robustness analysis by systematically varying
    the flux of a given reaction and recording the impact on the objective
    function.

    Parameters
    ----------
    model: cobra.Model
        COBRApy metabolic model.

    control_rxn: str
        Identifier of the reaction whose flux is varied.

    n_points: int, optional (default: 20)
        Number of flux values to evaluate across the feasible range.

    obj_rxn: str, optional (default: model's current objective)
        Identifier of the objective reaction.

    obj_type: str, optional (default: 'max')
        Optimisation direction: 'max' or 'min'.

    Returns
    -------
    pd.DataFrame
        Table with:
        - 'control_flux': sampled flux values of the control reaction.
        - 'objective_value': associated values of the objective function.
    """

    # Suppress COBRApy console output
    with contextlib.redirect_stdout(io.StringIO()):
        m = model.copy()

    # Check that the control reaction exists
    if control_rxn not in m.reactions:
        raise ValueError(f"Reaction '{control_rxn}' not found in the model.")

    # If a custom objective is specified, check its validity
    if obj_rxn and obj_rxn not in m.reactions:
        raise ValueError(f"Objective reaction '{obj_rxn}' not in the model.")

    # Determine the feasible flux range for the control reaction
    ctrl = m.reactions.get_by_id(control_rxn)
    m.objective = {ctrl: 1.0}
    sol_min = m.optimize(objective_sense="minimize")
    sol_max = m.optimize(objective_sense="maximise")

    # Build flux range for control variable
    flux_range = np.linspace(sol_min.objective_value,
                             sol_max.objective_value, n_points)

    # Re-set objective to the original
    m.objective = obj_rxn
    sense = "maximize" if obj_type == "max" else "minimize"

    # Evaluate the objective function at each fixed flux value
    obj_values = []
    for v in tqdm(flux_range, desc=f"Robustness on {control_rxn}"):
        rxn = m.reactions.get_by_id(control_rxn)
        rxn.upper_bound = v
        rxn.lower_bound = v
        sol = m.optimize(objective_sense=sense)
        obj_values.append(sol.objective_value)
    return pd.DataFrame({"control_flux": flux_range,
                         "objective_value": obj_values})


def perform_robustness_analysis(
    model,
    uptake_rxns,
    obj_rxn,
    value_ub=10.0,
    value_lb=0,
    change_bounds=True,
    n_points=20,
):
    """
    Perform a robustness analysis on a set of uptake reactions by evaluating
    the impact of their flux range on the objective function.

    Parameters
    ----------
    model: cobra.Model
        COBRApy metabolic model.

    uptake_rxns: list of str
        List of uptake reaction IDs to be analysed individually.

    obj_rxn: str
        Identifier of the objective reaction.

    value_ub: float, optional (default: 10.0)
        Upper bound set for each tested uptake reaction during analysis.

    value_lb: float, optional (default: 0.0)
        Lower bound set for each tested uptake reaction during analysis.

    change_bounds: bool, optional (default: True)
        If True, all tested uptake reactions are disabled during analysis
        except the one being evaluated.

    n_points: int, optional (default: 20)
        Number of flux values for robustness sampling.

    Returns
    -------
    pd.DataFrame
        Combined results with columns:
        - 'Uptake': reaction ID,
        - 'x': tested control flux,
        - 'y': resulting objective value.
    """

    results = []
    with contextlib.redirect_stdout(io.StringIO()):
        m = model.copy()

    # Optionally block all selected uptake reactions initially
    # e.g. test all sources of carbon or nitrogen
    if change_bounds:
        for rxn_id in uptake_rxns:
            rxn = m.reactions.get_by_id(rxn_id)
            rxn.upper_bound = 0.0
            rxn.lower_bound = 0.0
    else:
        # Store initial bounds to restore later
        original_bounds_ub = {
            r: m.reactions.get_by_id(r).upper_bound for r in uptake_rxns
        }
        original_bounds_lb = {
            r: m.reactions.get_by_id(r).lower_bound for r in uptake_rxns
        }

    # Sequentially enable and analyse each uptake reaction
    for rxn_id in uptake_rxns:
        rxn = m.reactions.get_by_id(rxn_id)
        rxn.upper_bound = value_ub
        rxn.lower_bound = value_lb

        # Perform robustness analysis on the current uptake
        df = robustness_analysis(
            model=m,
            control_rxn=rxn_id,
            n_points=n_points,
            obj_rxn=obj_rxn,
            obj_type="max",
        )

        # Collect results
        for _, row in df.iterrows():
            results.append(
                {
                    "Uptake": rxn_id,
                    "x": row["control_flux"],
                    "y": row["objective_value"],
                }
            )

        # Re-close the tested reaction or restore original bounds
        if change_bounds:
            rxn.upper_bound = 0.0
            rxn.lower_bound = 0.0
        else:
            rxn.upper_bound = original_bounds_ub[rxn_id]
            rxn.lower_bound = original_bounds_lb[rxn_id]

    return pd.DataFrame(results)


def robustness_analysis_plot(
    data: pd.DataFrame,
    title: str = None,
    filter_uptakes: list = None,
    experimental_value: float = None,
    point_intersection: bool = False,
    highlight: str = None,
    curve_colour: str = "darkblue",
    xlabel: str = "Uptake flux (mmol·gDW⁻¹·h⁻¹)",
    ylabel: str = "Growth rate (h⁻¹)",
    legend: bool = False,
    save_png: str = None,
    save_svg: str = None,
):
    """
    Plot the relationship between uptake fluxes and growth rate from robustness
    analysis. This function visualizes the flux-response curves obtained from a
    robustness analysis. It supports optional filtering, highlighting of
    specific uptakes, annotation of experimental intersection points, and
    rendering of multiple curves with distinct styles.

    Parameters
    ----------
    data: pd.DataFrame
        DataFrame containing the results from robustness analysis. Must include
        columns: 'Uptake' (reaction ID), 'x' (tested uptake flux), and
        'y' (objective value).
    title: str, optional (default: None)
        Title of the plot.
    filter_uptakes: list of str, optional (default: None)
        Subset of uptake reactions to retain for plotting.
    experimental_value: float, optional (default: None)
        Reference value on the y-axis used for annotating intersection points.
    point_intersection: bool, optional (default: False)
        If True and experimental_value is provided, intersection points with
        the experimental value are computed and annotated.
    highlight: str, optional (default: None)
        Uptake reaction ID to highlight when more than two uptake reactions
        are plotted.
    curve_colour: str, optional (default: darkblue)
        Uptake colour to highlight if multiple are plotted.
    xlabel: str, optional (default: "Uptake flux (mmol·gDW⁻¹·h⁻¹)")
        Label for the x-axis.
    ylabel: str, optional (default: "Growth rate (h⁻¹)")
        Label for the y-axis.
    legend: bool, optional (default: False)
        If True, displays the legend for uptake curves.
    save_png: optional string.
        File path to save the plot as PNG. If None, no PNG is saved.
    save_svg: optional string.
        File path to save the plot as SVG. If None, no SVG is saved.

    Returns
    -------
    tuple
        Matplotlib figure and axes objects (fig, ax) representing the
        robustness plot.
    """

    # Subset data if specific uptake reactions are provided
    plot_data = data.copy()
    if filter_uptakes is not None:
        plot_data = plot_data[plot_data["Uptake"].isin(filter_uptakes)]

    # Ensure 'Uptake' is treated as a factor with preserved ordering
    plot_data["Uptake"] = pd.Categorical(
        plot_data["Uptake"],
        categories=plot_data["Uptake"].unique(),
        ordered=True
    )
    levels = plot_data["Uptake"].cat.categories
    n_curves = len(levels)

    # Initialize plot layout
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=10, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)

    colors = {}
    linestyles = {}

    # Case: exactly two uptake curves → black and grey, solid and dashed lines
    if n_curves == 2:
        uptake_levels = filter_uptakes
        colors = {uptake_levels[0]: "black", uptake_levels[1]: "grey"}
        linestyles = {uptake_levels[0]: "solid", uptake_levels[1]: "dashed"}
        for uptake in uptake_levels:
            subset = plot_data[plot_data["Uptake"] == uptake]
            ax.plot(
                subset["x"],
                subset["y"],
                label=uptake,
                color=colors[uptake],
                linestyle=linestyles[uptake],
                linewidth=0.8,
            )

    # Case: more than two curves → all grey, optional highlight
    elif n_curves > 2:
        color_default = "#b3b3b3"
        for uptake in levels:
            if uptake == highlight:
                colors[uptake] = curve_colour
            else:
                colors[uptake] = color_default

        # Plot all non-highlighted curves
        for uptake in levels:
            if uptake != highlight:
                subset = plot_data[plot_data["Uptake"] == uptake]
                ax.plot(
                    subset["x"],
                    subset["y"],
                    label=uptake,
                    color=colors[uptake],
                    linewidth=1.1,
                )

        # Plot the highlighted curve last
        if highlight in levels:
            subset = plot_data[plot_data["Uptake"] == highlight]
            ax.plot(
                subset["x"],
                subset["y"],
                label=highlight,
                color=curve_colour,
                linewidth=1.5,
            )
    # Case: single uptake curve → black line
    else:
        subset = plot_data
        ax.plot(subset["x"], subset["y"], color="black", linewidth=0.8)

    # Add horizontal reference line if experimental_value is provided
    # and highlight is defined
    if experimental_value is not None and highlight is not None:
        ax.axhline(
            experimental_value, color="darkorange",
            linestyle="dotted", linewidth=0.7
        )

    # Intersection point computation by linear interpolation
    def compute_intersections(df, y_ref):
        intersections = []
        x_vals = df["x"].values
        y_vals = df["y"].values
        for i in range(len(df) - 1):
            y1, y2 = y_vals[i], y_vals[i + 1]
            if (y1 - y_ref) * (y2 - y_ref) <= 0:
                x1, x2 = x_vals[i], x_vals[i + 1]
                if y2 != y1:
                    x_int = x1 + (y_ref - y1) * (x2 - x1) / (y2 - y1)
                else:
                    x_int = x1
                intersections.append((x_int, y_ref))

        # Remove duplicates using rounded coordinates
        unique = {}
        for x, y in intersections:
            key = (round(x, 4), round(y, 4))
            if key not in unique:
                unique[key] = (x, y)
        return list(unique.values())

    # Annotate intersection points if requested
    if point_intersection and (
        n_curves <= 2 or (highlight is not None and n_curves > 2)
    ):
        if n_curves > 2:
            df_int = plot_data[plot_data["Uptake"] == highlight]
        else:
            df_int = plot_data

        intersections = compute_intersections(df_int, experimental_value)
        texts = []
        for x_int, y_int in intersections:
            ax.plot(x_int, y_int, "o", color="darkorange", markersize=6)
            ax.vlines(x_int, 0, y_int, color="darkorange", linewidth=0.5)
            label = f"{x_int:.2e}"
            texts.append(
                ax.text(
                    x_int,
                    y_int,
                    label,
                    color="darkorange",
                    fontsize=8,
                    weight="bold",
                    bbox=dict(facecolor="white", edgecolor="none", pad=1),
                )
            )

        adjust_text(texts, arrowprops=dict(arrowstyle="-", color="darkorange"))

    # Add legend if required and more than one curve
    if legend and n_curves > 1:
        ax.legend(loc="lower center", fontsize=9, frameon=False,
                  ncol=min(n_curves, 4))

    plt.tight_layout()

    # Save plot if save_svg or save_png paths are provided
    if save_png is not None:
        fig.savefig(save_png, format="png", dpi=300, bbox_inches="tight")

    if save_svg is not None:
        fig.savefig(save_svg, format="svg", bbox_inches="tight")

    return fig, ax


def spaghetti_plots(
    data,
    title=None,
    dist_threshold=1e-5,
    curve_colour="darkblue",
    group_prefix="Group ",
    xlabel=None,
    ylabel="Growth rate (h⁻¹)",
    legend_text=True,
    save_png=None,
    save_svg=None,
):
    """
    Plot a grid of 'spaghetti plots' with hierarchical clustering to group
    similar uptake curves. This function interpolates all curves on a common
    x-axis, performs hierarchical clustering, and assigns each curve to a
    group. One representative curve is highlighted per group. The output is
    a grid of subplots, each showing a group and its representative curve.

    Parameters
    ----------
    data : pandas.DataFrame
        Input data with columns: 'x', 'y', and 'Uptake' (curve identifier).

    title : str, optional (default: None)
        Title of the entire figure.

    dist_threshold : float, optional (default: 1e-5)
        Distance threshold for hierarchical clustering.

    curve_colour : str, optional (default: 'darkblue')
        Colour of the representative curve in each group.

    group_prefix : str, optional (default: 'Group ')
        Prefix for naming each group.

    xlabel : str, optional (default: None)
        Custom x-axis label; if None, the uptake IDs will be listed.

    ylabel : str, optional (default: "Growth rate (h⁻¹)")
        y-axis label for all subplots.

    save_png : str, optional
        Path to save the figure as a PNG (default: None).

    save_svg : str, optional
        Path to save the figure as an SVG (default: None).

    Returns
    -------
    matplotlib.figure.Figure
        The resulting matplotlib Figure object.
    """

    # Define common x-axis range over which all curves will be interpolated
    x_min = data.groupby("Uptake")["x"].min().max()
    x_max = data.groupby("Uptake")["x"].max().min()
    x_common = np.linspace(x_min, x_max, 100)

    # Interpolate all curves on the common x grid
    interpolated_curves = []
    for uptake_id, group in data.groupby("Uptake"):
        f = interp1d(group["x"], group["y"], bounds_error=False,
                     fill_value=np.nan)
        y_interp = f(x_common)
        interpolated_curves.append(
            pd.DataFrame({"x": x_common, "y": y_interp, "Uptake": uptake_id})
        )
    data_interp = pd.concat(interpolated_curves, ignore_index=True)

    # Construct matrix for clustering
    wide_df = data_interp.pivot(index="x", columns="Uptake", values="y")
    matrix = wide_df.T.astype(float).to_numpy()

    # Compute pairwise distances and perform hierarchical clustering
    distances = pdist(matrix, metric="euclidean")
    linkage_matrix = linkage(distances, method="ward")
    cluster_assignments = fcluster(
        linkage_matrix, t=dist_threshold, criterion="distance"
    )

    # Map curves to cluster labels
    cluster_map = pd.DataFrame(
        {"Uptake": wide_df.columns, "cluster": cluster_assignments}
    )
    data_grouped = data.merge(cluster_map, on="Uptake")

    # Identify one representative uptake per cluster
    rep_uptake = (
        data_grouped.groupby("cluster")["Uptake"]
        .first()
        .reset_index()
    )
    rep_uptake.columns = ["cluster", "RepUptake"]
    data_grouped = data_grouped.merge(rep_uptake, on="cluster")
    data_grouped["is_rep"] = (
        data_grouped["Uptake"] == data_grouped["RepUptake"]
    )

    # Order groups by decreasing max y of representative curve
    rep_max_y = (
        data_grouped[data_grouped["is_rep"]]
        .groupby("cluster")["y"]
        .max()
        .sort_values(ascending=False)
    )
    ordered_clusters = rep_max_y.index.tolist()

    # Assign formatted group names
    cluster_name_map = {
        cluster_id: f"{group_prefix}{i+1}"
        for i, cluster_id in enumerate(ordered_clusters)
    }
    data_grouped["Group"] = data_grouped["cluster"].map(cluster_name_map)

    # Order group names for plotting
    group_order = sorted(
        data_grouped["Group"].unique(),
        key=lambda x: int(x.replace(group_prefix, ""))
    )

    # Compute subplot grid dimensions
    n_groups = len(group_order)
    ncols = 4
    nrows = math.ceil(n_groups / ncols)

    # Determine global plot limits
    x_global_min = 0
    y_global_min = 0
    x_global_max = data_grouped["x"].max() * 1.05
    y_global_max = data_grouped["y"].max() * 1.05

    # Set up figure and subplot grid
    fig = plt.figure(figsize=(16, 5 * nrows))
    gs = gridspec.GridSpec(nrows, ncols, height_ratios=[1] * nrows, hspace=0.6)

    for i, group in enumerate(group_order):
        row = i // ncols
        col = i % ncols
        ax = fig.add_subplot(gs[row, col])

        sub_data = data_grouped[data_grouped["Group"] == group]

        # Plot all other groups in grey for context
        other_data = data_grouped[data_grouped["Group"] != group]
        for uptake_id in other_data["Uptake"].unique():
            d = other_data[other_data["Uptake"] == uptake_id]
            ax.plot(d["x"], d["y"], color="grey", linewidth=0.8)

        # Plot representative curve in colour
        rep = sub_data[sub_data["is_rep"]]
        ax.plot(rep["x"], rep["y"], color=curve_colour, linewidth=1.2)

        # Title with background colour for each facet
        ax.set_title(
            group,
            fontsize=9,
            weight="bold",
            color="white",
            backgroundcolor=curve_colour,
            pad=6,
        )

        # Axis limits
        ax.set_xlim(x_global_min, x_global_max)
        ax.set_ylim(y_global_min, y_global_max)

        # Label x-axis
        if xlabel is None:
            uptakes = sorted(sub_data["Uptake"].unique())
            uptakes_str = ", ".join(uptakes)
            uptakes_wrapped = textwrap.fill(uptakes_str, width=55)
            xlabel_text = f"{uptakes_wrapped}\n(mmol·gDW⁻¹·h⁻¹)"
            ax.set_xlabel(xlabel_text, fontsize=8, linespacing=1.5)
        else:
            ax.set_xlabel(xlabel, fontsize=8)

        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(axis="both", labelsize=7)

        # Adjust layout
        plt.subplots_adjust(top=0.95, bottom=0.05)

    # Main title
    if title:
        fig.suptitle(title, fontsize=14, weight="bold", x=0.05, ha="left")

    # Export
    if save_png:
        plt.savefig(save_png, dpi=300, bbox_inches="tight")
    if save_svg:
        plt.savefig(save_svg, format="svg", bbox_inches="tight")

    plt.show()

    return fig
