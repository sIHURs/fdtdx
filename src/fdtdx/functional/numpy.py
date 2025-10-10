# ruff: noqa: F811

import math
from typing import Sequence

import jax
import jax.numpy as jnp
import numpy as np
from jaxtyping import ArrayLike
from plum import dispatch, overload

from fdtdx.core.fraction import Fraction
from fdtdx.core.jax.utils import is_traced
from fdtdx.units.typing import SI
from fdtdx.units.unitful import (
    EMPTY_UNIT,
    MAX_STATIC_OPTIMIZED_SIZE,
    Unit,
    Unitful,
    align_scales,
    can_perform_scatic_ops,
    get_static_operand,
    output_unitful_for_array,
)
from fdtdx.units.utils import dim_after_multiplication, handle_n_scales, is_struct_optimizable


## Square Root ###########################
@overload
def sqrt(
    x: Unitful,
) -> Unitful:
    new_dim: dict[SI, int | Fraction] = {}
    for k, v in x.unit.dim.items():
        if isinstance(v, int):
            if v % 2 == 0:
                new_dim[k] = v // 2
            else:
                new_dim[k] = Fraction(v, 2)
        elif isinstance(v, Fraction):
            new_dim[k] = v / 2
        else:
            raise Exception(f"Invalid dimension exponent: {v}")
    if x.unit.scale % 2 == 0:
        new_val = jnp._orig_sqrt(x.val)  # type: ignore
        new_scale = x.unit.scale // 2
    else:
        new_val = jnp._orig_sqrt(x.val) * math.sqrt(10)  # type: ignore
        new_scale = math.floor(x.unit.scale / 2)
    # static arr computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.sqrt(x_arr)
            if x.unit.scale % 2 != 0:
                new_static_arr = new_static_arr * math.sqrt(10)
    return Unitful(val=new_val, unit=Unit(scale=new_scale, dim=new_dim), static_arr=new_static_arr)


@overload
def sqrt(x: int | float) -> float:
    return math.sqrt(x)


@overload
def sqrt(x: jax.Array) -> jax.Array:
    return jnp._orig_sqrt(x)  # type: ignore


@dispatch
def sqrt(x):  # type: ignore
    del x
    raise NotImplementedError()


