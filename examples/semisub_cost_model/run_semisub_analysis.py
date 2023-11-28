# Nick Riccobono

import os

import numpy as np
import pandas as pd
import matplotlib as plt
from ORBIT import ProjectManager, load_config
from ORBIT.core.library import initialize_library
from ORBIT.phases.design import CustomSemiSubmersibleDesign

# Inputs/Flags/Filenames
debug = False
saveCsv = False

tag = "custom" # Or baseline 
config_file = "semisubmersible_baseline.yaml"
#config_file = "semisubmersible_custom.yaml"
output_filename = "orbit_semisub_cost_model_" + tag + ".csv"
output_capex_filename = "orbit_semisub_capex_kW_" + tag + ".csv"

# Define turbine types
# Need to ensure that the turbine library contains all turbine files 
#turbine_names = ["12MW", "15MW", "17MW", "18MW", "20MW"]
turbine_names = ["18MW"]

turbine_files = [i + "_generic" for i in turbine_names]
print(turbine_files)

# Set up directories
this_dir = os.getcwd()
orbit_dir = os.path.abspath(os.path.join(this_dir, os.pardir))
lib_dir = os.path.join(orbit_dir, "library")
output_dir = os.path.join(this_dir, "outputs")
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

# ORBIT configuration file
float_config = load_config(os.path.join(this_dir, config_file))

if debug:
    print("Floating Config: ", float_config)
    print(f"Site Depth: {float_config['site']['depth']}")
    print(f"Design phases: {float_config['design_phases']}")

output = pd.DataFrame()
output_capex = pd.DataFrame()

# Run ORBIT Simulations
initialize_library(lib_dir)
ProjectManager.register_design_phase(CustomSemiSubmersibleDesign)

for i, n in enumerate(turbine_names):
    float_config["turbine"] = turbine_files[i]
    if debug:
        print(f"Test turbine value {n}: \n {float_config['turbine']}")

    # No weather files, assume 20% downtown (placeholder)
    print(f"Running ORBIT: {n} config")
    project = ProjectManager(float_config)
    project.run(availability=0.8)

    if debug:
        print("Design phases: ", project._design_phases)

    # dct = project.capex_breakdown
    dct = project.design_results["substructure"]
    dct = {k: [np.round(v)] for k, v in dct.items()}

    df = pd.DataFrame.from_dict(dct, orient="columns")

    output = pd.concat([output, df], ignore_index=True)  # , axis=1)
    print("SubStructure: ($US) \n", df)
    # print("detailed output \n", project.detailed_outputs)

    dct2 = project.capex_breakdown_per_kw
    dct2 = {k: [np.round(v)] for k, v in dct2.items()}

    df2 = pd.DataFrame.from_dict(dct2, orient="columns")

    output_capex = pd.concat(
        [output_capex, df2], ignore_index=True
    )  # , axis=1)
    # print("Substructure: ", project.design_results["substructure"])
    # print("Custom Substructure: ", project.design_results["custom_substructure"])

output = pd.concat(
    [output, pd.DataFrame.from_dict({"Turbine Rating": turbine_names})], axis=1
)
output_capex = pd.concat(
    [output_capex, pd.DataFrame.from_dict({"Turbine Rating": turbine_names})],
    axis=1,
)

if saveCsv:
    print(f"Saving {output_filename} in {output_dir}")
    output.to_csv(os.path.join(output_dir, output_filename))

    print(f"Saving {output_capex_filename} in {output_dir}")
    output_capex.to_csv(os.path.join(output_dir, output_capex_filename))
