from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from .evaluate_hint import evaluate_hint
    
class HintGenerator(AssistantAgent):
    """
    An agent responsible for generating hints in the Taboo game.

    This agent provides hints to help another player guess the target word 
    while avoiding the use of forbidden words and their derivatives. 
    It must also ensure that it does not repeat previously provided information 
    and generates concise hints.

    Attributes:
        target_word (str): The word the player needs to guess.
        forbidden (list[str]): A list of forbidden words that cannot be used in the hints.
        model_client (OpenAIChatCompletionClient): The language model client used to generate responses.
    """
    def __init__(self, target_word : str, forbidden : list, model_client : OpenAIChatCompletionClient):
        name = "Hint_Generator"
        system_message = f"""Eres una parte del juego de tabú. Tu misión es dar pistas para adivinar la palabra: {target_word}, sin usar ninguna palabra ni
                            derivados de las palabras de la siguiente lista: {",".join(forbidden)}. Si te proporcionan pistas que has dado anteriormente,
                            tenlas en cuenta para aportar información nueva. Sólo debes generar pistas basándote en los criterios. No des pistas de más de 15 palabras"""
        super().__init__(name=name, system_message=system_message, model_client=model_client)

class HintEvaluator(AssistantAgent):
    """
    An agent responsible for evaluating hints in the Taboo game.

    This agent receives a hint and analyzes it using the `evaluate_hint` function 
    to determine whether forbidden words were used or if the hint is valid.

    Attributes:
        target_word (str): The target word that players are trying to guess.
        forbidden (list): A list of forbidden words that cannot appear in hints.
        model_client (OpenAIChatCompletionClient): The language model client used to evaluate hints.
    """
    def __init__(self, target_word : str, forbidden : list, model_client : OpenAIChatCompletionClient):
        name="Hint_Evaluator"
        system_message=f"""Tienes que recoger el texto que te manden y analizarlo con la función evaluate_hint, pasando como forbidden_words la 
                           lista {",".join(forbidden + [target_word])}"""
        tools=[evaluate_hint]
        super().__init__(name=name, system_message=system_message, model_client=model_client, tools=tools)

class GuessGenerator(AssistantAgent):
    """
    An agent responsible for generating guesses in the Taboo game.

    This agent listens to the hints provided by another player and tries to guess the target word.
    It must avoid repeating previous guesses and respond with a single word only.

    Attributes:
        model_client (OpenAIChatCompletionClient): The language model client used to generate guesses.
    """
    def __init__(self, model_client : OpenAIChatCompletionClient):
        name="Guess_Generator"
        system_message=f"""Eres una parte del juego de tabú. Tu misión es adivinar la palabra escuchando las pistas dadas por el otro jugador. 
                           No repitas ninguna de las respuestas dadas anteriormente. Contesta únicamente la palabra que quieras responder."""
        super().__init__(name=name, system_message=system_message, model_client=model_client)
        
class GuessEvaluator(AssistantAgent):
    """
    An agent responsible for evaluating guesses in the Taboo game.

    This agent checks whether the player's guess is correct or incorrect.
    The guess must either exactly match or mean the same as the target word.
    It can only respond with "ACIERTO" (CORRECT) or "NOK" (INCORRECT).

    Attributes:
        target_word (str): The target word the player must guess.
        model_client (OpenAIChatCompletionClient): The language model client used to evaluate the guesses.
    """
    def __init__(self, target_word : str, model_client : OpenAIChatCompletionClient):
        name="Guess_Evaluator"
        system_message=f"""Eres una parte del juego de tabú. Tu misión es evaluar si el jugador ha adivinado la palabra correcta y contestar'ACIERTO' o 'RESPUESTA INCORRECTA'. 
                           Para evaluar si se ha acertado, la palabra debe ser la misma o significar exactamente lo mismo que la siguiente palabra: {target_word}
                           Solo puedes contestar "ACIERTO" o "NOK", tienes terminantemente prohibido contestar cualquier otra cosa."""
        super().__init__(name=name, system_message=system_message, model_client=model_client)

class Player(UserProxyAgent):
    """
    Represents the human player in the Taboo game.

    This agent acts as an intermediary between the user and the system, 
    allowing the human player to interact with the AI agents.

    Attributes:
        name (str): The name of the agent representing the player.
    """
    def __init__(self):
        name="Player"
        super().__init__(name=name, input_func=input)
