from fastapi.testclient import TestClient


def test_health_and_seed(monkeypatch, tmp_path):
    # Use a temporary DB for the app
    db_file = tmp_path / "api_test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    # import and create app lazily
    from app.main import create_app
    # ensure DB module picks up the monkeypatched DB_PATH before app creation
    import importlib
    import app.core.database as adb
    importlib.reload(adb)
    import sys
    # remove the package entry to ensure fresh module imports
    if 'app.models' in sys.modules:
        del sys.modules['app.models']
    for _m in ('app.models.story', 'app.models.cultural', 'app.models.user', 'app.models.sync'):
        if _m in sys.modules:
            del sys.modules[_m]
        importlib.import_module(_m)

    # Ensure schema exists for the test DB before creating the app
    adb.init_db(reset=True)

    app = create_app()

    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    # seed culture endpoint should succeed (idempotent)
    r2 = client.get("/seed-culture")
    assert r2.status_code == 200
    assert r2.json().get("seeded") is True
