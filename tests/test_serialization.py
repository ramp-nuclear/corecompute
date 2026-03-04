import json
from collections import Counter
from pathlib import Path, PurePath
from string import ascii_lowercase

import hypothesis.strategies as st
import numpy as np
import xarray
from coremaker import jsonable as coremaker_jsonable
from coremaker.mesh import CartesianMesh, CylindricalMesh, SphericalMesh
from coremaker.surfaces import Plane
from cytoolz import valmap
from hypothesis import given, settings
from hypothesis.extra.numpy import arrays
from isotopes import ZAID
from ramp_core import RampJSONDecoder, RampJSONEncoder
from reactions import (
    ProductionReaction,
    ProtoReaction,
    Reaction,
    Typus,
)
from reactions import (
    jsonable as reac_jsonable,
)
from reactions.particle import NamedParticle

from corecompute import jsonable
from corecompute.query import (
    HeatingRateQuery,
    KQuery,
    MeshQuery,
    ReactionScore,
    Score,
    SurfaceCurrentQuery,
    SurfaceTracksQuery,
    TabulatedScore,
    VolumeQuery,
)
from corecompute.result import KResult, MeshResult, VolumeResult
from corecompute.result.meshresult import LONG_NAME, UNITS

scorenames = st.sampled_from(["flux", "fission-q-prompt", "heating"])
scores = st.builds(Score, name=scorenames, volume_specific=st.booleans())
posval = st.floats(min_value=1e-6, max_value=1e8)
energies = arrays(dtype=float, 
                  shape=st.integers(min_value=2, max_value=10), 
                  elements=posval,
                  unique=True).map(np.sort)
tab_e = st.shared(energies, key="tab")
tabscores = st.builds(TabulatedScore,
                      energy=tab_e,
                      score=tab_e.flatmap(lambda v: arrays(dtype=float, shape=st.just(len(v)), elements=posval)),
                      volume_specific=st.booleans())
zaids = st.integers(min_value=10000, max_value=10_000 * 200 + 999 * 10 + 9).map(ZAID.from_int)
reactypes = st.sampled_from(Typus).map(str)
branches = st.dictionaries(keys=zaids, values=posval, max_size=10
                           ).map(lambda d: valmap(lambda x: x/sum(d.values()), d))
protoreacs = st.builds(ProtoReaction, parent=zaids, typus=reactypes, branching=branches)
prodreacs = st.builds(ProductionReaction, parent=zaids, target=zaids, typus=reactypes)
creacs = st.builds(Reaction, proto=protoreacs, target=zaids)
reacs = st.one_of(creacs, protoreacs, prodreacs)
reacscores = st.builds(ReactionScore, reaction=reacs, 
                       volume_specific=st.booleans(), 
                       density_specific=st.booleans())

pnames = st.text(min_size=1, max_size=20, alphabet=ascii_lowercase)
paths = st.lists(min_size=1, max_size=10, elements=pnames).map(lambda x: PurePath('/'.join(x)))
paths_none = st.none () | paths
particles = st.sampled_from(NamedParticle)
volq = st.builds(VolumeQuery,
                 names=st.lists(min_size=1, elements=paths).map(tuple),
                 scores=st.lists(min_size=1, elements=scores | reacscores | tabscores).map(tuple),
                 energies = st.just(()) | energies.map(lambda x: tuple(x.tolist())),
                 particle=particles | st.lists(min_size=1, elements=particles).map(tuple),
                 )
kq = st.just(KQuery())

cartmesh = st.builds(CartesianMesh, x=energies, y=energies, z=energies)
rad_vec = arrays(dtype=float,
                 shape=st.integers(min_value=2, max_value=10),
                 elements=st.floats(min_value=1e-10, max_value=100, allow_subnormal=False),
                 unique=True,
                 ).map(np.sort).map(lambda x: np.concatenate([[0], x]))
tau_vec = arrays(dtype=float,
                 shape=st.integers(min_value=2, max_value=10),
                 elements=st.floats(min_value=1e-10, max_value=2 * np.pi - 1e-10, allow_subnormal=False),
                 unique=True,
                 ).map(np.sort).map(lambda x: np.concatenate([[0], x, [2 * np.pi]]))
pi_vec = tau_vec.map(lambda x: x/2)
cylmesh = st.builds(CylindricalMesh, r=rad_vec, z=energies, theta=tau_vec)
sphmesh = st.builds(SphericalMesh, r=rad_vec, phi=tau_vec, theta=pi_vec)
meshq = st.builds(MeshQuery,
                  mesh=cartmesh | cylmesh | sphmesh,
                  scores=st.lists(min_size=1, elements=scores).map(tuple),
                  energies=energies.map(lambda x: tuple(x.tolist())),
                  )
