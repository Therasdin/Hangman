
import random
import pandas as pd
import time
import torch
import sys
from collections import defaultdict, Counter

# --- Helper functions ---
def checkWordContainsVowel(word):
    vowels = {'a', 'e', 'i', 'o', 'u'}
    return any(letter in vowels for letter in word.lower())

def load_words():
    words = []
    frequencies = []
    with open('unigram_freq.csv', 'r') as f:
        next(f)
        for i, line in enumerate(f):
            parts = line.strip().split(',')
            if len(parts) != 2:
                continue
            word, freq = parts
            if word.isalpha() and len(word) >= 3 and checkWordContainsVowel(word):
                raw_freq = float(freq)
                weight = raw_freq / 12711
                if i < 30:
                    weight = i / 1000
                elif i < 1000:
                    weight *= i / 1000
                words.append(word.lower())
                frequencies.append(weight)
    return words, frequencies

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

def update_game_board(attempts_remaining, guessed_letters, word_completion):
    stage_index = MAX_ATTEMPTS - attempts_remaining
    stage_index = min(stage_index, len(stages) - 1)
    print(stages[stage_index])
    print(f"Word: {word_completion}")
    print("Guessed letters:", " ".join(guessed_letters))
    print(f"Attempts remaining: {attempts_remaining}")
    print("-" * 20)

def get_bot_guess(guessed_letters):
    for letter in letter_ranking:
        if letter not in guessed_letters:
            return letter
    return None

def get_best_letter_from_likely_word(word_completion, guessed_letters, words, frequencies):
    possible = []
    for w, wt in zip(words, frequencies):
        if len(w) != len(word_completion):
            continue
        match = True
        for wc, c in zip(word_completion, w):
            if (wc != '_' and wc != c) or (wc == '_' and c in guessed_letters):
                match = False
                break
        if match:
            possible.append((w, wt))
    if not possible:
        return None
    possible.sort(key=lambda x: x[1], reverse=True)
    for c in possible[0][0]:
        if c not in guessed_letters:
            return c
    return None

# --- AI Distribution by Word Length ---
def train_ai_by_word_length(words):
    length_freq = defaultdict(Counter)
    for w in words:
        length_freq[len(w)].update(set(w))
    dist = {}
    for length, ctr in length_freq.items():
        total = sum(ctr.values())
        vec = torch.zeros(26)
        for letter, cnt in ctr.items():
            vec[ord(letter) - ord('a')] = cnt / total
        dist[length] = vec
    return dist

# --- AI Guess using Pattern + Length Distribution ---
def get_ai_guess_from_distribution(dist_map, word_completion, guessed_letters, words, frequencies):
    length = len(word_completion)
    # Filter matching words
    pattern_words = []
    pattern_weights = []
    for w, wt in zip(words, frequencies):
        if len(w) != length:
            continue
        match = True
        for wc, c in zip(word_completion, w):
            if (wc != '_' and wc != c) or (wc == '_' and c in guessed_letters):
                match = False
                break
        if match:
            pattern_words.append(w)
            pattern_weights.append(wt)
    # Accumulate letter scores
    letter_scores = {}
    if pattern_words:
        for w, wt in zip(pattern_words, pattern_weights):
            for c in set(w):
                if c not in guessed_letters:
                    letter_scores[c] = letter_scores.get(c, 0) + wt
    else:
        vec = dist_map.get(length, torch.ones(26) / 26)
        for i in range(26):
            c = chr(i + ord('a'))
            if c not in guessed_letters:
                letter_scores[c] = vec[i].item()
    if not letter_scores:
        return None
    return max(letter_scores, key=letter_scores.get)

# --- Main Hangman Logic ---
def hangman(player_type, words, frequencies):
    guessed_letters = []
    attempts_remaining = MAX_ATTEMPTS
    word = random.choices(words, weights=frequencies, k=1)[0]
    word_completion = "_" * len(word)
    ai_dist = train_ai_by_word_length(words) if (player_type == 'ai' or player_type == 'batch_bot') else None

    while attempts_remaining > 0 and "_" in word_completion:
        if player_type != 'batch_bot':
            update_game_board(attempts_remaining, guessed_letters, word_completion)

        if player_type == 'bot':
            guess = get_best_letter_from_likely_word(word_completion, guessed_letters, words, frequencies) \
                if attempts_remaining <= 2 else get_bot_guess(guessed_letters)
            print("Bot guesses:", guess)
        elif player_type == 'ai':
            guess = get_ai_guess_from_distribution(ai_dist, word_completion, guessed_letters, words, frequencies)
            print("AI guesses:", guess)
        elif player_type == 'human':
            guess = input("Please guess a letter or type exit: ").lower()
        else:
            guess = get_ai_guess_from_distribution(ai_dist, word_completion, guessed_letters, words, frequencies)
        if guess == 'exit':
            print("Exiting the game.")
            return {
                "word": word,
                "won": 0,
                "word_length": len(word),
                "attempts_used": MAX_ATTEMPTS - attempts_remaining,
                "total_guesses": len(guessed_letters)
            }

        if not guess or len(guess) != 1 or not guess.isalpha():
            print("Invalid input. Please enter a single letter.")
            continue

        if guess in guessed_letters:
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


def play_hangman():
    playAgain = True
    words, frequencies = load_words()

    print("Welcome to Hangman!")
    time.sleep(1.5)
    print("Choose player type:")
    print("1. Human")
    print("2. Bot")
    print("3. AI")
    print("4. Batch AI")
    player_input = input("Enter 1, 2, 3, or 4: ")
    while player_input not in ['1', '2', '3','4']:
        print("Invalid input. Please enter 1, 2, or 3.")
        player_input = input("Enter 1, 2, 3, or 4: ")
    player_type = {'1': 'human', '2': 'bot', '3': 'ai', '4': 'batch_bot'}[player_input]


    while playAgain:
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
            df.to_csv("hangmanAItest1_batch_results.csv", index=False)
            print("Results saved to hangman_batch_results.csv")

            playAgain = False
        else:
            hangman(player_type, words, frequencies, ai_dist)

            print("Do you want to play again?")
            print("Press 0 to exit, 1 to play again, or 2 to change player type")
            num = input("Enter 0, 1, or 2: ")
            while num not in ['0', '1', '2']:
                print("Invalid input. Please enter 0, 1, or 2.")
                num = input("Enter 0, 1, or 2: ")

            if num == '1':
                print("Starting a new game...")
            elif num == '0':
                playAgain = False
                print("Thanks for playing!")
            elif num == '2':
                print("Choose player type:")
                print("1. Human")
                print("2. Bot")
                print("3. AI")
                player_input = input("Enter 1, 2, or 3: ")
                while player_input not in ['1', '2', '3']:
                    print("Invalid input. Please enter 1, 2, or 3.")
                    player_input = input("Enter 1, 2, or 3: ")
                player_type = {'1': 'human', '2': 'bot', '3': 'ai'}[player_input]


# --- Run the game ---
play_hangman()