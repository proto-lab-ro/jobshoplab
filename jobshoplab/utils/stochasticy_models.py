import numpy as np
from abc import ABC, abstractmethod


class StochasticFunction(ABC):
    """Abstract class for stochastic functions."""

    def __init__(self, base_time: int):
        self.base_time = base_time

    @abstractmethod
    def __call__(self, *args, **kwargs) -> int:
        pass

    @abstractmethod
    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def __repr__(self):
        return self.__str__()

    @abstractmethod
    def __eq__(self, value: object) -> bool:
        pass


class PoissonFunction(StochasticFunction):
    def __init__(self, base_time: int, mean: float):
        super().__init__(base_time)
        self.mean = mean

    def __call__(self) -> int:
        return self.base_time + np.random.poisson(self.mean)

    def __str__(self):
        return f"{self.__class__.__name__}(base_time={self.base_time}, mean={self.mean})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PoissonFunction):
            return False
        return self.base_time == other.base_time and self.mean == other.mean


class GaussianFunction(StochasticFunction):
    def __init__(self, base_time: int, mean: float, std: float):
        super().__init__(base_time)
        self.mean = mean
        self.std = std

    def __call__(self) -> int:
        return int(round(self.base_time + np.random.normal(self.mean, self.std)))

    def __str__(self):
        return f"{self.__class__.__name__}(base_time={self.base_time}, mean={self.mean}, std={self.std})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GaussianFunction):
            return False
        return (
            self.base_time == other.base_time and self.mean == other.mean and self.std == other.std
        )


class BetaFunction(StochasticFunction):
    def __init__(self, base_time: int, alpha: float, beta: float):
        super().__init__(base_time)
        self.alpha = alpha
        self.beta = beta

    def __call__(self) -> int:
        return int(round(self.base_time + np.random.beta(self.alpha, self.beta)))

    def __str__(self):
        return f"{self.__class__.__name__}(base_time={self.base_time}, alpha={self.alpha}, beta={self.beta})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BetaFunction):
            return False
        return (
            self.base_time == other.base_time
            and self.alpha == other.alpha
            and self.beta == other.beta
        )


class GammaFunction(StochasticFunction):
    def __init__(self, base_time: int, shape: float, scale: float):
        super().__init__(base_time)
        self.shape = shape
        self.scale = scale

    def __call__(self) -> int:
        return int(round(self.base_time + np.random.gamma(self.shape, self.scale)))

    def __str__(self):
        return f"{self.__class__.__name__}(base_time={self.base_time}, shape={self.shape}, scale={self.scale})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GammaFunction):
            return False
        return (
            self.base_time == other.base_time
            and self.shape == other.shape
            and self.scale == other.scale
        )
