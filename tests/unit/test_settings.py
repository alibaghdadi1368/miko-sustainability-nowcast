from pathlib import Path
import pytest
from miko.settings import PROJECT_ROOT, load_settings

def test_local_settings_load():
    s = load_settings("local")
    assert s.env == "local"
    assert s.spark_shuffle_partitions == 4

def test_paths_are_absolute_and_inside_the_project():
    s = load_settings("local")
    for path in (s.landing_dir, s.landing_dir, s.checkpoint_dir):
        assert isinstance(path, Path)
        assert path.is_absolute()
        assert PROJECT_ROOT in path.parents

def test_env_variable_is_used(monkeypatch):
    monkeypatch.setenv("MIKO_ENV", "local")
    assert load_settings().env == "local"

def test_unknown_environment_fails_loudly():
    with pytest.raises(FileNotFoundError):
        load_settings("does-not-exist")
