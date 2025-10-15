import importlib


def test_conceptnet_cache(tmp_path, monkeypatch):
    db_file = tmp_path / "cache_test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

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

    from app.models.sync import ConceptNetCache

    with adb.get_db() as db:
        obj = ConceptNetCache(concept='apple', relations={'is-a': ['fruit']})
        db.add(obj)
        db.commit()

        fetched = db.query(ConceptNetCache).filter_by(concept='apple').first()
        assert fetched is not None
        assert isinstance(fetched.relations, dict)
