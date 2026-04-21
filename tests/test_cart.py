import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cart_module_uses_live_product_data():
    result = subprocess.run(
        ["node", str(ROOT / "tests" / "js" / "cart_validation_test.js")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
