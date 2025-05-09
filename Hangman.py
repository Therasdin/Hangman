import random
import pandas as pd
import time
import sys

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
def hangman(player_type, words, frequencies):
    guessed_letters = []
    attempts_remaining = MAX_ATTEMPTS
    word = random.choices(words, weights=frequencies, k=1)[0]
    word_completion = "_" * len(word)

    while attempts_remaining > 0 and "_" in word_completion:
        if player_type != 'batch_bot':  # Only show visuals if not batch running
            update_game_board(attempts_remaining, guessed_letters, word_completion)

        if player_type in ['bot', 'batch_bot']:
            if attempts_remaining <= 2:
                guess = get_best_letter_from_likely_word(
                    word_completion, guessed_letters, words, frequencies
                )
                if player_type != 'batch_bot':
                    print("Bot is guessing strategically! with letter:", guess)
            else:
                guess = get_bot_guess(guessed_letters)
        else:
            guess = input("Please guess a letter or type exit: ").lower()

        if guess == 'exit':
            print("Exiting the game.")
            return {
                "word": word,
                "won": 0,
                "word_length": len(word),
                "attempts_used": MAX_ATTEMPTS - attempts_remaining,
                "total_guesses": len(guessed_letters)
            }

        if len(guess) != 1 or not guess.isalpha():
            if player_type != 'batch_bot':
                print("Invalid input. Please enter a single letter.")
            continue

        if guess in guessed_letters:
            if player_type != 'batch_bot':
                print("You've already guessed that letter. Try again.")
            continue

        guessed_letters.append(guess)
        guessed_letters.sort()

        if guess in word:
            if player_type != 'batch_bot':
                print(f"Good guess! '{guess}' is in the word.")
        else:
            if player_type != 'batch_bot':
                print(f"Sorry, '{guess}' is not in the word.")
            attempts_remaining -= 1

        word_completion = "".join([letter if letter in guessed_letters else "_" for letter in word])

    if player_type != 'batch_bot':
        update_game_board(attempts_remaining, guessed_letters, word_completion)

    won = int("_" not in word_completion)
    if player_type != 'batch_bot':
        if won:
            print(f"Congratulations! You guessed the word: {word}")
        else:
            print(f"Game over! The word was: {word}")

    return {
        "word": word,
        "won": won,
        "word_length": len(word),
        "attempts_used": MAX_ATTEMPTS - attempts_remaining,
        "total_guesses": len(guessed_letters)
    }


# --- Game entry point ---
def play_hangman():
    playAgain = True
    words, frequencies = load_words()


    print("Welcome to Hangman!")
    time.sleep(1.5)
    print("Choose player type:")
    print("1. Human")
    print("2. Bot")
    print("3. 50,000 bot games")

    player_input = input("Enter 1, 2 or 3: ")
    while player_input not in ['1', '2', '3']:
        print("Invalid input. Please enter 1, 2 or 3.")
        player_input = input("Enter 1, 2 or 3: ")
    
    if player_input == '1':
        player_type = 'human'
    elif player_input == '2':
        player_type = 'bot'
    else:
        player_type = 'batch_bot'

    while (playAgain == True):
        if player_type == 'batch_bot':
            num_games = int(input("Enter the number of games to run (default is 50,000): ") or 50000)
            while num_games <= 0:
                print("Invalid input. Please enter a positive number.")
                num_games = int(input("Enter the number of games to run (default is 50,000): ") or 50000)
            print("Running " + str(num_games) + " bot games...")
            results = []
            
            for i in range(num_games):
                game_data = hangman(player_type, words, frequencies)
                results.append(game_data)
                
                if i % (num_games/100) == 0:
                    percent = (i / num_games) * 100
                    sys.stdout.write(f"\rProgress: {percent:.1f}%")
                    sys.stdout.flush()

            df = pd.DataFrame(results)
            win_rate = df["won"].mean()

            print("Batch run complete.")
            print(f"Total wins: {df['won'].sum()} out of " + str(num_games) + " games.")
            print(f"Win rate: {win_rate:.4f}")

            # Save to CSV
            df.to_csv("hangman_batch_results.csv", index=False)
            print("Results saved to hangman_batch_results.csv")

            playAgain = False
        else:
            hangman(player_type, words, frequencies)

            print ("Do you want to play again?")
            print("Press 0 to exit, 1 to play again, or 2 to change player type")
            num = input("Enter 0, 1, or 2: ")
            while num not in ['0', '1', '2']:
                print("Invalid input. Please enter 0, 1, or 2.")
                num = input("Enter 0, 1, or 2: ")
            if num == '1':
                print("Starting a new game...")
                time.sleep(1.5)
            elif num == '0':
                playAgain = False
                print("Thanks for playing!")
            elif num == '2':
                print("Choose player type:")
                print("1. Human")
                print("2. Bot")
                player_input = input("Enter 1 or 2: ")
                player_type = 'bot' if player_input == '2' else 'human'

play_hangman()