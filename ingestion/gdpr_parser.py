"""
GDPR Ingestion Parser & Atomic Requirement Extractor
Parses the official condensed GDPR reference PDF, splits text into 11 Chapters & 99 Articles,
generates atomic requirements (REQ-001..REQ-N) with vector embeddings,
and stores them in Supabase & local JSON cache.
"""

import os
import json
import re
import math
import pymupdf as fitz
from db.supabase_client import supabase_db
from config import config

# Optional SentenceTransformer with fallback vector generator
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("[INFO] sentence_transformers not installed yet. Using fallback lightweight vector embedder.")

# GDPR Chapter Taxonomy Reference Map
GDPR_CHAPTER_MAP = {
    "I": {"title": "General provisions", "articles": list(range(1, 5))},
    "II": {"title": "Principles", "articles": list(range(5, 12))},
    "III": {"title": "Rights of the data subject", "articles": list(range(12, 24))},
    "IV": {"title": "Controller and processor", "articles": list(range(24, 44))},
    "V": {"title": "Transfers of personal data to third countries or international organisations", "articles": list(range(44, 51))},
    "VI": {"title": "Independent supervisory authorities", "articles": list(range(51, 60))},
    "VII": {"title": "Cooperation and consistency", "articles": list(range(60, 77))},
    "VIII": {"title": "Remedies, liability and penalties", "articles": list(range(77, 85))},
    "IX": {"title": "Provisions relating to specific processing situations", "articles": list(range(85, 91))},
    "X": {"title": "Delegated and implementing acts", "articles": list(range(91, 94))},
    "XI": {"title": "Final provisions", "articles": list(range(94, 100))}
}

def get_chapter_for_article(article_num: int) -> tuple:
    """Returns (chapter_roman, chapter_title) for a given article number."""
    for ch_num, ch_info in GDPR_CHAPTER_MAP.items():
        if article_num in ch_info["articles"]:
            return ch_num, ch_info["title"]
    return "XI", "Final provisions"

class LightweightEmbedder:
    """Fallback 384-dim normalized vector generator for zero-dependency execution."""
    def __init__(self, dim=384):
        self.dim = dim

    def encode(self, text: str) -> list:
        vec = [0.0] * self.dim
        for i, char in enumerate(text):
            idx = (ord(char) * (i + 1) * 31) % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

class GDPRParser:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                print(f"[INFO] Loading embedding model: {self.model_name}...")
                self.embedder = SentenceTransformer(self.model_name)
                print("[INFO] Embedding model loaded successfully.")
            except Exception as e:
                print(f"[WARNING] Could not load SentenceTransformer ({e}). Using lightweight embedder.")
                self.embedder = LightweightEmbedder()
        else:
            self.embedder = LightweightEmbedder()

    def parse_pdf(self, pdf_path: str) -> list:
        """
        Parses condensed GDPR PDF and extracts text per article.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"GDPR PDF file not found at: {pdf_path}")

        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"

        # Split by Article headers
        article_blocks = re.split(r'Article\s+(\d+)\s+—\s+', full_text)
        
        parsed_articles = []
        if len(article_blocks) > 1:
            for i in range(1, len(article_blocks), 2):
                art_num = int(article_blocks[i])
                art_body = article_blocks[i+1] if i+1 < len(article_blocks) else ""
                
                lines = art_body.strip().split('\n')
                art_title = lines[0] if lines else f"Article {art_num}"
                art_content = "\n".join(lines[1:]).strip()
                
                ch_num, ch_title = get_chapter_for_article(art_num)
                parsed_articles.append({
                    "article_num": art_num,
                    "article_label": f"Art. {art_num}",
                    "article_title": art_title,
                    "chapter_number": ch_num,
                    "chapter_title": ch_title,
                    "content": art_content
                })
        return parsed_articles

    def generate_atomic_requirements(self, parsed_articles: list) -> list:
        """
        Splits article content into atomic requirements (REQ-001..REQ-N) with embeddings.
        """
        requirements = []
        req_counter = 1

        for art in parsed_articles:
            content = art["content"]
            clauses = re.split(r';|\.\s+', content)
            
            for clause in clauses:
                clean_clause = clause.strip()
                if len(clean_clause) < 15:
                    continue
                
                req_id = f"REQ-{req_counter:03d}"
                
                # Generate embedding vector
                embedding_vector = self.embedder.encode(clean_clause)
                if hasattr(embedding_vector, 'tolist'):
                    embedding_vector = embedding_vector.tolist()

                req_obj = {
                    "id": req_id,
                    "chapter_number": art["chapter_number"],
                    "chapter_title": art["chapter_title"],
                    "article_number": art["article_label"],
                    "article_title": art["article_title"],
                    "atomic_requirement": clean_clause,
                    "embedding": embedding_vector
                }
                requirements.append(req_obj)
                req_counter += 1

        return requirements

    def ingest(self, pdf_path: str = "gdpr_condensed.pdf", output_cache_json: str = "gdpr_requirements_master.json") -> list:
        """
        Runs full ingestion pipeline: PDF -> Articles -> Requirements + Embeddings -> Supabase & Local Cache.
        """
        print(f"[INFO] Extracting GDPR text from: {pdf_path}")
        articles = self.parse_pdf(pdf_path)
        print(f"[INFO] Extracted {len(articles)} articles across 11 GDPR Chapters.")

        print("[INFO] Generating atomic requirements & embeddings...")
        requirements = self.generate_atomic_requirements(articles)
        print(f"[INFO] Created {len(requirements)} atomic requirements (REQ-001 to REQ-{len(requirements):03d}).")

        # Save to local JSON cache
        with open(output_cache_json, "w", encoding="utf-8") as f:
            readable_cache = [{k: v for k, v in r.items() if k != "embedding"} for r in requirements]
            json.dump(readable_cache, f, indent=2)
        print(f"[INFO] Local JSON requirements cache saved to: {output_cache_json}")

        # Store in Supabase Cloud DB
        if supabase_db.is_connected():
            print("[INFO] Syncing requirements to Supabase Cloud `gdpr_requirements` table...")
            success_count = 0
            for req in requirements:
                if supabase_db.store_gdpr_requirement(req):
                    success_count += 1
            print(f"[INFO] Successfully stored {success_count}/{len(requirements)} requirements in Supabase.")
        else:
            print("[WARNING] Supabase not connected. Requirements saved locally only.")

        return requirements

if __name__ == "__main__":
    pdf_file = "gdpr_condensed.pdf"
    if not os.path.exists(pdf_file):
        from generate_gdpr_pdf import generate_gdpr_reference_pdf
        generate_gdpr_reference_pdf(pdf_file)
        
    parser = GDPRParser()
    parser.ingest(pdf_file)
