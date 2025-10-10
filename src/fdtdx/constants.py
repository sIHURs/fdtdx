"""Module containing physical constants and material properties for FDTD simulations.

This module provides fundamental physical constants and material properties used in FDTD simulations.
It includes both universal constants (like speed of light, vacuum permittivity) and relative permittivity
values for various materials commonly used in photonic simulations.

The module also defines standard permittivity configurations for different material combinations
used in simulations.
"""

from fdtdx.units.unitful import SI, Unit, Unitful

c: Unitful = Unitful(val=2.99792458, unit=Unit(scale=8, dim={SI.m: 1, SI.s: -1}))
"""Speed of light in vacuum (m/s)."""

mu0: Unitful = Unitful(val=1.25663706127, unit=Unit(scale=-6, dim={SI.kg: 1, SI.m: 1, SI.s: -2, SI.A: -2}))
"""Vacuum permeability (H/m)."""

# eps0: Unitful = 1.0 / (mu0 * c**2)
eps0: Unitful = Unitful(val=8.8541878188, unit=Unit(scale=-12, dim={SI.A: 2, SI.kg: -1, SI.m: -3, SI.s: 4}))
"""Vacuum permittivity (F/m)."""

# eta0: Unitful = mu0 * c
eta0: Unitful = Unitful(val=3.76730313412, unit=Unit(scale=2, dim={SI.kg: 1, SI.m: 2, SI.s: -3, SI.A: -2}))
"""Free space impedance (Ω)."""

# Relative Permittivities of different materials
relative_permittivity_air: float = 1.0
"""Relative permittivity of air."""

relative_permittivity_substrate: float = 2.1025
"""Relative permittivity of standard substrate material."""

relative_permittivity_polymer: float = 2.368521
"""Relative permittivity of standard polymer material."""

relative_permittivity_silicon: float = 12.25
"""Relative permittivity of silicon."""

relative_permittivity_silica: float = 2.25
"""Relative permittivity of silica."""

relative_permittivity_SZ_2080: float = 2.1786
"""Relative permittivity of SZ2080 photoresist."""

relative_permittivity_ma_N_1400_series: float = 2.6326
"""Relative permittivity of ma-N 1400 series photoresist."""

relative_permittivity_bacteria: float = 1.96
"""Relative permittivity of bacteria."""

relative_permittivity_water: float = 1.737
"""Relative permittivity of water."""

relative_permittivity_fused_silica: float = 2.13685924
"""Relative permittivity of fused silica."""

relative_permittivity_coated_silica: float = 1.69
"""Relative permittivity of coated silica."""

relative_permittivity_resin: float = 2.202256
"""Relative permittivity of standard resin."""

relative_permittivity_ormo_prime: float = 1.817104
"""Relative permittivity of Ormocer primer."""

SHARD_STR: str = "shard"
"""String constant used to identify sharded computations."""


def wavelength_to_period(wavelength: Unitful) -> Unitful:
    """Convert wavelength to time period using speed of light.

    Uses the speed of light constant to calculate the corresponding time period
    for a given wavelength.

    Args:
        wavelength (float): The wavelength in meters.

    Returns:
        float: The corresponding time period in seconds.
    """
    return wavelength / c
