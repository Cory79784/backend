"""
Test BM25 store loading with the actual data files
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.search.bm25_store import build_all_stores

print("=" * 60)
print("Testing BM25 Store Loading")
print("=" * 60)
print()

# Change to backend directory for correct relative paths
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

print(f"Current directory: {os.getcwd()}")
print()

# Build stores
stores = build_all_stores()

print()
print("=" * 60)
print("Store Summary")
print("=" * 60)

for name, store in stores.items():
    stats = store.get_stats()
    print(f"\n{name}:")
    print(f"  Path: {stats['jsonl_path']}")
    print(f"  Documents: {stats['document_count']}")
    print(f"  Indexed: {stats['indexed']}")
    print(f"  Key Fields: {stats['key_fields']}")

# Test a search
print()
print("=" * 60)
print("Testing Search")
print("=" * 60)

if 'geogli' in stores and stores['geogli'].documents:
    print("\nSearching 'geogli' store for 'Kenya drought':")
    results = stores['geogli'].search("Kenya drought", k=3)
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Score: {result.get('_score', 0):.3f}")
        print(f"    Country: {result.get('country', 'N/A')}")
        print(f"    Title: {result.get('title', 'N/A')}")
        print(f"    Section: {result.get('section', 'N/A')}")
        text = result.get('text', '')
        if text:
            preview = text[:100] + "..." if len(text) > 100 else text
            print(f"    Text: {preview}")
else:
    print("\n⚠️  No documents loaded in 'geogli' store")

print()
print("=" * 60)
print("Test Complete")
print("=" * 60)
