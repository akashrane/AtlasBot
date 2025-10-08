# agent.py
from tools.geo_lookup import geo_lookup
from tools.atlas_logic import play_turn

def run():
    print("🌍 Welcome to Atlas AI! Type 'quit' to stop.\n")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ["quit", "exit"]:
            break
        result = play_turn(user_input)
        print("Bot:", result["response"])
        print("Map:", result["map"])

if __name__ == "__main__":
    run()
