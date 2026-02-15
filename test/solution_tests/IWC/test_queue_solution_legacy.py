from __future__ import annotations

from .utils import call_dequeue, call_enqueue, iso_ts, run_queue


def test_rule_of_3() -> None:
    # GIVEN: Multiple users enqueue tasks
    # WHEN: User 1 reaches 3 tasks in the queue
    # THEN: All of user 1's tasks are moved to the front
    run_queue(
        [
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=0)).expect(2),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=0)).expect(3),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(4),
            # All user 1 tasks should be dequeued first
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("id_verification", 1),
            call_dequeue().expect("bank_statements", 1),
            call_dequeue().expect("bank_statements", 2),
        ]
    )


def test_timestamp_ordering() -> None:
    # GIVEN: Two tasks with different timestamps are enqueued
    # WHEN: Tasks are dequeued
    # THEN: The task with the older timestamp is processed first
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=5)).expect(1),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=0)).expect(2),
            # Older timestamp (delta=0) should be dequeued first
            call_dequeue().expect("bank_statements", 2),
            call_dequeue().expect("bank_statements", 1),
        ]
    )

def test_dependency_resolution() -> None:
    # GIVEN: A task with dependencies is enqueued
    # WHEN: credit_check task is enqueued
    # THEN: Both the dependency (companies_house) and the task are added, dependency first
    run_queue(
        [
            # Enqueuing credit_check should add 2 tasks (dependency + task)
            call_enqueue("credit_check", 1, iso_ts(delta_minutes=0)).expect(2),
            # Dependency should be dequeued first
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("credit_check", 1),
        ]
    )
