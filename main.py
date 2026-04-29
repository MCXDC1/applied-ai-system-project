from pawpal_system import Pet, Owner, Task

Pet1 = Pet("Max", "Dog", 11, "Golden")
Pet2 = Pet("Mumu", "Cat", 8, "Mix")
Pets = [Pet1, Pet2]
Owner1 = Owner("Mia", "07:00", "21:00", Pets)

task1 = Task("Walk dog", "daily", "01:00", 3, "08:00")
task2 = Task("Scoop Litter", "daily", "00:10", 3, "19:00")
task3 = Task("Give treat", "daily", "00:10", 1, "17:00")
task4 = Task("Bathe pet", "monthly", "01:00", 3, "05:00")
task5 = Task("Give food", "daily", "00:10", 1, "17:00")

Pet1.add_task(task1)
Pet1.add_task(task4)
Pet2.add_task(task2)
Pet2.add_task(task3)
Pet2.add_task(task5)

print(f"Owner: {Owner1.name}")
for pet in Owner1.pets:
    print(f"  {pet.name} ({pet.species}) — {len(pet.tasks)} task(s)")
    for t in pet.tasks:
        print(f"    • {t.description} [{t.frequency}]")
