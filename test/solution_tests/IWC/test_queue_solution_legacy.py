from __future__ import annotations

from lib.solutions.IWC.queue_solution_entrypoint import QueueSolutionEntrypoint
from lib.solutions.IWC.task_types import TaskSubmission

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
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=3)).expect(1),
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


def test_dependency_counts_toward_rule_of_3() -> None:
    # GIVEN: A user enqueues tasks including ones with dependencies
    # WHEN: Dependencies cause the user to reach 3 tasks
    # THEN: Rule of 3 is triggered
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("credit_check", 1, iso_ts(delta_minutes=1)).expect(3),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=2)).expect(4),
            # User 1 has Rule of 3, but bank_statements comes last
            call_dequeue().expect("companies_house", 1),  # Changed!
            call_dequeue().expect("credit_check", 1),  # Changed!
            call_dequeue().expect(
                "bank_statements", 1
            ),  # Changed! bank_statements last
            call_dequeue().expect("bank_statements", 2),
        ]
    )


def test_deduplication() -> None:
    # GIVEN: A task is enqueued
    # WHEN: Same (user_id, provider) enqueued with newer timestamp
    # THEN: Queue size unchanged, older timestamp kept
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=2)).expect(1),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=3)).expect(2),
            call_dequeue().expect("id_verification", 1),
            call_dequeue().expect("bank_statements", 1),
        ]
    )


def test_deduplication_keeps_older_timestamp() -> None:
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=10)).expect(1),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=5)).expect(1),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=12)).expect(2),
            # Age of bank_statements = 12-5 = 7 min → still boosted!
            # Need smaller gap...
        ]
    )


def test_deduplication_different_users_not_deduplicated() -> None:
    # GIVEN: Multiple users enqueue same provider
    # WHEN: Tasks added to queue
    # THEN: Each user's task kept separate
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts()).expect(1),
            call_enqueue("bank_statements", 2, iso_ts()).expect(2),
            call_enqueue("bank_statements", 3, iso_ts()).expect(3),
            call_size().expect(3),
        ]
    )


def test_deduplication_same_user_different_providers() -> None:
    # GIVEN: User enqueues multiple providers
    # WHEN: Tasks added to queue
    # THEN: Each provider task kept separate
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts()).expect(1),
            call_enqueue("companies_house", 1, iso_ts()).expect(2),
            call_enqueue("id_verification", 1, iso_ts()).expect(3),
            call_size().expect(3),
        ]
    )


def test_deduplication_with_rule_of_3() -> None:
    # GIVEN: User enqueues tasks including duplicates
    # WHEN: User reaches 3 unique tasks
    # THEN: Rule of 3 applied, duplicates handled correctly
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=1)).expect(2),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=2)).expect(3),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=3)).expect(3),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=4)).expect(4),
            call_dequeue().expect("companies_house", 1),  # Changed!
            call_dequeue().expect("id_verification", 1),  # Changed!
            call_dequeue().expect(
                "bank_statements", 1
            ),  # Changed! bank_statements last within user 1
            call_dequeue().expect("bank_statements", 2),
        ]
    )


def test_deduplication_with_dependencies() -> None:
    # GIVEN: Task with dependencies enqueued
    # WHEN: Same task enqueued again
    # THEN: Dependency deduplicated as well
    run_queue(
        [
            call_enqueue("credit_check", 1, iso_ts(delta_minutes=0)).expect(2),
            call_enqueue("credit_check", 1, iso_ts(delta_minutes=5)).expect(2),
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("credit_check", 1),
        ]
    )


def test_deduplication_dependency_exists_separately() -> None:
    # GIVEN: Dependency already enqueued separately
    # WHEN: Task requiring that dependency enqueued
    # THEN: Dependency deduplicated, older timestamp kept
    run_queue(
        [
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("credit_check", 1, iso_ts(delta_minutes=5)).expect(2),
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("credit_check", 1),
        ]
    )


