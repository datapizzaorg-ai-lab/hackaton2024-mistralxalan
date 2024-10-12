import pandas as pd
from mistralai import Mistral
from dotenv import load_dotenv
import os
from asyncio import Semaphore

load_dotenv()


api_key = os.getenv("MISTRAL_API_KEY")  # your API key
questions_file = "./data/dataset/questions.csv"  # path to the questions file

output_path = "./data/output/"  # path to the output file

instructions = (
    "Answer the following question with the letters of the correct answer. Each question can have multiple answers that are right. "
    "For each answwer think this way: 'is it true compared to the question provided?'"
    "For each question first explain the medical condition and what are the implication, give context, then print the corrects answers."
    "Your answer must contain the letter of the answers, separated by commas and without any space. An ideal output is like: 'A,B', for instance."
    "You output the letters that you are asked to provide, e.g. 'A,B,C' or 'C'. Your answer is always sorted alphabetically. You must not put letters in a different order"
    "Don't use markdown, give the answer saying 'The answer is: '"
)


def question_prompt(
    instructions,
    question,
    possible_answer_a,
    possible_answer_b,
    possible_answer_c,
    possible_answer_d,
    possible_answer_e,
):
    return (
        f"{instructions}\n"
        f"{question}\n"
        f"A: {possible_answer_a}\n"
        f"B: {possible_answer_b}\n"
        f"C: {possible_answer_c}\n"
        f"D: {possible_answer_d}\n"
        f"E: {possible_answer_e}\n"
    )


def create_list_of_prompts(df, insstructions):
    prompts = []
    for row_idx, row in df.iterrows():
        prompts.append(
            question_prompt(
                instructions,
                row["question"],
                row["answer_A"],
                row["answer_B"],
                row["answer_C"],
                row["answer_D"],
                row["answer_E"],
            )
        )
    return prompts


async def answer(client, prompt, semaphore):
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


if __name__ == "__main__":
    df = pd.read_csv(questions_file)
    prompts = create_list_of_prompts(df, instructions)

    client = Mistral(api_key=api_key)
    chat_response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "user", "content": prompts[1]},
        ],
        temperature=0.0,
    )
    print(chat_response.choices[0].message.content)
