import numpy as np
import pytest

from jobshoplab.types.stochasticy_models import (
    PoissonFunction,
    GaussianFunction,
    BetaFunction,
    GammaFunction,
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
    computed = compute_func(rng, **kwargs)
    return base_time + computed


def poisson_sample(rng, mean):
    return int(round(rng.poisson(mean)))


def gaussian_sample(rng, mean, std):
    # We use normal distribution and round the value.
    return int(round(rng.normal(mean, std)))


def beta_sample(rng, alpha, beta):
    # beta returns value in [0,1], so rounding is performed.
    return int(round(rng.beta(alpha, beta)))


def gamma_sample(rng, shape, scale):
    return int(round(rng.gamma(shape, scale)))


@pytest.mark.parametrize(
    "base_time,mean,start_seed",
    [
        (10, 5, 42),
        (0, 3, 100),
    ],
)
def test_poisson_function_time(base_time, mean, start_seed):
    func = PoissonFunction(base_time=base_time, mean=mean, start_seed=start_seed)
    # Get expected value using our helper mimicking _update_random_generator.
    expected = get_expected_value(
        PoissonFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=poisson_sample,
        mean=mean,
    )
    val = func.time  # This call get a value from a fixed seed random generator.
    assert isinstance(val, int)
    assert val == expected
    # assert multiple calls to time then same value
    for _ in range(10):
        assert func.time == expected
    # assert different seed generates different value
    func.update()
    new_expected = func.time
    assert new_expected != expected
    for _ in range(10):
        assert func.time == new_expected


def test_poisson_function_str_and_eq():
    func1 = PoissonFunction(base_time=10, mean=5, start_seed=42)
    func2 = PoissonFunction(base_time=10, mean=5)
    assert str(func1) == "PoissonFunction(base_time=10, mean=5)"
    assert func1 == func2


@pytest.mark.parametrize(
    "base_time,mean,std,start_seed",
    [
        (20, 0, 1, 123),
    ],
)
def test_gaussian_function_time(base_time, mean, std, start_seed):
    func = GaussianFunction(base_time=base_time, mean=mean, std=std, start_seed=start_seed)
    expected = get_expected_value(
        GaussianFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=gaussian_sample,
        mean=mean,
        std=std,
    )
    val = func.time
    assert isinstance(val, int)
    assert val == expected


def test_gaussian_function_str_and_eq():
    func1 = GaussianFunction(base_time=20, mean=0, std=1, start_seed=123)
    func2 = GaussianFunction(base_time=20, mean=0, std=1)
    expected_str = "GaussianFunction(base_time=20, mean=0, std=1)"
    assert str(func1) == expected_str
    assert func1 == func2


@pytest.mark.parametrize(
    "base_time,alpha,beta,start_seed",
    [
        (5, 2.0, 5.0, 7),
    ],
)
def test_beta_function_time(base_time, alpha, beta, start_seed):
    func = BetaFunction(base_time=base_time, alpha=alpha, beta=beta, start_seed=start_seed)
    expected = get_expected_value(
        BetaFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=beta_sample,
        alpha=alpha,
        beta=beta,
    )
    val = func.time
    assert isinstance(val, int)
    assert val == expected


def test_beta_function_str_and_eq():
    func1 = BetaFunction(base_time=5, alpha=2.0, beta=5.0, start_seed=7)
    func2 = BetaFunction(base_time=5, alpha=2.0, beta=5.0)
    expected_str = "BetaFunction(base_time=5, alpha=2.0, beta=5.0)"
    assert str(func1) == expected_str
    assert func1 == func2


@pytest.mark.parametrize(
    "base_time,shape,scale,start_seed",
    [
        (15, 2.0, 3.0, 99),
    ],
)
def test_gamma_function_time(base_time, shape, scale, start_seed):
    func = GammaFunction(base_time=base_time, shape=shape, scale=scale, start_seed=start_seed)
    expected = get_expected_value(
        GammaFunction,
        base_time=base_time,
        start_seed=start_seed,
        compute_func=gamma_sample,
        shape=shape,
        scale=scale,
    )
    val = func.time
    assert isinstance(val, int)
    assert val == expected


def test_gamma_function_str_and_eq():
    func1 = GammaFunction(base_time=15, shape=2.0, scale=3.0, start_seed=99)
    func2 = GammaFunction(base_time=15, shape=2.0, scale=3.0)
    expected_str = "GammaFunction(base_time=15, shape=2.0, scale=3.0)"
    assert str(func1) == expected_str
    assert func1 == func2
