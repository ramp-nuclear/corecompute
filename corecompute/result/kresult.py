"""Module for common way to report k eigenvalue results.

"""
from statistics import NormalDist
from typing import Any, Type, TypeVar
try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

from ramp_core.serializable import Serializable

PCM = float

__all__ = ['KResult', 'PCM']


class KResult(Serializable):
    """Result object for k-eigenvalue results

    TODO: Replace this implementation with uncertainties' ufloat

    """
    ser_identifier = "KResult"

    def __init__(self, k: float, dk: float):
        r"""

        Parameters
        ----------
        k: float
            k-eigenvalue
        dk: float
            Error in k-eigenvalue. This usually means 1-\sigma standard
            deviation, but in other cases it can also mean just the
            convergence error, which is bounded rather than distributed
            normally.
        """

        self.k = k
        self.dk = dk

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.k == other.k and self.dk == other.dk

    def __str__(self):
        return f'KResult({self.k:.2f} ± {self.dk:.2f})'

    __repr__ = __str__

    @property
    def rho_dist(self) -> NormalDist:
        """The distribution of the reactivity according to the data.

        """
        return NormalDist(mu=self.rho, sigma=self.drho)

    @classmethod
    def from_reactivity(cls, rho: PCM, drho: PCM) -> "KResult":
        r"""Create a k-result from reactivity values.

        Parameters
        ----------
        rho: PCM
            Reactivity of the core, in PCM
        drho: PCM
            Error in terms of reactivity, in PCM. Currently used only for
            1-\sigma standard deviation. Other errors need to be included
            in the future.

        """

        k = 1. / (1. - (rho / XXX))
        return cls(k=k, dk=(k ** 2) * (drho / XXX))

    @property
    def reactivity(self) -> PCM: return 1e5 * (1. - (1. / self.k))

    rho = reactivity

    @property
    def reactivity_error(self) -> PCM: return 1e5 * (self.dk / (self.k ** 2))

    drho = reactivity_error

