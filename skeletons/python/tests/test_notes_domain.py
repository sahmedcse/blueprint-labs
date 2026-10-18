import pytest

from __PKG__.domain.notes import MAX_BODY_LENGTH, InvalidNoteError, normalize_body


@pytest.mark.parametrize(
    ("given", "want"),
    [
        ("buy oat milk", "buy oat milk"),
        ("  call the plumber \n", "call the plumber"),
        ("x" * MAX_BODY_LENGTH, "x" * MAX_BODY_LENGTH),
    ],
)
def test_normalize_body_accepts(given: str, want: str) -> None:
    assert normalize_body(given) == want


@pytest.mark.parametrize("given", ["", "   ", "x" * (MAX_BODY_LENGTH + 1)])
def test_normalize_body_rejects(given: str) -> None:
    with pytest.raises(InvalidNoteError):
        normalize_body(given)
