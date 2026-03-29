from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Literal, Optional, Sequence, Tuple

RecurringFrequency = Literal["none", "daily", "weekly"]
PriorityValue = Literal["low", "medium", "high"]


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def from_value(cls, value: PriorityValue | str) -> "Priority":
        """Convert a string like 'high' or 'low' to a Priority enum member."""
        normalized = str(value).strip().lower()
        if normalized == "high":
            return cls.HIGH
        if normalized == "low":
            return cls.LOW
        return cls.MEDIUM

    def label(self) -> str:
        """Return the lowercase string name of this priority level."""
        return self.name.lower()


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_start: Optional[time] = None
    preferred_end: Optional[time] = None
    recurring: RecurringFrequency = "none"
    day_of_week: Optional[int] = None
    notes: Optional[str] = None
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate and normalize task fields after dataclass initialization."""
        self.priority = Priority.from_value(self.priority)
        if self.duration_minutes < 0:
            raise ValueError("Task duration must be zero or positive")
        if self.preferred_start and self.preferred_end:
            if self.preferred_start >= self.preferred_end:
                raise ValueError("preferred_start must be before preferred_end")
        if self.recurring not in {"none", "daily", "weekly"}:
            raise ValueError("recurring must be 'none', 'daily', or 'weekly'")
        if self.recurring == "weekly" and self.day_of_week is None:
            self.day_of_week = 0

    @classmethod
    def from_dict(cls, raw: Dict) -> "Task":
        """Construct a Task from a plain dictionary, applying safe defaults."""
        return cls(
            title=raw.get("title", "Untitled task"),
            duration_minutes=int(raw.get("duration_minutes", 0)),
            priority=raw.get("priority", "medium"),
            preferred_start=raw.get("preferred_start"),
            preferred_end=raw.get("preferred_end"),
            recurring=raw.get("recurring", "none"),
            day_of_week=raw.get("day_of_week"),
            notes=raw.get("notes"),
        )

    def is_scheduled_on(self, target_date: date) -> bool:
        """Return True if this task should run on the given date based on its recurrence rule."""
        if self.recurring == "daily":
            return True
        if self.recurring == "weekly":
            return self.day_of_week == target_date.weekday()
        return True

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return a new Task for the next occurrence if recurring."""
        self.completed = True
        if self.recurring == "daily":
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                preferred_start=self.preferred_start,
                preferred_end=self.preferred_end,
                recurring=self.recurring,
                day_of_week=self.day_of_week,
                notes=self.notes,
            )
        if self.recurring == "weekly":
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                preferred_start=self.preferred_start,
                preferred_end=self.preferred_end,
                recurring=self.recurring,
                day_of_week=self.day_of_week,
                notes=self.notes,
            )
        return None

    def window_start(self, target_date: date, fallback: time) -> datetime:
        """Return the task's preferred start as a datetime, falling back to the provided time."""
        return datetime.combine(target_date, self.preferred_start or fallback)

    def window_end(self, target_date: date, fallback: time) -> datetime:
        """Return the task's preferred end as a datetime, falling back to the provided time."""
        return datetime.combine(target_date, self.preferred_end or fallback)


@dataclass
class Pet:
    name: str
    species: str = "other"
    age_months: Optional[int] = None
    preferences: Dict[str, bool] = field(default_factory=dict)


