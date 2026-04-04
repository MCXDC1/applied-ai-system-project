# PawPal+ Project Reflection

## 1. System Design

- The system should be able to hold information about the users schedule, the users pet info, and be able to put this information together to create a schedule.

**a. Initial design**

- Briefly describe your initial UML design.
    - There should be a task class (holding task info). The scheduler should be able to add/remove tasks as well as update them. There should be a class holding user info and pet info seperately. This information will have priorites and time constraints attached to them. The schedule pulls from owner to understand tasks and time slots.

- What classes did you include, and what responsibilities did you assign to each?
    - I included four classes, three classes holding info for pets, user, and task. Then a class that acts as a manager. The managing class will be updating, removing, and addings info/tasks.

**b. Design changes**

- Did your design change during implementation?
    - Yes, the amount of classes changed and the methods.
- If yes, describe at least one change and why you made it.
    - I changed the way my classes were set up. I originally did had tasks seperated from a task manager. The AI suggested to connect the pets tasks to the schedule. I accepted this change in order to delegate tasks more efficiently. It also suggested I add in more helper methods to take the complexity out of the scheduler.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
