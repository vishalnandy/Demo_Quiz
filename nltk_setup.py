import nltk

nltk.data.path.append('C:\\Users\\vishal.nandy\\AppData\\Roaming\\nltk_data')

nltk.download('wordnet')
nltk.download('punkt', force=True)
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('omw-1.4')
nltk.download('punkt_tab')



print("heelo NLTK Vishal", nltk.data.path)

from nltk.tokenize import word_tokenize

text = "This is a test sentence."
tokens = word_tokenize(text)
print(tokens)