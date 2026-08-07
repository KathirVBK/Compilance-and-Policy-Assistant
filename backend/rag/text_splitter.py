import re
from backend.utils.logger import Logger

def recursive_split(text: str, separators: list, chunk_size: int, overlap: int) -> list:
    """Recursively splits text using the provided list of separators."""
    final_chunks = []
    
    if len(text) <= chunk_size:
        return [text]
        
    separator = separators[-1] if separators else ""
    for sep in separators:
        if sep == "":
            separator = sep
            break
        if sep in text:
            separator = sep
            break
            
    if separator:
        splits = text.split(separator)
    else:
        splits = list(text)
        
    good_splits = [s for s in splits if s]
            
    current_chunk = []
    current_length = 0
    
    for split in good_splits:
        if len(split) > chunk_size and len(separators) > 1:
            if current_chunk:
                final_chunks.append(separator.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            sub_chunks = recursive_split(split, separators[1:], chunk_size, overlap)
            final_chunks.extend(sub_chunks)
            continue
            
        if current_length + len(split) + (len(separator) if current_chunk else 0) > chunk_size:
            if current_chunk:
                joined = separator.join(current_chunk)
                final_chunks.append(joined)
                
                while current_length > overlap and len(current_chunk) > 1:
                    popped = current_chunk.pop(0)
                    current_length -= len(popped) + len(separator)
                    
            if not current_chunk or current_length + len(split) + (len(separator) if current_chunk else 0) > chunk_size:
                current_chunk = [split]
                current_length = len(split)
            else:
                current_chunk.append(split)
                current_length += len(split) + len(separator)
        else:
            current_chunk.append(split)
            current_length += len(split) + (len(separator) if current_chunk else 0)
            
    if current_chunk:
        joined = separator.join(current_chunk)
        final_chunks.append(joined)
        
    return final_chunks

def split_text(text, chunk_size=800, overlap=150):
    """
    Splits document text into chunks using RecursiveCharacterTextSplitter logic.
    Separators: ["\n\n", "\n", " ", ""]
    """
    separators = ["\n\n", "\n", " ", ""]
    
    Logger.info("Splitting text using RecursiveCharacterTextSplitter logic...")
    raw_chunks = recursive_split(text, separators, chunk_size, overlap)
    
    chunks = []
    for chunk_text in raw_chunks:
        clean_text = chunk_text.strip()
        if len(clean_text) > 30:
            chunks.append({
                'text': clean_text,
                'section': 'Extracted Section',
                'page': 1
            })
            
    Logger.info(f"Split document into {len(chunks)} chunks.")
    return chunks
