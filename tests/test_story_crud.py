import importlib


def test_story_crud(tmp_path, monkeypatch):
    db_file = tmp_path / "story_test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    # reload DB module
    import app.core.database as adb
    importlib.reload(adb)
    import sys
    if 'app.models' in sys.modules:
        del sys.modules['app.models']
    for _m in ('app.models.story', 'app.models.cultural', 'app.models.user', 'app.models.sync'):
        if _m in sys.modules:
            del sys.modules[_m]
        importlib.import_module(_m)

    adb.init_db(reset=True)

    from app.models.story import Story

    with adb.get_db() as db:
        # create
        s = Story(title='Test Story', content='Once upon a time')
        db.add(s)
        db.commit()
        assert s.id is not None

        # read
        fetched = db.query(Story).filter_by(id=s.id).first()
        assert fetched.title == 'Test Story'

        # update
        fetched.title = 'Updated'
        db.add(fetched)
        db.commit()
        reloaded = db.query(Story).filter_by(id=s.id).first()
        assert reloaded.title == 'Updated'

        # delete
        db.delete(reloaded)
        db.commit()
        assert db.query(Story).filter_by(id=s.id).first() is None
