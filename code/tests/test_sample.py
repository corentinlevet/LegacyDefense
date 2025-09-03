from core.sample import add


def test_add_positive_numbers():
    assert add(2, 3) == 5


def test_add_with_zero():
    assert add(7, 0) == 7


def test_add_negative_numbers():
    assert add(-2, -3) == -5
