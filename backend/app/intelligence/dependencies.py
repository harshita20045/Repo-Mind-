import json
import re
from typing import List, Dict, Any, Optional
from backend.app.intelligence.schemas import PackageDependencySchema


class DependencyExtractor:
    """
    Extracts third-party package dependencies from project manifests
    (requirements.txt, pyproject.toml, package.json, go.mod, Cargo.toml).
    """

    def extract_from_manifests(self, file_dict: Dict[str, str]) -> List[PackageDependencySchema]:
        results: List[PackageDependencySchema] = []

        for path, content in file_dict.items():
            clean = path.replace("\\", "/").lower()
            filename = clean.split("/")[-1]

            if filename == "package.json":
                results.extend(self._parse_package_json(path, content))
            elif filename == "requirements.txt" or (filename.endswith(".txt") and "requirements" in filename):
                results.extend(self._parse_requirements_txt(path, content))
            elif filename == "pyproject.toml":
                results.extend(self._parse_pyproject_toml(path, content))
            elif filename == "go.mod":
                results.extend(self._parse_go_mod(path, content))
            elif filename == "cargo.toml":
                results.extend(self._parse_cargo_toml(path, content))

        return results

    def _parse_package_json(self, path: str, content: str) -> List[PackageDependencySchema]:
        deps: List[PackageDependencySchema] = []
        try:
            data = json.loads(content)
        except Exception:
            return []

        # Production dependencies
        prod_deps = data.get("dependencies", {})
        if isinstance(prod_deps, dict):
            for name, spec in prod_deps.items():
                deps.append(PackageDependencySchema(
                    ecosystem="npm",
                    package_name=name,
                    version_spec=str(spec),
                    is_dev=False,
                    file_path=path,
                ))

        # Dev dependencies
        dev_deps = data.get("devDependencies", {})
        if isinstance(dev_deps, dict):
            for name, spec in dev_deps.items():
                deps.append(PackageDependencySchema(
                    ecosystem="npm",
                    package_name=name,
                    version_spec=str(spec),
                    is_dev=True,
                    file_path=path,
                ))

        return deps

    def _parse_requirements_txt(self, path: str, content: str) -> List[PackageDependencySchema]:
        deps: List[PackageDependencySchema] = []
        is_dev = "dev" in path.lower() or "test" in path.lower()

        for line in content.splitlines():
            sline = line.strip()
            if not sline or sline.startswith(("#", "-r", "--", "-e", "git+")):
                continue

            # Match package name and version specifier
            match = re.match(r"^([A-Za-z0-9_.\-]+)(.*)", sline)
            if match:
                pkg_name = match.group(1).strip()
                spec = match.group(2).strip() or None
                deps.append(PackageDependencySchema(
                    ecosystem="pypi",
                    package_name=pkg_name,
                    version_spec=spec,
                    is_dev=is_dev,
                    file_path=path,
                ))
        return deps

    def _parse_pyproject_toml(self, path: str, content: str) -> List[PackageDependencySchema]:
        deps: List[PackageDependencySchema] = []
        current_section = None

        for line in content.splitlines():
            sline = line.strip()
            if sline.startswith("[") and sline.endswith("]"):
                current_section = sline[1:-1].strip()
                continue

            if not sline or sline.startswith("#"):
                continue

            # Check Poetry dependencies: [tool.poetry.dependencies]
            if current_section == "tool.poetry.dependencies":
                m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*["\']([^"\']+)["\']', sline)
                if m and m.group(1).lower() != "python":
                    deps.append(PackageDependencySchema(
                        ecosystem="pypi",
                        package_name=m.group(1),
                        version_spec=m.group(2),
                        is_dev=False,
                        file_path=path,
                    ))
            elif current_section == "tool.poetry.group.dev.dependencies":
                m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*["\']([^"\']+)["\']', sline)
                if m:
                    deps.append(PackageDependencySchema(
                        ecosystem="pypi",
                        package_name=m.group(1),
                        version_spec=m.group(2),
                        is_dev=True,
                        file_path=path,
                    ))

        return deps

    def _parse_go_mod(self, path: str, content: str) -> List[PackageDependencySchema]:
        deps: List[PackageDependencySchema] = []
        in_require = False

        for line in content.splitlines():
            sline = line.strip()
            if sline.startswith("require ("):
                in_require = True
                continue
            elif in_require and sline == ")":
                in_require = False
                continue

            if in_require or sline.startswith("require "):
                target = sline.replace("require ", "").strip()
                parts = target.split()
                if len(parts) >= 2:
                    deps.append(PackageDependencySchema(
                        ecosystem="go",
                        package_name=parts[0],
                        version_spec=parts[1],
                        is_dev=False,
                        file_path=path,
                    ))
        return deps

    def _parse_cargo_toml(self, path: str, content: str) -> List[PackageDependencySchema]:
        deps: List[PackageDependencySchema] = []
        current_section = None

        for line in content.splitlines():
            sline = line.strip()
            if sline.startswith("[") and sline.endswith("]"):
                current_section = sline[1:-1].strip()
                continue

            if current_section in ("dependencies", "dev-dependencies"):
                m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*["\']([^"\']+)["\']', sline)
                if m:
                    deps.append(PackageDependencySchema(
                        ecosystem="cargo",
                        package_name=m.group(1),
                        version_spec=m.group(2),
                        is_dev=(current_section == "dev-dependencies"),
                        file_path=path,
                    ))
        return deps
