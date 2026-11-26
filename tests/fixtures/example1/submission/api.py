"""API side of the toy recall: GET /recall?since=YYYY-MM-DD."""
from recall import recall


def get_recall(params):
    try:
        return {"status": 200, "memories": recall(params.get("since"))}
    except ValueError as e:
        return {"status": 400, "error": str(e)}
