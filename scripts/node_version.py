from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEMPLATED_ROOT = ROOT / "template"
NVMRC = TEMPLATED_ROOT / ".nvmrc"
PACKAGE_JSON = TEMPLATED_ROOT / "package.json"


def main() -> None:
    new_version = get_version_from_nvmrc()
    old_version = get_version_from_package_json()
    if old_version != new_version:
        update_package_json_version(old_version, new_version)


def get_version_from_nvmrc() -> str:
    return NVMRC.read_text().strip()


def get_version_from_package_json() -> str:
    package_json = json.loads(PACKAGE_JSON.read_text())
    return package_json["engines"]["node"]


def update_package_json_version(old_version: str, new_version: str) -> None:
    package_json_text = PACKAGE_JSON.read_text()
    package_json_text = package_json_text.replace(
        f'"node": "{old_version}"',
        f'"node": "{new_version}"',
    )
    PACKAGE_JSON.write_text(package_json_text)


if __name__ == "__main__":
    main()
