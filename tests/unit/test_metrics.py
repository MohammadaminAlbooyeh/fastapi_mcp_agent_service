from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.metrics import REQUEST_COUNT
from src.main import app


class TestMetricsCardinality:
    def test_dynamic_path_params_do_not_create_separate_label_series(self) -> None:
        """Hitting the same route template with different path parameters
        (e.g. two different task_ids) must collapse to a single Prometheus
        label series keyed by the route template, not grow unboundedly with
        every distinct id ever requested."""
        client = TestClient(app)

        client.get(
            "/api/v1/agent/status/task-id-one", headers={"Authorization": "Bearer x"}
        )
        client.get(
            "/api/v1/agent/status/task-id-two", headers={"Authorization": "Bearer x"}
        )

        samples = [
            sample
            for metric in REQUEST_COUNT.collect()
            for sample in metric.samples
            if sample.labels.get("endpoint") == "/api/v1/agent/status/{task_id}"
        ]
        assert samples, "expected the route-template endpoint label to be recorded"

        raw_path_samples = [
            sample
            for metric in REQUEST_COUNT.collect()
            for sample in metric.samples
            if "task-id-one" in sample.labels.get("endpoint", "")
            or "task-id-two" in sample.labels.get("endpoint", "")
        ]
        assert (
            raw_path_samples == []
        ), "task_id values must never leak into metric labels"
