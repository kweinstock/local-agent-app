from llm import generate

def main():
    print("Local LLM Started. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower == "exit":
            break

        respone = generate(user_input)
        print("\nAssistant: ", respone, "\n")

if __name__ == "__main__":
    main()