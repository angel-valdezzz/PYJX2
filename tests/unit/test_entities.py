"""Unit tests for domain entities."""
import pytest
from pyjx2.domain.entities import Test, TestSet, TestExecution, TestPlan


class TestTestEntity:
    def test_creation_with_required_fields(self):
        t = Test(key="PROJ-1", summary="My test")
        assert t.key == "PROJ-1"
        assert t.summary == "My test"

    def test_default_test_type_is_manual(self):
        t = Test(key="PROJ-1", summary="My test")
        assert t.test_type == "Manual"

    def test_optional_fields_default_to_none_or_empty(self):
        t = Test(key="PROJ-1", summary="My test")
        assert t.status is None
        assert t.labels == []
        assert t.description is None
        assert t.steps == []
        assert t.precondition is None
        assert t.issue_id is None

    def test_explicit_fields(self):
        t = Test(
            key="PROJ-2",
            summary="Login",
            test_type="Automated",
            status="PASS",
            labels=["smoke", "login"],
            description="Tests login flow",
            issue_id="10002",
        )
        assert t.test_type == "Automated"
        assert t.status == "PASS"
        assert t.labels == ["smoke", "login"]
        assert t.description == "Tests login flow"
        assert t.issue_id == "10002"

    def test_repr(self):
        t = Test(key="PROJ-1", summary="My test")
        assert "PROJ-1" in repr(t)
        assert "My test" in repr(t)

    def test_labels_are_independent_per_instance(self):
        t1 = Test(key="PROJ-1", summary="A")
        t2 = Test(key="PROJ-2", summary="B")
        t1.labels.append("smoke")
        assert t2.labels == [], "Labels should be independent between instances"


class TestTestSetEntity:
    def test_creation(self):
        ts = TestSet(key="PROJ-20", summary="My Set")
        assert ts.key == "PROJ-20"
        assert ts.summary == "My Set"
        assert ts.issue_id is None
        assert ts.test_keys == []

    def test_with_test_keys(self):
        ts = TestSet(key="PROJ-20", summary="Set", test_keys=["PROJ-1", "PROJ-2"])
        assert len(ts.test_keys) == 2
        assert "PROJ-1" in ts.test_keys

    def test_repr(self):
        ts = TestSet(key="PROJ-20", summary="My Set")
        assert "PROJ-20" in repr(ts)


class TestTestExecutionEntity:
    def test_creation(self):
        te = TestExecution(key="PROJ-30", summary="Sprint 1")
        assert te.key == "PROJ-30"
        assert te.summary == "Sprint 1"
        assert te.issue_id is None
        assert te.test_set_keys == []
        assert te.test_keys == []

    def test_repr(self):
        te = TestExecution(key="PROJ-30", summary="Sprint 1")
        assert "PROJ-30" in repr(te)


class TestTestPlanEntity:
    def test_creation(self):
        tp = TestPlan(key="PROJ-1", summary="Sprint Plan")
        assert tp.key == "PROJ-1"
        assert tp.summary == "Sprint Plan"
        assert tp.issue_id is None
        assert tp.test_keys == []

    def test_repr(self):
        tp = TestPlan(key="PROJ-1", summary="Sprint Plan")
        assert "PROJ-1" in repr(tp)
