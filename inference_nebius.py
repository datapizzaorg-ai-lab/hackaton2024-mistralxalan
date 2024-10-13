import datetime
import os

import pandas as pd
import torch
import transformers
from transformers import AutoModelForCausalLM

import utils.prompts as prompts

model_id = "aaditya/OpenBioLLM-Llama3-70B"
model = AutoModelForCausalLM.from_pretrained(
    model_id, device_map="auto", torch_dtype=torch.bfloat16
)
tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, device_map="auto")
device = 0 if torch.cuda.is_available() else -1
pipeline = transformers.pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    batch_size=8,
    device_map="auto",
    truncation=True,
)
questions_file = (
    "./data/dataset/dataset_english_only_clean_final.csv"  # path to the questions file
)

output_path = "./data/output/"  # path to the output file

df = pd.read_csv(questions_file, sep=",")

question_prompt = lambda body: (f"{body}\n")

answers = []

list_prompts = [
    question_prompt(
        row["question"],
    )
    for row_idx, row in df.iterrows()
]
for p in list_prompts:
    messages = [
        {
            "role": "system",
            "content": prompts.TAGGING_PROMPT,
        },
        {
            "role": "user",
            "content": prompts.TAGGING_USER_PROMPT + p,
        },
    ]

    prompt = pipeline.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    terminators = [
        pipeline.tokenizer.eos_token_id,
        pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
    ]

    outputs = pipeline(
        prompt,
        max_new_tokens=4096,
        eos_token_id=terminators,
        do_sample=True,
        temperature=0.01,
        top_p=0.9,
    )
    print(outputs[0]["generated_text"][len(prompt) :])
    answers.append(outputs[0]["generated_text"][len(prompt) :])

output_df = pd.DataFrame({"questions": list_prompts, "tag": answers})
output_df.index.name = "id"

os.makedirs(output_path, exist_ok=True)

output_df.to_csv(
    f"{output_path}output_verbose_{datetime.datetime.now().strftime('%H:%M:%S')}.csv"
)
