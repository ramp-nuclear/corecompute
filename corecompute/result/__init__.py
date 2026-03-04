"""Subpackage that handles and defines how output from a transport calculation
should look like

"""

from .kresult import KResult, PCM as PCM
from .meshresult import MeshResult
from .tracksresult import SurfaceTracksResult as SurfaceTracksResult
from .volumeresult import VolumeResult

jsonable = [KResult, MeshResult, VolumeResult]

EnergyMap = dict[str, tuple[float, float]]
