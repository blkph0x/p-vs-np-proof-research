"""Record current checkpoint files; leave every imported archival manifest alone."""
import hashlib
import json
from pathlib import Path

CHECKPOINT = Path(__file__).resolve().parent.parent
TARGET = CHECKPOINT/'WORKING_MANIFEST.json'


def files():
    return sorted(p for p in CHECKPOINT.rglob('*') if p.is_file() and p != TARGET
                  and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo'))


def main():
    manifest = {p.relative_to(CHECKPOINT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files()}
    TARGET.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    replay = json.loads(TARGET.read_text(encoding='utf-8'))
    assert set(replay) == {p.relative_to(CHECKPOINT).as_posix() for p in files()}
    assert all(hashlib.sha256((CHECKPOINT/name).read_bytes()).hexdigest() == expected for name, expected in replay.items())
    print(json.dumps({'verified_files': len(replay), 'manifest': str(TARGET)}))


if __name__ == '__main__':
    main()