## Roll #####################################
@overload
def roll(
    x: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_roll(x.val, *args, **kwargs)  # type: ignore
    # static arr computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.roll(x_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def roll(
    x: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_roll(x, *args, **kwargs)  # type: ignore


@dispatch
def roll(  # type: ignore
    x,
    *args,
    **kwargs,
):
    del x, args, kwargs
    raise NotImplementedError()


## Square #####################################
@overload
def square(
    x: Unitful,
) -> Unitful:
    return x * x


@overload
def square(x: int | float) -> float:
    return x * x


@overload
def square(x: complex) -> complex:
    return x * x


@overload
def square(x: jax.Array) -> jax.Array:
    return x * x


@dispatch
def square(  # type: ignore
    x,
):
    del x
    raise NotImplementedError()


## Cross #####################################
@overload
def cross(
    a: Unitful,
    b: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_cross(a.val, b.val, *args, **kwargs)  # type: ignore
    new_scale = a.unit.scale + b.unit.scale
    unit_dict = dim_after_multiplication(a.unit.dim, b.unit.dim)
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(a)
        y_arr = get_static_operand(b)
        if x_arr is not None and y_arr is not None:
            new_static_arr = np.cross(x_arr, y_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=Unit(scale=new_scale, dim=unit_dict), static_arr=new_static_arr)


@overload
def cross(
    a: jax.Array,
    b: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_cross(a, b, *args, **kwargs)  # type: ignore


@overload
def cross(  # type: ignore
    a,
    b,
    *args,
    **kwargs,
):
    raise NotImplementedError(f"Currently not implemented for {a}, {b}, {args}, {kwargs}")


@dispatch
def cross(  # type: ignore
    a,
    b,
    *args,
    **kwargs,
):
    del a, b, args, kwargs
    raise NotImplementedError()


## Conjugate #####################################
@overload
def conj(
    x: Unitful,
) -> Unitful:
    new_val = jnp._orig_conj(x.val)  # type: ignore
    # static arr computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.conj(x_arr)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def conj(
    x: int,
) -> int:
    return x


@overload
def conj(
    x: float,
) -> float:
    return x


@overload
def conj(
    x: complex,
) -> complex:
    return x.conjugate()


@overload
def conj(
    x: jax.Array,
) -> jax.Array:
    return jnp._orig_conj(x)  # type: ignore


@dispatch
def conj(  # type: ignore
    x,
):
    del x
    raise NotImplementedError()


## dot #####################################
@overload
def dot(
    a: Unitful,
    b: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_dot(a.val, b.val, *args, **kwargs)  # type: ignore
    unit_dict = dim_after_multiplication(a.unit.dim, b.unit.dim)
    new_scale = a.unit.scale + b.unit.scale
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(a)
        y_arr = get_static_operand(b)
        if x_arr is not None and y_arr is not None:
            new_static_arr = np.dot(x_arr, y_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=Unit(scale=new_scale, dim=unit_dict), static_arr=new_static_arr)


@overload
def dot(
    a: Unitful,
    b: jax.Array | np.ndarray,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_dot(a.val, b, *args, **kwargs)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(a)
        y_arr = get_static_operand(b)
        if x_arr is not None and y_arr is not None:
            new_static_arr = np.dot(x_arr, y_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=a.unit, static_arr=new_static_arr)


@overload
def dot(
    a: jax.Array | np.ndarray,
    b: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_dot(a, b.val, *args, **kwargs)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(a)
        y_arr = get_static_operand(b)
        if x_arr is not None and y_arr is not None:
            new_static_arr = np.dot(x_arr, y_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=b.unit, static_arr=new_static_arr)


@overload
def dot(
    a: jax.Array,
    b: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_dot(a, b, *args, **kwargs)  # type: ignore


@dispatch
def dot(  # type: ignore
    a,
    b,
    *args,
    **kwargs,
):
    del a, b, args, kwargs
    raise NotImplementedError()


## Transpose #####################################
@overload
def transpose(
    x: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_transpose(x.val, *args, **kwargs)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.transpose(x_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def transpose(
    x: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_transpose(x, *args, **kwargs)  # type: ignore


@dispatch
def transpose(  # type: ignore
    x,
    *args,
    **kwargs,
):
    del x, args, kwargs
    raise NotImplementedError()


## pad #####################################
@overload
def pad(
    x: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_pad(x.val, *args, **kwargs)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.pad(x_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def pad(
    x: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_pad(x, *args, **kwargs)  # type: ignore


@dispatch
def pad(  # type: ignore
    x,
    *args,
    **kwargs,
):
    del x, args, kwargs
    raise NotImplementedError()


## stack #####################################
@overload
def stack(
    arrays: Unitful | Sequence[Unitful],
    *args,
    **kwargs,
) -> Unitful:
    if isinstance(arrays, Sequence):
        for a in arrays:
            if a.unit.dim != arrays[0].unit.dim:
                raise Exception(f"jnp.stack requires all Unitful to have the same dimension, but got: {arrays}")
        # bring all values to same scale
        new_scale, factors = handle_n_scales([a.unit.scale for a in arrays])
        scaled = [a.val * f for a, f in zip(arrays, factors)]
        # simply call original function
        new_val = jnp._orig_stack(scaled, *args, **kwargs)  # type: ignore
        new_unit = Unit(scale=new_scale, dim=arrays[0].unit.dim)
        # static computation
        new_static_arr = None
        if is_traced(new_val):
            arrs = [get_static_operand(v) for v in arrays]
            if all([v is not None for v in arrs]):
                scaled_arrs = [a * f for a, f in zip(arrs, factors)]  # type: ignore
                new_static_arr = np.stack(scaled_arrs, *args, **kwargs)  # type: ignore
    else:
        new_val = jnp._orig_stack(arrays, *args, **kwargs)  # type: ignore
        new_unit = arrays.unit
        # static computation
        new_static_arr = None
        if is_traced(new_val):
            x_arr = get_static_operand(arrays)
            if x_arr is not None:
                new_static_arr = np.stack(x_arr, *args, **kwargs)  # type: ignore
    return Unitful(val=new_val, unit=new_unit, static_arr=new_static_arr)


@overload
def stack(
    x: ArrayLike | Sequence[ArrayLike],
    *args,
    **kwargs,
) -> ArrayLike:
    if isinstance(x, Sequence):
        all_physical = all([output_unitful_for_array(x_i) for x_i in x])
    else:
        all_physical = output_unitful_for_array(x)
    # axis/dtype args/kwargs needs to be static for eval_shape
    partial_orig_fn = jax.tree_util.Partial(jnp._orig_stack, x, *args, **kwargs)  # type: ignore
    result_shape_dtype = jax.eval_shape(partial_orig_fn)
    # if we cannot convert to unitful just call original function
    if not output_unitful_for_array(result_shape_dtype) or not all_physical:
        return jnp._orig_stack(x, *args, **kwargs)  # type: ignore
    # convert inputs to unitful without dimension
    if isinstance(x, Sequence):
        unit_input = [Unitful(val=x_i, unit=EMPTY_UNIT) for x_i in x]  # type: ignore
    else:
        unit_input = Unitful(val=x, unit=EMPTY_UNIT)
    unit_result = stack(unit_input, *args, **kwargs)
    return unit_result  # type: ignore


@dispatch
def stack(  # type: ignore
    x,
    *args,
    **kwargs,
):
    del x, args, kwargs
    raise NotImplementedError()


## isfinite #####################################
@overload
def isfinite(
    x: Unitful,
    *args,
    **kwargs,
) -> jax.Array:
    new_val = jnp._orig_isfinite(x.val, *args, **kwargs)  # type: ignore
    return new_val


@overload
def isfinite(
    x: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_isfinite(x, *args, **kwargs)  # type: ignore


@dispatch
def isfinite(  # type: ignore
    x,
    *args,
    **kwargs,
):
    del x, args, kwargs
    raise NotImplementedError()


## real #####################################
@overload
def real(
    val: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_real(val.val, *args, **kwargs)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(val)
        if x_arr is not None:
            new_static_arr = np.real(x_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=val.unit, static_arr=new_static_arr)


@overload
def real(val: int, *args, **kwargs) -> int:
    return val


@overload
def real(val: float, *args, **kwargs) -> float:
    return val


@overload
def real(val: complex, *args, **kwargs) -> complex:
    return val.real


@overload
def real(val: jax.Array, *args, **kwargs) -> jax.Array:
    return jnp._orig_real(val, *args, **kwargs)  # type: ignore


@dispatch
def real(  # type: ignore
    val,
    *args,
    **kwargs,
):
    del val, args, kwargs
    raise NotImplementedError()


## imag #####################################
@overload
def imag(val: Unitful, *args, **kwargs) -> Unitful:
    new_val = jnp._orig_imag(val.val, *args, **kwargs)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(val)
        if x_arr is not None:
            new_static_arr = np.imag(x_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=val.unit, static_arr=new_static_arr)


@overload
def imag(val: int, *args, **kwargs) -> int:
    return val


@overload
def imag(val: float, *args, **kwargs) -> float:
    return val


@overload
def imag(val: complex, *args, **kwargs) -> complex:
    return val.imag


@overload
def imag(val: jax.Array, *args, **kwargs) -> jax.Array:
    return jnp._orig_imag(val, *args, **kwargs)  # type: ignore


@dispatch
def imag(  # type: ignore
    val,
    *args,
    **kwargs,
):
    del val, args, kwargs
    raise NotImplementedError()


## sin #####################################
@overload
def sin(x: Unitful) -> Unitful:
    new_val = jnp._orig_sin(x.val)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.sin(x_arr)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def sin(x: int | float) -> float:
    return math.sin(x)


@overload
def sin(x: np.ndarray | np.number) -> np.ndarray:
    return np.sin(x)


@overload
def sin(x: jax.Array) -> jax.Array:
    return jnp._orig_sin(x)  # type: ignore


@dispatch
def sin(  # type: ignore
    x,
):
    del x
    raise NotImplementedError()


## cos #####################################
@overload
def cos(x: Unitful) -> Unitful:
    new_val = jnp._orig_cos(x.val)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.cos(x_arr)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def cos(x: jax.Array) -> jax.Array:
    return jnp._orig_cos(x)  # type: ignore


@overload
def cos(x: int | float) -> float:
    return math.cos(x)


@overload
def cos(x: np.ndarray | np.number) -> np.ndarray:
    return np.cos(x)


@dispatch
def cos(  # type: ignore
    x,
):
    del x
    raise NotImplementedError()


## tan #####################################
@overload
def tan(x: Unitful) -> Unitful:
    new_val = jnp._orig_tan(x.val)  # type: ignore
    # static computation
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.tan(x_arr)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def tan(x: jax.Array) -> jax.Array:
    return jnp._orig_tan(x)  # type: ignore


@overload
def tan(x: int | float) -> float:
    return math.tan(x)


@overload
def tan(x: np.ndarray | np.number) -> np.ndarray:
    return np.tan(x)


@dispatch
def tan(  # type: ignore
    x,
):
    del x
    raise NotImplementedError()


## asarray #####################################
def asarray(
    a,
    *args,
    **kwargs,
) -> jax.Array:
    materialised = jax.tree.map(
        lambda x: x.materialise() if isinstance(x, Unitful) else x,
        a,
        is_leaf=lambda x: isinstance(x, Unitful),
    )
    partial_orig_fn = jax.tree_util.Partial(jnp._orig_asarray, materialised, *args, **kwargs)  # type: ignore
    result_shape_dtype = jax.eval_shape(partial_orig_fn)
    result: jax.Array = jnp._orig_asarray(materialised, *args, **kwargs)  # type: ignore
    if not output_unitful_for_array(result_shape_dtype):
        # cannot use this as Unitful, wrong dtype
        return result

    # try to get a static version of the array and save to trace metadata
    static_arr = None
    result_size = math.prod(result.shape)
    if is_struct_optimizable(a) and result_size <= MAX_STATIC_OPTIMIZED_SIZE:
        static_arr = np.asarray(a, copy=True)

    # return Unitful without unit. We lie to typechecker here
    return Unitful(val=result, unit=Unit(scale=0, dim={}), static_arr=static_arr)  # type: ignore


def array(
    a,
    *args,
    **kwargs,
) -> jax.Array:
    return asarray(a, *args, **kwargs)


## exp #########################################
@overload
def exp(
    x: Unitful,
) -> Unitful:
    assert x.unit.dim == {}, f"Cannot use unitful with dim {x.unit.dim} as exponent"
    # TODO: improve numerical accuracy
    new_val = jnp._orig_exp((10**x.unit.scale) * x.val)  # type: ignore
    # static arr
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.exp((10**x.unit.scale) * x_arr)
    return Unitful(val=new_val, unit=Unit(scale=0, dim={}), static_arr=new_static_arr)


@overload
def exp(
    x: jax.Array,
) -> jax.Array:
    return jnp._orig_exp(x)  # type: ignore


@overload
def exp(x: int | float) -> float:
    return math.exp(x)


@dispatch
def exp(  # type: ignore
    x,
):
    del x
    raise NotImplementedError()


## expand dims #########################################
@overload
def expand_dims(
    x: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    new_val = jnp._orig_expand_dims(x.val, *args, **kwargs)  # type: ignore
    # static arr
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.expand_dims(x_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def expand_dims(
    x: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_expand_dims(x, *args, **kwargs)  # type: ignore


@dispatch
def expand_dims(  # type: ignore
    x, *args, **kwargs
):
    del x, args, kwargs
    raise NotImplementedError()


## where #########################################
@overload
def where(
    condition: Unitful,
    x: Unitful,
    y: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    assert x.unit.dim == y.unit.dim, f"{x} and {y} need the same units for jnp.where"
    assert condition.unit.dim == {} and condition.unit.scale == 0, f"Invalid condition input: {condition}"
    x_align, y_align = align_scales(x, y)
    c_val = condition.val
    new_val = jnp._orig_where(c_val, x_align.val, y_align.val, *args, **kwargs)  # type: ignore
    # static arr
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        y_arr = get_static_operand(y)
        c_arr = get_static_operand(condition)
        if x_arr is not None and y_arr is not None and c_arr is not None:
            new_static_arr = np.where(c_arr, x_arr, y_arr, *args, **kwargs)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def where(
    condition: jax.Array | Unitful,
    x: ArrayLike,
    y: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    c = condition if isinstance(condition, Unitful) else Unitful(val=condition, unit=EMPTY_UNIT)
    return where(c, Unitful(val=x, unit=EMPTY_UNIT), y, *args, **kwargs)


@overload
def where(
    condition: jax.Array | Unitful,
    x: Unitful,
    y: ArrayLike,
    *args,
    **kwargs,
) -> Unitful:
    c = condition if isinstance(condition, Unitful) else Unitful(val=condition, unit=EMPTY_UNIT)
    return where(c, x, Unitful(val=y, unit=EMPTY_UNIT), *args, **kwargs)


@overload
def where(
    condition: jax.Array,
    x: ArrayLike,
    y: ArrayLike,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_where(condition, x, y, *args, **kwargs)  # type: ignore


@dispatch
def where(  # type: ignore
    condition, x, y, *args, **kwargs
):
    del condition, x, y, args, kwargs
    raise NotImplementedError()


## arange #########################################
def arange(
    *args,
    **kwargs,
) -> ArrayLike:
    # test if we should output unitful instead of array
    partial_orig_fn = jax.tree_util.Partial(jnp._orig_arange, *args, **kwargs)  # type: ignore
    result_shape_dtype = jax.eval_shape(partial_orig_fn)
    result = jnp._orig_arange(*args, **kwargs)  # type: ignore
    if not output_unitful_for_array(result_shape_dtype):
        return result
    # return Unitful instead of array
    static_arr = np.arange(*args, **kwargs)
    return Unitful(val=result, unit=EMPTY_UNIT, static_arr=static_arr)  # type: ignore


## meshgrid ########################################
@overload
def meshgrid(
    *args: Unitful,
    **kwargs,
) -> list[Unitful]:
    dim = args[0].unit.dim
    for xi in args:
        if xi.unit.dim != dim:
            raise Exception(f"Inconsistent units in meshgrid: {args}")
    # align the scales
    orig_scales = [a.unit.scale for a in args]
    new_scale, factors = handle_n_scales(orig_scales)
    aligned_arrs = [a.val * f for a, f in zip(args, factors)]
    new_vals = jnp._orig_meshgrid(*aligned_arrs, **kwargs)  # type: ignore
    # test if we should create static arr as well
    static_ops = [get_static_operand(a) for a in args]
    if all([can_perform_scatic_ops(o) for o in static_ops]):
        scaled_ops = [
            s * f  # type: ignore
            for s, f in zip(static_ops, factors)
        ]
        static_arrs = np.meshgrid(*scaled_ops, **kwargs)
        new_unitfuls = [
            Unitful(val=v, unit=Unit(scale=new_scale, dim=dim), static_arr=s) for v, s in zip(new_vals, static_arrs)
        ]
    else:
        new_unitfuls = [Unitful(val=v, unit=Unit(scale=new_scale, dim=dim)) for v in new_vals]
    return new_unitfuls


@overload
def meshgrid(
    *args: ArrayLike,
    **kwargs,
) -> list[ArrayLike]:
    # TODO: return Unitfuls instead of arrays if situation allows it
    return jnp._orig_meshgrid(*args, **kwargs)  # type: ignore


@dispatch
def meshgrid(  # type: ignore
    *args,
    **kwargs,
):
    del args, kwargs
    raise NotImplementedError()


## floor #########################################
@overload
def floor(
    x: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    assert x.unit.dim == {}, f"Cannot use floor on a value with non-empty unit: {x}"
    new_val = jnp._orig_floor(x.materialise(), *args, **kwargs)  # type: ignore
    # static arr
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.floor(x_arr * (10**x.unit.scale), *args, **kwargs)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def floor(
    x: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_floor(x, *args, **kwargs)  # type: ignore


@dispatch
def floor(  # type: ignore
    x, *args, **kwargs
):
    del x, args, kwargs
    raise NotImplementedError()


## ceil #########################################
@overload
def ceil(
    x: Unitful,
    *args,
    **kwargs,
) -> Unitful:
    assert x.unit.dim == {}, f"Cannot use floor on a value with non-empty unit: {x}"
    new_val = jnp._orig_ceil(x.materialise(), *args, **kwargs)  # type: ignore
    # static arr
    new_static_arr = None
    if is_traced(new_val):
        x_arr = get_static_operand(x)
        if x_arr is not None:
            new_static_arr = np.ceil(x_arr * (10**x.unit.scale), *args, **kwargs)
    return Unitful(val=new_val, unit=x.unit, static_arr=new_static_arr)


@overload
def ceil(
    x: jax.Array,
    *args,
    **kwargs,
) -> jax.Array:
    return jnp._orig_ceil(x, *args, **kwargs)  # type: ignore


@dispatch
def ceil(  # type: ignore
    x, *args, **kwargs
):
    del x, args, kwargs
    raise NotImplementedError()
