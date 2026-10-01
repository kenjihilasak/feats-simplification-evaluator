from phase6_degraded_corpus.src.selection.select_fose_pools import finalize


def test_finalize_excludes_wikipedia_vikidia_before_quality_gate():
    row = {
        "canonical_pair_id": "pair:en:test",
        "corpus": "Wikipedia-Vikidia",
        "eligible_axes": ["FLUENCY", "OMIT"],
    }
    scores = {
        "pair:en:test": {
            "acceptability": 1.0,
            "nli_probabilities": {"contradiction": 0.0},
        }
    }
    config = {
        "corpora": ["WikiAutoEN", "ASSET"],
        "tau_accept": 0.9,
        "nli_contradiction_threshold": 0.5,
        "existing_axis_pair_counts": {"MEANING": 1},
        "seed": 20260930,
        "experiment_id": "test",
        "nli_model": "test",
        "nli_revision": "test",
        "acceptability_model": "test",
        "acceptability_revision": "test",
        "wordfreq_version": "test",
    }

    pools, report = finalize(config, [row], scores)

    assert all(not values for values in pools.values())
    assert report["drop_reasons"]["FLUENCY"]["source_excluded"] == 1
    assert report["drop_reasons"]["OMIT"]["source_excluded"] == 1
    assert all("Wikipedia-Vikidia" not in cell for cell in report["cells"])
