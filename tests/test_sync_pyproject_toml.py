"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for sync_pyproject_toml.py - Comprehensive test coverage
 Log:
 v1.0.0 : Initial test implementation
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
# Standard Library
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Add bin directory to path for import
bin_path = Path(__file__).parent.parent / "bin"
sys.path.insert(0, str(bin_path))

# Project modules - must import after path manipulation
from sync_pyproject_toml import (  # noqa: E402
    SyncPyprojectToml,
    SyncPyprojectTomlError,
    PRESERVE_SECTIONS,
    SYNC_SECTIONS,
)


# -------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------
@pytest.fixture
def mock_basefunctions():
    """Mock basefunctions module to avoid output during tests."""
    with patch("sync_pyproject_toml.basefunctions") as mock_bf:
        # Mock logger
        mock_logger = MagicMock()
        mock_bf.get_logger.return_value = mock_logger
        mock_bf.setup_logger.return_value = None

        # Mock OutputFormatter
        mock_formatter = MagicMock()
        mock_bf.OutputFormatter.return_value = mock_formatter

        # Mock runtime path
        mock_bf.runtime.get_runtime_path.return_value = "/mock/runtime/path"

        yield mock_bf


@pytest.fixture
def template_data():
    """Provide sample template data."""
    return {
        "project": {
            "name": "<package_name>",
            "version": "0.1.0",
            "authors": [{"name": "neuraldevelopment", "email": "info@neuraldevelopment.de"}],
            "readme": "README.md",
            "license": {"text": "MIT"},
            "requires-python": ">=3.12",
            "optional-dependencies": {"dev": ["black", "pytest"]},
        },
        "build-system": {
            "requires": ["setuptools>=65.0"],
            "build-backend": "setuptools.build_meta",
        },
        "tool": {
            "setuptools": {
                "packages": {"find": {"where": ["src"]}},
                "package-data": {"<package_name>": ["py.typed"]},
            },
            "pytest": {"ini_options": {"testpaths": ["tests"]}},
        },
    }


@pytest.fixture
def target_data():
    """Provide sample target pyproject.toml data."""
    return {
        "project": {
            "name": "mypackage",
            "version": "1.2.3",
            "description": "My custom package",
            "authors": [{"name": "Old Author"}],
            "dependencies": ["requests>=2.28.0"],
        },
        "tool": {"pytest": {"ini_options": {"testpaths": ["old_tests"]}}},
    }


@pytest.fixture
def temp_project_structure(tmp_path):
    """Create temporary project structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create required files
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test_project'\n")
    (project_dir / "src").mkdir()
    (project_dir / "src" / "test_project").mkdir()

    vscode_dir = project_dir / ".vscode"
    vscode_dir.mkdir()
    (vscode_dir / "settings.json").write_text("{}")

    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.local.json").write_text("{}")

    return project_dir


@pytest.fixture
def mock_template_path(tmp_path):
    """Create mock template file."""
    template_path = tmp_path / "template" / "pyproject.toml"
    template_path.parent.mkdir(parents=True)
    template_content = """
