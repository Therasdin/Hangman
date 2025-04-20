import random
import pandas as pd

def load_words():
    words = []
    frequencies = []

    with open('unigram_freq.csv', 'r') as f:
        next(f)  # Skip header
        for i, line in enumerate(f):
            parts = line.strip().split(',')
            if len(parts) != 2:
                continue
            word, freq = parts
            if word.isalpha() and len(word) >= 3:
                weight = float(freq)

                if i < 30:
                    continue  # Skip first 30 entries entirely
                elif i < 400:
                    weight *= (i / 400)  # Reduce weights drastically for 31–100

                words.append(word.lower())
                frequencies.append(weight)
    
    return words, frequencies

    # --- Load and sort letter frequencies for bot logic ---
def load_letter_ranking(filename='letter_frequency.csv'):
    df = pd.read_csv(filename)
    df = df.sort_values(by='Frequency', ascending=False)
    return [row['Letter'].lower() for _, row in df.iterrows()]

letter_ranking = load_letter_ranking()
MAX_ATTEMPTS = 6

stages = [
    """
      +---+
      |   |
          |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
      |   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     /    |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     / \\  |
          |
    =========
    """
]

    # --- Game board display ---
def update_game_board(attempts_remaining, guessed_letters, word_completion):
    stage_index = MAX_ATTEMPTS - attempts_remaining
    stage_index = min(stage_index, len(stages) - 1)
    print(stages[stage_index])
    print(f"Word: {word_completion}")
    print("Guessed letters:", " ".join(guessed_letters))
    print(f"Attempts remaining: {attempts_remaining}")
    print("-" * 20)

    # --- Bot guessing logic ---
def get_bot_guess(guessed_letters):
    for letter in letter_ranking:
        if letter not in guessed_letters:
            return letter
    return None

# --- Main game logic ---
def hangman(words, player_type):
    word_to_guess = random.choice(words)
    guessed_letters = []
    attempts_remaining = MAX_ATTEMPTS
    word_completion = "_" * len(word_to_guess)

    while attempts_remaining > 0 and "_" in word_completion:
        update_game_board(attempts_remaining, guessed_letters, word_completion)

        if player_type == 'bot':
            guess = get_bot_guess(guessed_letters)
            print(f"Bot guesses: {guess}")
        else:
            guess = input("Please guess a letter or type exit: ").lower()
            
        if guess == 'exit':
            print("Exiting the game.")
            return

        if len(guess) != 1 or not guess.isalpha():
            print("Invalid input. Please enter a single letter.")
            continue

        if guess in guessed_letters:
            print("You've already guessed that letter. Try again.")
            continue

        guessed_letters.append(guess)
        guessed_letters.sort()

        if guess in word_to_guess:
            print(f"Good guess! '{guess}' is in the word.")
        else:
            print(f"Sorry, '{guess}' is not in the word.")
            attempts_remaining -= 1

        word_completion = "".join([letter if letter in guessed_letters else "_" for letter in word_to_guess])

    update_game_board(attempts_remaining, guessed_letters, word_completion)

    if "_" not in word_completion:
        print(f"Congratulations! You guessed the word: {word_to_guess}")
    else:
        print(f"Game over! The word was: {word_to_guess}")

# --- Game entry point ---
def play_hangman():
    print("Choose player type:")
    print("1. Human")
    print("2. Bot")
    player_input = input("Enter 1 or 2: ")
    player_type = 'bot' if player_input == '2' else 'human'

    print("Welcome to Hangman!")

    words, frequencies = load_words()
    # Pick a word weighted by frequency
    word_to_guess = random.choices(words, weights=frequencies, k=1)[0]

    hangman([word_to_guess], player_type)

# --- Run the game ---
play_hangman()
