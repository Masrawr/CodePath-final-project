# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [ ] Describe the game's purpose.
   The game requires user to guess a number between 0-100. If the user's input is higher than the guess, the game tells the user too high, if too low, the game returns too low. 
- [ ] Detail which bugs you found.
   There were 5 different bugs I found. The two I focused on fixing were: 1. Game accepting out of range input. 2.New game Button not working.
- [ ] Explain what fixes you applied.
   Added code to check for out of range exceptions and output an out of range message. Added code to update game status when "New game" button is pressed.


## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without watching a video:

1. User enters a guess of 101 → game rejects it with "Guess is out of range (0-100)"
2. User enters a guess of 40 → "Too Low"
3. User enters a guess of 70 → "Too High"
4. Score updates correctly after each guess
5. User enters the correct number → "🎉 Correct!" and the game ends with a win
6. User clicks "New Game 🔁" → the game fully resets and is playable again

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
# Paste your pytest output here, e.g.:
=============================================== test session starts ================================================
platform darwin -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/masroor/Downloads/Academics/Codepath/ai110-module1show-gameglitchinvestigator-starter
plugins: anyio-4.13.0
collected 9 items                                                                                                  

tests/test_game_logic.py .........                                                                           [100%]

================================================ 9 passed in 0.01s =================================================

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
