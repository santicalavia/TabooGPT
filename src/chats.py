from autogen.agentchat import initiate_chats
from autogen import register_function
from agents import HintEvaluator, HintEvaluatorAssistant, HintGenerator, GuessEvaluator, GuessGenerator, GameHelper, Player
from evaluate_hint import evaluate_hint

class PlayerHintChat():
    """
    Handles the player's hint-giving phase in the game.

    Attributes:
        verbose (bool): Whether to print some chats for debugging purposes.
        target_word (str): The word the player is trying to guess.
        forbidden (list): A list of forbidden words for the hints.
        hint_evaluator_assistant (HintEvaluatorAssistant): Assistant to evaluate hints.
        hint_evaluator (HintEvaluator): Evaluates hints for validity.
        game_helper (GameHelper): Manages game-related communication.
        guess_evaluator (GuessEvaluator): Evaluates guesses for correctness.
        player (Player): Represents the player giving hints.
        guess_generator (GuessGenerator): Generates guesses based on hints.
    """
    def __init__(self, model : str, forbidden : list, target_word : str, verbose : bool):
        """
        Initializes the PlayerHintChat class with necessary game components.

        Args:
            model (str): The model used llm calls.
            forbidden (list): A list of forbidden words.
            target_word (str): The target word to guess.
            verbose (bool): Whether to print some chats for debugging purposes.
        """
        self.verbose = verbose
        self.target_word = target_word
        self.forbidden = forbidden
        self.hint_evaluator_assistant = HintEvaluatorAssistant(target_word, forbidden, model)
        self.hint_evaluator = HintEvaluator()
        self.game_helper = GameHelper()
        register_function(
            evaluate_hint,
            caller=self.hint_evaluator_assistant,  
            executor=self.hint_evaluator,  
            name="evaluate_hint",  
            description="Evaluar la pista"
        )
        self.guess_evaluator = GuessEvaluator(target_word, model)
        self.player = Player()
        self.guess_generator = GuessGenerator(model)

    def initiate_round(self) -> tuple:
        """
        Starts the player's hint-giving round.

        Returns (tuple): A string indicating the termination condition and the number of attempts made.
        """
        previous_hints = []
        previous_guesses = []
        terminate_condition = ''
        tries = 0
        while terminate_condition == '':
            chat_result = initiate_chats([
                        {
                            "sender": self.game_helper,
                            "recipient": self.player,
                            "message": "¡COMIENZA A DAR PISTAS!" if previous_hints == [] else f"DA OTRA PISTA\nPALABRA : {self.target_word}\nPALABRAS PROHIBIDAS : {', '.join(self.forbidden)}",
                            "max_turns": 1,
                            "summary_method": "last_msg",
                        },                      
                        {
                            "sender": self.hint_evaluator,
                            "recipient": self.hint_evaluator_assistant,
                            "message": "Esta es la pista:",
                            "max_turns": 2,
                            "summary_method": "last_msg",
                            "silent" : not self.verbose
                        },
                        {
                            "sender": self.game_helper,
                            "recipient": self.guess_generator,
                            "message": "Esta es la pista:" if previous_guesses == [] else "" ,
                            "max_turns": 1,
                            "carryover" :  "" if previous_guesses == [] else "Respuestas dadas hasta ahora:\n" + '\n'.join(previous_guesses) + "\nPistas generadas hasta ahora:\n" + '\n'.join(previous_hints),
                            "summary_method": "last_msg",
                            "silent" : not self.verbose
                        },
                        {
                            "sender": self.guess_generator,
                            "recipient": self.guess_evaluator,
                            "message": "Esta es la respuesta:",
                            "max_turns": 1,
                            "finished_chat_indexes_to_exclude_from_carryover" : [0],
                            "summary_method": "last_msg",
                        }
                    ])
            user_input = chat_result[0].summary
            agent_guess = chat_result[2].summary
            guess_evaluator_result = chat_result[-1].summary
            if user_input == 'PASO':
                terminate_condition = user_input
            elif user_input == 'SALIR':
                terminate_condition = user_input
            elif guess_evaluator_result == 'ACIERTO':
                terminate_condition = guess_evaluator_result
            elif 'PISTA PROHIBIDA' in guess_evaluator_result:
                terminate_condition = 'PISTA PROHIBIDA'
            previous_hints.append(user_input)
            previous_guesses.append(agent_guess)
            tries += 1
        return terminate_condition, tries
    
