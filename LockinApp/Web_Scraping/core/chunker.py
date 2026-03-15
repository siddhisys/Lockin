import nltk # type: ignore
from nltk.tokenize import sent_tokenize # type: ignore
from config.settings import SENTENCES_PER_CHUNK

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt")

def chunk_text(text):
    sentences = sent_tokenize(text)
    chunks = []

    for i in range(0, len(sentences), SENTENCES_PER_CHUNK):
        chunk = " ".join(sentences[i:i + SENTENCES_PER_CHUNK])
        if len(chunk) > 40:
            chunks.append(chunk)

    return chunks
