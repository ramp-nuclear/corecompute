""""Queries that are averaged over the volume of a component

"""
from dataclasses import dataclass
from pathlib import PurePath
from typing import Sequence, ClassVar, Any, Type, TypeVar
try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

from more_itertools import pairwise
from ramp_core.serializable import Serializable, deserialize_default
from reactions import Neutron
from reactions.particle import NamedParticle, Particle

from corecompute.query.score import Score, ReactionScore, TabulatedScore

eV = float
Scorable = Score | ReactionScore | TabulatedScore


@dataclass(init=True, frozen=True, repr=True)
class VolumeQuery(Serializable):
    """A query about some volume averaged quantity.

    Parameters
    ----------
    names: tuple[PurePath, ...]
        A tuple of component paths to tally at.
    scores: tuple[Scorable, ...] 
        A sequence of things to tally at the component volumes.
        Usually these would be reaction rates, or the default flux score.
    energies: tuple[eV, ...]
        A sequence of incoming energy values such that each successive pair
        defines the bounds of a bin in an energy grid. Should be either empty
        or longer than 2, positive and strictly increasing. Incoming energies
        are given in units of eV.
    particle: NamedParticle | tuple[NamedParticle, ...]
        Inducing Particle type[s]

    """
    ser_identifier = "VolumeQuery"
    names: tuple[PurePath, ...]
    scores: Sequence[Score | ReactionScore] = (Score('flux', volume_specific=True),)
    energies: tuple[eV, ...] = ()
    particle: NamedParticle | tuple[NamedParticle, ...] = Neutron

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
        parts = (self.particle.serialize() if isinstance(self.particle, NamedParticle)
                 else [p.serialize() for p in self.particle])
        return self.ser_identifier, dict(names=[str(name) for name in self.names],
                                         scores=[s.serialize() for s in self.scores],
                                         energies = list(self.energies),
                                         particle=parts,
                                         )

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *, supported: dict[str, Type[Serializable]]) -> Self:
        particle = d["particle"]
        parts = (deserialize_default(particle, supported=supported, default=Particle) 
                 if isinstance(particle[0], str) else 
                 tuple(deserialize_default(p, supported=supported, default=Particle) for p in particle)
                 )
        scores=tuple(deserialize_default(s, supported=supported) for s in d["scores"])
        return cls(names=tuple(map(PurePath, d["names"])),
                   scores=scores,
                   energies=tuple(d["energies"]),
                   particle=parts,
                   )

