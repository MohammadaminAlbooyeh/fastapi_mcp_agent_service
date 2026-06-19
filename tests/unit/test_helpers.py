from __future__ import annotations

from src.utils.helpers import compute_hash, generate_task_id, timestamp, truncate_text


class TestHelpers:
    def test_generate_task_id(self) -> None:
        task_id = generate_task_id()
        assert isinstance(task_id, str)
        assert len(task_id) > 0

    def test_generate_task_id_unique(self) -> None:
        ids = {generate_task_id() for _ in range(100)}
        assert len(ids) == 100

    def test_compute_hash(self) -> None:
        h = compute_hash("hello")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_compute_hash_deterministic(self) -> None:
        assert compute_hash("hello") == compute_hash("hello")
        assert compute_hash("hello") != compute_hash("world")

    def test_timestamp(self) -> None:
        ts = timestamp()
        assert "T" in ts

    def test_truncate_text_short(self) -> None:
        assert truncate_text("hello", 10) == "hello"

    def test_truncate_text_long(self) -> None:
        result = truncate_text("hello world this is long", 10)
        assert result.endswith("...")
        assert len(result) == 13

    def test_truncate_text_exact(self) -> None:
        assert truncate_text("12345", 5) == "12345"