@dataclass
class Owner:
    name: str
    available_start: time = time(hour=8, minute=0)
    available_end: time = time(hour=20, minute=0)
    max_daily_minutes: Optional[int] = None

    def daily_window_minutes(self) -> int:
        """Return the total number of minutes between available_start and available_end."""
        window = datetime.combine(date.today(), self.available_end) - datetime.combine(date.today(), self.available_start)
        return int(window.total_seconds() // 60)

    def effective_daily_limit(self) -> int:
        """Return the usable daily minutes, capped by max_daily_minutes if set."""
        if self.max_daily_minutes is None or self.max_daily_minutes <= 0:
            return self.daily_window_minutes()
        return min(self.max_daily_minutes, self.daily_window_minutes())


@dataclass
class ScheduleItem:
    task: Task
    start_time: datetime
    end_time: datetime
    explanation: str

    def to_row(self) -> Dict[str, str]:
        """Serialize this schedule item to a flat dict suitable for st.table."""
        return {
            "Task": self.task.title,
            "Priority": self.task.priority.label(),
            "Start": self.start_time.strftime("%H:%M"),
            "End": self.end_time.strftime("%H:%M"),
            "Duration": f"{self.task.duration_minutes} min",
            "Notes": self.explanation,
        }


class Scheduler:
    def build_daily_schedule(
        self,
        owner: Owner,
        pet: Pet,
        tasks: Sequence[Task],
        schedule_date: Optional[date] = None,
    ) -> Tuple[List[ScheduleItem], List[str]]:
        """Build a greedy daily schedule respecting priority, availability, and preferred windows."""
        schedule_date = schedule_date or date.today()
        available_start = datetime.combine(schedule_date, owner.available_start)
        available_end = datetime.combine(schedule_date, owner.available_end)
        daily_limit = owner.effective_daily_limit()

        active_tasks = [task for task in tasks if task.is_scheduled_on(schedule_date) and task.duration_minutes > 0]
        active_tasks = sorted(active_tasks, key=self._preferred_sort_key)

        schedule: List[ScheduleItem] = []
        explanations: List[str] = []
        current_start = available_start
        minutes_used = 0

        for task in active_tasks:
            if minutes_used + task.duration_minutes > daily_limit:
                explanations.append(
                    f"Skipped '{task.title}' because the daily plan is fully booked and lower-priority tasks came first."
                )
                continue

            start_candidate = self._find_start_for_task(task, current_start, available_start, available_end)
            if start_candidate is None:
                explanations.append(
                    f"Could not place '{task.title}' because its preferred window does not fit after earlier tasks."
                )
                continue

            end_candidate = start_candidate + timedelta(minutes=task.duration_minutes)
            if end_candidate > available_end:
                explanations.append(
                    f"Skipped '{task.title}' because it would end after owner's available time."
                )
                continue

            schedule.append(
                ScheduleItem(
                    task=task,
                    start_time=start_candidate,
                    end_time=end_candidate,
                    explanation=self._build_explanation(task, start_candidate),
                )
            )
            minutes_used += task.duration_minutes
            current_start = end_candidate

        if not schedule and active_tasks:
            explanations.append("No task could be scheduled with the current availability and preferences.")
        if not active_tasks:
            explanations.append("No valid tasks were available for scheduling today.")

        return schedule, explanations

    def _preferred_sort_key(self, task: Task) -> Tuple[int, int, int]:
        """Return a sort tuple: high priority first, then earliest preferred start, then shortest duration."""
        priority_value = -task.priority.value
        if task.preferred_start:
            preferred_start_value = task.preferred_start.hour * 60 + task.preferred_start.minute
        else:
            preferred_start_value = 24 * 60
        return (priority_value, preferred_start_value, task.duration_minutes)

    def _find_start_for_task(
        self,
        task: Task,
        current_start: datetime,
        available_start: datetime,
        available_end: datetime,
    ) -> Optional[datetime]:
        """Return the earliest valid start time for a task, or None if it cannot be placed."""
        if task.preferred_start or task.preferred_end:
            window_start = task.window_start(current_start.date(), available_start.time())
            window_end = task.window_end(current_start.date(), available_end.time())
            candidate = max(current_start, window_start)
            if candidate + timedelta(minutes=task.duration_minutes) <= min(window_end, available_end):
                return candidate
            return None
        if current_start + timedelta(minutes=task.duration_minutes) <= available_end:
            return current_start
        return None

    def filter_tasks(
        self,
        tasks: Sequence[Task],
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
        pet_task_map: Optional[Dict[str, Sequence[Task]]] = None,
    ) -> List[Task]:
        """Return tasks matching the given completion status and/or pet name."""
        result = list(tasks)
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_name is not None and pet_task_map is not None:
            pet_tasks = set(id(t) for t in pet_task_map.get(pet_name, []))
            result = [t for t in result if id(t) in pet_tasks]
        return result

    def detect_conflicts(
        self,
        owner: Owner,
        tasks: Sequence[Task],
        schedule_date: Optional[date] = None,
    ) -> List[str]:
        """Return warning messages for overbooked days or overlapping preferred windows."""
        schedule_date = schedule_date or date.today()
        warnings: List[str] = []
        day_tasks = [task for task in tasks if task.is_scheduled_on(schedule_date) and task.duration_minutes > 0]
        total_minutes = sum(task.duration_minutes for task in day_tasks)
        if total_minutes > owner.effective_daily_limit():
            warnings.append(
                f"Total task duration ({total_minutes} min) exceeds available time ({owner.effective_daily_limit()} min)."
            )
        for first in range(len(day_tasks)):
            for second in range(first + 1, len(day_tasks)):
                a = day_tasks[first]
                b = day_tasks[second]
                if a.preferred_start and a.preferred_end and b.preferred_start and b.preferred_end:
                    if self._windows_overlap(a, b):
                        warnings.append(
                            f"'{a.title}' and '{b.title}' have overlapping preferred windows."
                        )
        return warnings

    @staticmethod
    def _windows_overlap(first: Task, second: Task) -> bool:
        """Return True if two tasks have overlapping preferred time windows."""
        if not first.preferred_start or not first.preferred_end or not second.preferred_start or not second.preferred_end:
            return False
        latest_start = max(first.preferred_start, second.preferred_start)
        earliest_end = min(first.preferred_end, second.preferred_end)
        return latest_start < earliest_end

    @staticmethod
    def _build_explanation(task: Task, start: datetime) -> str:
        """Generate a human-readable explanation for why and when a task was scheduled."""
        time_range = f"{start.strftime('%H:%M')}–{(start + timedelta(minutes=task.duration_minutes)).strftime('%H:%M')}"
        reason = "based on priority" if task.priority == Priority.HIGH else "to keep a balanced day"
        return f"Scheduled {time_range} {reason}."