class PlayerGuessChat():
    """
    Handles the player's guessing phase in the game.

    Attributes:
        verbose (bool): Whether to print some chats for debugging purposes.
        hint_evaluator_assistant (HintEvaluatorAssistant): Assistant to evaluate hints.
        hint_evaluator (HintEvaluator): Evaluates hints for validity.
        game_helper (GameHelper): Manages game-related communication.
        hint_generator (HintGenerator): Generates hints for the player.
        guess_evaluator (GuessEvaluator): Evaluates guesses for correctness.
        player (Player): Represents the player making guesses.
    """
    def __init__(self, model : str, forbidden : list, target_word : str, verbose : bool):
        """
        Initializes the PlayerGuessChat class with necessary game components.

        Args:
            model (str): The model used for llm calls.
            forbidden (list): A list of forbidden words.
            target_word (str): The target word to guess.
            verbose (bool): Whether to print some chats for debugging purposes.
        """
        self.verbose = verbose
        self.hint_evaluator_assistant = HintEvaluatorAssistant(target_word, forbidden, model)
        self.hint_evaluator = HintEvaluator()
        self.game_helper = GameHelper()
        register_function(
            evaluate_hint,
            caller=self.hint_evaluator_assistant,  
            executor=self.hint_evaluator,  
            name="evaluate_hint",  
            description="Evaluar la pista"
        )
        self.hint_generator = HintGenerator(target_word, forbidden, model)
        self.guess_evaluator = GuessEvaluator(target_word, model)
        self.player = Player()
    
    def initiate_round(self) -> tuple:
        """
        Starts the player's guessing round.

        Returns (tuple): A string indicating the termination condition and the number of attempts made.
        """
        previous_hints = []
        terminate_condition = ''
        tries = 0
        while terminate_condition == '':
            chat_result = initiate_chats([
                                    {
                                        "sender": self.game_helper,
                                        "recipient": self.hint_generator,
                                        "message": "¡QUE COMIENCEN LAS PISTAS!" if previous_hints == [] else 'PISTAS ANTERIORES:\n' + '\n'.join(previous_hints),
                                        "max_turns": 1,
                                        "summary_method": "last_msg",
                                    },                      
                                    {
                                        "sender": self.hint_evaluator,
                                        "recipient": self.hint_evaluator_assistant,
                                        "message": "Esta es la pista:",
                                        "max_turns": 2,
                                        "summary_method": "last_msg",
                                        "silent" : not self.verbose
                                    }
                                    ])
            if chat_result[1].summary != 'PISTA PROHIBIDA':
                hint = chat_result[0].summary
                previous_hints.append(hint)
                chat_result = initiate_chats([
                                        {
                                            "sender": self.game_helper,
                                            "recipient": self.player,
                                            "message": "Estas son las pistas generadas hasta ahora:",
                                            "max_turns": 1,
                                            "carryover" : '\n'.join(previous_hints),
                                            "summary_method": "last_msg",
                                        },
                                        {
                                            "sender": self.game_helper,
                                            "recipient": self.guess_evaluator,
                                            "message": "Esta es la respuesta:",
                                            "max_turns": 1,
                                            "summary_method": "last_msg",
                                        }
                                    ])
                user_input = chat_result[0].summary
                guess_evaluator_result = chat_result[-1].summary
                if user_input == 'PASO':
                    terminate_condition = user_input
                elif user_input == 'SALIR':
                    terminate_condition = user_input
                elif guess_evaluator_result == 'ACIERTO':
                    terminate_condition = guess_evaluator_result
            else:
                terminate_condition = 'PISTA PROHIBIDA'
            tries += 1
            
        return terminate_condition, tries
    
