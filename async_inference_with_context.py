import asyncio
import datetime
import json
import os
import re
from asyncio import Semaphore

import pandas as pd
from dotenv import load_dotenv
from mistralai import Mistral

from utils import prompts
from utils.config import models

MAX_CONCURRENT_CALLS = 20
MAX_TRY_NUMBER = 2
MODEL_ID = "mistral_large_first_ft"
MODEL_NAME = models[MODEL_ID]

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
questions_file = "./data/dataset/dataset_english_only_clean_final.csv"
output_path = "./data/output/"

df = pd.read_csv(questions_file, sep=",")
df_context = pd.read_csv("./data/dataset/context_21:33:00.csv", sep=",")

question_prompt = lambda body, possible_answer_a, possible_answer_b, possible_answer_c, possible_answer_d, possible_answer_e: (
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
                model=MODEL_NAME,
                messages=[
                    {
                        "content": prompts.PIZZA_MODIFIER
                        + prompts.THINK_PROMPT_CONTEXT.format(context=df_context["tag"])
                        + prompts.THINK_PROMPT_CONTEXT_FEW_SHOTS,
                        "role": "system",
                    },
                    {"content": prompt, "role": "user"},
                ],
                temperature=0.0,
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

    for _, result in results:
        json_strings = re.findall(
            r"\{(?:[^{}]|\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})*\}", result
        )
        if json_strings:
            try:
                answer_dict = json.loads(json_strings[0])
                answers.append(",".join(answer_dict["answer"]))
            except json.JSONDecodeError:
                answers.append("Error: Invalid JSON")
        else:
            answers.append("Error: No valid JSON found")


if __name__ == "__main__":
    list_prompts = [
        question_prompt(
            row["question"],
            row["answer_A"],
            row["answer_B"],
            row["answer_C"],
            row["answer_D"],
            row["answer_E"],
        )
        for _, row in df.iterrows()
    ]
    asyncio.run(main(prompts=list_prompts))

    output_df = pd.DataFrame(answers, columns=["Answer"])
    output_df.index.name = "id"

    os.makedirs(output_path, exist_ok=True)

    output_df.to_csv(
        f"{output_path}output_verbose_{datetime.datetime.now().strftime('%H:%M:%S')}.csv"
    )
