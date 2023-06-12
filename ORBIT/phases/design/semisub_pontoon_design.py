"""Provides the `SemiSubmersibleDesign` class.  Based on semisub design from 15 MW RWT

[1]	C. Allen et al., “Definition of the UMaine VolturnUS-S Reference Platform Developed
 for the IEA Wind 15-Megawatt Offshore Reference Wind Turbine,” NREL/TP--5000-76773, 
 1660012, MainId:9434, Jul. 2020. doi: 10.2172/1660012.
[2]	K. L. Roach, M. A. Lackner, and J. F. Manwell, “A New Methodology for Upscaling 
 Semi-submersible Platforms for Floating Offshore Wind Turbines,” Wind Energy Science 
 Discussions, pp. 1–33, Feb. 2023, doi: 10.5194/wes-2023-18.

"""

__author__ = "Matt Shields"
__copyright__ = "Copyright 2020, National Renewable Energy Laboratory"
__maintainer__ = "Matt Shields"
__email__ = "matt.shields@nrel.gov"

import numpy as np
from ORBIT.phases.design import DesignPhase


class CustomSemiSubmersibleDesign(DesignPhase):
    """Customized Semi-Submersible Substructure Design"""

    expected_config = {
        "site": {"depth": "m"},
        "plant": {"num_turbines": "int"},
        "turbine": {"turbine_rating": "MW"},
        "semisubmersible_design": {
            "column_diameter": "m",
            "wall_thickness": "m",
            "column_height": "m",
            "pontoon_length": "m",
            "pontoon_width": "m",
            "pontoon_height": "m",
            "strut_diameter": "m",
            "steel_density": "kg/m^3 (optional, default: 8050)",
            "ballast_mass": "tonnes (optional, default 0)",
            "tower_interface_mass": "tonnes (optional, default 0)",
            "steel_cost_rate": "$/tonne (optional, default: 4500)",
            "ballast_cost_rate": "$/tonne (optional, default: 150)",
        },
    }

    output_config = {
        "substructure": {
            "mass": "t",
            "unit_cost": "USD",
            "towing_speed": "km/h",
        }
    }

    def __init__(self, config, **kwargs):
        """
        Creates an instance of `CustomSemiSubmersibleDesign`.

        Parameters
        ----------
        config : dict
        """

        config = self.initialize_library(config, **kwargs)
        self.config = self.validate_config(config)
        self._design = self.config.get("semisubmersible_design", {})

        # Upscaling Methodology from [2] using IEA-15MW reference platform [1]
        ref_turbine_radius = 120.0
        new_turbine_radius = np.float(config["turbine"]["rotor_diameter"] / 2)

        # power-law parameter Lines 335-340 [2]
        alpha = 0.72  

        self.geom_scale_factor = (
            new_turbine_radius / ref_turbine_radius
        ) ** alpha
        print("scale factor", self.geom_scale_factor)
        self._outputs = {}

    def run(self):
        """Main run function."""

        substructure = {
            "mass": self.substructure_mass,
            "unit_cost": self.substructure_unit_cost,
            "towing_speed": self._design.get("towing_speed", 6),
        }
        print("Inside design: ", substructure)
        self._outputs["substructure"] = substructure

    @property
    def bouyant_column_volume(self):
        """
        Calculates the volume of a single (hollow) cylindrical buoyant column
        Wall-thickness remains constant [2]
        """

        d = (
            self.config["semisubmersible_design"]["column_diameter"]
            * self.geom_scale_factor
        )
        t = self.config["semisubmersible_design"]["wall_thickness"]
        h = (
            self.config["semisubmersible_design"]["column_height"]
            * self.geom_scale_factor
        )

        volume = (np.pi / 4) * ( 
            h * d**2 - (h - 2 * t) * (d - 2 * t) ** 2
        ) 

        return volume
    
    @property
    def center_column_volume(self):
        """
        Calculates the volume of a single (hollow) center column under the turbine
        Wall-thickness remains constant [2]
        """

        d = 10.0 # fixed tower diameter 
        t = self.config["semisubmersible_design"]["wall_thickness"]
        h = (
            self.config["semisubmersible_design"]["column_height"]
            * self.geom_scale_factor
        )
        h2 = (
            self.config["semisubmersible_design"]["pontoon_height"]
            * self.geom_scale_factor
        )

        volume = (np.pi / 4) * ( 
            (h - h2) * d**2 - (h - t - h2) * (d - 2 * t) ** 2
        ) 

        return volume

    @property
    def pontoon_volume(self):
        """
        Calculates the volume of a single (hollow) pontoon that connects
        the central column to the outer columns.
        Wall-thickness reamins constant [2]
        """
        # TODO: Subtract semi-circular area from center column and fairlead column

        l = (
            self.config["semisubmersible_design"]["pontoon_length"]
            * self.geom_scale_factor
        )
        w = (
            self.config["semisubmersible_design"]["pontoon_width"]
            * self.geom_scale_factor
        )
        h = (
            self.config["semisubmersible_design"]["pontoon_height"]
            * self.geom_scale_factor
        )
        t = self.config["semisubmersible_design"]["wall_thickness"]

        volume = (h * w - (h - 2 * t) * (w - 2 * t)) * l
        
        return volume

    @property
    def strut_volume(self):
        """
        Calculates the volume of a single strut that connects
        the central column to the outer columns.
        """

        l = (
            self.config["semisubmersible_design"]["pontoon_length"]
            * self.geom_scale_factor
        )
        d = (
            self.config["semisubmersible_design"]["strut_diameter"]
            * self.geom_scale_factor
        )

        volume = (np.pi / 4) * (d**2) * l

        return volume

    @property
    def substructure_steel_mass(self):
        """
        Calculates the total mass of structural steel in the substructure.

        """
        # TODO: Separate out different steels for each component 

        dens = self._design.get("steel_density", 7980) # 8050)

        mass = (dens / 1000) * (
            3 * self.bouyant_column_volume
            + self.center_column_volume
            + 3 * self.pontoon_volume
            + 3 * self.strut_volume
        )
        print("Volumes: ", 3 * self.bouyant_column_volume,
              self.center_column_volume,
            3 * self.pontoon_volume,
            3 * self.strut_volume)

        return mass

    @property 
    def ballast_mass(self):
        """
        Calculates the mass of fixed ballast. Default value from [1]

        """
        #TODO: Scale ballast mass with some factor? Fixed/Fluid needs to be addressed 

        mass = self._design.get("ballast_mass", 2540) 
        
        return mass 
    
    @property 
    def tower_interface_mass(self):
        """
        Calculates the mass of tower interface. Default value from [1]

        """
        #TODO: Find a model to estimate the mass for a tower interface

        mass = self._design.get("tower_interface_mass", 100)

        return mass 
    @property
    def substructure_steel_cost(self):
        """
        Calculates the total cost of structural steel in the substructure in $USD.
        """
        # TODO: Apply different cost rates for different steels

        steel_cr = self._design.get("steel_cost_rate", 4500)

        cost = steel_cr * self.substructure_steel_mass

        return cost

    @property
    def substructure_mass(self):
        """
        Calculates the total mass of structural steel and iron ore ballast in the substructure.
        """
        tower_interface_mass = self.tower_interface_mass
        ballast_mass = self.ballast_mass
        print("inside substruct mass: ", tower_interface_mass, ballast_mass)

        mass = self.substructure_steel_mass + ballast_mass + tower_interface_mass

        return mass

    @property
    def substructure_unit_cost(self):
        """
        Calculates the total material cost of a single substructure.
        Does not include final assembly or transportation costs.
        """
        
        ballast_mass = self.ballast_mass
        ballast_cr = self._design.get("ballast_cost_rate", 150)

        cost = self.substructure_steel_cost + ballast_cr * ballast_mass

        return cost

    @property
    def design_result(self):
        """Returns the result of `self.run()`"""

        if not self._outputs:
            raise Exception("Has `SemiSubmersibleDesign` been ran yet?")

        return self._outputs

    @property
    def total_cost(self):
        """Returns total phase cost in $USD."""

        num = self.config["plant"]["num_turbines"]
        return num * self.substructure_unit_cost

    @property
    def detailed_output(self):
        """Returns detailed phase information."""

        _outputs = {
            "substructure_steel_mass": self.substructure_steel_mass,
            "substructure_steel_cost": self.substructure_steel_cost,
            "substructure_mass": self.substructure_mass,
            "substructure_cost": self.substructure_unit_cost,
        }

        return _outputs
