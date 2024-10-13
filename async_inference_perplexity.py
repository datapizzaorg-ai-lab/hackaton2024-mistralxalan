import asyncio
import datetime
import json
import os
import re

import aiohttp
import pandas as pd  # Assuming you have this import already
from dotenv import load_dotenv

import prompts

load_dotenv()
import pandas as pd

questions_file = (
    "./data/dataset/dataset_english_only_clean_final.csv"  # path to the questions file
)

output_path = "./data/output/"  # path to the output file

df = pd.read_csv(questions_file, sep=",")

question_prompt = lambda body, possible_answer_a, possible_answer_b, possible_answer_c, possible_answer_d, possible_answer_e: (
    f"{body}\n"
    f"A: {possible_answer_a}\n"
    f"B: {possible_answer_b}\n"
    f"C: {possible_answer_c}\n"
    f"D: {possible_answer_d}\n"
    f"E: {possible_answer_e}\n"
)

url = "https://api.perplexity.ai/chat/completions"
answers = []

list_prompts = [
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

headers = {
    "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
    "Content-Type": "application/json",
}

semaphore = asyncio.Semaphore(15)


async def fetch(session, prompt):
    payload = {
        "model": "llama-3.1-sonar-huge-128k-online",
        "messages": [
            {
                "role": "system",
                "content": prompts.PIZZA_MODIFIER + prompts.THINK_PROMPT,
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "top_p": 0.9,
        "return_citations": True,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
    }
    async with semaphore:  # Limit to 30 concurrent requests
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            # Extract the answer from the response
            message_content = result["choices"][0]["message"]["content"]
            json_string = re.findall(
                r"\{(?:[^{}]|\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})*\}",
                message_content,
            )[0]
            return ",".join(json.loads(json_string)["answer"])


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, prompt) for prompt in list_prompts]
        results = await asyncio.gather(*tasks)
        return results


# Run the async event loop
answers = asyncio.run(main())

# Output the results to a DataFrame and save as CSV
output_df = pd.DataFrame(answers, columns=["Answer"])
output_df.index.name = "id"

os.makedirs(output_path, exist_ok=True)

output_df.to_csv(
    f"{output_path}output_verbose_{datetime.datetime.now().strftime('%H:%M:%S')}.csv"
)
