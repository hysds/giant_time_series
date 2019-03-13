import pytest


def test_version():
    import giant_time_series
    assert giant_time_series.__version__ == "0.0.2"
