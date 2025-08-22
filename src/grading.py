import re

def rule_based_grade(user_response, correct_answer):
    """
    A simple rule-based grading system.

    This function grades the user's response based on how many keywords from the
    correct answer are present in the user's response.

    :param user_response: The user's free recall response.
    :param correct_answer: The correct answer for the concept.
    :return: A grade between 0 and 1.
    """
    # Normalize the text: lowercase and remove punctuation
    user_response_normalized = re.sub(r'[^\w\s]', '', user_response.lower())
    correct_answer_normalized = re.sub(r'[^\w\s]', '', correct_answer.lower())

    # Split into words
    user_words = set(user_response_normalized.split())
    correct_words = set(correct_answer_normalized.split())

    if not correct_words:
        return 1.0 if not user_words else 0.0

    # Calculate the number of matching words
    matching_words = user_words.intersection(correct_words)

    # Calculate the grade
    grade = len(matching_words) / len(correct_words)

    return min(grade, 1.0)