cartmeshq = st.builds(MeshQuery,
                      mesh=cartmesh,
                      scores=st.lists(min_size=1, elements=scores).map(tuple),
                      energies=energies.map(lambda x: tuple(x.tolist())),
                      )
heatq = st.builds(HeatingRateQuery, method=st.just("score heating"))
posf = st.floats(min_value=1e-10, max_value=10)
planes = st.builds(Plane, posf, posf, posf, posf)
surfacecurq = st.builds(SurfaceCurrentQuery,
                        surface=planes,
                        from_component=paths_none,
                        to_component=paths_none,
                        energies=energies.map(lambda x: tuple(x.tolist())),
                        particle=particles
                        )
surfacetrackq = st.builds(SurfaceTracksQuery,
                          path=paths.map(Path),
                          surfaces=st.lists(min_size=1, elements=planes).map(tuple),
                          particles=st.lists(min_size=1, elements=particles).map(tuple),
                          )

kresults = st.tuples(st.floats(min_value=0, max_value=3), st.floats(min_value=1e-10, max_value=3)
                     ).map(lambda t: KResult(*t))
lowe = st.shared(st.none() | st.floats(min_value=0, max_value=1e7), key="lowe")
volresults = st.builds(VolumeResult,
                       component=paths,
                       score=scores,
                       value=st.floats(min_value=0, max_value=10),
                       error=st.floats(min_value=0, max_value=1),
                       particle=particles,
                       upper_energy=lowe.flatmap(
                           lambda e: st.none() | st.floats(min_value=e+1, max_value=(1+e)*1e5) 
                           if e is not None else st.none()),
                       lower_energy=lowe,
                       )


def _res_from_meshquery(query: MeshQuery):
    mesh = query.mesh
    x, y, z = mesh.x, mesh.y, mesh.z
    e = np.array(query.energies)
    dims = {k: len(v)-1 for k, v in zip("xyze", [x, y, z, e])}
    coords = {k: 0.5 * (v[:-1] + v[1:]) for k, v in zip("xyze", [x, y, z, e])}
    attrs = {k: {UNITS: "eV" if k == "e" else "cm", LONG_NAME: v}
             for k, v in zip("xyze", ("width", "length", "height", "energy"))}

    means = arrays(dtype=float, shape=tuple(dims.values()), elements=st.floats(min_value=-10, max_value=10))
    stds = arrays(dtype=float, shape=tuple(dims.values()), elements=st.floats(min_value=-1, max_value=1))
    tpls = st.tuples(means, stds)

    def _set_from_values(t: tuple) -> xarray.Dataset:
        mean_da = xarray.DataArray(
                data=t[0], coords=coords, dims=dims.keys(), name="mean"
                )
        std_da = xarray.DataArray(
                data=t[1], coords=coords, dims=dims.keys(), name="std"
                )
        ds = xarray.Dataset(data_vars={"mean": mean_da, "std": std_da})
        for dim, dim_data in attrs.items():
            ds[dim].attrs = dim_data
        return ds

    return tpls.map(_set_from_values)


cartmeshres = cartmeshq.flatmap(_res_from_meshquery).map(MeshResult)


strats = {Score: scores,
          TabulatedScore: tabscores,
          ReactionScore: reacscores,
          KQuery: kq,
          MeshQuery: meshq,
          HeatingRateQuery: heatq,
          SurfaceCurrentQuery: surfacecurq,
          SurfaceTracksQuery: surfacetrackq,
          VolumeQuery: volq,
          KResult: kresults,
          MeshResult: cartmeshres,
          VolumeResult: volresults,
          }


def test_no_two_identifiers_the_same():
    c = dict(Counter([c.ser_identifier for c in jsonable]))
    assert set(c.values()) == {1}, {key: value for key, value in c.items() if value != 1}


def test_strat_for_all_supported():
    assert set(strats) == set(jsonable), (set(jsonable) - set(strats), (set(strats) - set(jsonable)))


RampJSONDecoder.supported = {c.ser_identifier: c 
                             for c in list(jsonable) + list(reac_jsonable) + list(coremaker_jsonable)}


def _test_ser_deser(x):
    s = json.dumps(x, cls=RampJSONEncoder)
    try:
        v = json.loads(s, cls=RampJSONDecoder)
    except (RuntimeError, TypeError):
        print(s)
        raise
    assert x == v, (x, v, s)


for cls, strat in strats.items():
    globals()[f"test_ser_deser_{cls.__name__}"] = settings(deadline=None)(given(strat)(_test_ser_deser))

