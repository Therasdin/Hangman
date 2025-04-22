import random
import pandas as pd
import time

def checkWordContainsVowel(word):
    vowels = {'a', 'e', 'i', 'o', 'u'}
    word = word.lower()

    for letter in word:
        if letter in vowels:
            return True

    return False

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
            if word.isalpha() and len(word) >= 3 and checkWordContainsVowel(word):
                raw_freq = float(freq)

                # Normalize relative to the lowest freq you found manually
                weight = raw_freq / 12711

                # Penalize high-frequency (common) words
                if i < 30:
                    weight = (i / 1000)  # Make them very low
                elif i < 1000:
                    weight *= (i / 1000)  # Gradual reduction for semi-common words

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

def get_best_letter_from_likely_word(word_completion, guessed_letters, words, frequencies):
    possible = []

    for word, weight in zip(words, frequencies):
        if len(word) != len(word_completion):
            continue
        match = True
        for wc, actual in zip(word_completion, word):
            if wc != '_' and wc != actual:
                match = False
                break
            if wc == '_' and actual in guessed_letters:
                match = False
                break
        if match:
            possible.append((word, weight))
    
    if not possible:
        return None  # fallback to letter ranking?

    # Sort by highest frequency
    possible.sort(key=lambda x: x[1], reverse=True)
    best_word = possible[0][0]

    for letter in best_word:
        if letter not in guessed_letters:
            return letter

    return None  # All letters already guessed


# --- Main game logic ---
def hangman(word, player_type, words, frequencies):
    guessed_letters = []
    attempts_remaining = MAX_ATTEMPTS
    word_completion = "_" * len(word)

    while attempts_remaining > 0 and "_" in word_completion:
        update_game_board(attempts_remaining, guessed_letters, word_completion)

        if player_type == 'bot':
            if attempts_remaining <= 2:
                guess = get_best_letter_from_likely_word(
                    word_completion, guessed_letters, words, frequencies
                )
                print("Bot is guessing strategically! with letter:", guess)
            else:
                guess = get_bot_guess(guessed_letters)
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

        if guess in word:
            print(f"Good guess! '{guess}' is in the word.")
        else:
            print(f"Sorry, '{guess}' is not in the word.")
            attempts_remaining -= 1

        word_completion = "".join([letter if letter in guessed_letters else "_" for letter in word])

    update_game_board(attempts_remaining, guessed_letters, word_completion)

    if "_" not in word_completion:
        print(f"Congratulations! You guessed the word: {word}")
    else:
        print(f"Game over! The word was: {word}")

# --- Game entry point ---
def play_hangman():
    print("Welcome to Hangman!")
    time.sleep(1.5)
    print("Choose player type:")
    print("1. Human")
    print("2. Bot")
    player_input = input("Enter 1 or 2: ")
    player_type = 'bot' if player_input == '2' else 'human'

    words, frequencies = load_words()
    print(f"Loaded {len(words)} words with frequencies.")
    print
    word_to_guess = random.choices(words, weights=frequencies, k=1)[0]

    hangman(word_to_guess, player_type, words, frequencies)
# --- Run the game ---
play_hangman()