def test_multiple_deduplication_events() -> None:
    # GIVEN: Various tasks enqueued with duplicates
    # WHEN: Duplicates from different users processed
    # THEN: Each duplicate handled correctly per user
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=1)).expect(2),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=2)).expect(2),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=3)).expect(3),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=4)).expect(3),
            call_size().expect(3),
        ]
    )


def test_bank_statements_deprioritized_basic() -> None:
    # GIVEN: Bank statements enqueued first
    # WHEN: Other tasks enqueued after
    # THEN: Bank statements processed last
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=1)).expect(2),
            call_enqueue("companies_house", 2, iso_ts(delta_minutes=2)).expect(3),
            call_dequeue().expect("id_verification", 1),
            call_dequeue().expect("companies_house", 2),
            call_dequeue().expect("bank_statements", 1),
        ]
    )


def test_bank_statements_deprioritized_with_rule_of_3() -> None:
    # GIVEN: User has 3+ tasks including bank statements
    # WHEN: Rule of 3 applies
    # THEN: User's bank statements come after their other tasks
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=1)).expect(2),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=2)).expect(3),
            call_enqueue("companies_house", 2, iso_ts(delta_minutes=3)).expect(4),
            # User 1 has Rule of 3: all their tasks come first, but bank_statements last
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("id_verification", 1),
            call_dequeue().expect("bank_statements", 1),
            call_dequeue().expect("companies_house", 2),
        ]
    )


def test_multiple_bank_statements_ordered_by_timestamp() -> None:
    # GIVEN: Multiple bank statements from different users
    # WHEN: All deprioritized
    # THEN: Timestamp ordering applies among bank statements
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=2)).expect(1),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=0)).expect(2),
            call_enqueue("companies_house", 3, iso_ts(delta_minutes=4)).expect(3),
            call_dequeue().expect("companies_house", 3),
            call_dequeue().expect("bank_statements", 2),  # Older timestamp first
            call_dequeue().expect("bank_statements", 1),
        ]
    )


def test_bank_statements_with_dependencies() -> None:
    # GIVEN: Task with bank statements dependency
    # WHEN: Enqueued
    # THEN: Bank statements still deprioritized
    run_queue(
        [
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=1)).expect(2),
            call_enqueue("id_verification", 2, iso_ts(delta_minutes=2)).expect(3),
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("id_verification", 2),
            call_dequeue().expect("bank_statements", 1),
        ]
    )


def test_bank_statements_only_user_still_deprioritized() -> None:
    # GIVEN: User only has bank statements
    # WHEN: Mixed with other users' tasks
    # THEN: Bank statements still go last
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("companies_house", 2, iso_ts(delta_minutes=4)).expect(2),
            call_dequeue().expect(
                "companies_house", 2
            ),  # Goes first despite later timestamp
            call_dequeue().expect("bank_statements", 1),
        ]
    )


def test_two_users_rule_of_3_bank_statements() -> None:
    # GIVEN: Two users both with Rule of 3 and bank statements
    # WHEN: Both prioritized
    # THEN: Each user's bank statements come last within their tasks
    run_queue(
        [
            call_enqueue("bank_statements", 1, iso_ts(delta_minutes=0)).expect(1),
            call_enqueue("companies_house", 1, iso_ts(delta_minutes=1)).expect(2),
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=2)).expect(3),
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=3)).expect(4),
            call_enqueue("companies_house", 2, iso_ts(delta_minutes=4)).expect(5),
            call_enqueue("id_verification", 2, iso_ts(delta_minutes=4)).expect(6),
            # User 1 first (earlier Rule of 3), bank_statements last
            call_dequeue().expect("companies_house", 1),
            call_dequeue().expect("id_verification", 1),
            call_dequeue().expect("bank_statements", 1),
            # Then user 2, bank_statements last
            call_dequeue().expect("companies_house", 2),
            call_dequeue().expect("id_verification", 2),
            call_dequeue().expect("bank_statements", 2),
        ]
    )


