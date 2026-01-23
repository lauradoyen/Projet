import cobra
from nicegui import ui


def load_model():

    iPrub22_path = "iPrub22.sbml"
    model = cobra.io.read_sbml_model(iPrub22_path)
    return model



