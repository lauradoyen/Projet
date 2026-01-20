from nicegui import ui, event
import cobra
import V1_Bloc1_ui

# -----------------------------------------------------
# Charger le modèle SBML
# -----------------------------------------------------
model = cobra.io.read_sbml_model("iPrub22.sbml")

print("Modèle :", model.name)
print("Nombre de réactions :", len(model.reactions))
print("Nombre de métabolites :", len(model.metabolites))

# -----------------------------------------------------
# Interface NiceGUI : En-tête
# -----------------------------------------------------
with ui.column().classes("m-4"):
    ui.label("Mon interface NiceGUI").classes("text-3xl font-bold")
    ui.label("Bienvenue dans votre application de reconstruction métabolique !").classes("text-lg mt-2")

    ui.label("Nom du modèle").classes("text-xl mt-4")
    ui.label(model.name).classes("text-lg")

# -----------------------------------------------------
# Onglets principaux
# -----------------------------------------------------
with ui.tabs().classes('w-full') as tabs:
    tab_accueil = ui.tab("Accueil")
    tab_reconstruction = ui.tab("Reconstruction")
    tab_identification = ui.tab("Identification des métabolites")
    tab_representation = ui.tab("Représentation chimique")
    tab_fba = ui.tab("Simulation FBA")
    tab_fva = ui.tab("FVA")

with ui.tab_panels(tabs, value=tab_accueil).classes('w-full'):

    # -----------------------------------------------------
    # Onglet 1 : Accueil
    # -----------------------------------------------------
    with ui.tab_panel(tab_accueil):
        V1_Bloc1_ui.display(model)

    # -----------------------------------------------------
    # Onglet 2 : Reconstruction (ancien fichier 1)
    # -----------------------------------------------------
    with ui.tab_panel(tab_reconstruction):
        ui.label("Informations générales du modèle").classes("text-xl")
        ui.label(f"Métabolites : {len(model.metabolites)}")
        ui.label(f"Réactions : {len(model.reactions)}")
        ui.label(f"Gènes : {len(model.genes)}")

    # -----------------------------------------------------
    # Onglet 3 : Identification des métabolites
    # -----------------------------------------------------
    with ui.tab_panel(tab_identification):
        ui.label("Identification des métabolites").classes("text-xl")

    # -----------------------------------------------------
    # Onglet 4 : Représentation chimique
    # -----------------------------------------------------
    with ui.tab_panel(tab_representation):
        ui.label("Représentation chimique des métabolites").classes("text-xl")

    # -----------------------------------------------------
    # Onglet 5 : FBA simple
    # -----------------------------------------------------
    with ui.tab_panel(tab_fba):
        ui.label("Simulation FBA simple").classes("text-xl")

    # -----------------------------------------------------
    # Onglet 6 : FVA
    # -----------------------------------------------------
    with ui.tab_panel(tab_fva):
        ui.label("Analyse FVA").classes("text-xl")

# ---------------------------------------------------------
# Lancer l'application
# ---------------------------------------------------------
ui.run(port=8080, reload=False)
