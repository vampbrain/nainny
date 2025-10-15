from fastapi.testclient import TestClient
import importlib


def test_adapt_story(tmp_path, monkeypatch):
    # use a temp DB
    db_file = tmp_path / "adapt_test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    # reload DB module and rebuild engine
    import app.core.database as adb
    importlib.reload(adb)
    # ensure models are re-imported cleanly
    import sys
    if 'app.models' in sys.modules:
        del sys.modules['app.models']

    for m in ('app.models.story', 'app.models.cultural', 'app.models.user', 'app.models.sync'):
        if m in sys.modules:
            del sys.modules[m]
        importlib.import_module(m)

    adb.init_db(reset=True)

    from app.main import create_app
    app = create_app()
    client = TestClient(app)

    # seed a dummy story
    from app.core.database import get_db
    from app.models.story import Story
    with get_db() as db:
        s = Story(title='Festival', content='During Diwali, people light lamps.')
        db.add(s)
        db.commit()
        db.refresh(s)

    resp = client.post('/adapt-story', json={
        'story_id': s.id,
        'target_culture': 'western',
        'target_age': 'child'
    })

    assert resp.status_code == 200
    data = resp.json()
    assert 'adapted_story' in data
    assert isinstance(data.get('score', 0), (int, float))
