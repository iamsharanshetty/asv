from duckduckgo_search import DDGS
import time

def test_basic_ddg():
    try:
        # For version 8.x, the initialization might be different
        ddgs = DDGS()
        query = "BITS Pilani student death"
        print(f"Testing query: {query}")
        
        # Try the text search
        results = list(ddgs.text(query, max_results=5))  # Note: convert to list
        print(f"Results found: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"Title: {result.get('title', 'No title')}")
            print(f"URL: {result.get('href', 'No URL')}")
            print(f"Body: {result.get('body', 'No body')[:100]}...")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_ddg()
    print(f"\nBasic search working: {success}")