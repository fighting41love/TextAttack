import textattack.utils as utils
import torch

from textattack.tokenizers import BERTTokenizer
from transformers.modeling_bert import BertForSequenceClassification


class BERTForClassification:
    """ 
    BERT fine-tuned for sentiment classification. 

    Args:
        max_seq_length(:obj:`string`): Path to the pre-trained model.
        max_seq_length(:obj:`int`, optional):  Number of class labels for 
            prediction, if different than 2.
        max_seq_length(:obj:`int`, optional):  Maximum length of a sequence after tokenizing.
            Defaults to 32.
            
    """
    def __init__(self, model_relative_path, num_labels=2):
        model_file_path = utils.download_if_needed(model_relative_path)
        print('TextAttack BERTForClassification Loading from path', model_file_path)
        self.model = BertForSequenceClassification.from_pretrained(
            model_file_path, num_labels=num_labels)
        self.model.to(utils.get_device())
        self.model.eval()
        self.tokenizer = BERTTokenizer(model_file_path)
    
    def __call__(self, text_ids):
        if not isinstance(text_ids, torch.Tensor):
            raise TypeError(f'Object of type {type(text_ids)} must be of type ' 
                'torch.tensor')
        with torch.no_grad():
            pred = self.model(text_ids)[0]
        return torch.nn.functional.softmax(pred, dim=-1)
