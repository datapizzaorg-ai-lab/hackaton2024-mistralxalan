import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import LlamaTokenizer, MistralForCausalLM
import bitsandbytes
import pandas as pd
import json
import re

tokenizer = LlamaTokenizer.from_pretrained('NousResearch/Nous-Hermes-2-Mistral-7B-DPO', trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

model = MistralForCausalLM.from_pretrained(
    "NousResearch/Nous-Hermes-2-Mistral-7B-DPO",
    torch_dtype=torch.float16,
    device_map="auto",
)

base =  """<|im_start|>system
You are a sentient, superintelligent artificial general intelligence, here to teach and assist me.<|im_end|>
<|im_start|>user
{}<|im_end|>
<|im_start|>assistant"""

df = pd.read_csv("questions.csv")

question_prompt = lambda instructions, body, possible_answer_a, possible_answer_b, possible_answer_c, possible_answer_d, possible_answer_e: (
    f"{instructions}\n"
    f"{body}\n"
)

COT_PROMPT = (
        "Give me the complete medical context i need to answer this question:"
)

list_prompts = [
        base.format(question_prompt(
            COT_PROMPT,
            row["question"],
            row["answer_A"],
            row["answer_B"],
            row["answer_C"],
            row["answer_D"],
            row["answer_E"],
        ))
        for row_idx, row in df.iterrows()
    ]

answers = []
for chat in list_prompts:
    # print(chat)
    inputs = tokenizer(chat, return_tensors="pt")
    input_ids = inputs.input_ids.to("cuda")
    attention_mask = inputs.attention_mask.to("cuda")
    generated_ids = model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=4096, temperature=0.8, repetition_penalty=1.1, do_sample=True, eos_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(generated_ids[0][input_ids.shape[-1]:], skip_special_tokens=True, clean_up_tokenization_space=True)
    #print(response)
    #json_string = re.findall(
    #        r"\{(?:[^{}]|\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})*\}", response
    #)[0]
    #solution = ",".join(json.loads(json_string)["answer"])
    #print(solution)
    answers.append(response)

output_df = pd.DataFrame(answers, columns=["Answer"])
output_df.index.name = "id"
output_df.to_csv("output_question_context.csv")
