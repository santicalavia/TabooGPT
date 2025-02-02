from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from .evaluate_hint import evaluate_hint
    
class HintGenerator(AssistantAgent):
    def __init__(self, target_word, forbidden, model_client):
        name = "Hint_Generator"
        system_message = f"""Eres una parte del juego de tabú. Tu misión es dar pistas para adivinar la palabra: {target_word}, sin usar ninguna palabra ni
                            derivados de las palabras de la siguiente lista: {",".join(forbidden)}. Si te proporcionan pistas que has dado anteriormente,
                            tenlas en cuenta para aportar información nueva. Sólo debes generar pistas basándote en los criterios. No des pistas de más de 15 palabras"""
        super().__init__(name=name, system_message=system_message, model_client=model_client)

class HintEvaluator(AssistantAgent):
    def __init__(self, target_word, forbidden, model_client):
        name="Hint_Evaluator"
        system_message=f"""Tienes que recoger el texto que te manden y analizarlo con la función evaluate_hint, pasando como forbidden_words la 
                           lista {",".join(forbidden + [target_word])}"""
        tools=[evaluate_hint]
        super().__init__(name=name, system_message=system_message, model_client=model_client, tools=tools)

class GuessGenerator(AssistantAgent):
    def __init__(self, model_client):
        name="Guess_Generator"
        system_message=f"""Eres una parte del juego de tabú. Tu misión es adivinar la palabra escuchando las pistas dadas por el otro jugador. 
                           No repitas ninguna de las respuestas dadas anteriormente. Contesta únicamente la palabra que quieras responder."""
        super().__init__(name=name, system_message=system_message, model_client=model_client)
        
class GuessEvaluator(AssistantAgent):
    def __init__(self, target_word, model_client):
        name="Guess_Evaluator"
        system_message=f"""Eres una parte del juego de tabú. Tu misión es evaluar si el jugador ha adivinado la palabra correcta y contestar'ACIERTO' o 'RESPUESTA INCORRECTA'. 
                           Para evaluar si se ha acertado, la palabra debe ser la misma o significar exactamente lo mismo que la siguiente palabra: {target_word}
                           Solo puedes contestar "ACIERTO" o "NOK", tienes terminantemente prohibido contestar cualquier otra cosa."""
        super().__init__(name=name, system_message=system_message, model_client=model_client)

class Player(UserProxyAgent):
    def __init__(self):
        name="Player"
        super().__init__(name=name, input_func=input)
