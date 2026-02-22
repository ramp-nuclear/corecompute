"""Definitions of questions we want answered about a reactor core state.

These can include values of the flux in a specific component, on a mesh,
the eigenvalue of the system and so on.

By defining these questions abstractly in a way that isn't solver-dependent,
they should allow for interoperability in answering them.

"""
from .meshquery import MeshQuery
from .powerquery import HeatingRateQuery
from .query import Query, KQuery
from .score import Score, ReactionScore, TabulatedScore
from .surfacequery import SurfaceCurrentQuery
from .tracksquery import SurfaceTracksQuery
from .volumequery import VolumeQuery

query_types = [MeshQuery, HeatingRateQuery, KQuery, SurfaceTracksQuery, 
               SurfaceCurrentQuery, VolumeQuery]
score_types = [Score, ReactionScore, TabulatedScore]
jsonable = score_types + query_types

