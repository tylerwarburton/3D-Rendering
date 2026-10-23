import ast
from pathlib import Path


SOURCE = Path(__file__).parents[1] / "blender_scene.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
CONSTANTS = {
    node.targets[0].id: ast.literal_eval(node.value)
    for node in TREE.body
    if isinstance(node, ast.Assign)
    and len(node.targets) == 1
    and isinstance(node.targets[0], ast.Name)
    and isinstance(node.value, ast.Constant)
}


def test_timeline_is_exactly_ten_seconds():
    assert CONSTANTS["FPS"] == 30
    assert CONSTANTS["FRAME_END"] == 300


def test_one_second_head_start_is_locked():
    assert CONSTANTS["CAR_START"] == 45
    assert CONSTANTS["IGNITION"] == 75
    assert CONSTANTS["IGNITION"] - CONSTANTS["CAR_START"] == CONSTANTS["FPS"]


def test_liftoff_and_title_are_separate_events():
    assert CONSTANTS["LIFTOFF"] == 165
    assert CONSTANTS["TITLE_START"] == 270

