from university_reviews import university_analyzer
import json

def test_real_university_search():
    # Test with a well-known university
    test_universities = [
        "Indian Institute of Technology Delhi",
        "Delhi University,Delhi",
        "Jawaharlal Nehru University"
    ]
    
    for uni in test_universities:
        print(f"\n🧪 Testing: {uni}")
        results = university_analyzer.search_university_reviews(uni)
        
        # Check for real data
        has_real_nirf = results.get('nirf_ranking', {}).get('verified', False)
        has_real_reviews = len(results.get('negative_reviews', [])) > 0
        has_real_sources = len([s for s in results.get('sources', []) if s.get('url', '').startswith('http')]) > 0
        
        print(f"✅ Real NIRF: {has_real_nirf}")
        print(f"✅ Real Reviews: {has_real_reviews}")
        print(f"✅ Real Sources: {has_real_sources}")
        
        # Save results
        with open(f'test_results_{uni.replace(" ", "_")}.json', 'w') as f:
            json.dump(results, f, indent=2)

if __name__ == "__main__":
    test_real_university_search()