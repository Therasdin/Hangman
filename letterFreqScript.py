from collections import Counter
import csv

# Step 1: Load just the words from your frequency dataset
with open('unigram_freq.csv', 'r') as f:
    words = [line.strip().split(',')[0].lower() for line in f if line.strip() and line[0].isalpha()]

# Step 2: Count letter totals and unique word occurrences
letter_total = Counter()
letter_word_occurrence = Counter()

for word in words:
    letter_total.update(word)
    letter_word_occurrence.update(set(word))  # Only count each letter once per word

# Step 3: Total number of letters (for percentages)
total_letters = sum(letter_total.values())

# Step 4: Write to CSV
with open('letter_frequency.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Letter', 'Occurrences', 'Word_Occurrences', 'Frequency_Percentage'])

    for letter in sorted(letter_total):
        frequency_percentage = (letter_total[letter] / total_letters) * 100
        writer.writerow([
            letter,
            letter_total[letter],
            letter_word_occurrence[letter],
            f"{frequency_percentage:.2f}%"
        ])
