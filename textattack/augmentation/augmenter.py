import random
import tqdm

from textattack.constraints.pre_transformation import PreTransformationConstraint
from textattack.shared import TokenizedText

class Augmenter:
    """ 
    A class for performing data augmentation using TextAttack.
    
    Returns all possible transformations for a given string. Currently only 
        supports transformations which are word swaps.
    
    Args:
        transformation (textattack.Transformation): the transformation
            that suggests new texts from an input.
        constraints: (list(textattack.Constraint)): constraints
            that each transformation must meet
        num_words_to_swap: (int): Number of words to swap per augmented example
        transformations_per_example: (int): Maximum number of augmentations
            per input
    """
    def __init__(self, transformation, constraints=[], num_words_to_swap=1, 
        transformations_per_example=1):
        self.transformation = transformation
        self.num_words_to_swap = num_words_to_swap
        self.transformations_per_example = transformations_per_example
        
        self.constraints = []
        self.pre_transformation_constraints = []
        for constraint in constraints:
            if isinstance(constraint, PreTransformationConstraint):
                self.pre_transformation_constraints.append(constraint)
            else:
                self.constraints.append(constraint)
    
    def _filter_transformations(self, transformed_texts, current_text, original_text):
        """ 
        Filters a list of ``TokenizedText`` objects to include only the ones 
        that pass ``self.constraints``.
        """
        for C in self.constraints:
            if len(transformed_texts) == 0: break
            transformed_texts = C.call_many(transformed_texts, current_text, original_text=original_text)
        return transformed_texts
    
    def augment(self, text):
        """ 
        Returns all possible augmentations of ``text`` according to 
        ``self.transformation``.
        """
        tokenized_text = TokenizedText(text, DummyTokenizer())
        original_text = tokenized_text
        all_transformed_texts = set()
        for _ in range(self.transformations_per_example):
            index_order = list(range(len(tokenized_text.words)))
            random.shuffle(index_order)
            current_text = tokenized_text
            words_swapped = 0
            for i in index_order:
                transformed_texts = self.transformation(current_text, 
                                    self.pre_transformation_constraints, [i])
                # Get rid of transformations we already have
                transformed_texts = [t for t in transformed_texts if t not in all_transformed_texts]
                # Filter out transformations that don't match the constraints.
                transformed_texts = self._filter_transformations(transformed_texts, current_text,
                                    original_text)
                if not len(transformed_texts):
                    continue
                current_text = random.choice(transformed_texts)
                words_swapped += 1
                if words_swapped == self.num_words_to_swap:
                    break
            all_transformed_texts.add(current_text)
        return [t.clean_text() for t in all_transformed_texts]
    
    def augment_many(self, text_list, show_progress=False):
        """
        Returns all possible augmentations of a list of strings according to
        ``self.transformation``.
    
        Args:
            text_list (list(string)): a list of strings for data augmentation
            
        Returns a list(string) of augmented texts.
        """
        if show_progress:
            text_list = tqdm.tqdm(text_list, desc='Augmenting data...')
        return [self.augment(text) for text in text_list]
        
    def augment_text_with_ids(self, text_list, id_list, show_progress=True):
        """ 
        Supplements a list of text with more text data. Returns the augmented
        text along with the corresponding IDs for each augmented example.
        """
        if len(text_list) != len(id_list):
            raise ValueError('List of text must be same length as list of IDs')
        if self.transformations_per_example == 0:
            return text_list, id_list
        all_text_list = []
        all_id_list = []
        if show_progress:
            text_list = tqdm.tqdm(text_list, desc='Augmenting data...')
        for text, _id in zip(text_list, id_list):
            all_text_list.append(text)
            all_id_list.append(_id)
            augmented_texts = self.augment(text)
            all_text_list.extend
            all_text_list.extend([text] + augmented_texts)
            all_id_list.extend([_id] * (1 + len(augmented_texts)))
        return all_text_list, all_id_list
        
class DummyTokenizer:
    """ 
    A dummy tokenizer class. Data augmentation applies a transformation
    without querying a model, which means that tokenization is unnecessary.
    In this case, we pass a dummy tokenizer to `TokenizedText`. 
    """
    def encode(self, _):
        return []
