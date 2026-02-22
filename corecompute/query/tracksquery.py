from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Any, Type, TypeVar
try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

from coremaker.protocols.surface import Surface
from ramp_core.serializable import Serializable, deserialize_default
from reactions import Particle


@dataclass(init=True, frozen=True)
class SurfaceTracksQuery(Serializable):
    """A query about particle tracks that pass a given surface.
    These are supposed to be a bunch of particle tracks, but the current
    implementation uses a file. The format is unknown and must be defined.
    Currently only really usable by the OpenMC Oracle...

    TODO: Define the file format or change this to actual data.

    """
    ser_identifier: ClassVar[str] = "SurfaceTracksQuery"
    path: Path
    surfaces: tuple[Surface, ...]
    particles: tuple[Particle, ...]
    maximal_number_of_particles: int | None = None

    def __post_init__(self):
        object.__setattr__(self, 'path', self.path.absolute())

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, dict(
                path=str(self.path),
                surfaces=[sur.serialize() for sur in self.surfaces],
                particles=[p.serialize() for p in self.particles],
                max_particles=self.maximal_number_of_particles
                )

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *, supported: dict[str, Type[Serializable]]) -> Self:
        surfaces = tuple(deserialize_default(s, supported=supported) 
                         for s in d["surfaces"])
        particles = tuple(deserialize_default(p, supported=supported) 
                          for p in d["particles"])
        return cls(path=Path(d["path"]),
                   surfaces=surfaces,
                   particles=particles,
                   maximal_number_of_particles=d["max_particles"],
                   )

