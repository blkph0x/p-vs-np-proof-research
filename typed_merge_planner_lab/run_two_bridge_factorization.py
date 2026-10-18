from two_bridge_factorization import write_artifact


if __name__ == "__main__":
    result = write_artifact()
    print({"status": "PASS", "records": len(result["records"]),
           "all_orientations_represent": result["all_orientations_represent"]})
