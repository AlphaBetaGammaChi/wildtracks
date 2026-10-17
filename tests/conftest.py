import pandas as pd
import pytest

STUDY_META = {
    "title": "Test study",
    "authors": ["Test, A."],
    "year": "2020",
    "license": "CC0 1.0",
    "data_citation": "Test, A. (2020). Test study. Movebank Data Repository. https://doi.org/10.5441/001/1.test",
    "doi": "10.5441/001/1.test",
    "repository_url": "https://example.org",
}


def make_track(points, animal="TEST A1", taxon="Ciconia ciconia", start="2013-07-01"):
    """points: list of (lat, lon) or (day_offset, lat, lon), one fix per day at 18:00."""
    rows = []
    for i, p in enumerate(points):
        if len(p) == 3:
            day_off, lat, lon = p
        else:
            day_off, lat, lon = i, p[0], p[1]
        rows.append(
            {
                "timestamp": pd.Timestamp(start, tz="UTC") + pd.Timedelta(days=day_off, hours=18),
                "lat": lat,
                "lon": lon,
                "animal": animal,
                "taxon": taxon,
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def stork_facts():
    """Real AR445 facts — slow to build once, reused across tests."""
    from wildtracks import facts as F
    from wildtracks.species import species_info
    from wildtracks.study import load_meta, load_reference, load_thinned, reference_for

    slug = "white-stork-8-populations"
    animal = "DER AR445"
    df = load_thinned(slug)
    g = df[df.animal == animal]
    facts, _ = F.build_facts(g, animal, species_info("Ciconia ciconia"), reference_for(load_reference(slug), animal), load_meta(slug))
    return facts
