import numpy as np
import pytest

from jobshoplab.types.stochasticy_models import (
    GammaFunction,
    GaussianFunction,
    PoissonFunction,
    UniformFunction,
)


# Helper function that mimics the _update_random_generator process.
def get_expected_value(func_cls, *args, start_seed, base_time, compute_func, **kwargs):
    """
    Given the function class and a fixed start_seed,
    compute the expected time value.
    The function simulates the _update_random_generator behavior.
    """
    seed_for_call = start_seed
    rng = np.random.default_rng(seed=seed_for_call)
    return compute_func(rng, base_time, **kwargs)


def poisson_sample(rng, base_time):
    mean = base_time + 0.5  # ensures mode = base_time
    return base_time + rng.poisson(mean)


def gaussian_sample(rng, base_time, std):
    return int(rng.normal(base_time, std))


def uniform_sample(rng, base_time, offset):
    return int(rng.uniform(base_time - offset, base_time + offset))


def gamma_sample(rng, base_time, scale):
    shape = ((base_time / scale) + 1) if base_time >= 0 and scale > 0 else 1
    return int(round(base_time + rng.gamma(base_time, scale)))


@pytest.mark.parametrize(
    "base_time,start_seed",
    [
        (10, 42),
        (0, 100),
    ],
)
def test_poisson_function_time(base_time, start_seed):
    func = PoissonFunction(base_time=base_time, start_seed=start_seed)
    # Get expected value using our helper mimicking _update_random_generator.
    expected = get_expected_value(
        PoissonFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=poisson_sample,
    )
    val = func.time  # This call get a value from a fixed seed random generator.
    assert isinstance(val, int)
    assert val == expected
    # assert multiple calls to time then same value
    for _ in range(10):
        assert func.time == expected
    # assert different seed generates different value
    # Since with base_time=0 and small random values, we might occasionally
    # get the same value even after seed update, so we'll update until different
    for _ in range(10):  # Try a few times to get a different value
        func.update()
        new_expected = func.time
        if new_expected != expected:
            break

    # Skip this assertion for base_time=0 as it's possible to get the same value
    if base_time > 0:
        assert new_expected != expected
    for _ in range(10):
        assert func.time == new_expected


def test_poisson_function_str_and_eq():
    func1 = PoissonFunction(base_time=10, start_seed=42)
    func2 = PoissonFunction(base_time=10)
    mean = 10 + 0.5  # Based on implementation
    assert str(func1) == f"PoissonFunction(base_time=10, mean={mean})"
    assert func1 == func2


@pytest.mark.parametrize(
    "base_time,std,start_seed",
    [
        (20, 1, 123),
    ],
)
def test_gaussian_function_time(base_time, std, start_seed):
    func = GaussianFunction(base_time=base_time, std=std, start_seed=start_seed)
    expected = get_expected_value(
        GaussianFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=gaussian_sample,
        std=std,
    )
    val = func.time
    assert isinstance(val, int)
    assert val == expected


def test_gaussian_function_str_and_eq():
    func1 = GaussianFunction(base_time=20, std=1, start_seed=123)
    func2 = GaussianFunction(base_time=20, std=1)
    expected_str = "GaussianFunction(mean=20, std=1)"
    assert str(func1) == expected_str
    assert func1 == func2


@pytest.mark.parametrize(
    "base_time,offset,start_seed",
    [
        (5, 2, 7),
    ],
)
def test_uniform_function_time(base_time, offset, start_seed):
    func = UniformFunction(base_time=base_time, offset=offset, start_seed=start_seed)
    expected = get_expected_value(
        UniformFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=uniform_sample,
        offset=offset,
    )
    val = func.time
    assert isinstance(val, int)
    assert val == expected


def test_uniform_function_str_and_eq():
    func1 = UniformFunction(base_time=5, offset=2, start_seed=7)
    func2 = UniformFunction(base_time=5, offset=2)
    expected_str = "UniformFunction(base_time=5, low=3, high=7)"
    assert str(func1) == expected_str
    assert func1 == func2


@pytest.mark.parametrize(
    "base_time,scale,start_seed",
    [
        (15, 3.0, 99),
    ],
)
def test_gamma_function_time(base_time, scale, start_seed):
    func = GammaFunction(base_time=base_time, scale=scale, start_seed=start_seed)
    expected = get_expected_value(
        GammaFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=gamma_sample,
        scale=scale,
    )
    val = func.time
    assert isinstance(val, int)
    assert val == expected


def test_gamma_function_str_and_eq():
    func1 = GammaFunction(base_time=15, scale=3.0, start_seed=99)
    func2 = GammaFunction(base_time=15, scale=3.0)
    # Calculate the expected shape based on the implementation
    shape = func1._compute_gamma_shape_from_mode(15, 3.0)
    expected_str = f"GammaFunction(base_time=15, shape={shape}, scale=3.0)"
    assert str(func1) == expected_str
    assert func1 == func2
