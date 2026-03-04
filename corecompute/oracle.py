"""The Oracle protocol, used to define how transport-related queries are answered.

"""
from typing import Any, Protocol

from coreoperator.operational_state import OperationalState

from .query import Query

OracleResult = dict[Query, Any]


class Oracle(Protocol):
    """An Oracle is used to answer queries about operational states.

    This protocol defines what we expect solvers to act like, so we can choose
    them interchangably for reactor analysis.
    The idea is that support for different solvers will be done by other packages
    which will implement an Oracle for those solvers.
    We include our own OpenMC Oracle in our ramp-openmc package, for example.

    """

    def direct(self, state: OperationalState, *queries: Query) -> OracleResult:
        """A function that answers queries for a given reactor state.

        This function exists explicitly because we want to be able to reference
        it as a function which can be delayed for use with the Dask framework,
        for example. Otherwise, it should be equivalent to the __call__ method.

        """
        ...

    def __call__(self, state: OperationalState, *queries: Query) -> OracleResult:
        return self.direct(state, *queries)

