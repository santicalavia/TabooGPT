# TabooGPT
TabooGPT is a Taboo command-line game built with AutoGen using OpenAI LLM agents.

The goal of the game is to guess the target word based on hints provided by your partner. When giving hints, you must avoid using words from the forbidden words list (including the target word itself, of course!), as well as words that are contained within the forbidden words or are too similar.

In this version of the game, you'll team up with an LLM partner to compete against a rival team of LLMs.

The game features three types of turns:

**Player guesses:** You must guess the word based on the hints provided by your LLM partner.

**Player gives hints:** You provide hints, and your LLM partner must guess the word. Be careful not to use any forbidden words!

**CPU turn:** A rival team of LLMs will take their turn.
You'll score more points if your team guesses the word with fewer hints.

Each of the described turns works thanks to a series of agents, each fulfilling a specific function:

**HintGenerator:**
This agent generates hints for the game using an LLM, avoiding forbidden words or their derivatives. It ensures that previously given hints are not repeated and generates concise clues.

**HintEvaluator:**
This agent evaluates the given hint to determine if any forbidden words are used. It uses the evaluate_hint function to validate the hint. This functions is implemented using Spacy to filter main words, combined with Levehnstein distance to evaluate similarity of words, and also checks if a word is contained in the hint.

**GuessGenerator:**
This agent listens to the hints provided by another player and generates a guess for the target word using an LLM. It ensures that no previous guesses are repeated and that the response is a single word.

**GuessEvaluator:**
This agent checks whether a guess is correct. The guess must exactly match or mean the same as the target word. It can only respond with "ACIERTO" (correct) or "NOK" (incorrect).

**Player:**
This agent represents the human player in the game. It acts as an intermediary between the user and the system, allowing the player to interact with the AI agents.





## Installation

This project was tested using Python 3.10. Create an environment with this Python version and install requirements.txt

```bash
  pip install -r requirements.txt
```

Then, download Spanish language model for Spacy:

```bash
  python -m spacy download es_core_news_sm 
```

Finally, create a .env file with your OpenAI API key : 

```bash
  'OPENAI_API_KEY' = 'your-api-key'
  'AUTOGEN_USE_DOCKER' = "False"
```

## Usage
To play the game, execute main.py from in your new python environment:
```bash
python main.py
```
You can use the following arguments to customize the configuration. However, the default settings are sufficient for a standard game.
```bash
  -h, --help            show this help message and exit
  -p CARDS_PATH, --cards_path CARDS_PATH
                        Path for cards.csv file
  -m MODEL, --model MODEL
                        OpenAI model to use
  -r ROUNDS, --rounds ROUNDS
                        Number of rounds (each round consists of 4 turns: 2 by the player and 2 by the CPU)
  -c CARDS_PER_TURN, --cards_per_turn CARDS_PER_TURN
                        Number of cards per turn 
```

The different turns will proceed consecutively. In the user's interactions, if the word "PASO" is typed, the game will move to the next card. If "SALIR" is typed, the game will end.

Enjoy!