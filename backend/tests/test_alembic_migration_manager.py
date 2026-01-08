"""Tests for AlembicMigrationManager"""

import pytest
from pathlib import Path
from app.database.alembic_migration_manager import AlembicMigrationManager, AlembicMigrationPaths


def test_migration_paths_resolution():
    """Test that migration paths resolve correctly"""
    manager = AlembicMigrationManager()
    paths = manager._paths
    
    # Verify backend directory is correct
    assert paths.backend_dir.exists(), "Backend directory should exist"
    assert paths.backend_dir.is_dir(), "Backend directory should be a directory"
    
    # Verify alembic.ini exists
    assert paths.alembic_ini_path.exists(), "alembic.ini should exist"
    assert paths.alembic_ini_path.name == "alembic.ini", "Should point to alembic.ini"
    
    # Verify alembic script location exists
    assert paths.alembic_script_location.exists(), "Alembic script location should exist"
    assert paths.alembic_script_location.is_dir(), "Alembic script location should be a directory"


def test_config_building():
    """Test that Alembic config builds correctly"""
    manager = AlembicMigrationManager()
    cfg = manager._build_config()
    
    # Verify script_location is set
    script_location = cfg.get_main_option("script_location")
    assert script_location, "Script location should be set"
    assert Path(script_location).exists(), "Script location path should exist"
    
    # Verify it's an absolute path (required for Render)
    assert Path(script_location).is_absolute(), "Script location should be absolute"


def test_manager_initialization():
    """Test that manager initializes without errors"""
    manager = AlembicMigrationManager()
    assert manager is not None
    assert manager._paths is not None


@pytest.mark.skip(reason="Requires database connection - run manually in production")
def test_upgrade_head_execution():
    """Test that upgrade_head actually runs (requires DB connection)"""
    manager = AlembicMigrationManager()
    # This would actually run migrations - only test in staging/production
    # manager.upgrade_head()
    pass



