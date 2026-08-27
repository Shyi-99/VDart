# Helper script to pick the right MAX_DISTANCE value in chatbot.py.
#
# MAX_DISTANCE decides when the chatbot says "I don't have that in the FAQ"
# instead of answering. Set it too low and it refuses real customers.
# Set it too high and it invents answers for questions the FAQ never covered.
#
# This script prints the actual distances so you can pick a good number
# instead of guessing.
#
# Run with:
#     python check_threshold.py

import chatbot
from test_chatbot import SEARCH_TESTS, OFF_TOPIC_QUESTIONS


def main():
    print("\nREAL QUESTIONS (these should be ANSWERED - low distance)")
    print("-" * 60)

    real_distances = []
    for question, expected_word in SEARCH_TESTS:
        results = chatbot.search_faq(question)
        distance = results[0][1]
        real_distances.append(distance)
        print(str(round(distance, 3)).ljust(8) + question)

    print("\nOFF-TOPIC QUESTIONS (these should be REFUSED - high distance)")
    print("-" * 60)

    off_distances = []
    for question in OFF_TOPIC_QUESTIONS:
        results = chatbot.search_faq(question)
        distance = results[0][1]
        off_distances.append(distance)
        print(str(round(distance, 3)).ljust(8) + question)

    worst_real = max(real_distances)
    best_off = min(off_distances)

    print("\n" + "-" * 60)
    print("Worst real question : " + str(round(worst_real, 3)))
    print("Closest off-topic   : " + str(round(best_off, 3)))
    print("MAX_DISTANCE now    : " + str(chatbot.MAX_DISTANCE))

    if worst_real < best_off:
        # There is a clear gap, so put the cut-off in the middle of it
        suggested = round((worst_real + best_off) / 2, 2)
        print("\nGood news: there is a clear gap between the two groups.")
        print("Suggested MAX_DISTANCE in chatbot.py: " + str(suggested))
    else:
        print("\nWarning: the two groups overlap, so no cut-off separates them")
        print("perfectly. Try a value just above " + str(round(worst_real, 2)) +
              " so real questions still work.")


if __name__ == "__main__":
    main()
