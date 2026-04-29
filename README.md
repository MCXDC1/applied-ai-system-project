
Explicitly name your original project (from Modules 1-3) and provide a 2-3 sentence summary of its original goals and capabilities.
    - My original project was the PAWPAL project. Originally the system was able to place tasks into a calendar based on user input. It would time block these out based on priority.
Title and Summary: What your project does and why it matters.
    - The PetPal Hotel: My project is an updated version of this schedule that is used in pet hotels by employees. The system will take in information about pets from the owner and store this information. Then, it will create an AI daily schedule based on the animals and information that it has.
Architecture Overview: A short explanation of your system diagram.
    - The hotel system is in charge of guest check in and stores the information on the pets.
    - The RAG engine is used for the calendar. It is scanned based on the 8 pet care guidelines it has information on. This is all standard information gathered from online on basic pet care needs.
    - There are guardrails in place to make sure that before outputting a schedule the requests are being scanned for dangerous information.
    - The agent combines the pet information and the knowledge it scanned. It calls the Groq API in order to create the schedule.
Setup Instructions: Step-by-step directions to run your code.
    - Prerequisites — Python 3.10 or higher is required. 

    - Clone the repository

        git clone <your-repo-url>
        cd applied-ai-system-project

    - Install dependencies
        pip install -r requirements.txt

    - Set up your API key

        Create a free Groq API key at https://console.groq.com (sign up → API Keys)

    - Copy the example env file and add your key:

        cp .env.example .env
        Open .env and replace your_key_here with your actual Groq API key

    - Run the app:

        streamlit run app.py

Sample Interactions: Include at least 2-3 examples of inputs and the resulting AI outputs to demonstrate the system is functional.
    - (Included as pictures in folder labeled /assets/PHOTOS)
    - I will input two animals, the dog is allergic to chicken and the cat is scared of dogs. The system will take note of this and add a note/warning for the days these pets are in the hotel. The dog will have a medication that needs to be administered. The system will take note of this and fit the medicine into the schedule.
Design Decisions: Why you built it this way, and what trade-offs you made.
    - I used Groq as it is no cost but is capable of projects such as this one. I wanted to use RAG as I wanted a relevant source of baisc information for the pet care. I wanted to make sure that the system could not get misinformation into the schedule so I needed to instill a variety of guardrails. The testing happens multiple times in order to make sure that dangerous instructions are caught.
Testing Summary: What worked, what didn't, and what you learned.
    - I found that I had to test it myself instead of relying heavier on the tests. Testing the schedule itself instead of within the tests was more important. I learned a lot about how systems use AI with RAG.
Reflection: What this project taught you about AI and problem-solving.
    - It taught me a lot about guardrails and how much AI will ignore problems until you specifically ask for them. I tested a lot of differnet inputs that I believed to be ouright problematic but the AI would not catch it. For systems like these it is important to have a heavier hand in testing in order to make sure the information is being passed along safely.

LOOM LINK:
    - https://www.loom.com/share/fbcd5cd6819b4c23b92f4a97845709a8