class CpuChat():
    """
    Handles the CPU's turn in the game.

    Attributes:
        hint_evaluator_assistant (HintEvaluatorAssistant): Assistant to evaluate hints.
        hint_evaluator (HintEvaluator): Evaluates hints for validity.
        game_helper (GameHelper): Manages game-related communication.
        hint_generator (HintGenerator): Generates hints for the CPU.
        guess_evaluator (GuessEvaluator): Evaluates guesses for correctness.
        guess_generator (GuessGenerator): Generates guesses based on hints.
        verbose (bool): Whether to print some chats for debugging purposes.
    """
    def __init__(self, model : str, forbidden : list, target_word : str, verbose : bool):
        """
        Initializes the CpuChat class with necessary game components.

        Args:
            model (str): The model used for llm calls.
            forbidden (list): A list of forbidden words.
            target_word (str): The target word to guess.
            verbose (bool): Whether to print some chats for debugging purposes.
        """
        self.hint_evaluator_assistant = HintEvaluatorAssistant(target_word, forbidden, model)
        self.hint_evaluator = HintEvaluator()
        self.game_helper = GameHelper()
        self.verbose = verbose
        register_function(
            evaluate_hint,
            caller=self.hint_evaluator_assistant,  
            executor=self.hint_evaluator,  
            name="evaluate_hint",  
            description="Evaluar la pista"
        )
        self.hint_generator = HintGenerator(target_word, forbidden, model)
        self.guess_evaluator = GuessEvaluator(target_word, model)
        self.guess_generator = GuessGenerator(model)
    
    def initiate_round(self) -> tuple:
        """
        Starts the CPU's turn in the game.

        Returns (tuple): A string indicating the termination condition and the number of attempts made.
        """
        previous_hints = []
        previous_guesses = []
        terminate_condition = ''
        tries = 0
        while terminate_condition == '' and tries < 5:
            chat_result = initiate_chats([
                                    {
                                        "sender": self.game_helper,
                                        "recipient": self.hint_generator,
                                        "message": "¡QUE COMIENCEN LAS PISTAS!" if previous_hints == [] else 'PISTAS ANTERIORES:\n' + '\n'.join(previous_hints),
                                        "max_turns": 1,
                                        "summary_method": "last_msg",
                                    },                      
                                    {
                                        "sender": self.hint_evaluator,
                                        "recipient": self.hint_evaluator_assistant,
                                        "message": "Esta es la pista:",
                                        "max_turns": 2,
                                        "summary_method": "last_msg",
                                        "silent" : not self.verbose
                                    },
                                    {
                                        "sender": self.game_helper,
                                        "recipient": self.guess_generator,
                                        "message": "Esta es la pista:" if previous_guesses == [] else "" ,
                                        "max_turns": 1,
                                        "carryover" :  "" if previous_guesses == [] else "Respuestas dadas hasta ahora:\n" + '\n'.join(previous_guesses) + "\nPistas generadas hasta ahora:\n" + '\n'.join(previous_hints),
                                        "summary_method": "last_msg",
                                        "silent" : not self.verbose
                                    },
                                    {
                                        "sender": self.guess_generator,
                                        "recipient": self.guess_evaluator,
                                        "message": "Esta es la respuesta:",
                                        "max_turns": 1,
                                        "finished_chat_indexes_to_exclude_from_carryover" : [0],
                                        "summary_method": "last_msg",
                                    }
                                ])
            hint = chat_result[0].summary
            agent_guess = chat_result[2].summary
            guess_evaluator_result = chat_result[-1].summary
            if guess_evaluator_result == 'ACIERTO':
                terminate_condition = guess_evaluator_result
            elif 'PISTA PROHIBIDA' in guess_evaluator_result:
                terminate_condition = 'PISTA PROHIBIDA'
            previous_hints.append(hint)
            previous_guesses.append(agent_guess)
            tries+=1
        return terminate_condition, tries