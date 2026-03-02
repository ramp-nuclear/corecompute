"""Query for power distributions"""

from typing import Any
from ramp_core.serializable import Serializable

MW = float

class HeatingRateQuery(Serializable):
    """Query about the total heating rate per neutron source.
    This has units of J per neutron source, and is often used for power
    normalization.

    There are many ways to estimate the power, depending on what reactions are
    accounted for. The power estimation method is specified by this object,
    and each Oracle may support different sets of methods.
    For example, the OpenMC Oracle supports the use of "heating", "heating-local",
    "kappa-fission", "fission-q-prompt" and "fission-q-recoverable", which
    correspond to their proper OpenMC scores.

    If the Oracle maintainers for your Oracle made the effort, you may find an
    Enum of applicable methods in their package.

    Parameters
    ----------
    method: str
        The method to use. Hopefully supported by your Oracle.
    kwargs:
        Keyword arguments which make sense for this particular method.

    """

    ser_identifier = "HeatingRateQuery"

    def __init__(self, method: str, **kwargs):
        self.method = method
        self.__dict__.update(kwargs)
        self._keys = list(kwargs.keys())

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return self.ser_identifier, self._asdict()

    @classmethod
    def deserialize(cls, d: dict[str, Any], *_, **__):
        return cls(**d)

    def _asdict(self) -> dict:
        return {a: getattr(self, a) for a in self._keys} | {"method": self.method}

    def __hash__(self) -> int:
        return hash(self.method)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._asdict() == other._asdict()

    def __repr__(self):
        return f"<HeatingRateQuery using method {self.method}>"

