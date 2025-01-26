import os
from autogen import ConversableAgent

class HintGenerator(ConversableAgent):
    """
    Generates hints for the Taboo game while adhering to specific constraints.
    
    Attributes:
        target_word (str): The target word that the player must guess.
        forbidden (list): A list of forbidden words that cannot be used in hints.
        model (str): The language model used for generating hints.
    """
    def __init__(self, target_word, forbidden, model):
        name = "Hint_Generator"
        system_message = f"""Eres una parte del juego de tabú. Tu misión es dar pistas para adivinar la palabra: {target_word}, sin usar ninguna palabra ni
                            derivados de las palabras de la siguiente lista: {",".join(forbidden)}. Si te proporcionan pistas que has dado anteriormente,
                            tenlas en cuenta para aportar información nueva. Sólo debes generar pistas basándote en los criterios. No des pistas de más de 15 palabras"""
        llm_config = {"config_list": [{"model": model, "api_key": os.environ["OPENAI_API_KEY"]}]}
        human_input_mode = "NEVER"
        super().__init__(name=name, system_message=system_message, llm_config=llm_config, human_input_mode=human_input_mode)

class HintEvaluatorAssistant(ConversableAgent):
    """
    Suggest evaluate_hint function call using the last hint given in the chat.
    
    Attributes:
        target_word (str): The target word that must not appear in hints.
        forbidden (list): A list of forbidden words and derivatives.
        model (str): The language model used for evaluation.
    """
    def __init__(self, target_word, forbidden, model):
        name="Hint_Evaluator_Assistant"
        system_message=f"""Tienes que recoger la última pista dada y analizarla con la función evaluate_hint, pasando como forbidden_words la 
                           lista {",".join(forbidden + [target_word])}"""
        llm_config={"config_list": [{"model": model, "api_key": os.environ["OPENAI_API_KEY"]}]}
        is_termination_msg=lambda msg: msg.get("content") is not None and msg["content"] == '' or "PISTA PROHIBIDA" in msg["content"] or "PASO" in msg["content"] or "SALIR" in msg["content"]
        human_input_mode="NEVER"
        super().__init__(name=name, system_message=system_message, llm_config=llm_config, is_termination_msg=is_termination_msg, human_input_mode=human_input_mode)

class HintEvaluator(ConversableAgent):
    """ Executor for the evaluate_hint call suggested by HintEvaluatorAssistant"""
    def __init__(self):
        name="Hint_Evaluator"
        llm_config=False
        human_input_mode="NEVER"
        super().__init__(name=name, llm_config=llm_config, human_input_mode=human_input_mode)

class GuessGenerator(ConversableAgent):
    """
    Generates guesses based on the hints provided during the game.
    
    Attributes:
        model (str): The language model used for generating guesses.
    """
    def __init__(self, model):
        name="Guess_Generator"
        system_message=f"""Eres una parte del juego de tabú. Tu misión es adivinar la palabra escuchando las pistas dadas por el otro jugador. 
                           No repitas ninguna de las respuestas dadas anteriormente. Contesta únicamente la palabra que quieras responder."""
        llm_config={"config_list": [{"model": model, "api_key": os.environ["OPENAI_API_KEY"]}]}
        is_termination_msg=lambda msg: msg.get("content") is not None and "PISTA PROHIBIDA" in msg["content"] or "PASO" in msg["content"] or "SALIR" in msg["content"]
        human_input_mode="NEVER"
        super().__init__(name=name, system_message=system_message, llm_config=llm_config, is_termination_msg=is_termination_msg, human_input_mode=human_input_mode)
        
class GuessEvaluator(ConversableAgent):
    """
    Evaluates guesses to determine if they match the target word.
    
    Attributes:
        target_word (str): The correct word to guess.
        model (str): The language model used for evaluation.
    """
    def __init__(self, target_word, model):
        name="Guess_Evaluator"
        system_message=f"""Eres una parte del juego de tabú. Tu misión es evaluar si el jugador ha adivinado la palabra correcta y contestar ACIERTO o NOK. 
                           Para evaluar si se ha acertado, la palabra debe ser la misma o significar exactamente lo mismo que la siguiente palabra: {target_word}
                           Solo puedes contestar "ACIERTO" o "NOK", tienes terminantemente prohibido contestar cualquier otra cosa."""
        llm_config={"config_list": [{"model": model, "temperature": 0, "api_key": os.environ["OPENAI_API_KEY"]}]}
        is_termination_msg=lambda msg: msg.get("content") is not None and "PISTA PROHIBIDA" in msg["content"] or "PASO" in msg["content"] or "SALIR" in msg["content"]
        human_input_mode="NEVER"
        super().__init__(name=name, system_message=system_message, llm_config=llm_config, is_termination_msg=is_termination_msg, human_input_mode=human_input_mode)
    
class GameHelper(ConversableAgent):
    """
    Facilitates the flow of the game by managing communication between agents.
    """
    def __init__(self):
        name="Game_Helper"
        llm_config=False
        human_input_mode="NEVER"
        super().__init__(name=name, llm_config=llm_config, human_input_mode=human_input_mode)

class Player(ConversableAgent):
    """
    Represents the human player in the game, allowing them to interact with the system.
    """
    def __init__(self):
        name="Player"
        human_input_mode="ALWAYS"
        super().__init__(name=name, human_input_mode=human_input_mode)
