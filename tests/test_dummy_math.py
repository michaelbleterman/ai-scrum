from project_tracking.dummy_math import add

def test_add():
    assert add(2, 3) == 5, f"Expected 5, but got {add(2, 3)}"
