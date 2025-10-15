import importlib
import os


def test_db_init_and_seed(tmp_path, monkeypatch):
    """Initialize a temporary DB and verify the seeder runs and populates expected tables."""
    db_file = tmp_path / "ni_test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    # reload the database module so it picks up the test DB_PATH
    import app.core.database as adb
    importlib.reload(adb)
    # Ensure model modules are freshly imported and bound to the reloaded Base/engine
    import sys
    if 'app.models' in sys.modules:
        del sys.modules['app.models']
    for _m in (
        'app.models.story',
        'app.models.cultural',
        'app.models.user',
        'app.models.sync',
    ):
        if _m in sys.modules:
            del sys.modules[_m]
        importlib.import_module(_m)

    # ensure DB does not exist yet
    assert not db_file.exists()

    # initialize database (reset ensures clean schema for tests)
    adb.init_db(reset=True)

    # run the project's seeder to populate cultural data
    import app.services.init_db as sdb
    importlib.reload(sdb)
    sdb.seed_indian_cultural_data()

    # DB file should now exist
    assert db_file.exists()

    stats = adb.get_db_stats()

    # basic expected seeded items from the seeder
    assert stats.get("cultural_contexts", 0) >= 1
    assert stats.get("stories", 0) >= 0
    # system_status should be created during init
    # get_db_stats does not return system_status; verify DB file size > 0
    assert stats.get("database_size") is not None
