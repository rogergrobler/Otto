from app.llm.prompts import build_system_prompt


def test_build_system_prompt_minimal():
    prompt = build_system_prompt(
        soul_doc="You are Sofia.",
        training_notes=[],
        client_profile="Name: Test Client",
        memory_summary=None,
        coursework_context=None,
    )
    assert "You are Sofia." in prompt
    assert "Name: Test Client" in prompt


def test_build_system_prompt_full():
    prompt = build_system_prompt(
        soul_doc="You are Sofia, a coaching assistant.",
        training_notes=["Be more empathetic", "Ask deeper questions"],
        client_profile="Name: Alice\nCoach's notes: Working on self-discovery",
        memory_summary="Alice discussed her career transition last session.",
        coursework_context="**Week 1 Exercise**: Journaling about your wild self.",
    )
    assert "You are Sofia" in prompt
    assert "Be more empathetic" in prompt
    assert "Ask deeper questions" in prompt
    assert "Alice" in prompt
    assert "career transition" in prompt
    assert "Journaling" in prompt
