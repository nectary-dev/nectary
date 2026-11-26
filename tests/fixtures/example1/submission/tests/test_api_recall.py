import api
import recall


def test_since_param():
    assert api.get_recall({"since": "2026-11-01"})["memories"] == recall.recall("2026-11-01")
