import pytest

from app.models.user import User
from app.services.profile_completion_service import ProfileCompletionService


def _make_user(*, display_name: str | None, profile_completed: bool) -> User:
    user = User()
    user.email = "test@example.com"
    user.profile_completed = profile_completed
    user.display_name = display_name
    return user


def test_apply_auto_completion_noop_when_already_completed():
    svc = ProfileCompletionService()
    user = _make_user(display_name="Already Done", profile_completed=True)

    changed = svc.apply_auto_completion(user)

    assert changed is False
    assert user.profile_completed is True


@pytest.mark.parametrize("display_name", [None, "", "   "])
def test_apply_auto_completion_does_not_complete_without_display_name(display_name: str | None):
    svc = ProfileCompletionService()
    user = _make_user(display_name=display_name, profile_completed=False)

    changed = svc.apply_auto_completion(user)

    assert changed is False
    assert user.profile_completed is False


def test_apply_auto_completion_marks_complete_when_display_name_present():
    svc = ProfileCompletionService()
    user = _make_user(display_name="Fawler", profile_completed=False)

    changed = svc.apply_auto_completion(user)

    assert changed is True
    assert user.profile_completed is True





