import argparse
import asyncio
from dotenv import load_dotenv
from src import Game

# Load environment variables from .env
load_dotenv()

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--cards_path", type=str, help="Path for cards.csv file", default="data/cards.csv")
parser.add_argument("-m", "--model", type=str, help="OpenAI model to use", default="gpt-4o-mini")
parser.add_argument("-r", "--rounds", type=int, help="Number of rounds (each round consists of 4 turns: 2 by the player and 2 by the CPU)", default=2)
parser.add_argument("-c", "--cards_per_turn", type=int, help="Number of cards per turn", default=5)
args = parser.parse_args()

# Create game instance and start
game = Game(cards_path = args.cards_path, model = args.model, rounds = args.rounds, cards_per_turn = args.cards_per_turn)

chat_result = asyncio.run(game.start_game())

# Print results of the game
print(chat_result)