import os
import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from .agents import HintEvaluator, HintGenerator, GuessEvaluator, GuessGenerator, Player

async def assistant_run(agent : AssistantAgent, text_message : TextMessage) -> Response:
    """
    Runs an assistant agent with the given message.
    This function sends a message to an AssistantAgent and retrieves its response.

    Args:
        agent (AssistantAgent): The assistant agent that processes the message.
        text_message (TextMessage): The message to be processed.

    Returns:
        response (Response): The agent's response message.
    """
    response = await agent.on_messages([text_message], cancellation_token=CancellationToken())
    print(f'{response.chat_message.source} : {response.chat_message.content}')
    return response

async def user_proxy_run(agent : UserProxyAgent, text_message : TextMessage) -> Response:
    """
    Runs a user proxy agent asynchronously.
    This function sends a message to a UserProxyAgent and retrieves its response.

    Args:
        agent (UserProxyAgent): The user proxy agent that processes the message.
        text_message (TextMessage): The message to be processed.

    Returns:
        response (Response): The agent's response message.
    """
    response = await asyncio.create_task(
        agent.on_messages([text_message], cancellation_token=CancellationToken())
    )
    return response

class PlayerHintChat():
    """
    Handles the game round where the player gives hints.

    This class manages interactions between the player, hint evaluator,
    guess generator, and guess evaluator.

    Attributes:
        model (str): The language model used for OpenAI API calls.
        forbidden (list): A list of forbidden words in the game.
        target_word (str): The word to be guessed.
        hint_evaluator (HintEvaluator): Evaluates whether the hint follows the rules.
        guess_generator (GuessGenerator): Generates a guess based on hints.
        guess_evaluator (GuessEvaluator): Evaluates whether the guess is correct.
        player (Player): Represents the user playing the game.
    """
    def __init__(self, model : str, forbidden : list, target_word : str):
        self.target_word = target_word
        self.forbidden = forbidden
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
        Starts a round where the player gives hints, and the AI evaluates them.

        Returns:
            tuple: The result of the round and the number of attempts.
        """
        tries = 1
        while tries <= 10:
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
        return 'MÁXIMO DE INTENTOS ALCANZADO', tries
    
class PlayerGuessChat():
    """
    Handles the game round where the player makes guesses.
    This class manages interactions between the hint generator, hint evaluator,
    and guess evaluator.

    Attributes:
        model (str): The language model used for OpenAI API calls.
        forbidden (list): A list of forbidden words in the game.
        target_word (str): The word to be guessed.
        hint_generator (HintGenerator): Generates hints for the player.
        hint_evaluator (HintEvaluator): Evaluates whether the hint follows the rules.
        guess_evaluator (GuessEvaluator): Evaluates whether the guess is correct.
        player (Player): Represents the user playing the game.
    """
    def __init__(self, model : str, forbidden : list, target_word : str):

        self.target_word = target_word
        self.forbidden = forbidden
        self.hint_generator = HintGenerator(target_word, forbidden, OpenAIChatCompletionClient(model=model, 
                                                                                               api_key=os.environ['OPENAI_API_KEY']))
        self.hint_evaluator = HintEvaluator(target_word, forbidden,  OpenAIChatCompletionClient(model=model, 
                                                                                                api_key=os.environ['OPENAI_API_KEY'],
                                                                                                temperature=0))
        self.guess_evaluator = GuessEvaluator(target_word,  OpenAIChatCompletionClient(model=model, 
                                                                                       api_key=os.environ['OPENAI_API_KEY'],
                                                                                       temperature=0))
        self.player = Player()
    
    async def initiate_round(self) -> tuple:
        """
        Starts a round where the AI gives hints, and the player makes guesses.

        Returns:
            tuple: The result of the round and the number of attempts.
        """
        tries = 1
        hints = []
        while tries <= 10:
            assistant_hint = await assistant_run(self.hint_generator, TextMessage(content="Da una pista.", source="system"))
            hint_evaluation = await assistant_run(self.hint_evaluator, assistant_hint.chat_message)
            await self.hint_evaluator.on_reset(CancellationToken())
            if hint_evaluation.chat_message.content == 'PISTA PROHIBIDA':
                return hint_evaluation.chat_message.content, tries
            hints.append(f"- {assistant_hint.chat_message.content}")
            print(f'Pistas dadas hasta ahora:\n' + "\n".join(hints))
            user_guess = await user_proxy_run(self.player, assistant_hint.chat_message)
            if user_guess.chat_message.content == 'PASO' or user_guess.chat_message.content == 'SALIR':
                return user_guess.chat_message.content, tries
            guess_evaluation = await assistant_run(self.guess_evaluator, user_guess.chat_message)
            await self.guess_evaluator.on_reset(CancellationToken())
            if guess_evaluation.chat_message.content == 'ACIERTO':
                return guess_evaluation.chat_message.content, tries 
            tries += 1
        return 'MÁXIMO DE INTENTOS ALCANZADO', tries
    
class CpuChat():
    """
    Handles a game round where both hint generation and guessing are automated.
    This class manages interactions between the hint generator, hint evaluator,
    guess generator, and guess evaluator.

    Attributes:
        model (str): The language model used for OpenAI API calls.
        forbidden (list): A list of forbidden words in the game.
        target_word (str): The word to be guessed.
        hint_generator (HintGenerator): Generates hints.
        hint_evaluator (HintEvaluator): Evaluates whether the hint follows the rules.
        guess_generator (GuessGenerator): Generates guesses based on hints.
        guess_evaluator (GuessEvaluator): Evaluates whether the guess is correct.
    """
    def __init__(self, model : str, forbidden : list, target_word : str):

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
    
    async def initiate_round(self) -> tuple:
        """
        Starts a fully automated game round where AI generates hints and guesses.

        Returns:
            tuple: The result of the round and the number of attempts.
        """
        tries = 1
        hints = []
        while tries <= 10:
            assistant_hint = await assistant_run(self.hint_generator, TextMessage(content="Da una pista.", source="system"))
            hint_evaluation = await assistant_run(self.hint_evaluator, assistant_hint.chat_message)
            await self.hint_evaluator.on_reset(CancellationToken())
            if hint_evaluation.chat_message.content == 'PISTA PROHIBIDA':
                return hint_evaluation.chat_message.content, tries
            hints.append(f"- {assistant_hint.chat_message.content}")
            print(f'Pistas dadas hasta ahora:\n' + "\n".join(hints))
            generated_guess = await assistant_run(self.guess_generator, assistant_hint.chat_message)
            guess_evaluation = await assistant_run(self.guess_evaluator, generated_guess.chat_message)
            await self.guess_evaluator.on_reset(CancellationToken())
            if guess_evaluation.chat_message.content == 'ACIERTO':
                return guess_evaluation.chat_message.content, tries 
            tries += 1
        return 'MÁXIMO DE INTENTOS ALCANZADO', tries