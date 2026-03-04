from dataclasses import dataclass
from itertools import pairwise
from pathlib import PurePath
from typing import Any, Callable, ClassVar, Type, TypeVar

try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

from coremaker.protocols.surface import Surface
from ramp_core.serializable import Serializable, deserialize_default
from reactions.particle import NamedParticle, Neutron

eV = float
T = TypeVar("T")


def _do_unless_none(x, func: Callable[[Any], T]) -> T | None:
    return None if x is None else func(x)


@dataclass(init=True, frozen=True, repr=True)
class SurfaceCurrentQuery(Serializable):
    """Query about the current across a surface

    Parameters
    ----------
    surface: Surface
        Surface across which we compute the current
    from_component: PurePath or None
        Path of the component from which the current is coming. 
        Default is None and then all contributing components are accounted.
    to_components: PurePath or None
        Path of the component to whom the current is going.
        Default is None and then all contributing components are accounted.
    energies: tuple[eV, ...]
        A sequence of incoming energy values such that each successive pair
        defines the bounds of a bin in an energy grid. Should be either empty
        or longer than 2, positive and strictly increasing. Incoming energies
        are given in units of eV.
    particle: NamedParticle
        Particle type we count when passing the surface

    """
    ser_identifier: ClassVar[str] = "SurfaceCurrentQuery"
    surface: Surface
    from_component: PurePath | None = None
    to_component: PurePath | None = None
    energies: tuple[eV, ...] = ()
    particle: NamedParticle = Neutron

    def __post_init__(self):
        if any(a >= b for a, b in pairwise(self.energies)):
            raise ValueError("The energy grid must be strictly increasing, "
                             f"and {self.energies} isn't")
        if any(a < 0. for a in self.energies):
            raise ValueError("The energy grid must be strictly positive. "
                             f"L owest energy bound was {self.energies[0]}<0.")
        if len(self.energies) == 1:
            raise ValueError("The energy grid means energy boundaries, so it"
                             "cannot be of length 1.")

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, dict(
                surface=self.surface.serialize(),
                from_component=_do_unless_none(self.from_component, str),
                to_component=_do_unless_none(self.to_component, str),
                energies=list(self.energies),
                particle=self.particle.serialize()
                )

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *, supported: dict[str, Type[Serializable]]) -> Self:
        surface = deserialize_default(d["surface"], supported=supported)
        particle = deserialize_default(d["particle"], supported=supported)
        return cls(surface=surface,
                   from_component=_do_unless_none(d["from_component"], PurePath),
                   to_component=_do_unless_none(d["to_component"], PurePath),
                   energies=tuple(d["energies"]),
                   particle=particle)

