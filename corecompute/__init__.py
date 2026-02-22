"""Core computation definitions to allow for interoperable transport solvers

"""
from .oracle import OracleResult, Oracle
from .query import Query, jsonable as query_json, TabulatedScore, ReactionScore
from .result import KResult, jsonable as result_json

jsonable = [*query_json, *result_json]

