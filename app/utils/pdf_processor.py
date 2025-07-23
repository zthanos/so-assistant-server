import fitz  # PyMuPDF
import re

def clean_text(text):
    # Αφαιρούμε control chars, null bytes, περίεργα σύμβολα
    text = text.replace('\x00', ' ')
    text = re.sub(r'[^\x20-\x7E\n\r]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_into_chunks(text, max_length=1000):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) <= max_length:
            current += " " + sentence
        else:
            if current:
                chunks.append(current.strip())
            current = sentence
    if current:
        chunks.append(current.strip())
    return chunks

def process_pdf(pdf_path, max_chunk_length=1000):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    cleaned_text = clean_text(full_text)
    if not cleaned_text:
        return []
    chunks = split_into_chunks(cleaned_text, max_chunk_length)
    return chunks
