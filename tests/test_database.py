"""Unit tests for SQLite database schema, CRUD operations, and memory tracking."""
import uuid
from backend.core.database import (
    create_project,
    get_project,
    update_project_state,
    list_projects,
    delete_project_record,
    save_topic,
    get_recent_topics,
    save_script,
    get_script,
    save_claims,
    get_claims,
)
from backend.models import (
    ProjectModel,
    ProjectState,
    ScriptModel,
    ScriptScene,
    FactualClaim,
    ClaimStatus,
)


def test_project_crud():
    pid = f"test_proj_{uuid.uuid4().hex[:6]}"
    proj = ProjectModel(
        id=pid,
        title="Test Space Short",
        category="space",
        state=ProjectState.IDEA,
    )
    create_project(proj)

    fetched = get_project(pid)
    assert fetched is not None
    assert fetched.id == pid
    assert fetched.title == "Test Space Short"
    assert fetched.state == ProjectState.IDEA

    # Update state
    update_project_state(pid, ProjectState.RENDERED, video_path="projects/test/final.mp4", duration_sec=32.5)
    updated = get_project(pid)
    assert updated.state == ProjectState.RENDERED
    assert updated.video_path == "projects/test/final.mp4"
    assert updated.duration_sec == 32.5

    # Delete
    delete_project_record(pid)
    assert get_project(pid) is None


def test_topic_memory_tracking():
    test_topic = f"Unique Quantum Mystery {uuid.uuid4().hex[:4]}"
    save_topic(project_id=None, topic=test_topic, category="science", selected=True)
    recent = get_recent_topics(limit=20)
    assert test_topic in recent


def test_script_and_claims_persistence():
    pid = f"test_script_proj_{uuid.uuid4().hex[:6]}"
    create_project(ProjectModel(id=pid, title="Script Test", category="tech", state=ProjectState.SCRIPTING))

    script = ScriptModel(
        hook="Why do airplane windows have tiny holes?",
        context="It looks like a crack, but it protects you.",
        main_facts="It balances air pressure between the cabin and outside.",
        payoff="Without it, the outer window pane could fail under stress.",
        cta="Subscribe for more tech facts!",
        full_narration="Why do airplane windows have tiny holes? It balances air pressure.",
        word_count=13,
        estimated_duration_sec=5.2,
        scenes=[
            ScriptScene(scene_index=1, narration="Why do airplane windows have tiny holes?", duration_est=3.0, visual_description="Airplane window"),
            ScriptScene(scene_index=2, narration="It balances air pressure.", duration_est=2.2, visual_description="Pressure diagram"),
        ],
    )
    save_script(pid, script)
    fetched_script = get_script(pid)
    assert fetched_script is not None
    assert fetched_script.word_count == 13
    assert len(fetched_script.scenes) == 2

    # Save Claims
    claims = [
        FactualClaim(claim_text="Holes balance air pressure", status=ClaimStatus.VERIFIED, confidence=0.96, evidence="FAA aircraft documentation"),
    ]
    save_claims(pid, claims)
    fetched_claims = get_claims(pid)
    assert len(fetched_claims) == 1
    assert fetched_claims[0].status == ClaimStatus.VERIFIED

    delete_project_record(pid)
