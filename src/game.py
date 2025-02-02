import random
import pandas as pd
from .utils import CircularBuffer
from .chats import PlayerHintChat, PlayerGuessChat, CpuChat

class Game():
    """
    Represents the game logic, managing scoring, rounds, turns, and cards.

    Attributes:
        player_score (int): Player's score.
        cpu_score (int): CPU's score.
        turns_order (CircularBuffer): Order of turns in the game.
        cards_df (pd.DataFrame): DataFrame containing the game cards.
        model (str): Model used for llm calls.
        rounds (int): Number of rounds in the game.
        cards_per_turn (int): Number of cards used per turn.
    """
    def __init__(self, cards_path : str, model : str, rounds : int, cards_per_turn : int):
        """
        Initializes the game instance with the given parameters.

        Args:
            cards_path (str): Path to the CSV file containing the cards csv.
            model (str): Model to be used for llm calls.
            rounds (int): Number of rounds in the game.
            cards_per_turn (int): Number of cards per turn.
        """
        self.player_score = 0
        self.cpu_score = 0
        self.turns_order = None
        self.cards_df = pd.read_csv(cards_path)
        self.cards_df['discarded'] = False
        self.model = model
        self.rounds = rounds
        self.cards_per_turn = cards_per_turn
    
    def add_score(self, turn_type : str, tries : int) -> int:
        """
        Calculates and adds the score based on the number of attempts.

        Args:
            turn_type (str): Type of turn (e.g., 'player_hint_turn', 'cpu').
            tries (int): Number of attempts made.

        Returns (int): Score added.
        """
        # Add 5 points if tries = 1, substract number of tries if tries > 1, add 1 point if tries >= 5
        if tries <= 5:
            score_to_add = 5 - (tries - 1)
        else:
            score_to_add = 1
        if 'player' in turn_type:
            self.player_score += score_to_add
        else:
            self.cpu_score += score_to_add
        return score_to_add

    def roll_turn_order(self) -> list:
        """
        Randomly determines the turn order for a round.

        Returns (list): List with the turn order.
        """
        player_turns = ['player_hint_turn', 'player_guess_turn']
        teams = ['player', 'cpu']
        start_team = random.choice(teams)
        start_player_turn_type = random.choice(player_turns)
        if start_team == 'cpu' and start_player_turn_type == 'player_hint_turn':
            turns_order_list = ['cpu', 'player_hint_turn', 'cpu', 'player_guess_turn']
        elif start_team == 'cpu' and start_player_turn_type == 'player_guess_turn':
            turns_order_list = ['cpu', 'player_guess_turn', 'cpu', 'player_hint_turn']
        elif start_team == 'player' and start_player_turn_type == 'player_hint_turn':
            turns_order_list = ['player_hint_turn', 'cpu', 'player_guess_turn', 'cpu']
        elif start_team == 'player' and start_player_turn_type == 'player_guess_turn':
            turns_order_list = ['player_guess_turn', 'cpu', 'player_hint_turn', 'cpu']
        return turns_order_list

    def get_random_card(self) -> dict:
        """
        Retrieves a random, non-discarded card and marks it as discarded.

        Returns (dict): The selected card with its attributes.
        """
        random_card = self.cards_df.loc[self.cards_df['discarded'] == False].sample(n = 1).to_dict(orient='records')[0]
        id_ = random_card['ID']
        self.cards_df.loc[self.cards_df['ID'] == id_ , 'discarded'] = True
        return random_card
    
    async def start_game(self) -> str:
        """
        Starts the game, managing rounds and turns.

        Returns (str): Final game results with the scores.
        """
        turns_order_list = self.roll_turn_order()
        self.turns_order = CircularBuffer(turns_order_list)
        turns = 4 # Each round consist on 4 turns (2 turns for player, 2 turns for CPU) 
        ### Round
        for r in range(self.rounds):
            ### Turn
            for t in range(turns):
                turn_type = self.turns_order.next()
                ### Cards
                for r in range(self.cards_per_turn):
                    card = self.get_random_card()
                    forbidden = [card['forbidden_1'], card['forbidden_2'], card['forbidden_3'], card['forbidden_4']]
                    target_word = card['target']
                    if turn_type == 'player_hint_turn':
                        print('EL JUGADOR DA PISTAS')
                        print(f'PALABRA : {target_word}')
                        print(f'PALABRAS PROHIBIDAS : {", ".join(forbidden)}')
                        game_round = PlayerHintChat(self.model, forbidden, target_word)
                    elif turn_type == 'player_guess_turn':
                        print('EL JUGADOR ADIVINA')
                        game_round = PlayerGuessChat(self.model, forbidden, target_word)
                    elif turn_type == 'cpu':
                        print('JUEGA LA CPU')
                        print(f'PALABRA : {target_word}')
                        print(f'PALABRAS PROHIBIDAS : {", ".join(forbidden)}')
                        game_round = CpuChat(self.model, forbidden, target_word)
                    chat_result, tries = await game_round.initiate_round()
                    if chat_result == 'ACIERTO':
                        score_to_add = self.add_score(turn_type, tries)
                        print(f'¡ACIERTO! SE SUMAN {score_to_add} PUNTOS.\n')
                    elif chat_result == 'PASO':
                        print(f'La palabra era {target_word}')
                    elif chat_result == 'SALIR':
                        return f'HAS SALIDO DEL JUEGO\nRESULTADOS : \n JUGADOR : {self.player_score} \n CPU : {self.cpu_score}'
                    elif chat_result == 'PISTA PROHIBIDA':
                        print('PISTA PROHIBIDA. NO SE SUMARÁN PUNTOS PARA ESTA CARTA.\n')
                    elif chat_result == 'MÁXIMO DE INTENTOS ALCANZADO':
                        print(f'La palabra era {target_word}')
                        print('MÁXIMO DE INTENTOS ALCANZADO. NO SE SUMARÁN PUNTOS PARA ESTA CARTA.\n')
                        
        return f'RESULTADOS : \n JUGADOR : {self.player_score} \n CPU : {self.cpu_score}'