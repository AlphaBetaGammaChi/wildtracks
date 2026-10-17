"""Common names and simple wording for species. Add new species here as the channel grows."""

SPECIES = {
    "Ciconia ciconia": {"common": "white stork", "verb": "flew", "icon": "bird"},
    "Ciconia nigra": {"common": "black stork", "verb": "flew", "icon": "bird"},
    "Cuculus canorus": {"common": "common cuckoo", "verb": "flew", "icon": "bird"},
    "Limosa lapponica": {"common": "bar-tailed godwit", "verb": "flew", "icon": "bird"},
    "Pandion haliaetus": {"common": "osprey", "verb": "flew", "icon": "bird"},
    "Larus fuscus": {"common": "lesser black-backed gull", "verb": "flew", "icon": "bird"},
    "Larus argentatus": {"common": "herring gull", "verb": "flew", "icon": "bird"},
    "Grus grus": {"common": "common crane", "verb": "flew", "icon": "bird"},
    "Chelonia mydas": {"common": "green turtle", "verb": "swam", "icon": "turtle"},
    "Carcharodon carcharias": {"common": "great white shark", "verb": "swam", "icon": "fish"},
}


def species_info(taxon: str) -> dict:
    info = SPECIES.get(taxon)
    if info:
        return {"taxon": taxon, **info}
    return {"taxon": taxon, "common": taxon, "verb": "travelled", "icon": "bird"}
