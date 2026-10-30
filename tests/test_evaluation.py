from ai.evaluation.run import evaluate


def test_rules_meet_the_recall_floor():
    # Regression guard: a rules change that drops recall on the labelled
    # set below this floor should fail CI, not ship.
    report = evaluate(use_llm=False)
    assert report["overall"]["cases"] >= 80
    assert report["overall"]["recall"] >= 0.9
    for lang in ("hi", "hi-latn", "kn", "kn-latn"):
        assert report["by_language"][lang]["recall"] == 1.0
