"""Generate the exhaustive one-bridge factorization artifact."""
import json

from bridge_factorization import save_artifact


if __name__ == "__main__":
    output = save_artifact()
    print(json.dumps({"status": "PASS", "records": len(output["records"]),
                      "all_orientations_reject": output["all_orientations_reject"]}))
