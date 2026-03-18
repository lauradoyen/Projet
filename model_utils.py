import cobra
from nicegui import ui


def load_model():

    model_path = "iPrub22.sbml"
    model = cobra.io.read_sbml_model(model_path)
    return model



