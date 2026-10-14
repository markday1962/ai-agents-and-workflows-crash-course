import ollama


def ollama_prompt(prompt: str, model: str = "gemma3:1b") -> str:
    try:
        response = ollama.chat(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except (ollama.ResponseError, ConnectionError) as e:
        print(f"Error calling Ollama: {e}")
        return ""


def main():
    usr_input = input("Enter your input: ")
    result = ollama_prompt(usr_input)
    print("Result: \n", result)


if __name__ == "__main__":
    main()
