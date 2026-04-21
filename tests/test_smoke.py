"""Smoke tests for package structure."""


def test_version_exposed():
    import kiwi_core
    assert kiwi_core.__version__ == "0.1.0"


def test_subpackages_importable():
    from kiwi_core import agents, memory, tools
    assert tools.__package__ == "kiwi_core.tools"
    assert agents.__package__ == "kiwi_core.agents"
    assert memory.__package__ == "kiwi_core.memory"
