import json
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://api.crossref.org/works/10.1109/ASSIC70037.2026.11717448"
message = requests.get(URL, timeout=30).json()["message"]
keep = {key: message.get(key) for key in (
    "DOI", "title", "author", "page", "published-print", "created",
    "reference-count", "reference", "link", "resource", "URL", "publisher", "type"
)}
Path("VOHRA_CROSSREF_METADATA.json").write_text(
    json.dumps({
        "source_url": URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "message": keep,
    }, indent=2),
    encoding="utf-8",
)
print(json.dumps({"doi": message.get("DOI"), "references": message.get("reference-count"), "links": message.get("link")}))
