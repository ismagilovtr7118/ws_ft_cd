import fasttext
import fasttext.util

class FT_class(object):
    ft = ''
    def __init__(self, model_fn):
        self.ft = fasttext.load_model(model_fn)

    def give_a_vector(self, text):
        vect = self.ft.get_sentence_vector(text)
        return vect

if __name__ == "__main__":
    ft = FT_class('../../models/model_FT.bin')
    while True:
        text = input()
        print (ft.give_a_vector(text))
    
