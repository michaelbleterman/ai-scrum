from project_tracking.dummy_math import add

def test_add_correctly():
    """
    This test checks the intended functionality of the 'add' function.
    It is expected to FAIL because of the known bug (a - b).
    """
    # The function should return 5 + 3 = 8, but the buggy code will return 5 - 3 = 2.
    assert add(5, 3) == 8
