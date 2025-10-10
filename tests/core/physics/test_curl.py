import jax.numpy as jnp

import fdtdx.functional as ff
from fdtdx.core.physics.curl import curl_E, curl_H, interpolate_fields
from fdtdx.units import A, V, m


def test_interpolate_fields_basic():
    """Test basic interpolation functionality with simple field configuration."""
    # Create simple test fields
    E_field = (V / m) * jnp.ones((3, 5, 5, 5))
    H_field = (A / m) * jnp.ones((3, 5, 5, 5)) * 0.5

    E_interp, H_interp = interpolate_fields(E_field, H_field)

    # Check output shapes
    assert E_interp.shape == (3, 5, 5, 5)
    assert H_interp.shape == (3, 5, 5, 5)

    # Check that interpolated values are reasonable
    assert jnp.all(E_interp[2].value() == 1.0)  # E_z should remain unchanged
    assert jnp.all(ff.isfinite(E_interp))
    assert jnp.all(ff.isfinite(H_interp))


def test_interpolate_fields_periodic_boundaries():
    """Test interpolation with periodic boundary conditions."""
    # Create test fields with gradients
    x = jnp.linspace(0, 2 * jnp.pi, 6)
    y = jnp.linspace(0, 2 * jnp.pi, 6)
    z = jnp.linspace(0, 2 * jnp.pi, 6)
    X, Y, Z = jnp.meshgrid(x, y, z, indexing="ij")

    E_field = (V / m) * jnp.stack([jnp.sin(X), jnp.cos(Y), jnp.sin(Z)], axis=0)
    H_field = (A / m) * jnp.stack([jnp.cos(X), jnp.sin(Y), jnp.cos(Z)], axis=0)

    # Test with all periodic boundaries
    E_interp, H_interp = interpolate_fields(E_field, H_field, periodic_axes=(True, True, True))

    assert E_interp.shape == (3, 6, 6, 6)
    assert H_interp.shape == (3, 6, 6, 6)
    assert jnp.all(ff.isfinite(E_interp))
    assert jnp.all(ff.isfinite(H_interp))


def test_interpolate_fields_mixed_boundaries():
    """Test interpolation with mixed periodic and PEC boundary conditions."""
    E_field = (V / m) * jnp.ones((3, 6, 6, 6))
    H_field = (A / m) * jnp.ones((3, 6, 6, 6)) * 2.0

    # Test with periodic x, PEC y,z
    E_interp, H_interp = interpolate_fields(E_field, H_field, periodic_axes=(True, False, False))

    assert E_interp.shape == (3, 6, 6, 6)
    assert H_interp.shape == (3, 6, 6, 6)
    assert jnp.all(ff.isfinite(E_interp))
    assert jnp.all(ff.isfinite(H_interp))


def test_interpolate_fields_zero_fields():
    """Test interpolation with zero input fields."""
    E_field = (V / m) * jnp.zeros((3, 4, 4, 4))
    H_field = (A / m) * jnp.zeros((3, 4, 4, 4))

    E_interp, H_interp = interpolate_fields(E_field, H_field)

    assert E_interp.shape == (3, 4, 4, 4)
    assert H_interp.shape == (3, 4, 4, 4)
    assert jnp.allclose(E_interp.value(), 0.0)
    assert jnp.allclose(H_interp.value(), 0.0)


def test_curl_E_uniform_field():
    """Test curl_E with uniform electric field (should give zero curl)."""
    E = (V / m) * jnp.ones((3, 5, 5, 5))
    resolution = 1 * m

    curl_result = curl_E(E, resolution, periodic_axes=(True, True, True))

    assert curl_result.shape == (3, 5, 5, 5)
    assert jnp.allclose(curl_result.value(), 0.0, atol=1e-10)


def test_curl_E_linear_field():
    """Test curl_E with a linear field that has known curl."""
    # Create a field with E_x = y, E_y = -x, E_z = 0
    # This should give curl = (0, 0, -2)
    nx, ny, nz = 6, 6, 6
    x = jnp.arange(nx)
    y = jnp.arange(ny)
    z = jnp.arange(nz)
    X, Y, Z = jnp.meshgrid(x, y, z, indexing="ij")

    E = (V / m) * jnp.stack(
        [
            Y.astype(float),  # E_x = y
            -X.astype(float),  # E_y = -x
            jnp.zeros_like(X, dtype=float),  # E_z = 0
        ],
        axis=0,
    )
    resolution = 1 * m

    curl_result = curl_E(E, resolution, periodic_axes=(True, True, True))

    assert curl_result.shape == (3, 6, 6, 6)
    # The z-component should be approximately -2 (discrete approximation)
    assert jnp.allclose(curl_result[2][:-1, :-1].value(), -2.0, atol=0.1)


def test_curl_E_periodic_boundaries():
    """Test curl_E with periodic boundary conditions."""
    # Create sinusoidal field
    x = jnp.linspace(0, 2 * jnp.pi, 8)
    y = jnp.linspace(0, 2 * jnp.pi, 8)
    z = jnp.linspace(0, 2 * jnp.pi, 8)
    X, Y, Z = jnp.meshgrid(x, y, z, indexing="ij")

    E = (V / m) * jnp.stack([jnp.sin(Y), jnp.cos(X), jnp.sin(Z)], axis=0)
    resolution = 1 * m

    curl_result = curl_E(E, resolution, periodic_axes=(True, True, True))

    assert curl_result.shape == (3, 8, 8, 8)
    assert jnp.all(ff.isfinite(curl_result))


def test_curl_H_uniform_field():
    """Test curl_H with uniform magnetic field (should give zero curl)."""
    H = (A / m) * jnp.ones((3, 5, 5, 5)) * 2.0

    curl_result = curl_H(H, 1 * m, periodic_axes=(True, True, True))

    assert curl_result.shape == (3, 5, 5, 5)
    assert jnp.allclose(curl_result.value(), 0.0, atol=1e-10)


def test_curl_H_linear_field():
    """Test curl_H with a linear field that has known curl."""
    # Create a field with H_x = z, H_y = 0, H_z = -x
    # This should give curl = (0, 2, 0)
    nx, ny, nz = 6, 6, 6
    x = jnp.arange(nx)
    y = jnp.arange(ny)
    z = jnp.arange(nz)
    X, Y, Z = jnp.meshgrid(x, y, z, indexing="ij")

    H = (A / m) * jnp.stack(
        [
            Z.astype(float),  # H_x = z
            jnp.zeros_like(Y, dtype=float),  # H_y = 0
            -X.astype(float),  # H_z = -x
        ],
        axis=0,
    )

    curl_result = curl_H(H, 1 * m)

    assert curl_result.shape == (3, 6, 6, 6)
    # The y-component should be approximately 2 (discrete approximation)
    assert jnp.allclose(curl_result[1][1:-1, 1:-1, 1:-1].value(), 2.0, atol=0.1)


def test_curl_H_periodic_boundaries():
    """Test curl_H with periodic boundary conditions."""
    # Create sinusoidal field
    x = jnp.linspace(0, 2 * jnp.pi, 8)
    y = jnp.linspace(0, 2 * jnp.pi, 8)
    z = jnp.linspace(0, 2 * jnp.pi, 8)
    X, Y, Z = jnp.meshgrid(x, y, z, indexing="ij")

    H = (A / m) * jnp.stack([jnp.cos(Y), jnp.sin(X), jnp.cos(Z)], axis=0)

    curl_result = curl_H(H, 1 * m, periodic_axes=(True, True, True))

    assert curl_result.shape == (3, 8, 8, 8)
    assert jnp.all(ff.isfinite(curl_result))
