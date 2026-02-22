import hypothesis.strategies as st
from hypothesis import given, settings
from isotopes import U235, Pu239, Al27, H1, He4, B10, Xe135m
from reactions import ProtoReaction, Typus

from corecompute.query import KQuery, VolumeQuery, Score, ReactionScore

kqueries = st.just(KQuery())
fluxscore = st.just((Score('flux', volume_specific=True),))
heatscore = st.just((Score('fission-q-prompt', volume_specific=True),))
components = st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz/', min_size=1),
                      min_size=1, max_size=10).map(tuple)
energies = st.one_of(st.lists(st.floats(min_value=0., max_value=20e6),
                              min_size=2, max_size=10,
                              unique=True),
                     st.just([])).map(sorted).map(tuple)
fluxqueries = st.builds(VolumeQuery, components, scores=fluxscore,
                        energies=energies)
fissenerqueries = st.builds(VolumeQuery, components, scores=heatscore)
reactypes = st.sampled_from(Typus)
zaids = st.sampled_from([U235, Pu239, Al27, H1, He4, B10, Xe135m])
reaction = st.builds(ProtoReaction, zaids, reactypes,
                     branching=st.just({}))
score = st.builds(ReactionScore, reaction, volume_specific=st.just(True))
scores = st.lists(score,
                  min_size=1, max_size=10).map(tuple)
reactionqueries = st.builds(VolumeQuery, components, scores=scores)
queries = st.one_of(kqueries, fissenerqueries, fluxqueries, reactionqueries)


@settings(max_examples=500)
@given(queries)
def test_query_types_are_hashable(q):
    assert isinstance(hash(q), int)

