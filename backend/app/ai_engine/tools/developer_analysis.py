"""Developer Track Record Analysis Tool."""
from typing import Any, Dict


_DEVELOPER_DB: Dict[str, Dict] = {
    "ora developers": {"on_time_delivery_rate": 85, "total_projects": 12, "reputation_score": 4.2},
    "palm hills": {"on_time_delivery_rate": 78, "total_projects": 30, "reputation_score": 3.9},
    "emaar": {"on_time_delivery_rate": 90, "total_projects": 50, "reputation_score": 4.5},
    "sodic": {"on_time_delivery_rate": 82, "total_projects": 20, "reputation_score": 4.1},
}


async def get_developer_track_record(developer_name: str) -> Dict[str, Any]:
    """Return track record metrics for a developer."""
    key = developer_name.lower().strip()
    data = _DEVELOPER_DB.get(key, {
        "on_time_delivery_rate": 70,
        "total_projects": 5,
        "reputation_score": 3.5,
    })

    return {
        "status": "success",
        "developer_name": developer_name,
        "track_record": {
            "on_time_delivery_rate": data["on_time_delivery_rate"],
            "total_projects": data["total_projects"],
            "reputation_score": data["reputation_score"],
        },
    }
