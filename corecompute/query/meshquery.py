"""Definitions of queries where we want the result over a mesh.

We currently type hint our support for Cartesian, Cylindrical and Spherical
meshes, but we don't actually have any restriction for users supplying their
own mesh objects.
We are still looking at a better way to define a mesh protocol so that general
decompositions of space are supported and one can query over them. Some Oracles
will support general meshes and some will only support certain mesh types, but
we want to be able to describe our most general meaning.

"""

from dataclasses import dataclass
from itertools import pairwise
from typing import ClassVar, Any, TypeVar, Type
try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

from coremaker.mesh import CartesianMesh, CylindricalMesh, SphericalMesh
from coremaker.transform import Transform, identity
from ramp_core.serializable import Serializable, deserialize_default
from reactions import Particle, Neutron

from corecompute.query.score import Score

eV = float
Mesh = CartesianMesh | CylindricalMesh | SphericalMesh


@dataclass(init=True, frozen=True)
class MeshQuery(Serializable):
    """Represents a mesh query about some volume-averaged quantity.

    Parameters
    ----------
    mesh: Mesh
        The mesh we calculate the flux scores over.
    energies: tuple[eV, ...]
        The energy as a tuple of monotonically increasing positive energy 
        boundaries.
        If an empty tuple, it means all energy, otherwise it should be of length
        2 or more. Given in eV.
    transform: Transform
        Transform for where the mesh is in space.
    particle: Particle
        Inducing particle for the score in question. Usually a neutron.

    """
    ser_identifier: ClassVar[str] = "MeshQuery"
    mesh: Mesh
    scores: tuple[Score, ...] = (Score("flux", volume_specific=True),)
    energies: tuple[eV, ...] = ()
    transform: Transform = identity
    particle: Particle = Neutron

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
        data = dict(mesh=self.mesh.serialize(),
                    scores=[score.serialize() for score in self.scores],
                    energies=list(self.energies),
                    transform=self.transform.serialize(),
                    particle=self.particle.serialize(),
                    )
        return self.ser_identifier, data

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *, supported: dict[str, Type[Serializable]]) -> Self:
        mesh = deserialize_default(d["mesh"], supported=supported)
        scores=tuple(deserialize_default(s, supported=supported) for s in d["scores"])
        energies=tuple(d["energies"])
        transform = Transform.deserialize(d["transform"])
        particle=deserialize_default(d["particle"], supported=supported, default=Particle)
        return cls(mesh=mesh, scores=scores, energies=energies, 
                   transform=transform, particle=particle)

