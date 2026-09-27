from use_cases.medevidence_research.release import (
    block_response,
    release_response,
    route_after_citation_validation,
)


def test_valid_citations_route_to_release() -> None:
    state = {"validation_status": "valid"}

    assert route_after_citation_validation(state) == "release"


def test_invalid_citations_route_to_block() -> None:
    state = {"validation_status": "invalid"}

    assert route_after_citation_validation(state) == "block"


def test_release_copies_validated_synthesis_to_final_answer() -> None:
    state = {
        "validation_status": "valid",
        "synthesis": "Grounded evidence response.",
    }

    update = release_response(state)

    assert update["final_answer"] == "Grounded evidence response."
    assert update["release_status"] == "released"


def test_block_does_not_release_invalid_synthesis() -> None:
    invalid_candidate = "Response containing an invented citation."
    state = {
        "validation_status": "invalid",
        "synthesis": invalid_candidate,
    }

    update = block_response(state)

    assert update["release_status"] == "blocked"
    assert update["response_mode"] == "abstain"
    assert update["final_answer"] != invalid_candidate


def test_empty_synthesis_is_blocked_even_after_validation() -> None:
    state = {
        "validation_status": "valid",
        "synthesis": None,
    }

    update = release_response(state)

    assert update["release_status"] == "blocked"
    assert update["response_mode"] == "abstain"
    assert update["errors"][0]["code"] == "MISSING_RENDERED_SYNTHESIS"