"""
Tests para el modulo de cache.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tempfile
from pathlib import Path
from unittest.mock import patch


class TestProblemCache:
    def test_init_creates_dirs(self):
        from src.utils.cache import ProblemCache
        with patch("src.utils.cache.PARSED_DIR") as mock_parsed:
            with patch("src.utils.cache.RESULTS_DIR") as mock_results:
                ProblemCache()
                mock_parsed.mkdir.assert_called()
                mock_results.mkdir.assert_called()

    def test_set_and_get_parsed(self):
        from src.utils.cache import ProblemCache
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.cache.PARSED_DIR", Path(tmpdir) / "parsed"):
                with patch("src.utils.cache.RESULTS_DIR", Path(tmpdir) / "results"):
                    cache = ProblemCache(ttl=3600)
                    cache.set_parsed("test content", {"key": "value"})
                    result = cache.get_parsed("test content")
                    assert result == {"key": "value"}

    def test_get_parsed_expired(self):
        import time
        from pathlib import Path

        from src.utils.cache import ProblemCache
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.cache.PARSED_DIR", Path(tmpdir) / "parsed"):
                with patch("src.utils.cache.RESULTS_DIR", Path(tmpdir) / "results"):
                    cache = ProblemCache(ttl=0)
                    cache.set_parsed("expired content", {"data": 1})
                    time.sleep(0.01)
                    result = cache.get_parsed("expired content")
                    assert result is None

    def test_get_parsed_missing(self):
        from src.utils.cache import ProblemCache
        result = ProblemCache().get_parsed("nonexistent")
        assert result is None

    def test_set_and_get_result(self):
        from pathlib import Path

        from src.utils.cache import ProblemCache
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.cache.PARSED_DIR", Path(tmpdir) / "parsed"):
                with patch("src.utils.cache.RESULTS_DIR", Path(tmpdir) / "results"):
                    cache = ProblemCache(ttl=3600)
                    cache.set_result("test content", "highs", {"status": "optimal"})
                    result = cache.get_result("test content", "highs")
                    assert result["status"] == "optimal"

    def test_get_result_expired(self):
        import time
        from pathlib import Path

        from src.utils.cache import ProblemCache
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.cache.PARSED_DIR", Path(tmpdir) / "parsed"):
                with patch("src.utils.cache.RESULTS_DIR", Path(tmpdir) / "results"):
                    cache = ProblemCache(ttl=0)
                    cache.set_result("expired", "highs", {"status": "ok"})
                    time.sleep(0.01)
                    result = cache.get_result("expired", "highs")
                    assert result is None

    def test_get_result_missing(self):
        from src.utils.cache import ProblemCache
        result = ProblemCache().get_result("nonexistent", "highs")
        assert result is None

    def test_invalidate_all(self):
        from pathlib import Path

        from src.utils.cache import ProblemCache
        with tempfile.TemporaryDirectory() as tmpdir:
            parsed_dir = Path(tmpdir) / "parsed"
            results_dir = Path(tmpdir) / "results"
            parsed_dir.mkdir(parents=True)
            results_dir.mkdir(parents=True)
            (parsed_dir / "test.pkl").write_text("data")
            (results_dir / "test.json").write_text("{}")
            with patch("src.utils.cache.PARSED_DIR", parsed_dir):
                with patch("src.utils.cache.RESULTS_DIR", results_dir):
                    cache = ProblemCache()
                    cache.invalidate_all()
                    assert not list(parsed_dir.iterdir())
                    assert not list(results_dir.iterdir())

    def test_invalidate_parsed(self):
        from pathlib import Path

        from src.utils.cache import ProblemCache
        with tempfile.TemporaryDirectory() as tmpdir:
            parsed_dir = Path(tmpdir) / "parsed"
            with patch("src.utils.cache.PARSED_DIR", parsed_dir):
                with patch("src.utils.cache.RESULTS_DIR", Path(tmpdir) / "results"):
                    cache = ProblemCache()
                    cache.set_parsed("invalid", {"x": 1})
                    cache.invalidate_parsed("invalid")
                    result = cache.get_parsed("invalid")
                    assert result is None

    def test_get_stats(self):
        from pathlib import Path

        from src.utils.cache import ProblemCache
        with tempfile.TemporaryDirectory() as tmpdir:
            parsed_dir = Path(tmpdir) / "parsed"
            results_dir = Path(tmpdir) / "results"
            with patch("src.utils.cache.PARSED_DIR", parsed_dir):
                with patch("src.utils.cache.RESULTS_DIR", results_dir):
                    cache = ProblemCache()
                    stats = cache.get_stats()
                    assert "parsed_entries" in stats
                    assert "result_entries" in stats
                    assert "cache_dir" in stats
