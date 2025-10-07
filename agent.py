# agent.py
from openai import OpenAI
from tools.geo_lookup import geo_lookup
from tools.atlas_logic import play_turn

client = OpenAI()

def run():
    print("🌍 Welcome to Atlas AI! Type 'quit' to stop.\n")
    used = set()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        result = play_turn(user_input)
        print("Bot:", result["response"])
        print("Map:", result["map"])

if __name__ == "__main__":
    run()
