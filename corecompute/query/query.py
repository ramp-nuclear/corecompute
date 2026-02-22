from typing import Hashable, Protocol

from ramp_core.serializable import Serializable


class Query(Hashable, Protocol):
    """General things required from any protocol"""

    def __eq__(self, other) -> bool:
        ...

    def __repr__(self) -> str:
        ...


class KQuery(Serializable):
    """Query about the system's k-eigenvalue.

    """
    ser_identifier = "KQuery"

    def __hash__(self): return hash(None)

    def __eq__(self, other) -> bool:
        return True if isinstance(other, type(self)) else NotImplemented

    def __repr__(self) -> str:
        return "KQuery()"

