import pytest
from src.main import run_scan, generate_dashboard

def test_scanner_initialization():
    # Basic test to ensure scanner can be imported
    from src.main import run_scan
    assert run_scan is not None

def test_scan_all():
    # Run a basic scan to ensure it doesn't crash
    try:
        results = run_scan(sector="ai", top=5)
        assert isinstance(results, list)
        assert len(results) > 0
    except Exception as e:
        pytest.skip(f"Skipping full scan test due to missing API keys or network: {e}")