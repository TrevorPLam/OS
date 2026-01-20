from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "inventory_api_coverage.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("inventory_api_coverage", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load inventory_api_coverage module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_module(base_dir: Path, name: str, with_urls: bool, with_views: bool) -> None:
    module_dir = base_dir / name
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "__init__.py").write_text("", encoding="utf-8")
    if with_urls:
        (module_dir / "urls.py").write_text("# urls", encoding="utf-8")
    if with_views:
        (module_dir / "views.py").write_text("# views", encoding="utf-8")


def create_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    modules_dir = tmp_path / "src/modules"
    api_dir = tmp_path / "src/api"
    modules_dir.mkdir(parents=True)
    api_dir.mkdir(parents=True)
    return tmp_path, modules_dir, api_dir


def test_inventory_happy_path(tmp_path: Path):
    module = load_script_module()
    repo_root, modules_dir, api_dir = create_repo(tmp_path)
    create_module(modules_dir, "alpha", with_urls=True, with_views=True)
    create_module(modules_dir, "beta", with_urls=False, with_views=False)
    create_module(api_dir, "beta", with_urls=True, with_views=True)

    inventory = module.build_inventory(repo_root)
    assert {entry["module"] for entry in inventory} == {"alpha", "beta"}

    alpha = next(entry for entry in inventory if entry["module"] == "alpha")
    assert alpha["module_urls"] is True
    assert alpha["module_views"] is True
    assert alpha["api_urls"] is False
    assert alpha["api_views"] is False
    assert module.coverage_status(alpha) == "module"

    beta = next(entry for entry in inventory if entry["module"] == "beta")
    assert beta["module_urls"] is False
    assert beta["api_urls"] is True
    assert beta["api_views"] is True
    assert module.coverage_status(beta) == "api"


def test_inventory_empty_modules_dir(tmp_path: Path):
    module = load_script_module()
    repo_root, _modules_dir, _api_dir = create_repo(tmp_path)

    inventory = module.build_inventory(repo_root)
    assert inventory == []


def test_inventory_large_module_set(tmp_path: Path):
    module = load_script_module()
    repo_root, modules_dir, _api_dir = create_repo(tmp_path)
    for index in range(200):
        create_module(modules_dir, f"module_{index}", with_urls=False, with_views=False)

    inventory = module.build_inventory(repo_root)
    assert len(inventory) == 200


def test_inventory_missing_modules_dir_raises(tmp_path: Path):
    module = load_script_module()
    repo_root = tmp_path

    with pytest.raises(FileNotFoundError):
        module.build_inventory(repo_root)
