from abc import ABC, abstractmethod

import numpy as np


class StochasticTimeConfig(ABC):
    """Abstract class for stochastic functions."""

    def __init__(self, base_time: int, start_seed: int | None = None):
        self.base_time = base_time
        if start_seed is None:
            start_seed = np.random.randint(0, 2**5 - 1)  # 0, 2**32 - 1)
        self._current_seed = start_seed
        self._random_generator = np.random.default_rng(seed=start_seed)
        self.time = max((0, self._get_time()))

    def _update_random_generator(self):
        """Update the random seed."""
        self._current_seed += 1
        self._random_generator = np.random.default_rng(seed=self._current_seed)

    def update(self):
        """Update the random seed."""
        self._update_random_generator()
        self.time = max((0, self._get_time()))

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
    def __init__(self, base_time: int, start_seed: int | None = None):
        self.mean = base_time + 0.5  # ensures mode = base_time is roughtly the same
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


class UniformFunction(StochasticTimeConfig):
    def __init__(self, base_time: int, offset: float, start_seed: int | None = None):
        self.low = base_time - offset
        self.high = base_time + offset
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        return int(self._random_generator.uniform(self.low, self.high))

    def __str__(self):
        return f"{self.__class__.__name__}(base_time={self.base_time}, low={self.low}, high={self.high})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UniformFunction):
            return False
        return (
            self.base_time == other.base_time and self.low == other.low and self.high == other.high
        )


class GaussianFunction(StochasticTimeConfig):
    def __init__(self, base_time: int, std: float, start_seed: int | None = None):
        self.std = std
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        return int(self._random_generator.normal(self.base_time, self.std))

    def __str__(self):
        return f"{self.__class__.__name__}(mean={self.base_time}, std={self.std})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GaussianFunction):
            return False
        return self.base_time == other.base_time and self.std == other.std

class GammaFunction(StochasticTimeConfig):
    """
    Travel time model:
        T = base_time + D,    D ~ Gamma(shape, scale)

    - base_time = minimum deterministic travel time (t_min)
    - scale > 0
    - shape > 0 (controls skewness / CV)

    """
    def __init__(self, base_time: int, shape: float, scale: float, start_seed: int | None = None):
        if scale <= 0:
            raise ValueError("Scale must be positive.")
        if shape <= 0:
            raise ValueError("Shape must be positive for the Gamma distribution.")
        if base_time < 0:
            raise ValueError("Base time must be non-negative.")

        self.base_time = base_time
        self.shape = shape
        self.scale = scale
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        # sample delay >= 0
        delay = self._random_generator.gamma(self.shape, self.scale)
        return int(round(self.base_time + delay))

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

class GammaFunction(StochasticTimeConfig):
    """
    Travel time model:
        T = base_time + D,    D ~ Gamma(shape, scale)

    - base_time = minimum deterministic travel time (t_min)
    - scale > 0
    - shape > 0 (controls skewness / CV)

    """
    def __init__(self, base_time: int, shape: float, scale: float, start_seed: int | None = None):
        if scale <= 0:
            raise ValueError("Scale must be positive.")
        if shape <= 0:
            raise ValueError("Shape must be positive for the Gamma distribution.")
        if base_time < 0:
            raise ValueError("Base time must be non-negative.")

        self.base_time = base_time
        self.shape = shape
        self.scale = scale
        super().__init__(base_time, start_seed)

    def _get_time(self) -> int:
        # sample delay >= 0
        delay = self._random_generator.gamma(self.shape, self.scale)
        return int(round(self.base_time + delay))

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
    poisson = PoissonFunction(base_time=10, start_seed=42)
    print(poisson.time)  # Random value based on Poisson distribution
    print(poisson)  # String representation
    print(poisson == PoissonFunction(base_time=10))  # True
