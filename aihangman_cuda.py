import random
import pandas as pd
import time
import torch
import numpy as np
from collections import defaultdict, Counter

# --- Device Setup ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# --- Helper functions ---
def check_word_contains_vowel(word):
    return any(v in word for v in 'aeiou')

def load_words(path='unigram_freq.csv'):
    df = pd.read_csv(path)
    df = df[df['word'].str.isalpha() & (df['word'].str.len() >= 3)]
    df = df[df['word'].apply(check_word_contains_vowel)]
    df['word'] = df['word'].str.lower()
    df['weight'] = df['count'] / df['count'].sum()
    return df['word'].tolist(), df['weight'].tolist()

def load_letter_ranking(filename='letter_frequency.csv'):
    df = pd.read_csv(filename)
    df = df.sort_values(by='Frequency', ascending=False)
    return [row['Letter'].lower() for _, row in df.iterrows()]

letter_ranking = load_letter_ranking()
MAX_ATTEMPTS = 6

# ASCII stages omitted for brevity; assume same as before
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
    """ ]
def update_game_board(attempts, guessed, pattern):
    idx = min(MAX_ATTEMPTS - attempts, len(stages) - 1)
    print(stages[idx])
    print(f"Word: {pattern}")
    print("Guessed letters:", " ".join(guessed))
    print(f"Attempts remaining: {attempts}")
    print("-" * 20)

# --- Length-based Distribution on GPU ---
def train_length_distribution(words):
    length_freq = defaultdict(Counter)
    for w in words:
        length_freq[len(w)].update(set(w))
    length_dist = {}
    for length, ctr in length_freq.items():
        total = sum(ctr.values())
        vec = torch.zeros(26, device=device)
        for letter, cnt in ctr.items():
            vec[ord(letter) - ord('a')] = cnt / total
        length_dist[length] = vec
    return length_dist

# --- AI Guess using Pattern + Length Distribution on GPU ---
def ai_guess_gpu(dist_map, pattern, guessed, words, freqs):
    length = len(pattern)
    # Filter matching words
    possible_indices = []
    for i, w in enumerate(words):
        if len(w) != length: continue
        if all((pattern[j] == '_' and w[j] not in guessed) or (pattern[j] == w[j]) for j in range(length)):
            possible_indices.append(i)
    # Score letters
    if possible_indices:
        scores = torch.zeros(26, device=device)
        for idx in possible_indices:
            w = words[idx]
            wt = freqs[idx]
            for c in set(w):
                if c not in guessed:
                    scores[ord(c) - ord('a')] += wt
    else:
        scores = dist_map.get(length, torch.ones(26, device=device) / 26)
        # zero out guessed
        for c in guessed:
            scores[ord(c) - ord('a')] = 0
    # pick best
    best = torch.argmax(scores).item()
    return chr(best + ord('a'))

# --- Simulation Function ---
def run_sim(word, words, freqs, dist_map):
    guessed = []
    attempts = MAX_ATTEMPTS
    pattern = '_' * len(word)
    while attempts > 0 and '_' in pattern:
        guess = ai_guess_gpu(dist_map, pattern, guessed, words, freqs)
        if guess in guessed: break
        guessed.append(guess)
        if guess not in word:
            attempts -= 1
        pattern = ''.join([c if c in guessed else '_' for c in word])
    return '_' not in pattern

# --- Main Hangman Logic ---
def hangman(word, mode, words, freqs, dist_map):
    guessed = []
    attempts = MAX_ATTEMPTS
    pattern = '_' * len(word)
    while attempts > 0 and '_' in pattern:
        update_game_board(attempts, guessed, pattern)
        if mode == 'bot':
            guess = random.choice([c for c in letter_ranking if c not in guessed]) if attempts > 2 else ai_guess_gpu(dist_map, pattern, guessed, words, freqs)
        elif mode == 'ai':
            guess = ai_guess_gpu(dist_map, pattern, guessed, words, freqs)
        else:
            guess = input("Guess a letter or 'exit': ").lower()
            if guess == 'exit': return
        print(f"{mode.upper()} guesses: {guess}")
        if not guess or len(guess) != 1 or guess in guessed or not guess.isalpha(): continue
        guessed.append(guess)
        if guess not in word:
            attempts -= 1
        pattern = ''.join([c if c in guessed else '_' for c in word])
    update_game_board(attempts, guessed, pattern)
    if '_' not in pattern:
        print(f"Congrats! You guessed: {word}")
    else:
        print(f"Game over. The word was: {word}")

# --- Entry Point ---
def play_hangman():
    print("Welcome to Hangman!")
    time.sleep(1.5)
    print("1. Human\n2. Bot\n3. AI\n4. Simulate AI Performance")
    choice = input("Enter 1-4: ")
    words, freqs = load_words()
    dist_map = train_length_distribution(words)
    if choice == '4':
        wins = 0
        for _ in range(500):
            w = random.choices(words, weights=freqs, k=1)[0]
            if run_sim(w, words, freqs, dist_map): wins += 1
        print(f"AI won {wins}/500 ({wins/5:.2f}%)")
        return
    mode = {'1':'human','2':'bot','3':'ai'}.get(choice, 'human')
    word = random.choices(words, weights=freqs, k=1)[0]
    hangman(word, mode, words, freqs, dist_map)

if __name__ == '__main__':
    play_hangman()