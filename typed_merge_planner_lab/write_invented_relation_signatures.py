"""Generate the independently replayable invented-relation signature artifact."""
import json
from pathlib import Path

from invented_relation_bridge import RESULTS_PATH, build_catalog_artifact


ROOT = Path(__file__).resolve().parent


def main():
    output = ROOT / "INVENTED_RELATION_SIGNATURES.json"
    output.write_text(json.dumps(build_catalog_artifact(RESULTS_PATH), indent=2) + "\n",
                      encoding="utf-8")
    print(f"wrote {output.name}")


if __name__ == "__main__":
    main()
