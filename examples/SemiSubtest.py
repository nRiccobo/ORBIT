# Nick Riccobono 

import os

import pandas as pd
import matplotlib as plt

from ORBIT import ProjectManager, load_config

# Inputs/Flags/Filenames 
debug = False 
saveCsv = True

output_filename = "orbit_semisub_cost_model"

# Set up directories 
this_dir = os.getcwd()
orbit_dir = os.path.abspath(os.path.join(this_dir, os.pardir))
results_dir = os.path.join(orbit_dir, 'results')
if not os.path.isdir(results_dir):
    os.makedirs(results_dir)

# ORBIT configuration file 
config_file = 'semisubmersible_project.yaml'
float_config = load_config(os.path.join(this_dir, 'configs', config_file))

if debug: print("Floating Config: ", float_config)
print(f"Site Depth: {float_config['site']['depth']}")
print(f"Design phases: {float_config['design_phases']}")
print(f"\nInstall phases: {list(float_config['install_phases'].keys())}")

# Define turbine types
turbine_names = ['6MW', '12MW', '15MW', '18MW']
turbine_files = ['SWT_6MW_154m_110m','12MW_generic', '15MW_generic', '18MW_generic']

output = pd.DataFrame()
# Existing ORBIT semi-submersible model (Baseline)
for i,n in enumerate(turbine_names):

    float_config['turbine'] = turbine_files[i]
    if debug: print(f"Test appended value {n}: \n {float_config['turbine']}")
    print(f"Running ORBIT: {n} config")

    # No weather files, assume 20% downtown (placeholder)
    project = ProjectManager(float_config)
    project.run(availability=0.8)

    dct = project.capex_breakdown_per_kw
    #print("BOS: ", project.bos_capex_per_kw, "$US/kW")
    #print("CapEx:", project.bos_capex_per_kw * plant_capacity * 1000.0, "$US"
    #    )
    dct = {k: [v] for k, v in dct.items()}
    df = pd.DataFrame.from_dict(dct, orient="columns")
    #df = df.T

    #df_dictionary = pd.DataFrame([dictionary])
    output = pd.concat([output, df], ignore_index=True)
    #print(output.head())
    print("CapEx breakdown: ($US per kW) \n", df)
    
if saveCsv:
    print(f"Saving {output_filename} in {results_dir}")
    output.to_csv(os.path.join(results_dir, output_filename)) #.format(
    #            number, name, rt
    #        )
    #    )
