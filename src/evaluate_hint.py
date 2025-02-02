from functools import lru_cache
import unicodedata
import spacy

def lev_dist(a : str, b : str) -> int:
    '''
    This function will calculate the levenshtein distance between two input
    strings a and b
    
    params:
        a (str) : The first string you want to compare
        b (str) : The second string you want to compare
        
    returns (int): The distance between string a and b.
        
    example:
        a = 'stamp'
        b = 'stomp'
        lev_dist(a,b)
        >> 1.0
    '''
    
    @lru_cache(None)  # for memorization
    def min_dist(s1, s2):

        if s1 == len(a) or s2 == len(b):
            return len(a) - s1 + len(b) - s2

        # no change required
        if a[s1] == b[s2]:
            return min_dist(s1 + 1, s2 + 1)

        return 1 + min(
            min_dist(s1, s2 + 1),      # insert character
            min_dist(s1 + 1, s2),      # delete character
            min_dist(s1 + 1, s2 + 1),  # replace character
        )

    return min_dist(0, 0)

def remove_accents_and_non_alphanumeric(word: str) -> str:
    """
    Removes accents and any character that is not a letter or a number from a word or text.
    
    :param word (str): A string with accented characters and/or non-alphanumeric characters.
    :return (str): A string without accented characters or non-alphanumeric characters.
    """
    return ''.join(
        char for char in unicodedata.normalize('NFD', word)
        if unicodedata.category(char) != 'Mn' and char.isalnum()
    )

def extract_main_words(sentence : str) -> list:
    """
    Extracts the main words from a sentence by filtering out less significant parts of speech using Spacy model for spanish language.
    
    Args:
        sentence (str): The input sentence from which main words are extracted.
    
    Returns (list): A list of main words from the sentence, excluding determiners, prepositions, conjunctions, 
              auxiliary verbs, pronouns, adverbs, punctuation, and similar tokens.
    """
    spacy_nlp = spacy.load("es_core_news_sm")
    doc = spacy_nlp(sentence)
    # Filter main words
    main_words = [token.text for token in doc if token.pos_ not in {"DET", "ADP", "CONJ", "SCONJ", "PUNCT", "AUX", "PRON", "ADV"}]
    return main_words

def is_contained(w1 : str, w2 : str) -> bool:
    """
    Checks if one word is contained within another based on specific length and substring rules.
    
    Args:
        w1 (str): The first word to compare.
        w2 (str): The second word to compare.
    
    Returns (bool): True if one word is contained within the other based on the following rules:
                    - If the smaller word is 4 characters long, it must be a direct substring of the larger word.
                    - If the smaller word is longer than 4 characters, it must match the larger word except for the last character.
                    - Otherwise, returns False.
    """
    if len(w1)>=len(w2):
        larger_word = w1
        smaller_word = w2
    else:
        larger_word = w2
        smaller_word = w1
    if len(smaller_word)<=3:
        return False
    if len(smaller_word)==4 and smaller_word in larger_word:
        return True
    if len(smaller_word)>4 and smaller_word[:-1] in larger_word:
        return True
    else:
        return False
    
def evaluate_hint(forbidden_words : list, hint : str) -> str:
    """
    Evaluates whether a hint violates the rules by containing forbidden words or similar terms.
    
    Args:
        forbidden_words (list): A list of forbidden words or phrases.
        hint (str): The hint to be evaluated.
    
    Returns:
        str: Returns 'PISTA PROHIBIDA' if the hint contains or closely resembles any forbidden word,
             otherwise returns an empty string.
    """
    hint_main_words = extract_main_words(hint)
    for fw in forbidden_words:
        for word in fw.split(' '): # just in case a forbidden word is a compound word 
            word = word.lower()
            word = remove_accents_and_non_alphanumeric(word)
            for hmw in hint_main_words:
                hmw = hmw.lower()
                hmw = remove_accents_and_non_alphanumeric(hmw)
                # Evaluates if one word is contained in the other
                if is_contained(word,hmw):
                    return 'PISTA PROHIBIDA'
                # Evaluates similarity using Levenshtein distance
                elif lev_dist(word, hmw) <= 1:
                    return 'PISTA PROHIBIDA'
    return 'OK' 