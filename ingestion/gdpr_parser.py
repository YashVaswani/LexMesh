"""
GDPR Ingestion Parser & Atomic Requirement Extractor
Parses the official condensed GDPR reference PDF, splits text into 11 Chapters & 99 Articles,
generates atomic requirements (REQ-001..REQ-N) with local vector embeddings,
and stores them in Supabase & local JSON cache.
"""

import os
import json
import re
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from db.supabase_client import supabase_db
from config import config

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
    "IX": {"title": "Provisions relating to specific processing situations", "articles": list(range(85, 92))},
    "X": {"title": "Delegated and implementing acts", "articles": list(range(92, 94))},
    "XI": {"title": "Final provisions", "articles": list(range(94, 100))}
}

def get_chapter_for_article(article_num: int) -> tuple:
    """Returns (chapter_roman, chapter_title) for a given article number."""
    for ch_num, ch_info in GDPR_CHAPTER_MAP.items():
        if article_num in ch_info["articles"]:
            return ch_num, ch_info["title"]
    return "XI", "Final provisions"

class GDPRParser:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        print(f"[INFO] Loading embedding model: {self.model_name}...")
        self.embedder = SentenceTransformer(self.model_name)
        print("[INFO] Embedding model loaded successfully.")

    def parse_pdf(self, pdf_path: str) -> list:
        """
        Parses the condensed GDPR PDF and extracts text per article.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"GDPR PDF file not found at: {pdf_path}")

        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"

        # Regex split by Article headers (e.g. "Article 5 — Principles relating to...")
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
            # Split sentences/clauses into atomic mandates
            clauses = re.split(r';|\.\s+', content)
            
            for clause in clauses:
                clean_clause = clause.strip()
                if len(clean_clause) < 15:
                    continue
                
                req_id = f"REQ-{req_counter:03d}"
                
                # Generate embedding
                embedding_vector = self.embedder.encode(clean_clause).tolist()
                
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

    def ingest(self, pdf_path: str, output_cache_json: str = "gdpr_requirements_master.json") -> list:
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
            # Exclude raw float vector from readable cache for compact file size
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
    # Test runner using official GDPR PDF
    sample_gdpr_pdf = r"C:\Users\Admin\.gemini\antigravity-ide\brain\c5faa3e9-a1b3-44b7-9f5d-3671a9ebb9b8\scratch\gdpr_condensed.pdf"
    if os.path.exists(sample_gdpr_pdf):
        parser = GDPRParser()
        parser.ingest(sample_gdpr_pdf)
    else:
        print("[INFO] Ingestion script ready. Pass a valid GDPR PDF path to execute.")