[project]
name = "<package_name>"
authors = [{name = "neuraldevelopment"}]
"""
    template_path.write_text(template_content)
    return template_path


@pytest.fixture
def syncer(mock_basefunctions, mock_template_path):
    """Provide SyncPyprojectToml instance with mocked dependencies."""
    with patch.object(SyncPyprojectToml, "_get_template_path", return_value=mock_template_path):
        return SyncPyprojectToml()


# -------------------------------------------------------------
# TEST PROJECT DISCOVERY
# -------------------------------------------------------------
class TestFindProjects:
    """Tests for find_projects method."""

    def test_find_projects_empty_directory(self, syncer, tmp_path):
        """Test finding projects in empty directory returns empty list."""
        # Arrange
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Act
        result = syncer.find_projects(empty_dir)

        # Assert
        assert result == []

    def test_find_projects_nonexistent_directory(self, syncer, tmp_path):
        """Test finding projects in non-existent directory returns empty list."""
        # Arrange
        nonexistent = tmp_path / "nonexistent"

        # Act
        result = syncer.find_projects(nonexistent)

        # Assert
        assert result == []

    def test_find_projects_single_valid_project(self, syncer, temp_project_structure):
        """Test finding single valid project."""
        # Arrange
        search_path = temp_project_structure.parent

        # Act
        result = syncer.find_projects(search_path)

        # Assert
        assert len(result) == 1
        assert result[0] == temp_project_structure

    def test_find_projects_multiple_projects(self, syncer, tmp_path):
        """Test finding multiple valid projects."""
        # Arrange
        for i in range(3):
            project_dir = tmp_path / f"project_{i}"
            project_dir.mkdir()
            (project_dir / "pyproject.toml").write_text("[project]\n")
            (project_dir / "src").mkdir()
            vscode_dir = project_dir / ".vscode"
            vscode_dir.mkdir()
            (vscode_dir / "settings.json").write_text("{}")
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()
            (claude_dir / "settings.local.json").write_text("{}")

        # Act
        result = syncer.find_projects(tmp_path)

        # Assert
        assert len(result) == 3
        assert all(p.name.startswith("project_") for p in result)

    def test_find_projects_invalid_projects_excluded(self, syncer, tmp_path):
        """Test that invalid projects are excluded."""
        # Arrange - valid project
        valid = tmp_path / "valid"
        valid.mkdir()
        (valid / "pyproject.toml").write_text("[project]\n")
        (valid / "src").mkdir()
        vscode = valid / ".vscode"
        vscode.mkdir()
        (vscode / "settings.json").write_text("{}")
        claude = valid / ".claude"
        claude.mkdir()
        (claude / "settings.local.json").write_text("{}")

        # Arrange - invalid project (missing .vscode)
        invalid = tmp_path / "invalid"
        invalid.mkdir()
        (invalid / "pyproject.toml").write_text("[project]\n")
        (invalid / "src").mkdir()

        # Act
        result = syncer.find_projects(tmp_path)

        # Assert
        assert len(result) == 1
        assert result[0] == valid

    def test_find_projects_sorted_results(self, syncer, tmp_path):
        """Test that projects are returned sorted."""
        # Arrange - create projects in non-alphabetical order
        for name in ["charlie", "alice", "bob"]:
            project_dir = tmp_path / name
            project_dir.mkdir()
            (project_dir / "pyproject.toml").write_text("[project]\n")
            (project_dir / "src").mkdir()
            vscode = project_dir / ".vscode"
            vscode.mkdir()
            (vscode / "settings.json").write_text("{}")
            claude = project_dir / ".claude"
            claude.mkdir()
            (claude / "settings.local.json").write_text("{}")

        # Act
        result = syncer.find_projects(tmp_path)

        # Assert
        assert len(result) == 3
        assert result[0].name == "alice"
        assert result[1].name == "bob"
        assert result[2].name == "charlie"


class TestIsBasefunctionsProject:
    """Tests for is_basefunctions_project method."""

    def test_is_basefunctions_project_valid(self, syncer, temp_project_structure):
        """Test valid basefunctions project returns True."""
        # Act
        result = syncer.is_basefunctions_project(temp_project_structure)

        # Assert
        assert result is True

    def test_is_basefunctions_project_missing_pyproject(self, syncer, tmp_path):
        """Test project missing pyproject.toml returns False."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        (project / "src").mkdir()
        vscode = project / ".vscode"
        vscode.mkdir()
        (vscode / "settings.json").write_text("{}")
        claude = project / ".claude"
        claude.mkdir()
        (claude / "settings.local.json").write_text("{}")

        # Act
        result = syncer.is_basefunctions_project(project)

        # Assert
        assert result is False

    def test_is_basefunctions_project_missing_src(self, syncer, tmp_path):
        """Test project missing src/ directory returns False."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\n")
        vscode = project / ".vscode"
        vscode.mkdir()
        (vscode / "settings.json").write_text("{}")
        claude = project / ".claude"
        claude.mkdir()
        (claude / "settings.local.json").write_text("{}")

        # Act
        result = syncer.is_basefunctions_project(project)

        # Assert
        assert result is False

    def test_is_basefunctions_project_missing_vscode(self, syncer, tmp_path):
        """Test project missing .vscode/settings.json returns False."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\n")
        (project / "src").mkdir()
        claude = project / ".claude"
        claude.mkdir()
        (claude / "settings.local.json").write_text("{}")

        # Act
        result = syncer.is_basefunctions_project(project)

        # Assert
        assert result is False

    def test_is_basefunctions_project_missing_claude(self, syncer, tmp_path):
        """Test project missing .claude/settings.local.json returns False."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\n")
        (project / "src").mkdir()
        vscode = project / ".vscode"
        vscode.mkdir()
        (vscode / "settings.json").write_text("{}")

        # Act
        result = syncer.is_basefunctions_project(project)

        # Assert
        assert result is False

    def test_is_basefunctions_project_nonexistent_path(self, syncer, tmp_path):
        """Test non-existent path returns False."""
        # Arrange
        nonexistent = tmp_path / "nonexistent"

        # Act
        result = syncer.is_basefunctions_project(nonexistent)

        # Assert
        assert result is False


# -------------------------------------------------------------
# TEST TEMPLATE LOADING
# -------------------------------------------------------------
class TestTemplateLoading:
    """Tests for template loading functionality."""

    def test_load_template_success(self, syncer):
        """Test successful template loading."""
        # Act
        result = syncer._load_template()

        # Assert
        assert isinstance(result, dict)
        assert "project" in result

    def test_load_template_not_found(self, mock_basefunctions):
        """Test template file not found raises error."""
        # Arrange
        with patch.object(SyncPyprojectToml, "_get_template_path") as mock_get_path:
            mock_get_path.side_effect = SyncPyprojectTomlError("Template not found")

            # Act & Assert
            with pytest.raises(SyncPyprojectTomlError, match="Template not found"):
                SyncPyprojectToml()

    def test_get_template_path_missing_template(self, mock_basefunctions):
        """Test _get_template_path with missing template file."""
        # Arrange
        mock_basefunctions.runtime.get_runtime_path.return_value = "/nonexistent/path"

        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError, match="Template not found"):
            SyncPyprojectToml()


# -------------------------------------------------------------
# TEST BACKUP FUNCTIONALITY
# -------------------------------------------------------------
class TestBackupFunctionality:
    """Tests for backup operations."""

    def test_backup_pyproject_success(self, syncer, tmp_path):
        """Test successful backup creation."""
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test'\n")

        # Act
        with patch("sync_pyproject_toml.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 30, 45)
            backup_path = syncer._backup_pyproject(pyproject)

        # Assert
        assert backup_path.exists()
        assert backup_path.name == "pyproject.toml.backup_20250115_103045"
        assert backup_path.read_text() == "[project]\nname = 'test'\n"

    def test_backup_pyproject_timestamp_format(self, syncer, tmp_path):
        """Test backup timestamp format."""
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\n")

        # Act
        with patch("sync_pyproject_toml.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 31, 23, 59, 59)
            backup_path = syncer._backup_pyproject(pyproject)

        # Assert
        assert "20251231_235959" in backup_path.name

    def test_backup_pyproject_file_not_found(self, syncer, tmp_path):
        """Test backup of non-existent file raises error."""
        # Arrange
        nonexistent = tmp_path / "nonexistent.toml"

        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError, match="Failed to create backup"):
            syncer._backup_pyproject(nonexistent)

    def test_backup_pyproject_permission_error(self, syncer, tmp_path):
        """Test backup with permission error."""
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\n")

        # Act & Assert
        with patch(
            "sync_pyproject_toml.shutil.copy2",
            side_effect=PermissionError("Access denied"),
        ):
            with pytest.raises(
                SyncPyprojectTomlError,
                match="Failed to create backup",
            ):
                syncer._backup_pyproject(pyproject)

    def test_backup_pyproject_public_method(self, syncer, tmp_path):
        """Test public backup_pyproject method."""
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\n")

        # Act
        backup_path = syncer.backup_pyproject(pyproject)

        # Assert
        assert backup_path.exists()
        assert "backup_" in backup_path.name


# -------------------------------------------------------------
# TEST PACKAGE NAME DETECTION
# -------------------------------------------------------------
class TestPackageNameDetection:
    """Tests for package name detection."""

    def test_detect_package_name_from_toml(self, syncer, tmp_path):
        """Test detecting package name from pyproject.toml."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        data = {"project": {"name": "mypackage"}}

        # Act
        result = syncer._detect_package_name(project, data)

        # Assert
        assert result == "mypackage"

    def test_detect_package_name_from_src(self, syncer, tmp_path):
        """Test detecting package name from src/ directory."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        (src / "mypackage").mkdir()
        data = {}

        # Act
        result = syncer._detect_package_name(project, data)

        # Assert
        assert result == "mypackage"

    def test_detect_package_name_no_src(self, syncer, tmp_path):
        """Test detecting package name when src/ doesn't exist."""
        # Arrange
        project = tmp_path / "myproject"
        project.mkdir()
        data = {}

        # Act
        result = syncer._detect_package_name(project, data)

        # Assert
        assert result == "myproject"

    def test_detect_package_name_multiple_packages_in_src(self, syncer, tmp_path):
        """Test detecting package name with multiple packages in src/."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        (src / "package_a").mkdir()
        (src / "package_b").mkdir()
        data = {}

        # Act
        result = syncer._detect_package_name(project, data)

        # Assert
        assert result in ["package_a", "package_b"]

    def test_detect_package_name_ignores_dotfiles(self, syncer, tmp_path):
        """Test that dotfiles in src/ are ignored."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        (src / ".hidden").mkdir()
        (src / "mypackage").mkdir()
        data = {}

        # Act
        result = syncer._detect_package_name(project, data)

        # Assert
        assert result == "mypackage"

    def test_detect_package_name_prefers_toml_over_src(self, syncer, tmp_path):
        """Test that pyproject.toml name takes precedence over src/."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        (src / "different_name").mkdir()
        data = {"project": {"name": "preferred_name"}}

        # Act
        result = syncer._detect_package_name(project, data)

        # Assert
        assert result == "preferred_name"


# -------------------------------------------------------------
# TEST MERGING LOGIC
# -------------------------------------------------------------
class TestMergingLogic:
    """Tests for data merging functionality."""

    def test_merge_pyproject_preserve_values(self, syncer, template_data, target_data):
        """Test that preserved values are kept from target."""
        # Act
        result = syncer._merge_data(target_data, template_data, "mypackage")

        # Assert
        assert result["project"]["name"] == "mypackage"
        assert result["project"]["version"] == "1.2.3"
        assert result["project"]["description"] == "My custom package"
        assert result["project"]["dependencies"] == ["requests>=2.28.0"]

    def test_merge_pyproject_sync_sections(self, syncer, template_data, target_data):
        """Test that synced sections are taken from template."""
        # Act
        result = syncer._merge_data(target_data, template_data, "mypackage")

        # Assert
        assert result["project"]["authors"] == template_data["project"]["authors"]
        assert result["project"]["readme"] == "README.md"
        assert result["build-system"] == template_data["build-system"]

    def test_merge_pyproject_package_name_replacement(self, syncer, template_data, target_data):
        """Test that <package_name> placeholder is replaced."""
        # Act
        result = syncer._merge_data(target_data, template_data, "mypackage")

        # Assert
        assert "mypackage" in result["tool"]["setuptools"]["package-data"]
        assert "<package_name>" not in result["tool"]["setuptools"]["package-data"]

    def test_merge_pyproject_missing_preserved_keys(self, syncer, template_data):
        """Test merging when target is missing preserved keys."""
        # Arrange
        minimal_target = {"project": {"name": "testpkg"}}

        # Act
        result = syncer._merge_data(minimal_target, template_data, "testpkg")

        # Assert
        assert result["project"]["name"] == "testpkg"
        assert "authors" in result["project"]
        assert "requires-python" in result["project"]

    def test_merge_pyproject_empty_target(self, syncer, template_data):
        """Test merging with empty target data."""
        # Arrange
        empty_target = {}

        # Act
        result = syncer._merge_data(empty_target, template_data, "newpkg")

        # Assert
        assert isinstance(result, dict)
        assert "project" in result
        assert "build-system" in result


# -------------------------------------------------------------
# TEST CHANGE DETECTION
# -------------------------------------------------------------
class TestChangeDetection:
    """Tests for change detection functionality."""

    def test_detect_changes_no_changes(self, syncer, template_data):
        """Test detecting no changes when data is identical."""
        # Arrange
        target = syncer._deep_copy(template_data)

        # Act
        changes = syncer._detect_changes(target, template_data)

        # Assert
        assert changes == []

    def test_detect_changes_with_changes(self, syncer, template_data, target_data):
        """Test detecting changes between different data."""
        # Arrange
        merged = syncer._merge_data(target_data, template_data, "mypackage")

        # Act
        changes = syncer._detect_changes(target_data, merged)

        # Assert
        assert len(changes) > 0
        assert "project.authors" in changes

    def test_detect_changes_multiple_sections(self, syncer):
        """Test detecting changes in multiple sections."""
        # Arrange
        target = {
            "project": {"authors": [{"name": "Old"}], "readme": "OLD.md"},
            "build-system": {"requires": ["old"]},
        }
        merged = {
            "project": {"authors": [{"name": "New"}], "readme": "NEW.md"},
            "build-system": {"requires": ["new"]},
        }

        # Act
        changes = syncer._detect_changes(target, merged)

        # Assert
        assert "project.authors" in changes
        assert "project.readme" in changes
        assert "build-system" in changes

    def test_detect_changes_missing_sections(self, syncer):
        """Test detecting changes when target is missing sections."""
        # Arrange
        target = {"project": {}}
        merged = {"project": {"authors": [{"name": "New"}]}, "build-system": {"requires": []}}

        # Act
        changes = syncer._detect_changes(target, merged)

        # Assert
        assert "project.authors" in changes
        assert "build-system" in changes


# -------------------------------------------------------------
# TEST SYNC OPERATIONS
# -------------------------------------------------------------
class TestSyncOperations:
    """Tests for sync_project method."""

    def test_sync_project_success(self, syncer, temp_project_structure, template_data):
        """Test successful project synchronization."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test_project'\nversion = '1.0.0'\n")

        with patch.object(syncer, "_load_template", return_value=template_data):
            # Act
            result = syncer.sync_project(temp_project_structure, dry_run=False)

            # Assert
            assert result["status"] in ["synced", "up_to_date"]
            assert result["project"] == str(temp_project_structure)

    def test_sync_project_dry_run(self, syncer, temp_project_structure, template_data):
        """Test dry run doesn't modify files."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        original_content = "[project]\nname = 'test_project'\n"
        pyproject.write_text(original_content)

        with patch.object(syncer, "_load_template", return_value=template_data):
            # Act
            result = syncer.sync_project(temp_project_structure, dry_run=True)

            # Assert
            assert result["status"] in ["would_sync", "up_to_date"]
            assert pyproject.read_text() == original_content

    def test_sync_project_backup_created(self, syncer, temp_project_structure, template_data):
        """Test that backup is created during sync."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test_project'\n")

        with patch.object(syncer, "_load_template", return_value=template_data):
            with patch.object(syncer, "_detect_changes", return_value=["project.authors"]):
                # Act
                result = syncer.sync_project(temp_project_structure, dry_run=False)

                # Assert
                if result["status"] == "synced":
                    assert "backup" in result
                    backup_path = Path(result["backup"])
                    assert backup_path.exists()

    def test_sync_project_invalid_path(self, syncer, tmp_path):
        """Test sync with invalid project path."""
        # Arrange
        invalid_path = tmp_path / "nonexistent"

        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError, match="pyproject.toml not found"):
            syncer.sync_project(invalid_path)

    def test_sync_project_missing_pyproject(self, syncer, tmp_path):
        """Test sync when pyproject.toml doesn't exist."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()

        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError, match="pyproject.toml not found"):
            syncer.sync_project(project)

    def test_sync_project_toml_parse_error(self, syncer, temp_project_structure):
        """Test sync with invalid TOML syntax."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("invalid toml {{[[]")

        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError):
            syncer.sync_project(temp_project_structure)

    def test_sync_project_up_to_date(self, syncer, temp_project_structure, template_data):
        """Test sync when project is already up to date."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test_project'\n")

        with patch.object(syncer, "_load_template", return_value=template_data):
            with patch.object(syncer, "_detect_changes", return_value=[]):
                # Act
                result = syncer.sync_project(temp_project_structure)

                # Assert
                assert result["status"] == "up_to_date"
                assert result["changes"] == []


class TestSyncAll:
    """Tests for sync_all method."""

    def test_sync_all_multiple_projects(self, syncer, tmp_path, template_data):
        """Test syncing multiple projects."""
        # Arrange
        for i in range(2):
            project = tmp_path / f"project_{i}"
            project.mkdir()
            (project / "pyproject.toml").write_text(f"[project]\nname = 'project_{i}'\n")
            (project / "src").mkdir()
            vscode = project / ".vscode"
            vscode.mkdir()
            (vscode / "settings.json").write_text("{}")
            claude = project / ".claude"
            claude.mkdir()
            (claude / "settings.local.json").write_text("{}")

        with patch.object(syncer, "_load_template", return_value=template_data):
            # Act
            results = syncer.sync_all(tmp_path)

            # Assert
            assert len(results) == 2
            assert all("status" in r for r in results)

    def test_sync_all_with_failures(self, syncer, tmp_path, template_data):
        """Test sync_all handles individual project failures."""
        # Arrange - one valid, one invalid
        valid = tmp_path / "valid"
        valid.mkdir()
        (valid / "pyproject.toml").write_text("[project]\nname = 'valid'\n")
        (valid / "src").mkdir()
        vscode = valid / ".vscode"
        vscode.mkdir()
        (vscode / "settings.json").write_text("{}")
        claude = valid / ".claude"
        claude.mkdir()
        (claude / "settings.local.json").write_text("{}")

        invalid = tmp_path / "invalid"
        invalid.mkdir()
        (invalid / "pyproject.toml").write_text("invalid toml {{")
        (invalid / "src").mkdir()
        vscode2 = invalid / ".vscode"
        vscode2.mkdir()
        (vscode2 / "settings.json").write_text("{}")
        claude2 = invalid / ".claude"
        claude2.mkdir()
        (claude2 / "settings.local.json").write_text("{}")

        with patch.object(syncer, "_load_template", return_value=template_data):
            # Act
            results = syncer.sync_all(tmp_path)

            # Assert
            assert len(results) == 2
            statuses = [r["status"] for r in results]
            assert "error" in statuses

    def test_sync_all_no_projects_found(self, syncer, tmp_path):
        """Test sync_all with no projects."""
        # Arrange
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Act
        results = syncer.sync_all(empty_dir)

        # Assert
        assert results == []

    def test_sync_all_dry_run(self, syncer, temp_project_structure, template_data):
        """Test sync_all in dry run mode."""
        # Arrange
        search_path = temp_project_structure.parent

        with patch.object(syncer, "_load_template", return_value=template_data):
            # Act
            results = syncer.sync_all(search_path, dry_run=True)

            # Assert
            assert len(results) >= 1
            for result in results:
                assert result["status"] in ["would_sync", "up_to_date"]


class TestSyncStatus:
    """Tests for get_sync_status method."""

    def test_get_sync_status_in_sync(self, syncer, temp_project_structure, template_data):
        """Test status check for in-sync project."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test_project'\n")

        with patch.object(syncer, "_load_template", return_value=template_data):
            with patch.object(syncer, "_detect_changes", return_value=[]):
                # Act
                status = syncer.get_sync_status(temp_project_structure)

                # Assert
                assert status["status"] == "in_sync"

    def test_get_sync_status_out_of_sync(self, syncer, temp_project_structure, template_data):
        """Test status check for out-of-sync project."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test_project'\n")

        with patch.object(syncer, "_load_template", return_value=template_data):
            with patch.object(syncer, "_detect_changes", return_value=["project.authors"]):
                # Act
                status = syncer.get_sync_status(temp_project_structure)

                # Assert
                assert status["status"] == "out_of_sync"
                assert "changes" in status
                assert "project.authors" in status["changes"]

    def test_get_sync_status_invalid_project(self, syncer, tmp_path):
        """Test status check for invalid project."""
        # Arrange
        invalid = tmp_path / "invalid"
        invalid.mkdir()

        # Act
        status = syncer.get_sync_status(invalid)

        # Assert
        assert status["status"] == "not_found"

    def test_get_sync_status_error(self, syncer, temp_project_structure):
        """Test status check with error."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("invalid toml {{")

        # Act
        status = syncer.get_sync_status(temp_project_structure)

        # Assert
        assert status["status"] == "error"
        assert "error" in status


# -------------------------------------------------------------
# TEST HELPER METHODS
# -------------------------------------------------------------
class TestHelperMethods:
    """Tests for helper utility methods."""

    def test_get_nested_value_success(self, syncer):
        """Test getting nested value from dictionary."""
        # Arrange
        data = {"a": {"b": {"c": "value"}}}

        # Act
        result = syncer._get_nested_value(data, ("a", "b", "c"))

        # Assert
        assert result == "value"

    def test_get_nested_value_missing_key(self, syncer):
        """Test getting nested value with missing key returns None."""
        # Arrange
        data = {"a": {"b": {}}}

        # Act
        result = syncer._get_nested_value(data, ("a", "b", "c"))

        # Assert
        assert result is None

    def test_get_nested_value_single_level(self, syncer):
        """Test getting single-level value."""
        # Arrange
        data = {"key": "value"}

        # Act
        result = syncer._get_nested_value(data, ("key",))

        # Assert
        assert result == "value"

    def test_set_nested_value_existing_path(self, syncer):
        """Test setting nested value in existing path."""
        # Arrange
        data = {"a": {"b": {"c": "old"}}}

        # Act
        syncer._set_nested_value(data, ("a", "b", "c"), "new")

        # Assert
        assert data["a"]["b"]["c"] == "new"

    def test_set_nested_value_create_path(self, syncer):
        """Test setting nested value creates missing path."""
        # Arrange
        data = {}

        # Act
        syncer._set_nested_value(data, ("a", "b", "c"), "value")

        # Assert
        assert data["a"]["b"]["c"] == "value"

    def test_set_nested_value_single_level(self, syncer):
        """Test setting single-level value."""
        # Arrange
        data = {}

        # Act
        syncer._set_nested_value(data, ("key",), "value")

        # Assert
        assert data["key"] == "value"

    def test_deep_copy_dict(self, syncer):
        """Test deep copying dictionary."""
        # Arrange
        original = {"a": {"b": "value"}}

        # Act
        copy = syncer._deep_copy(original)
        copy["a"]["b"] = "modified"

        # Assert
        assert original["a"]["b"] == "value"
        assert copy["a"]["b"] == "modified"

    def test_deep_copy_list(self, syncer):
        """Test deep copying list."""
        # Arrange
        original = [1, [2, 3], {"key": "value"}]

        # Act
        copy = syncer._deep_copy(original)
        copy[1][0] = 999

        # Assert
        assert original[1][0] == 2
        assert copy[1][0] == 999

    def test_deep_copy_primitives(self, syncer):
        """Test deep copying primitive values."""
        # Arrange & Act
        assert syncer._deep_copy("string") == "string"
        assert syncer._deep_copy(42) == 42
        assert syncer._deep_copy(3.14) == 3.14
        assert syncer._deep_copy(True) is True
        assert syncer._deep_copy(None) is None


# -------------------------------------------------------------
# TEST TOML CONVERSION
# -------------------------------------------------------------
class TestTomlConversion:
    """Tests for TOML format conversion."""

    def test_value_to_toml_bool(self, syncer):
        """Test converting boolean to TOML."""
        # Act & Assert
        assert syncer._value_to_toml(True) == "true"
        assert syncer._value_to_toml(False) == "false"

    def test_value_to_toml_string(self, syncer):
        """Test converting string to TOML."""
        # Act & Assert
        assert syncer._value_to_toml("hello") == '"hello"'
        # Note: _value_to_toml does not escape newlines, they are preserved
        assert syncer._value_to_toml("line1\nline2") == '"line1\nline2"'

    def test_value_to_toml_string_escaping(self, syncer):
        """Test string escaping in TOML."""
        # Act & Assert
        assert syncer._value_to_toml('quote"test') == '"quote\\"test"'
        assert syncer._value_to_toml("back\\slash") == '"back\\\\slash"'

    def test_value_to_toml_number(self, syncer):
        """Test converting numbers to TOML."""
        # Act & Assert
        assert syncer._value_to_toml(42) == "42"
        assert syncer._value_to_toml(3.14) == "3.14"
        assert syncer._value_to_toml(-100) == "-100"

    def test_value_to_toml_list_empty(self, syncer):
        """Test converting empty list to TOML."""
        # Act
        result = syncer._value_to_toml([])

        # Assert
        assert result == "[]"

    def test_value_to_toml_list_short(self, syncer):
        """Test converting short list to TOML."""
        # Act
        result = syncer._value_to_toml([1, 2, 3])

        # Assert
        assert result == "[1, 2, 3]"

    def test_value_to_toml_list_long(self, syncer):
        """Test converting long list to TOML (multiline)."""
        # Act
        result = syncer._value_to_toml([1, 2, 3, 4, 5])

        # Assert
        assert "[\n" in result
        assert ",\n" in result

    def test_value_to_toml_dict(self, syncer):
        """Test converting dictionary to TOML."""
        # Act
        result = syncer._value_to_toml({"key": "value"})

        # Assert
        assert "key" in result
        assert "value" in result

    def test_dict_to_toml_simple(self, syncer):
        """Test converting simple dictionary to TOML."""
        # Arrange
        data = {"key": "value", "number": 42}

        # Act
        result = syncer._dict_to_toml(data)

        # Assert
        assert 'key = "value"' in result
        assert "number = 42" in result

    def test_dict_to_toml_nested(self, syncer):
        """Test converting nested dictionary to TOML."""
        # Arrange
        data = {"section": {"key": "value"}}

        # Act
        result = syncer._dict_to_toml(data)

        # Assert
        assert "[section]" in result
        assert 'key = "value"' in result

    def test_dict_to_toml_with_prefix(self, syncer):
        """Test converting dictionary with prefix."""
        # Arrange
        data = {"subsection": {"key": "value"}}

        # Act
        result = syncer._dict_to_toml(data, prefix="tool")

        # Assert
        assert "[tool.subsection]" in result

    def test_write_pyproject_success(self, syncer, tmp_path):
        """Test writing pyproject.toml file."""
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        data = {"project": {"name": "test", "version": "1.0.0"}}

        # Act
        syncer._write_pyproject(pyproject, data)

        # Assert
        assert pyproject.exists()
        content = pyproject.read_text()
        assert "[project]" in content
        assert 'name = "test"' in content

    def test_write_pyproject_error(self, syncer, tmp_path):
        """Test write error handling."""
        # Arrange
        pyproject = tmp_path / "readonly" / "pyproject.toml"
        data = {"project": {"name": "test"}}

        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError, match="Failed to write pyproject.toml"):
            syncer._write_pyproject(pyproject, data)


# -------------------------------------------------------------
# TEST ERROR HANDLING
# -------------------------------------------------------------
class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_exception_class_can_be_raised(self):
        """Test SyncPyprojectTomlError can be raised."""
        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError):
            raise SyncPyprojectTomlError("Test error")

    def test_exception_message(self):
        """Test exception message is preserved."""
        # Arrange
        message = "Custom error message"

        # Act & Assert
        with pytest.raises(SyncPyprojectTomlError, match=message):
            raise SyncPyprojectTomlError(message)

    def test_sync_project_wraps_exceptions(self, syncer, temp_project_structure):
        """Test that sync_project wraps exceptions properly."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("[project]\n")

        with patch.object(syncer, "_load_template", side_effect=Exception("Template error")):
            # Act & Assert
            with pytest.raises(SyncPyprojectTomlError, match="Failed to sync"):
                syncer.sync_project(temp_project_structure)


# -------------------------------------------------------------
# TEST EDGE CASES
# -------------------------------------------------------------
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_load_pyproject_valid_toml(self, syncer, tmp_path):
        """Test loading valid pyproject.toml."""
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test'\n")

        # Act
        result = syncer._load_pyproject(pyproject)

        # Assert
        assert isinstance(result, dict)
        assert result["project"]["name"] == "test"

    def test_merge_with_none_values(self, syncer, template_data):
        """Test merging when target has None values."""
        # Arrange
        target = {"project": {"name": "test", "version": None}}

        # Act
        result = syncer._merge_data(target, template_data, "test")

        # Assert
        assert result["project"]["name"] == "test"
        # Note: None values are not preserved, template value is used
        assert result["project"]["version"] == template_data["project"]["version"]

    def test_package_name_with_special_characters(self, syncer, tmp_path):
        """Test package name detection with special characters."""
        # Arrange
        project = tmp_path / "project"
        project.mkdir()
        data = {"project": {"name": "my-package_123"}}

        # Act
        result = syncer._detect_package_name(project, data)

        # Assert
        assert result == "my-package_123"

    def test_sync_sections_constant_integrity(self):
        """Test that SYNC_SECTIONS constant is properly defined."""
        # Assert
        assert isinstance(SYNC_SECTIONS, list)
        assert len(SYNC_SECTIONS) > 0
        assert all(isinstance(section, tuple) for section in SYNC_SECTIONS)

    def test_preserve_sections_constant_integrity(self):
        """Test that PRESERVE_SECTIONS constant is properly defined."""
        # Assert
        assert isinstance(PRESERVE_SECTIONS, list)
        assert len(PRESERVE_SECTIONS) > 0
        assert all(isinstance(section, tuple) for section in PRESERVE_SECTIONS)

    def test_empty_pyproject_toml(self, syncer, temp_project_structure, template_data):
        """Test syncing with empty pyproject.toml."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        pyproject.write_text("")

        with patch.object(syncer, "_load_template", return_value=template_data):
            # Act - Empty file is valid TOML (empty dict), should sync successfully
            result = syncer.sync_project(temp_project_structure)

            # Assert
            assert result["status"] in ["synced", "would_sync", "up_to_date"]

    def test_very_large_pyproject_toml(self, syncer, temp_project_structure):
        """Test syncing with large pyproject.toml."""
        # Arrange
        pyproject = temp_project_structure / "pyproject.toml"
        large_data = {
            "project": {
                "name": "test",
                "dependencies": [f"package{i}>=1.0.0" for i in range(100)],
            }
        }
        pyproject.write_text(str(large_data))

        # Note: This will fail due to invalid format, but tests handling
        with pytest.raises(SyncPyprojectTomlError):
            syncer.sync_project(temp_project_structure)

    def test_dict_to_toml_complex_nesting(self, syncer):
        """Test _dict_to_toml with complex nested structures."""
        # Arrange
        data = {
            "simple": "value",
            "number": 42,
            "section": {
                "nested": {
                    "deeply": {"key": "value"},
                }
            },
        }

        # Act
        result = syncer._dict_to_toml(data)

        # Assert
        assert 'simple = "value"' in result
        assert "number = 42" in result
        assert "section" in result

    def test_value_to_toml_empty_dict(self, syncer):
        """Test converting empty dictionary to TOML."""
        # Act
        result = syncer._value_to_toml({})

        # Assert
        assert result == "{}"

    def test_value_to_toml_nested_dict(self, syncer):
        """Test converting nested dictionary to TOML."""
        # Act
        result = syncer._value_to_toml({"inner": {"key": "val"}})

        # Assert
        assert "inner" in result

    def test_load_pyproject_missing_file(self, syncer, tmp_path):
        """Test loading non-existent pyproject.toml raises error."""
        # Arrange
        missing = tmp_path / "missing.toml"

        # Act & Assert
        with pytest.raises(Exception):
            syncer._load_pyproject(missing)
