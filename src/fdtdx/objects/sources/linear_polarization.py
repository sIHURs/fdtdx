from abc import ABC, abstractmethod

import jax
import jax.numpy as jnp

from fdtdx.core.grid import calculate_time_offset_yee
from fdtdx.core.jax.pytrees import autoinit, frozen_field
from fdtdx.core.linalg import get_wave_vector_raw, rotate_vector
from fdtdx.core.misc import linear_interpolated_indexing, normalize_polarization_for_source
from fdtdx.core.physics.metrics import normalize_by_averaged_flux
from fdtdx.objects.sources.tfsf import TFSFPlaneSource
from fdtdx.units import A, V, m
from fdtdx.units.unitful import Unitful


@autoinit
class LinearlyPolarizedPlaneSource(TFSFPlaneSource, ABC):
    fixed_E_polarization_vector: tuple[float, float, float] | None = frozen_field(default=None)
    fixed_H_polarization_vector: tuple[float, float, float] | None = frozen_field(default=None)
    normalize_by_flux: bool = frozen_field(default=True)

    def get_EH_variation(
        self,
        inv_permittivities: jax.Array,
        inv_permeabilities: jax.Array | float,
    ) -> tuple[
        Unitful,  # E: (3, *grid_shape)
        Unitful,  # H: (3, *grid_shape)
        Unitful,  # time_offset_E: (3, *grid_shape)
        Unitful,  # time_offset_H: (3, *grid_shape)
    ]:
        inv_permittivities = inv_permittivities[*self.grid_slice]
        if isinstance(inv_permeabilities, jax.Array) and inv_permeabilities.ndim > 0:
            inv_permeabilities = inv_permeabilities[*self.grid_slice]

        # determine E/H polarization
        e_pol_raw, h_pol_raw = normalize_polarization_for_source(
            direction=self.direction,
            propagation_axis=self.propagation_axis,
            fixed_E_polarization_vector=self.fixed_E_polarization_vector,
            fixed_H_polarization_vector=self.fixed_H_polarization_vector,
        )
        wave_vector_raw = get_wave_vector_raw(
            direction=self.direction,
            propagation_axis=self.propagation_axis,
        )

        center = self._get_center()

        # tilt polarizations
        axes_tpl = (self.horizontal_axis, self.vertical_axis, self.propagation_axis)
        wave_vector = rotate_vector(wave_vector_raw, self.azimuth_radians, self.elevation_radians, axes_tpl)
        e_pol = rotate_vector(e_pol_raw, self.azimuth_radians, self.elevation_radians, axes_tpl)
        h_pol = rotate_vector(h_pol_raw, self.azimuth_radians, self.elevation_radians, axes_tpl)

        # update is amplitude multiplied by polarization
        amplitude_raw = self._get_amplitude_raw(center)[None, ...]

        # map amplitude to propagation plane
        w, h = jnp.meshgrid(
            jnp.arange(self.grid_shape[self.horizontal_axis]),
            jnp.arange(self.grid_shape[self.vertical_axis]),
            indexing="ij",
        )
        wh_indices = jnp.stack((w, h), axis=-1)
        wh_indices -= jnp.asarray(center)
        # basis in plane
        h_list = [0, 0, 0]
        h_list[self.horizontal_axis] = 1
        h_axis = jnp.asarray(h_list, dtype=jnp.float32)
        u_basis = h_axis - jnp.dot(h_axis, wave_vector) * wave_vector
        u_basis = u_basis / jnp.linalg.norm(u_basis)
        v_basis = jnp.cross(wave_vector, u_basis)

        # projection
        def project(point):
            point_list = [point[0], point[1]]
            point_list.insert(self.propagation_axis, 0)
            point = jnp.asarray(point_list, dtype=jnp.float32)
            projection = point - jnp.dot(point, wave_vector) * wave_vector
            # Convert to plane coordinates
            u = jnp.dot(projection, u_basis)
            v = jnp.dot(projection, v_basis)
            return jnp.asarray((u, v), dtype=jnp.float32)

        float_projected = jax.vmap(project)(wh_indices.reshape(-1, 2))
        float_projected += jnp.asarray(center)
        # interpolate floating indices in original array
        index_fn = jax.vmap(linear_interpolated_indexing, in_axes=(0, None))
        interp = index_fn(float_projected, amplitude_raw.squeeze())
        amplitude = interp.reshape(*amplitude_raw.shape)

        E = (V / m) * amplitude * e_pol[:, None, None, None]
        H = (A / m) * amplitude * h_pol[:, None, None, None]

        if self.normalize_by_flux:
            normal_vec = [0, 0, 0]
            normal_vec[self.propagation_axis] = 1 if self.direction == "+" else -1
            E, H = normalize_by_averaged_flux(
                E=E,
                H=H,
                resolution=self._config.resolution,
                normal_vector=(normal_vec[0], normal_vec[1], normal_vec[2]),
            )

        # adjust H for impedance of the medium
        impedance = jnp.sqrt(inv_permittivities / inv_permeabilities)
        H = H / impedance

        time_offset_E, time_offset_H = calculate_time_offset_yee(
            center=center,
            wave_vector=wave_vector,
            inv_permittivities=inv_permittivities,
            inv_permeabilities=inv_permeabilities,
            resolution=self._config.resolution,
            time_step_duration=self._config.time_step_duration,
        )

        return E, H, time_offset_E, time_offset_H

    @abstractmethod
    def _get_amplitude_raw(
        self,
        center: tuple[float, float],
    ) -> jax.Array:  # shape (*grid_shape)
        # in normal coordinates, not yee grid
        del center
        raise NotImplementedError()


@autoinit
class GaussianPlaneSource(LinearlyPolarizedPlaneSource):
    radius: Unitful = frozen_field()
    std: float = frozen_field(default=1 / 3)  # relative to radius

    @staticmethod
    def _gauss_profile(
        width: int,
        height: int,
        axis: int,
        center: tuple[float, float],
        radii: tuple[float, float],
        std: float,
    ) -> jax.Array:  # shape (*grid_shape)
        grid = (
            jnp.stack(jnp.meshgrid(*map(jnp.arange, (height, width)), indexing="xy"), axis=-1) - jnp.asarray(center)
        ) / jnp.asarray(radii)
        euc_dist = (grid**2).sum(axis=-1)

        mask = euc_dist < 1
        mask = jnp.expand_dims(mask, axis=axis)

        exp_part = jnp.exp(-0.5 * euc_dist / std**2)
        exp_part = jnp.expand_dims(exp_part, axis=axis)

        profile = jnp.where(mask, exp_part, 0.0)
        profile = profile / profile.sum()

        return profile

    def _get_amplitude_raw(
        self,
        center: tuple[float, float],
    ) -> jax.Array:
        grid_radius = (self.radius / self._config.resolution).float_materialise()
        profile = self._gauss_profile(
            width=self.grid_shape[self.horizontal_axis],
            height=self.grid_shape[self.vertical_axis],
            axis=self.propagation_axis,
            center=center,
            radii=(grid_radius, grid_radius),
            std=self.std,
        )
        return profile


@autoinit
class UniformPlaneSource(LinearlyPolarizedPlaneSource):
    def _get_amplitude_raw(
        self,
        center: tuple[float, float],
    ) -> jax.Array:
        del center
        profile = jnp.ones(shape=self.grid_shape, dtype=jnp.float32)
        return profile
