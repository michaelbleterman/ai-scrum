from project_tracking.dummy_math import add

def test_add_positive_numbers():
    """
    Tests if the add function correctly adds two positive numbers.
    This test is expected to FAIL due to the intentional bug.
    """
    assert add(2, 3) == 5
