from __future__ import annotations

from .utils import call_dequeue, call_enqueue, call_size, iso_ts, run_queue


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


def test_size_method() -> None:
    # GIVEN: An empty queue
    # WHEN: Tasks are enqueued and dequeued
    # THEN: size() accurately reflects the current number of pending tasks
    run_queue(
        [
            call_size().expect(0),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_size().expect(1),
            call_dequeue().expect("bank_statements", 1),
            call_size().expect(0),
        ]
    )


def test_rule_of_3_overrides_timestamp() -> None:
    # GIVEN: User 2 enqueues first with an early timestamp
    # WHEN: User 1 enqueues 3 tasks with later timestamps
    # THEN: User 1's tasks are processed before user 2's despite older timestamps
    run_queue(
        [
            # User 2 has earliest timestamp
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=0)).expect(1),
            # User 1 enqueues 3 tasks with later timestamps
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=10)).expect(2),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=20)).expect(3),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=30)).expect(4),
            # User 1's tasks should come first despite later timestamps
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("id_verification", 1),
            call_dequeue().expect("bank_statements", 1),
            # User 2's task comes last despite earliest timestamp
            call_dequeue().expect("bank_statements", 2),
        ]
    )


def test_multiple_users_with_rule_of_3() -> None:
    # GIVEN: Multiple users are enqueuing tasks
    # WHEN: Two different users both reach 3 tasks
    # THEN: Both users' tasks should be prioritized by timestamp of when they hit 3
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=1)).expect(2),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=2)).expect(3),
            # User 1 now has Rule of 3 active
            call_enqueue("companies_house", 2, iso_ts(delta_minutes=3)).expect(4),
            call_enqueue("id_verification", 2, iso_ts(delta_minutes=4)).expect(5),
            call_enqueue("credit_check", 2, iso_ts(delta_minutes=5)).expect(
                7
            ),  # +dependency
            # User 1's tasks come first (hit Rule of 3 first)
            call_dequeue().expect("bank_statements", 1),
            call_dequeue().expect("bank_statements", 1),
            call_dequeue().expect("bank_statements", 1),
            # Then user 2's tasks
            call_dequeue().expect("companies_house", 2),
            call_dequeue().expect("id_verification", 2),
            call_dequeue().expect("companies_house", 2),  # dependency
            call_dequeue().expect("credit_check", 2),
        ]
    )


def test_dependency_counts_toward_rule_of_3() -> None:
    # GIVEN: A user enqueues tasks including ones with dependencies
    # WHEN: Dependencies cause the user to reach 3 tasks
    # THEN: Rule of 3 is triggered
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            # This adds 2 tasks (dependency + task), triggering Rule of 3
            call_enqueue("credit_check", 1, iso_ts(delta_minutes=1)).expect(3),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=2)).expect(4),
            # User 1's tasks should come first due to Rule of 3
            call_dequeue().expect("bank_statements", 1),
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("credit_check", 1),
            call_dequeue().expect("bank_statements", 2),
        ]
    )


def test_deduplication() -> None:
    # GIVEN: A task is enqueued with a specific timestamp
    # WHEN: The same (user_id, provider) pair is enqueued again with a newer timestamp
    # THEN: Queue size remains the same, and the older timestamp is kept
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=5)).expect(1),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=5)).expect(2),
            call_dequeue().expect("bank_statements", 1),
            call_dequeue().expect("id_verification", 1),
        ]
    )


def test_deduplication_keeps_older_timestamp() -> None:
    # GIVEN: A task is enqueued with a newer timestamp first
    # WHEN: The same task is enqueued with an older timestamp
    # THEN: The older timestamp replaces the newer one
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=10)).expect(1),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=5)).expect(1),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=15)).expect(2),
            # bank_statements should be processed first (delta=5)
            call_dequeue().expect("bank_statements", 1),
            call_dequeue().expect("id_verification", 1),
        ]
    )

def test_deduplication_different_users_not_deduplicated() -> None:
    """Different users with same provider are not deduplicated"""
    # GIVEN: Multiple users enqueue the same provider
    # WHEN: Tasks are added to the queue
    # THEN: Each user's task is kept separate
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=0)).expect(2),
            call_enqueue("bank_statements", 3, iso_ts(delta_minutes=0)).expect(3),
            call_size().expect(3),
        ]
    )


def test_deduplication_same_user_different_providers_not_deduplicated() -> None:
    """Same user with different providers are not deduplicated"""
    # GIVEN: A user enqueues multiple different providers
    # WHEN: Tasks are added to the queue
    # THEN: Each provider task is kept separate
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=0)).expect(2),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=0)).expect(3),
            call_size().expect(3),
        ]
    )


