import recall


def test_filters_by_day():
    got = [m["id"] for m in recall.recall("2026-11-01")]
    assert 1 not in got and 3 in got, got


def test_no_flag_unchanged():
    assert recall.recall() == recall.MEMORIES


def test_bad_date():
    assert recall.main(["--since", "yesterday"]) == 2
