import pytest

from tools.x import X


def test_post_length():
    x = X()
    with pytest.raises(ValueError):
        x.post("")
    with pytest.raises(ValueError):
        x.post("a" * 281)
