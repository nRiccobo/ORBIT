"""Provides the `SemiSubmersibleDesign` class.  Based on semisub design from 15 MW RWT

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
            "ballast_mass": "tonnes (optional, default 2540)",
            "steel_cost_rate": "$/tonne (optional, default: 3120)",
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

        # Geometric scale formula from U-Mass paper: Insert Ref
        ref_turbine_radius = 120.0
        new_turbine_radius = np.float(config["turbine"]["rotor_diameter"] / 2)

        alpha = 0.75  # 0.72-0.75 based on IEA-15MW turbine

        self.geom_scale_factor = (
            new_turbine_radius / ref_turbine_radius
        ) ** alpha

        self.mass_scale_factor = (
            new_turbine_radius / ref_turbine_radius
        ) ** 1.5

        self._outputs = {}

    def run(self):
        """Main run function."""

        substructure = {
            "mass": self.substructure_steel_mass,
            "unit_cost": self.substructure_unit_cost,
            "towing_speed": self._design.get("towing_speed", 6),
        }

        self._outputs["substructure"] = substructure

    @property
    def bouyant_column_volume(self):
        """
        Calculates the volume of a single (hollow) cylindrical buoyant column
        Wall-thickness remains constant (U-Mass ref)
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

        volume = (np.pi / 4) * (d**2 - (d - 2 * t) ** 2) * h

        return volume

    @property
    def pontoon_volume(self):
        """
        Calculates the volume of a single (hollow) pontoon that connects
        the central column to the outer columns.
        Wall-thickness reamins constant (U-Mass ref)
        """

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
        # TODO: Subtract semi-circular area from center column and fairlead column

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
        # TODO: Add tower interface point mass (U-Mass ref)

        dens = self._design.get("steel_density", 8050)

        mass = (dens / 1000) * (
            4 * self.bouyant_column_volume
            + 3 * self.pontoon_volume
            + 3 * self.strut_volume
        )

        return mass

    @property
    def substructure_steel_cost(self):
        """
        Calculates the total cost of structural steel in the substructure in $USD
        """

        steel_cr = self._design.get("steel_cost_rate", 3120)

        cost = steel_cr * self.substructure_steel_mass

        return cost

    @property
    def substructure_mass(self):
        """
        Calculates the total mass of structural steel and iron ore ballast in the substructure.
        """

        ballast_mass = self._design.get("ballast_mass", 2540)

        mass = self.substructure_steel_mass + ballast_mass

        return mass

    @property
    def substructure_unit_cost(self):
        """
        Calculates the total material cost of a single substructure.
        Does not include final assembly or transportation costs.
        """

        ballast_mass = self._design.get("ballast_mass", 2540)
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
