import os
import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from .agents import HintEvaluator, HintGenerator, GuessEvaluator, GuessGenerator, Player

async def assistant_run(agent : AssistantAgent, text_message : TextMessage) -> None:
    response = await agent.on_messages([text_message], cancellation_token=CancellationToken())
    print(f'{response.chat_message.source} : {response.chat_message.content}')
    return response

async def user_proxy_run(agent : UserProxyAgent, text_message : TextMessage):
    response = await asyncio.create_task(
        agent.on_messages([text_message], cancellation_token=CancellationToken())
    )
    return response

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
        self.hint_generator = HintGenerator(target_word, forbidden, OpenAIChatCompletionClient(model=model, 
                                                                                               api_key=os.environ['OPENAI_API_KEY']))
        self.hint_evaluator = HintEvaluator(target_word, forbidden,  OpenAIChatCompletionClient(model=model, 
                                                                                                api_key=os.environ['OPENAI_API_KEY'],
                                                                                                temperature=0))
        self.guess_generator = GuessGenerator(OpenAIChatCompletionClient(model=model, 
                                                                         api_key=os.environ['OPENAI_API_KEY']))
        self.guess_evaluator = GuessEvaluator(target_word,  OpenAIChatCompletionClient(model=model, 
                                                                                       api_key=os.environ['OPENAI_API_KEY'],
                                                                                       temperature=0))
        self.player = Player()


    async def initiate_round(self) -> tuple:
        """
        Starts the player's hint-giving round.

        Returns (tuple): A string indicating the termination condition and the number of attempts made.
        """
        tries = 0
        while tries < 10:
            user_hint = await user_proxy_run(self.player, TextMessage(content="start", source="system"))
            if user_hint.chat_message.content == 'PASO' or user_hint.chat_message.content == 'SALIR':
                return user_hint.chat_message.content, tries
            hint_evaluation = await assistant_run(self.hint_evaluator, user_hint.chat_message)
            await self.hint_evaluator.on_reset(CancellationToken())
            if hint_evaluation.chat_message.content == 'PISTA PROHIBIDA':
                return hint_evaluation.chat_message.content, tries
            generated_guess = await assistant_run(self.guess_generator, user_hint.chat_message)
            guess_evaluation = await assistant_run(self.guess_evaluator, generated_guess.chat_message)
            await self.guess_evaluator.on_reset(CancellationToken())
            if guess_evaluation.chat_message.content == 'ACIERTO':
                return guess_evaluation.chat_message.content, tries 
            tries += 1
    
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