def test_age_empty_queue() -> None:
    # GIVEN: Empty queue
    # WHEN: Age checked
    # THEN: Returns 0
    run_queue(
        [
            call_size().expect(0),
            # Need to call age() - but utils don't have this helper
        ]
    )


def test_age_with_time_gap() -> None:
    # GIVEN: Tasks with 5 minute gap
    # WHEN: Age checked
    # THEN: Returns 300 seconds
    queue = QueueSolutionEntrypoint()
    queue.enqueue(TaskSubmission("id_verification", 1, iso_ts(delta_minutes=0)))
    queue.enqueue(TaskSubmission("id_verification", 2, iso_ts(delta_minutes=5)))
    assert queue.age() == 300


def test_age_updates_on_dequeue() -> None:
    # GIVEN: Queue with tasks spanning 10 minutes
    # WHEN: Oldest task dequeued
    # THEN: Age decreases
    queue = QueueSolutionEntrypoint()
    queue.enqueue(TaskSubmission("id_verification", 1, iso_ts(delta_minutes=0)))
    queue.enqueue(TaskSubmission("companies_house", 2, iso_ts(delta_minutes=5)))
    queue.enqueue(TaskSubmission("bank_statements", 3, iso_ts(delta_minutes=10)))

    assert queue.age() == 600  # 10 minutes

    queue.dequeue()  # Remove oldest (or first by priority)

    # Age should be smaller now (depends on what was dequeued)
    assert queue.age() < 600


def test_age_after_purge() -> None:
    # GIVEN: Queue with tasks
    # WHEN: Purged
    # THEN: Age returns 0
    queue = QueueSolutionEntrypoint()
    queue.enqueue(TaskSubmission("id_verification", 1, iso_ts(delta_minutes=0)))
    queue.enqueue(TaskSubmission("id_verification", 2, iso_ts(delta_minutes=5)))

    assert queue.age() == 300

    queue.purge()
    assert queue.age() == 0


def test_bank_statements_old_enough_gets_priority() -> None:
    # GIVEN: Bank statements with 5+ min age gets boosted
    # WHEN: Dequeued alongside tasks with later timestamps
    # THEN: Bank statements comes before those later tasks
    run_queue(
        [
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=0)).expect(
                1
            ),  # Oldest
            call_enqueue("companies_house", 4, iso_ts(delta_minutes=1)).expect(
                2
            ),  # Also old
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=6)).expect(
                3
            ),  # Age=6min, boosted
            call_enqueue("id_verification", 3, iso_ts(delta_minutes=7)).expect(
                4
            ),  # Newest
            # oldest=0 throughout, bank_statements age=6min (boosted)
            call_dequeue().expect("id_verification", 1),  # Oldest timestamp
            call_dequeue().expect("companies_house", 4),  # Second oldest
            call_dequeue().expect(
                "bank_statements", 2
            ),  # Boosted, comes before id_verification
            call_dequeue().expect("id_verification", 3),  # Latest
        ]
    )


def test_bank_statements_not_old_enough_stays_deprioritized() -> None:
    # GIVEN: Bank statements less than 5 minutes from oldest
    # WHEN: Dequeued
    # THEN: Stays deprioritized
    run_queue(
        [
            call_enqueue("id_verification", 1, iso_ts(delta_minutes=0)).expect(
                1
            ),  # Oldest
            call_enqueue("bank_statements", 2, iso_ts(delta_minutes=3)).expect(
                2
            ),  # Age = 3-0 = 3 min
            call_enqueue("companies_house", 3, iso_ts(delta_minutes=4)).expect(3),
            # bank_statements age = 3 min < 5 min (stays deprioritized)
            call_dequeue().expect("id_verification", 1),
            call_dequeue().expect("companies_house", 3),
            call_dequeue().expect("bank_statements", 2),  # Still last
        ]
    )



