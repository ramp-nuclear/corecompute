"""Expected result for a VolumeQuery

When a VolumeQuery is answered, we expect to get a Generator of these result
types.

"""

from dataclasses import dataclass, field
from pathlib import PurePath
from typing import ClassVar, Any, Type, TypeVar
try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

from ramp_core.serializable import Serializable, deserialize_default
from reactions import Particle


from corecompute.query.score import Score, ReactionScore

eV = float


@dataclass(frozen=True)
class VolumeResult(Serializable):
    component: PurePath
    score: Score | ReactionScore
    value: float
    error: float
    particle: Particle
    upper_energy: eV | None = field(kw_only=True, default=None)
    lower_energy: eV | None = field(kw_only=True, default=None)
    ser_identifier: ClassVar[str] = "VolumeResult"

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, dict(component=str(self.component),
                                         score=self.score.serialize(),
                                         value=self.value,
                                         error=self.error,
                                         particle=self.particle.serialize(),
                                         energies=[self.lower_energy, self.upper_energy],
                                         )

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *, supported: dict[str, Type[Serializable]]) -> Self:
        low, up = d["energies"]
        score = deserialize_default(d["score"], supported=supported)
        particle = deserialize_default(d["particle"], supported=supported, default=Particle)
        return cls(component=PurePath(d["component"]),
                   score=score,
                   value=d["value"], error=d["error"],
                   particle=particle,
                   upper_energy=up, lower_energy=low,
                   )

