import os
from math import ceil
from collections import Counter
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import json

# ---------------- CONFIG ----------------
DATA_DIR = "data"
BASE_VECTORSTORE_DIR = "vectorstores"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
CHUNKS_PER_STORE = 900  

# ---------------- UTILS ----------------
def folder_size_mb(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return round(total / (1024 * 1024), 2)

def extract_keywords(text, k=8):
    stop = {"the","and","of","to","in","for","with","on","by","is","are"}
    words = [w.lower() for w in text.split() if w.isalpha() and w.lower() not in stop]
    return [w for w, _ in Counter(words).most_common(k)]

def generate_summary(text):
    sentences = text.split(".")
    return ". ".join(sentences[:3]).strip() + "."

def get_book_name_from_pdf(pdf_path):
    return os.path.splitext(os.path.basename(pdf_path))[0].replace("_", " ")

# ---------------- LOAD PDF ----------------
def load_pdf(pdf_path):
    return PyPDFLoader(pdf_path).load()

# ---------------- SPLIT + METADATA ----------------
def split_and_enrich(docs, book_name, pdf_path):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = splitter.split_documents(docs)

    sample_text = " ".join(c.page_content for c in chunks[:20])
    keywords = extract_keywords(sample_text)
    summary = generate_summary(sample_text)

    enriched_chunks = []
    for c in chunks:
        enriched_chunks.append(
            Document(
                page_content=c.page_content,
                metadata={
                    "book_name": book_name,
                    "keywords": keywords,
                    "summary": summary,
                    "page": c.metadata.get("page"),
                    "source": pdf_path
                }
            )
        )

    return enriched_chunks, keywords, summary

# ---------------- VECTOR STORES (900 chunks each) ----------------
def create_vectorstores(chunks, book_dir, book_name, pdf_path, keywords, summary):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    os.makedirs(book_dir, exist_ok=True)

    total_stores = ceil(len(chunks) / CHUNKS_PER_STORE)
    stats = []

    for i in range(total_stores):
        batch = chunks[i * CHUNKS_PER_STORE:(i + 1) * CHUNKS_PER_STORE]
        store_name = f"store_{i + 1}"
        store_path = os.path.join(book_dir, store_name)

        vectorstore = FAISS.from_documents(batch, embeddings)
        vectorstore.save_local(store_path)

        store_size_mb = folder_size_mb(store_path)

        # -------- STORE-LEVEL METADATA --------
        store_metadata = {
            "book_name": book_name,
            "store_name": store_name,
            "pdf_source": pdf_path,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "chunks_in_store": len(batch),
            "embedding_dimension": vectorstore.index.d,
            "storage_mb": store_size_mb,
            "context_summary": summary,
            "keywords": keywords
        }

        # save metadata.json inside the store folder
        with open(os.path.join(store_path, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(store_metadata, f, indent=2)

        stats.append(store_metadata)

    return stats


# ---------------- MAIN PIPELINE ----------------
def ingest_all_pdfs():
    results = []

    for filename in os.listdir(DATA_DIR):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(DATA_DIR, filename)
        book_name = get_book_name_from_pdf(pdf_path)

        print(f"\n📘 Processing: {book_name}")

        docs = load_pdf(pdf_path)
        chunks, keywords, summary = split_and_enrich(docs, book_name, pdf_path)

        book_vector_dir = os.path.join(BASE_VECTORSTORE_DIR, book_name.replace(" ", "_"))
        vectorstores = create_vectorstores(
            chunks,
            book_vector_dir,
            book_name,
            pdf_path,
            keywords,
            summary
        )

        results.append({
            "book_name": book_name,
            "pdf": pdf_path,
            "total_pages": len(docs),
            "total_chunks": len(chunks),
            "chunks_per_store": CHUNKS_PER_STORE,
            "total_vectorstores": len(vectorstores),
            "keywords": keywords,
            "summary": summary,
            "vectorstores": vectorstores
        })

    return results

# ---------------- RUN ----------------
if __name__ == "__main__":
    all_books = ingest_all_pdfs()

    print("\n📚 FINAL INGESTION REPORT\n" + "=" * 50)
    for book in all_books:
        print(f"\n📘 {book['book_name']}")
        print(f"Pages              : {book['total_pages']}")
        print(f"Chunks             : {book['total_chunks']}")
        print(f"Vectorstores       : {book['total_vectorstores']}")
        print(f"Keywords           : {book['keywords']}")
        print(f"Summary            : {book['summary'][:120]}...")
        for vs in book["vectorstores"]:
            print(f"  ➜ {vs}")
