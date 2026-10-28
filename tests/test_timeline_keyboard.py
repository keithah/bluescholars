from pathlib import Path
import shutil
import subprocess
import pytest


def test_keyboard_can_cross_a_missing_capture_year():
    if not shutil.which('node'):
        pytest.skip('Node is unavailable')
    root = Path(__file__).resolve().parents[1]
    subprocess.run(['node', 'tests/timeline_keyboard.cjs'], cwd=root, check=True,
                   capture_output=True, text=True)
