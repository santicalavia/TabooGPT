import argparse
from dotenv import load_dotenv
from src import Game

# Load environment variables from .env
load_dotenv()

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--cards_path", type=str, help="Ruta para el archivo cards.csv", default="data/cards.csv")
parser.add_argument("-m", "--model", type=str, help="Modelo de openai para usar", default="gpt-4o-mini")
parser.add_argument("-r", "--rounds", type=int, help="Numero de rondas (cada ronda son 4 turnos, 2 del jugador y 2 de la CPU)", default=2)
parser.add_argument("-c", "--cards_per_turn", type=int, help="Numero de cartas por turno", default=5)
parser.add_argument("-v", "--verbose", type=bool, help="True : Mostrar toda la información de las conversaciones (modo depuración). False : Silenciar partes (modo normal de juego)", default=False)
args = parser.parse_args()

# Create game instance and start
game = Game(cards_path = args.cards_path, model = args.model, rounds = args.rounds, cards_per_turn = args.cards_per_turn, verbose = args.verbose)
chat_result = game.start_game()

# Print results of the game
print(chat_result)