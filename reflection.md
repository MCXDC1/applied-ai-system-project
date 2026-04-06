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
    - I changed the way my classes were set up. I originally had tasks seperated from a task manager. This was how the AI originally structured it. The AI suggested to connect the pets tasks to the schedule based on this task manager. I then went back through what I wanted from the app and changed this to just four classes. I did this change in order to delegate tasks more efficiently. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    - It considers priority, frequency, duration.
- How did you decide which constraints mattered most?
    - Priority is what matters the most as I believe the app should follow what the user is telling it. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    - The scheduler will autofill tasks to wake time that are not specified.
- Why is that tradeoff reasonable for this scenario?
    - In this scenario, to create a schedule it is basing it off of information that is being given. This means that it will set to wake time at the moment to place it into the schedule. From there I will be able to fix to randomize the timing.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    - I used it for testing and the structure of the classes. It also aided in helping with streamlit as I am not as familiar with it.
- What kinds of prompts or questions were most helpful?
    - I found it most helpful to ask it to give me multiple suggestions for how I should fix a problem and often would combine solutions.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    - The AI wanted me to use a task manager to manage tasks which I found to not completely align with what was expected of the app.
- How did you evaluate or verify what the AI suggested?
    - I asked it to compare using just the scheduler instead of having a seperate manager, and then asked how to combine that with the task and pet class.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - I tested the tasks and how they were acting. Things like conflicts, overriding, and adding/deleting tasks.
- Why were these tests important?
    - I believed this to be the center of the schedule app and wanted to make sure it was functioning as expected when being used in combination with the pets.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    - I am 90% confident. I believe there are still things that would make the user experience smoother.
- What edge cases would you test next if you had more time?
    - I would most likely try more combinations of tasks of dates and animals and owners. I did my own testing within the app of different pets and task combinations but would love to go further and build a much larger schedule.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    - I am most satisfied with the task creation and the schedule.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    - I would improve the priority system and the timing of the schedule.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    - I had to do outside research to understand a lot of what the AI thought would be more efficient. It taught me how AI can soemtimes be a driving force to learn more information.
