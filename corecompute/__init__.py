"""Core computation definitions to allow for interoperable transport solvers"""

from .oracle import OracleResult as OracleResult, Oracle as Oracle
from .query import (
    Query as Query,
    jsonable as query_json,
    TabulatedScore as TabulatedScore,
    ReactionScore as ReactionScore,
)
from .result import KResult as KResult, jsonable as result_json

jsonable = [*query_json, *result_json]
