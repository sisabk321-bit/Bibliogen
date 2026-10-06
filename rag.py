import os
from pathlib import Path
import chromadb
from openai import OpenAI
from database import get_all_books

CHROMA_PATH = Path("chroma_db")
COLLECTION_NAME = "bibliogen_books"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-5-mini"

class BibliogenRAG:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key: raise ValueError("لم يتم العثور على OpenAI API Key.")
        self.client = OpenAI(api_key=self.api_key)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    @staticmethod
    def book_to_text(book):
        return f"""العنوان: {book.get('title','')}
المؤلف: {book.get('author','')}
الناشر: {book.get('publisher','')}
سنة النشر: {book.get('publication_year','')}
الموضوع: {book.get('subject','')}
ISBN: {book.get('isbn','')}
اللغة: {book.get('language','')}
نوع المورد: {book.get('resource_type','')}
الكلمات المفتاحية: {book.get('keywords','')}""".strip()

    def create_embedding(self, text):
        r = self.client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return r.data[0].embedding

    def index_book(self, book):
        text = self.book_to_text(book)
        emb = self.create_embedding(text)
        meta = {k:str(book.get(k,"")) for k in
                ["title","author","publisher","subject","isbn","language","resource_type","keywords"]}
        meta["publication_year"] = int(book.get("publication_year") or 0)
        self.collection.upsert(ids=[str(book["id"])], documents=[text],
                               embeddings=[emb], metadatas=[meta])

    def index_all_books(self):
        books = get_all_books()
        for b in books: self.index_book(b)
        return len(books)

    def vector_count(self): return self.collection.count()

    def search(self, query, n_results=5):
        emb = self.create_embedding(query)
        return self.collection.query(query_embeddings=[emb], n_results=n_results,
                                     include=["documents","metadatas","distances"])

    def build_context(self, results):
        docs = results.get("documents",[[]])[0]
        metas = results.get("metadatas",[[]])[0]
        parts=[]
        for i,doc in enumerate(docs):
            m = metas[i] if i < len(metas) else {}
            parts.append(f"""المصدر رقم {i+1}
العنوان: {m.get('title','')}
المؤلف: {m.get('author','')}
الناشر: {m.get('publisher','')}
سنة النشر: {m.get('publication_year','')}
الموضوع: {m.get('subject','')}
نوع المورد: {m.get('resource_type','')}
المحتوى:
{doc}""")
        return "\n\n".join(parts)

    def answer(self, question, n_results=5):
        results = self.search(question, n_results)
        context = self.build_context(results)
        instructions = """أنت المساعد الذكي لتطبيق Bibliogen لاسترجاع المعلومات الببليوغرافية.
أجب اعتمادًا على المصادر المسترجعة فقط. لا تخترع معلومات.
إذا لم تكن المعلومات كافية فقل: لم أجد معلومات كافية في قاعدة بيانات المكتبة.
أجب بالعربية بوضوح واختصار."""
        prompt = f"السؤال:\n{question}\n\nالمصادر المسترجعة:\n{context}"
        r = self.client.responses.create(model=CHAT_MODEL, instructions=instructions, input=prompt)
        return {"answer":r.output_text, "results":results, "context":context}
