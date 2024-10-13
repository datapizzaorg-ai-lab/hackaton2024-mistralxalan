import json
import re


def parse_qa_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    questions = re.split(r"---\n+### \*\*Question \d+\*\*", content)[1:]
    parsed_data = []

    for question in questions:
        question_text = re.search(r"(.*?)\n\*\*Questions :\*\*", question, re.DOTALL)
        options = re.findall(r"([A-E]\. .*?)\n", question)
        correct_answers = re.search(r"\*\*Réponses correctes :\*\* (.*?)\n", question)
        explanations = re.findall(r"- ([A-E]) : (.*?)\n", question)

        if question_text and options and correct_answers and explanations:
            question_content = (
                question_text.group(1).strip() + "\n\n" + "\n".join(options)
            )

            answer_content = (
                f"Réponses correctes : {correct_answers.group(1)}\n\n"
                "Explications :\n"
                + "\n".join(
                    [
                        f"{letter} : {explanation}"
                        for letter, explanation in explanations
                    ]
                )
            )

            parsed_data.append(
                {
                    "messages": [
                        {"role": "user", "content": question_content},
                        {"role": "assistant", "content": answer_content},
                    ]
                }
            )

    return parsed_data


def write_json(data, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")


def main():
    i = 4
    filename = f"trascription_{i}"

    parsed_data = parse_qa_text(f"./data/dataset/{filename}.txt")
    write_json(parsed_data, f"./data/dataset/{filename}.json")

    print("Parsing complete. Output written to 'output.json'.")


if __name__ == "__main__":
    main()
