from abc import ABC, abstractmethod

import numpy as np


class StochasticTimeConfig(ABC):
    """Abstract class for stochastic functions."""

    def __init__(self, base_time: int, start_seed: int | None = None):
        self.base_time = base_time
        if start_seed is None:
            start_seed = np.random.randint(0, 2**32 - 1)
        self._current_seed = start_seed
        self._random_generator = np.random.default_rng(seed=start_seed)
        self.time = self._get_time()

    def _update_random_generator(self):
        """Update the random seed."""
        self._current_seed += 1
        self._random_generator = np.random.default_rng(seed=self._current_seed)

    def update(self):
        """Update the random seed."""
        self._update_random_generator()
        self.time = self._get_time()

    @abstractmethod
    def _get_time(self) -> int:
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


class PoissonFunction(StochasticTimeConfig):
    def __init__(self, base_time: int, mean: float, start_seed: int | None = None):
        self.mean = mean
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        return self.base_time + self._random_generator.poisson(self.mean)

    def __str__(self):
        return f"{self.__class__.__name__}(base_time={self.base_time}, mean={self.mean})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PoissonFunction):
            return False
        return self.base_time == other.base_time and self.mean == other.mean


class GaussianFunction(StochasticTimeConfig):
    def __init__(self, base_time: int, mean: float, std: float, start_seed: int | None = None):
        self.mean = mean
        self.std = std
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        return int(round(self.base_time + self._random_generator.normal(self.mean, self.std)))

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


class BetaFunction(StochasticTimeConfig):
    def __init__(self, base_time: int, alpha: float, beta: float, start_seed: int | None = None):
        self.alpha = alpha
        self.beta = beta
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        return int(round(self.base_time + self._random_generator.beta(self.alpha, self.beta)))

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


class GammaFunction(StochasticTimeConfig):
    def __init__(self, base_time: int, shape: float, scale: float, start_seed: int | None = None):
        self.shape = shape
        self.scale = scale
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        return int(round(self.base_time + self._random_generator.gamma(self.shape, self.scale)))

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


if __name__ == "__main__":
    # Example usage
    poisson = PoissonFunction(base_time=10, mean=5, start_seed=42)
    print(poisson.time)  # Random value based on Poisson distribution
    print(poisson)  # String representation
    print(poisson == PoissonFunction(base_time=10, mean=5))  # True
