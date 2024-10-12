THINK_PROMPT = (
    "Answer the following question with the letters of the correct answer. Each question can have multiple answers that are right. "
    "For each answer think this way: 'is it true compared to the question provided?'"
    "For each question first explain the medical condition and what are the implication, give context, then print the corrects answers."
    "Your answer must contain the letter of the answers, separated by commas and WITHOUT ANY SPACE. An ideal output is like: 'A,B' DO NOT PRINT 'A, B' for instance."
    "You output the letters that you are asked to provide, e.g. 'A,B,C' or 'C'. Your answer is always sorted alphabetically. You must not put letters in a different order"
    'Output the answer as a json at the end od the prompt {"answer": ["A","B","D"]} for example'
)
