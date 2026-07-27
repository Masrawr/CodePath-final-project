from logic_utils import check_guess, new_game, parse_guess


class FakeSessionState:
    """Minimal stand-in for st.session_state (attribute access)."""
    pass


def test_new_game_resets_finished_game():
    # Simulate a finished game stuck in the "won" state with stale values.
    state = FakeSessionState()
    state.status = "won"
    state.attempts = 8
    state.score = 120
    state.history = [10, 20, 50]
    state.secret = 50

    new_game(state, low=1, high=100)

    # The core bug: status must return to "playing" so the game is playable again.
    assert state.status == "playing"
    # Score and history are cleared for a fresh round.
    assert state.score == 0
    assert state.history == []
    # Attempts reset to the starting value used at app init.
    assert state.attempts == 1


def test_new_game_secret_in_range():
    # A new secret must be drawn from the difficulty's range (inclusive).
    state = FakeSessionState()
    new_game(state, low=7, high=7)
    assert state.secret == 7

    new_game(state, low=1, high=20)
    assert 1 <= state.secret <= 20


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


def test_guess_below_range_rejected():
    # A negative guess is out of range and must be rejected.
    ok, value, err = parse_guess("-1")
    assert ok is False
    assert value is None
    assert err == "Guess is out of range (0-100)"


def test_guess_above_range_rejected():
    # A guess above 100 is out of range and must be rejected.
    ok, value, err = parse_guess("101")
    assert ok is False
    assert value is None
    assert err == "Guess is out of range (0-100)"


def test_guess_in_range_accepted():
    # A guess within 0-100 is accepted and parsed to an int.
    ok, value, err = parse_guess("42")
    assert ok is True
    assert value == 42
    assert err is None


def test_guess_at_range_boundaries_accepted():
    # The boundaries 0 and 100 are inclusive and must be accepted.
    assert parse_guess("0") == (True, 0, None)
    assert parse_guess("100") == (True, 100, None)
