from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.database.crud import CRUD
from src.database.models import TaskRecord
from src.database.queries import Queries


@pytest.fixture
def db_session() -> MagicMock:
    return MagicMock()


@pytest.fixture
def crud(db_session: MagicMock) -> CRUD:
    return CRUD(db_session)


@pytest.fixture
def sample_task_record() -> TaskRecord:
    return TaskRecord(
        task_id="test-task-001",
        query="test query",
        agent_type="query",
        tools=["database_tool"],
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestCRUD:
    def test_create_task(self, crud: CRUD, db_session: MagicMock) -> None:
        mock_task = MagicMock(spec=TaskRecord)
        mock_task.task_id = "new-id"
        db_session.add.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.side_effect = lambda x: None

        with patch("src.database.crud.TaskRecord", return_value=mock_task):
            task = crud.create_task("hello", "query", ["database_tool"])
            assert task is not None
            db_session.add.assert_called_once()
            db_session.commit.assert_called_once()

    def test_get_task_exists(self, crud: CRUD, db_session: MagicMock, sample_task_record: TaskRecord) -> None:
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_task_record
        db_session.query.return_value = query_mock

        task = crud.get_task("test-task-001")
        assert task is not None
        assert task.task_id == "test-task-001"
        assert task.query == "test query"

    def test_get_task_not_found(self, crud: CRUD, db_session: MagicMock) -> None:
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_session.query.return_value = query_mock

        task = crud.get_task("nonexistent")
        assert task is None

    def test_update_task(self, crud: CRUD, db_session: MagicMock, sample_task_record: TaskRecord) -> None:
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_task_record
        db_session.query.return_value = query_mock
        db_session.commit.return_value = None
        db_session.refresh.side_effect = lambda x: None

        updated = crud.update_task("test-task-001", {"status": "completed"})
        assert updated is not None
        assert updated.status == "completed"

    def test_update_task_not_found(self, crud: CRUD, db_session: MagicMock) -> None:
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_session.query.return_value = query_mock

        updated = crud.update_task("nonexistent", {"status": "completed"})
        assert updated is None

    def test_list_tasks_no_filters(self, crud: CRUD, db_session: MagicMock, sample_task_record: TaskRecord) -> None:
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [sample_task_record]
        db_session.query.return_value = query_mock

        tasks = crud.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].task_id == "test-task-001"

    def test_list_tasks_with_filters(self, crud: CRUD, db_session: MagicMock, sample_task_record: TaskRecord) -> None:
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [sample_task_record]
        db_session.query.return_value = query_mock

        tasks = crud.list_tasks({"status": "pending"})
        assert len(tasks) == 1


class _MockRow:
    _mapping: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        self._mapping = kwargs


class TestQueries:
    def test_execute_raw_sql_returns_rows(self, db_session: MagicMock) -> None:
        rows = [_MockRow(id=1, name="test")]
        result_mock = MagicMock()
        result_mock.returns_rows = True
        result_mock.__iter__.return_value = iter(rows)
        db_session.execute.return_value = result_mock

        queries = Queries(db_session)
        results = queries.execute_raw_sql("SELECT * FROM tasks")
        assert len(results) == 1
        assert results[0]["name"] == "test"

    def test_execute_raw_sql_no_rows(self, db_session: MagicMock) -> None:
        result_mock = MagicMock()
        result_mock.returns_rows = False
        db_session.execute.return_value = result_mock

        queries = Queries(db_session)
        results = queries.execute_raw_sql("DELETE FROM tasks")
        assert len(results) == 0

    def test_count_tasks_by_status(self, db_session: MagicMock) -> None:
        rows = [_MockRow(status="completed", count=5)]
        result_mock = MagicMock()
        result_mock.returns_rows = True
        result_mock.__iter__.return_value = iter(rows)
        db_session.execute.return_value = result_mock

        queries = Queries(db_session)
        results = queries.count_tasks_by_status()
        assert len(results) == 1
        assert results[0]["count"] == 5

    def test_get_recent_tasks(self, db_session: MagicMock) -> None:
        rows = [_MockRow(task_id="t1", query="q1", agent_type="query", status="completed")]
        result_mock = MagicMock()
        result_mock.returns_rows = True
        result_mock.__iter__.return_value = iter(rows)
        db_session.execute.return_value = result_mock

        queries = Queries(db_session)
        results = queries.get_recent_tasks(limit=5)
        assert len(results) == 1
        assert results[0]["task_id"] == "t1"
