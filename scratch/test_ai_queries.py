import os
import sys
sys.path.insert(0, ".")

from backend.app.db import SessionLocal
from backend.app.chat.classifier import classify_query
from backend.app.chat.retrieval import MultiSourceContextRetriever

QUERIES = [
    "Explain the complete business workflow of this project.",
    "What does each module do?",
    "How does the authentication module work?",
    "Which modules depend on this service?",
    "Why was this module refactored?",
    "Which PR introduced the database schema change?",
    "Have we faced a similar bug before?",
    "What should a new developer understand before modifying this module?",
    "What is the impact of changing this API?",
    "Which historical engineering decisions are relevant to this PR?",
]

def main():
    db = SessionLocal()
    retriever = MultiSourceContextRetriever(db=db)
    
    print("=" * 80)
    print("TESTING 10 AI KNOWLEDGE RETRIEVAL & SEARCH QUALITY QUERIES")
    print("Target Repository ID: 1 (Payments Platform / repomind-e2e-test-repository)")
    print("=" * 80)
    
    for idx, query in enumerate(QUERIES, 1):
        print(f"\n--- Query #{idx}: \"{query}\" ---")
        entities = classify_query(text=query, context_type="repository", context_id=1)
        print(f"Intent detected: {entities.intent.value if entities.intent else None}, Keywords: {entities.keywords}, Files: {entities.files}, Symbols: {entities.symbols}")
        
        evidence_text, sources, has_grounded = retriever.retrieve(
            repository_id=1,
            query=query,
            entities=entities,
            top_k=5
        )
        
        print(f"Grounded Evidence Found: {has_grounded}")
        print(f"Total Sources Retrieved: {len(sources)}")
        for s in sources[:4]:
            print(f"  * [{s.get('type')}] {s.get('path')} (Symbol: {s.get('symbol')}) -> {s.get('summary', '')[:80]}")
        print(f"Evidence Excerpt (first 150 chars): {evidence_text[:150].strip()}...")
        
    db.close()
    print("\n" + "=" * 80)
    print("ALL 10 QUERIES TESTED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    main()
