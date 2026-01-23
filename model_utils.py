import cobra
from nicegui import ui


def load_model():

    iPrub22_path = "C:/Users/laura/Desktop/EI2/PROENC/Projet_BIOSTIC_2025_2026/Model/iPrub22.sbml"
    model = cobra.io.read_sbml_model(iPrub22_path)
    return model



