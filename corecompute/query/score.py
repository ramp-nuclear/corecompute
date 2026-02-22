from dataclasses import dataclass, asdict
from typing import (
        Sequence, Protocol, Type, Iterable, Literal, Any, ClassVar, TypeVar,
        )
try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

import numpy as np
from ramp_core.serializable import Serializable, deserialize_default
from reactions import ReactionType

SUPPORTED_SCORE = Literal["flux", "flux-q-prompt", "heating"]


@dataclass(init=True, frozen=True)
class Score(Serializable):
    r"""A kind of score to tally that yields fluxes

    Parameters
    ----------
    name: SUPPORTED_SCORE
        Score name, which is used to pick how to calculate this score.
    volume_specific: bool
        If True, the results are an intrinsic, volume-distribution value.
        For example, a flux would have units of :math:`\frac{n}{cm^2 sn}`.
        If False, the results are extrinsic, meaning they are integrated over
        some volume. The units for flux would be :math:`\frac{n\cdot cm}{sn}`.
    """
    ser_identifier: ClassVar[str] = "Score"
    name: SUPPORTED_SCORE
    volume_specific: bool

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, asdict(self)


class TabulatedValues(Protocol):
    """A callable that has an underlying grid of points where it is evaluated.

    """

    x: Sequence[float]

    def __call__(self, x: float) -> float:
        ...


def thin(x: np.ndarray, y: np.ndarray, tolerance=1e-3) -> tuple[np.ndarray, np.ndarray]:
    """Check for [x,y] points that can be removed.

    Parameters
    ----------
    x: np.ndarray
        Independent variable
    y: np.ndarray
        Dependent variable
    tolerance: float
        Tolerance on interpolation error

    Returns
    -------
    np.ndarray, np.ndarray
        Filtered-out x, y vectors
    """
    x_out = x.copy()
    y_out = y.copy()
    N = x.shape[0]
    i_left, i_right = 0, 2
    while i_left < N - 2 and i_right < N:
        m = (y[i_right] - y[i_left]) / (x[i_right] - x[i_left])

        for i in range(i_left + 1, i_righj):
            y_interp = y[i_left] + m * (x[i]-x[i_left])
            error = abs((y_interp - y[i]) / y[i]) if abs(y[i]) > 0. else 2 * tolerance
            if error > tolerance:
                mask = slice(i_left+1, i_right-1)
                x_out[mask] = np.nan
                i_left = i_right-1
                i_right = i_left+1
                break
        i_right += 1

    mask = slice(i_left + 1, i_right - 1)
    x_out[mask], y_out[mask] = np.nan, np.nan
    return x_out[np.isfinite(x_out)], y_out[np.isfinite(x_out)]


def linearize(x: Iterable[float], f: Callable[[float], float], tolerance=1e-3
              ) -> tuple[np.ndarray, np.ndarray]:
    """Return a tabulated representation of a one-variable function

    Parameters
    ----------
    x: Iterable[float]
        Initial x values where we want to evaluate the function
    f: Callable[[float], float]
        Single variable scalar function.
    tolerance: float
        Tolerance on the allower interpolation error.

    Returns
    -------
    np.ndarray, np.ndarray
        Independent and dependent values, correspondingly.

    """
    x = np.asarray(x)
    x_out, y_out = [], []
    x_stack, y_stack = [x[0]], [f(x[0])]

    for i in range(x.shape[0] - 1):
        x_stack.insert(0, x[i + 1])
        y_stack.insert(0, f(x[i + 1]))

        while True:
            xhigh, xlow = x_stack[-2:]
            yhigh, ylow = y_stack[-2:]
            xmid = (xlow + xhigh) / 2
            ymid = f(xmid)
            m = (yhigh - ylow) / (xhigh - xlow)

            yinterp = ylow + m * (xmid-xlow)
            error = abs((yinterp-ymid) / ymid)
            if error > tolerance:
                x_stack.insert(-1, xmid)
                y_stack.insert(-1, ymid)
            else:
                x_out.append(x_stack.pop())
                y_out.append(y_stack.pop())
                if len(x_stack) == 1:
                    break
    x_out.append(x_stack.pop())
    y_out.append(y_stack.pop())
    return np.array(x_out), np.array(y_out)


@dataclass(init=True, frozen=True)
class TabulatedScore(Serializable):
    r"""Tabluated score with linear-linear interpolation

    Parameters
    ----------
    energy:
        Energy grid, in eV. Must have length>=2.
    score:
        Score values on the same energy grid
    volume_specific: bool
        If True, the results are an intrinsic, volume-distribution value.
        For example, a flux would have units of :math:`\frac{n}{cm^2 sn}`.
        If False, the results are extrinsic, meaning they are integrated over
        some volume. The units for flux would be :math:`\frac{n\cdot cm}{sn}`.

    """
    ser_identifier: ClassVar[str] = "TabulatedScore"
    energy: np.ndarray
    score: np.ndarray
    volume_specific: bool

    def __post_init__(self):
        if len(self.energy) < 2:
            raise ValueError("Length of energy grid must be >=2")
        if len(self.score) != len(self.energy):
            raise ValueError("Length of score vector must match the energy grid")

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (np.all(self.energy == other.energy)
                and np.all(self.score == other.score)
                and self.volume_specific == other.volume_specific)

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, dict(energy=self.energy.tolist(),
                                         score=self.score.tolist(),
                                         volume_specific=self.volume_specific)

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *_, **__) -> Self:
        return cls(energy=np.array(d["energy"]), score=np.array(d["score"]),
                   volume_specific=d["volume_specific"])

    @classmethod
    def from_tabulated(cls: Type[Self], 
                       tabulated: TabulatedValues, 
                       volume_specific: bool) -> Self:
        """Create this tabulated score from tabulated values.

        """
        energy, score = thin(*linearize(tabulated.x, tabulated))
        return cls(energy, score, volume_specific)


@dataclass(init=True, frozen=True)
class ReactionScore(Serializable):
    r"""Score for nuclear reactions.

    Parameters
    ----------
    reaction: ReactionType
    volume_specific: bool
        If True, the results are an intrinsic, volume-distribution value.
        For example, a flux would have units of :math:`\frac{n}{cm^2 sn}`.
        If False, the results are extrinsic, meaning they are integrated over
        some volume. The units for flux would be :math:`\frac{n\cdot cm}{sn}`.
    density_specific: bool
        If True, the results are given per number density (which itself has units
        of 1/barn-cm).

    """

    ser_identifier: ClassVar[str] = "ReactionScore"
    reaction: ReactionType
    volume_specific: bool
    density_specific: bool

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, dict(reaction=self.reaction.serialize(),
                                         volume_specific=self.volume_specific,
                                         density_specific=self.density_specific)

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *, supported: dict[str, Type[Serializable]]) -> Self:
        reaction: ReactionType = deserialize_default(d["reaction"], supported=supported)
        del d["reaction"]
        return cls(reaction=reaction, **d)
        

