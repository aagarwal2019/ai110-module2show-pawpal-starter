from datetime import date, time

from pawpal import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_start=time(hour=7), available_end=time(hour=18), max_daily_minutes=180)
    pet = Pet(name="Mochi", species="dog", preferences={"likes_walks": True})

    tasks = [
        Task(
            title="Morning walk",
            duration_minutes=30,
            priority="high",
            preferred_start=time(hour=7, minute=30),
            preferred_end=time(hour=9, minute=0),
            recurring="daily",
        ),
        Task(
            title="Feed breakfast",
            duration_minutes=15,
            priority="high",
            preferred_start=time(hour=8, minute=0),
            preferred_end=time(hour=9, minute=0),
            recurring="daily",
        ),
        Task(
            title="Administer medication",
            duration_minutes=10,
            priority="medium",
            preferred_start=time(hour=9, minute=0),
            preferred_end=time(hour=10, minute=0),
            recurring="weekly",
            day_of_week=date.today().weekday(),
        ),
        Task(
            title="Play enrichment",
            duration_minutes=25,
            priority="medium",
            recurring="none",
        ),
        Task(
            title="Brush fur",
            duration_minutes=20,
            priority="low",
            preferred_start=time(hour=17),
            preferred_end=time(hour=18),
            recurring="daily",
        ),
    ]

    scheduler = Scheduler()
    schedule, notes = scheduler.build_daily_schedule(owner=owner, pet=pet, tasks=tasks, schedule_date=date.today())

    print("PawPal+ Daily Plan")
    print("Owner:", owner.name)
    print("Pet:", pet.name, f"({pet.species})")
    print("Date:", date.today().isoformat())
    print()

    if schedule:
        for item in schedule:
            print(f"- {item.task.title}: {item.start_time.strftime('%H:%M')} to {item.end_time.strftime('%H:%M')} ({item.task.priority.label()})")
    else:
        print("No tasks were scheduled.")

    if notes:
        print("\nNotes:")
        for note in notes:
            print(f"- {note}")


if __name__ == "__main__":
    main()
