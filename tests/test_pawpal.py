from datetime import date, time

from pawpal import Owner, Pet, Priority, Scheduler, Task


def test_build_daily_schedule_orders_by_priority() -> None:
    owner = Owner(name="Jordan", available_start=time(hour=8), available_end=time(hour=12))
    pet = Pet(name="Mochi", species="dog")
    tasks = [
        Task(title="Low priority task", duration_minutes=30, priority="low"),
        Task(title="High priority task", duration_minutes=30, priority="high"),
        Task(title="Medium priority task", duration_minutes=30, priority="medium"),
    ]
    schedule, _ = Scheduler().build_daily_schedule(owner=owner, pet=pet, tasks=tasks, schedule_date=date(2026, 1, 1))

    assert schedule[0].task.priority == Priority.HIGH
    assert schedule[1].task.priority == Priority.MEDIUM
    assert schedule[2].task.priority == Priority.LOW


def test_schedule_respects_owner_availability() -> None:
    owner = Owner(name="Alex", available_start=time(hour=9), available_end=time(hour=10))
    pet = Pet(name="Buddy", species="cat")
    tasks = [
        Task(title="Long task", duration_minutes=90, priority="high"),
        Task(title="Short task", duration_minutes=30, priority="medium"),
    ]
    schedule, notes = Scheduler().build_daily_schedule(owner=owner, pet=pet, tasks=tasks, schedule_date=date(2026, 1, 2))

    assert len(schedule) == 1
    assert schedule[0].task.title == "Short task"
    assert any("daily plan is fully booked" in note.lower() or "would end after owner's available time" in note.lower() for note in notes)


def test_recurring_task_only_scheduled_on_matching_weekday() -> None:
    task = Task(
        title="Weekly medication",
        duration_minutes=10,
        priority="high",
        recurring="weekly",
        day_of_week=3,
    )
    assert not task.is_scheduled_on(date(2026, 1, 2))
    assert task.is_scheduled_on(date(2026, 1, 8))


def test_detect_conflicts_reports_overbooked_day() -> None:
    owner = Owner(name="Dana", available_start=time(hour=8), available_end=time(hour=10))
    tasks = [
        Task(title="Task A", duration_minutes=90, priority="high"),
        Task(title="Task B", duration_minutes=90, priority="low"),
    ]
    conflicts = Scheduler().detect_conflicts(owner=owner, tasks=tasks, schedule_date=date(2026, 1, 3))

    assert any("exceeds available time" in message.lower() for message in conflicts)


def test_mark_complete_sets_completed_flag() -> None:
    task = Task(title="Feed breakfast", duration_minutes=15, priority="high")
    assert not task.completed
    task.mark_complete()
    assert task.completed


def test_mark_complete_daily_returns_new_task() -> None:
    task = Task(title="Morning walk", duration_minutes=30, priority="high", recurring="daily")
    next_task = task.mark_complete()
    assert task.completed
    assert next_task is not None
    assert next_task.title == "Morning walk"
    assert not next_task.completed


def test_mark_complete_one_time_returns_none() -> None:
    task = Task(title="Vet visit", duration_minutes=60, priority="medium", recurring="none")
    next_task = task.mark_complete()
    assert task.completed
    assert next_task is None


def test_filter_tasks_by_completion_status() -> None:
    tasks = [
        Task(title="Done task", duration_minutes=10, priority="low"),
        Task(title="Pending task", duration_minutes=10, priority="high"),
    ]
    tasks[0].mark_complete()
    scheduler = Scheduler()
    incomplete = scheduler.filter_tasks(tasks, completed=False)
    complete = scheduler.filter_tasks(tasks, completed=True)
    assert len(incomplete) == 1
    assert incomplete[0].title == "Pending task"
    assert len(complete) == 1
    assert complete[0].title == "Done task"
