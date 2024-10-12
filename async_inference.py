import asyncio
import os
from asyncio import Semaphore

import pandas as pd
from dotenv import load_dotenv
from mistralai import Mistral

MAX_CONCURRENT_CALLS = 30

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")  # your API key
questions_file = "./data/dataset/questions.csv"  # path to the questions file

output_path = "./data/output/"  # path to the output file

df = pd.read_csv(questions_file)

question_prompt = lambda body, possible_answer_a, possible_answer_b, possible_answer_c, possible_answer_d, possible_answer_e: (
    "Answer the following question with the letters of the correct answer. Each question can have multiple answers that are right. "
    "For each answwer think this way: 'is it true compared to the question provided?'"
    "For each question first explain the medical condition and what are the implication, give context, then print the corrects answers."
    "Your answer must contain the letter of the answers, separated by commas and without any space. An ideal output is like: 'A,B', for instance."
    "You output the letters that you are asked to provide, e.g. 'A,B,C' or 'C'. Your answer is always sorted alphabetically. You must not put letters"
    "in a different order"
    f"{body}\n"
    f"A: {possible_answer_a}\n"
    f"B: {possible_answer_b}\n"
    f"C: {possible_answer_c}\n"
    f"D: {possible_answer_d}\n"
    f"E: {possible_answer_e}\n"
)

answers = []


async def process_prompt(client, prompt, semaphore):
    async with semaphore:
        try:
            res = await client.chat.complete_async(
                model="mistral-small-latest",
                messages=[{"content": prompt, "role": "user"}],
            )
            if res is not None:
                return prompt, res.choices[0].message.content
        except Exception as e:
            return prompt, f"Error: {str(e)}"
    return prompt, None


async def main(prompts=None):
    s = Mistral(api_key=os.getenv("MISTRAL_API_KEY", ""))

    semaphore = Semaphore(MAX_CONCURRENT_CALLS)
    tasks = [process_prompt(s, prompt, semaphore) for prompt in prompts]
    results = await asyncio.gather(*tasks)

    for prompt, result in zip(prompts, results):
        print(f"Prompt: {prompt}")
        print(f"Response: {result}")
        print()
        answers.append(result[1])


if __name__ == "__main__":
    prompts = [
        question_prompt(
            row["question"],
            row["answer_A"],
            row["answer_B"],
            row["answer_C"],
            row["answer_D"],
            row["answer_E"],
        )
        for row_idx, row in df.iterrows()
    ]
    asyncio.run(main(prompts=prompts))

    output_df = pd.DataFrame(answers, columns=["Answer"])
    output_df.index.name = "id"

    os.makedirs(output_path, exist_ok=True)

    output_df.to_csv(f"{output_path}output_verbose.csv")
