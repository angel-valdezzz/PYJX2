from pathlib import Path

from pyjx2.docs_runtime import bundled_docs_index, package_root, repo_root


def test_package_root_resolves_from_custom_base_file(tmp_path):
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    marker = pkg_dir / "docs_runtime.py"
    marker.write_text("# test")

    assert package_root(str(marker)) == pkg_dir


def test_bundled_docs_index_returns_index_when_present(tmp_path):
    pkg_dir = tmp_path / "pyjx2"
    docs_dir = pkg_dir / "_bundled_docs"
    docs_dir.mkdir(parents=True)
    index = docs_dir / "index.html"
    index.write_text("<html></html>")

    assert bundled_docs_index(str(pkg_dir / "docs_runtime.py")) == index


def test_repo_root_detects_local_mkdocs_project(tmp_path):
    repo = tmp_path / "repo"
    pkg_dir = repo / "pyjx2"
    pkg_dir.mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "mkdocs.yml").write_text("site_name: test")

    assert repo_root(str(pkg_dir / "docs_runtime.py")) == repo


def test_repo_root_returns_none_without_project_structure(tmp_path):
    pkg_dir = tmp_path / "pyjx2"
    pkg_dir.mkdir()

    assert repo_root(str(pkg_dir / "docs_runtime.py")) is None
