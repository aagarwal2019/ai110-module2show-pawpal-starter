# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

When I first started thinking about this, I knew I needed something to represent the pet, the owner, and the actual tasks. I ended up with four classes: `Owner`, `Pet`, `Task`, and `Scheduler`. Owner keeps track of when the person is available during the day. Pet is pretty simple — just the animal's name, species, and some preferences. Task holds all the details about a care activity like how long it takes, how urgent it is, and when it should happen. Scheduler is the part that actually figures out what gets done and when.

**b. Design changes**

One thing I didn't plan at first was `ScheduleItem`. I originally thought I'd just return the tasks directly, but then I realized I also wanted to show the actual start/end times and an explanation for each one. So I added `ScheduleItem` to wrap all of that together. It made the Streamlit table way cleaner to build too.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler has to think about a few things at once — when the owner is free, how much total time they have in a day, what priority each task is, whether a task has a preferred time window, and whether it repeats daily or weekly. I put availability first because there's no point sorting tasks if they don't even fit in the day. After that, priority decides the order, and the preferred windows help narrow down exactly when something gets placed.

**b. Tradeoffs**

I went with a greedy approach instead of trying to find the "perfect" schedule. Basically it just goes through tasks in priority order and fits each one in where it can. This means it won't always find the absolute best arrangement, but for daily pet care it's good enough and it's easy to understand what it's doing. The bigger tradeoff I noticed is that it only catches conflicts by looking at exact preferred windows — if two tasks just happen to run back to back and feel tight, it won't flag that. That would need more complex logic I didn't have time to add.

---

## 3. AI Collaboration

**a. How you used AI**

I used Copilot a decent amount throughout this project. Agent Mode was helpful early on when I was setting up the class skeletons — I gave it my UML and it filled in the basic structure pretty fast. Inline Chat was useful when I was working on the sort key logic because I could highlight the code and ask it to walk me through what each part was doing before I committed to it.

For testing I used the Generate Tests feature to get a starting point, then I went in and added my own cases for things like `mark_complete` and filtering since those weren't in the auto-generated version.

One suggestion I didn't use: Copilot wanted conflict detection to raise an exception when it found overlapping tasks. I didn't go with that because it would just crash the app, which isn't helpful for a user. I changed it to return a list of warning strings instead so the UI can show them without breaking.

I also kept separate chat sessions for each phase (design, then coding, then testing) which helped a lot. If you use the same session the whole time, the AI starts mixing up context from earlier conversations.

**b. Judgment and verification**

I ran the code after every major change to make sure things actually worked the way I expected. The sort key was one spot where I had to adjust — the first version Copilot suggested didn't handle the case where a high priority task also had a late preferred window. I tweaked it so priority always wins, and preferred start is just a tiebreaker.

---

## 4. Testing and Verification

**a. What you tested**

I wrote tests for the things I was most worried about breaking:
- that high priority tasks actually show up before lower ones in the schedule
- that tasks don't get scheduled if they run past the owner's end time
- that weekly tasks only appear on the right day of the week
- that the conflict detector catches overbooking
- that `mark_complete()` correctly marks a task as done and returns a new one for recurring tasks
- that filtering by completion status works

**b. Confidence**

I'd say I'm pretty confident in the core stuff — priority ordering, availability, and mark_complete all have direct tests and they pass. I'm less confident about edge cases with overlapping preferred windows across multiple pets. That's an area I'd want to test more before calling it production-ready.

---

## 5. Reflection

**a. What went well**

The thing I'm happiest with is that the same backend logic works in both the CLI demo and the Streamlit UI without any changes. That felt like a sign the design was actually modular the way it was supposed to be.

**b. What you would improve**

If I had more time I'd make the task editor in the UI more flexible — right now you can't set a preferred time window from the browser, only through the code. I'd also want better handling for tasks that are close together but not technically overlapping.

**c. Key takeaway**

The biggest thing I learned is that it's worth spending time on the design before writing any code. Having the UML done first made it much easier to know what I was building and where AI help was actually useful versus where I needed to think it through myself.
