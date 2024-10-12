import openai

def ask_perplexity(query, api_key):
    openai.api_key = api_key
    openai.api_base = "https://api.perplexity.ai"

    try:
        response = openai.ChatCompletion.create(
            model="mixtral-8x7b-instruct",
            messages=[
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        return f"Error: {str(e)}"

# Example usage
# if __name__ == "__main__":
#     api_key = "your_api_key_here"  # Replace with your actual Perplexity API key
#     question = "What is the capital of France?"
#     answer = ask_perplexity(question, api_key)
#     print(f"Question: {question}")
#     print(f"Answer: {answer}")
