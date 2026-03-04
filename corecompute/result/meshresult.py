"""Results of a MeshQuery"""
from dataclasses import dataclass
from typing import Any, ClassVar, Type, TypeVar

try:
    from typing import Self
except ImportError:
    Self = TypeVar("Self")

import xarray
from ramp_core.serializable import Serializable

UNITS = "units"
LONG_NAME = "long_name"


@dataclass(frozen=True)
class MeshResult(Serializable):
    r"""Mesh query result.

    This is a thin wrapper over a xarray.Dataset. We are using this composition
    based wrapper because we want to control serialization while having the
    Dataset tools for output post-processing.

    However, to ensure adapter compatibility, we need all adapters to return a
    similarly structured xarray.
    Therefore, we define it here:

    The dataset has dimensions that correspond to the query mesh.
    For Cartesian mesh, this is "xyz" and possibly "e".
    For Cylindrical mesh, this is "rzθ" and possibly "e".
    For Spherical mesh, this is currently undefined behavior.
    The "e" dimension exists if the query energies are not :math:`[0, \infty]`,
    to define the non-infinite range.

    The dataset coordinates lie in the center of each mesh direction (center of
    :math:`r^2` for cylinders).
    The dataset should have attrs for each dimension to explain its units. These
    should be a dict of the form {UNITS: str, LONG_NAME: str}, according to the
    constants UNITS, LONG_NAME in this module.

    The data_vars should be "mean" and "std", which are the nominal value and
    its standard error. The choice of names assumes that the standard error
    corresponds to a normal distribution, because this is mostly used by MC codes.

    """

    ser_identifier: ClassVar[str] = "MeshResult"
    array: xarray.Dataset

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.array.equals(other.array)

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, self.array.compute().to_dict(data="list")

    @classmethod
    def deserialize(cls: Type[Self], d: dict[str, Any], *, supported: dict[str, Type[Serializable]]) -> Self:
        return cls(xarray.Dataset.from_dict(d))

