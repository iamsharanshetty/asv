# university_reviews.py - FIXED VERSION
import re
import time
import json
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import quote, urlparse
import random

try:
    from fake_useragent import UserAgent
    UA_AVAILABLE = True
except ImportError:
    UA_AVAILABLE = False
    print("⚠️ fake-useragent not available, using default user agent")

try:
    from duckduckgo_search import DDGS
    WEB_SEARCH_AVAILABLE = True
    print("✅ DuckDuckGo search available")
except ImportError:
    try:
        # Try the old package name
        from ddgs import DDGS
        WEB_SEARCH_AVAILABLE = True
        print("✅ DDGS search available")
    except ImportError:
        WEB_SEARCH_AVAILABLE = False
        print("⚠️ DuckDuckGo search not available")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
    print("✅ BeautifulSoup available")
except ImportError:
    BS4_AVAILABLE = False
    print("⚠️ BeautifulSoup not available")

class UniversityReviewAnalyzer:
    def __init__(self):
        if UA_AVAILABLE:
            self.ua = UserAgent()
            user_agent = self.ua.random
        else:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.last_request_time = 0
        self.min_delay = 2.0
        
        # FIXED: Map to actual method names
        self.review_platforms = {
            'collegedunia.com': self.scrape_collegedunia_reviews,
            'shiksha.com': self.scrape_shiksha_reviews,
            'careers360.com': self.scrape_careers360_reviews,
            'getmyuni.com': self.scrape_getmyuni_reviews
        }
    
    def search_university_reviews(self, university_name: str) -> Dict[str, Any]:
        """Main function to search for REAL university reviews and data"""
        print(f"🔍 Starting REAL-TIME search for: {university_name}")
        
        if not WEB_SEARCH_AVAILABLE:
            return self._return_error("Web search dependencies not available")
        
        results = {
            'university_name': university_name,
            'nirf_ranking': None,
            'negative_reviews': [],
            'positive_reviews': [],
            'review_summary': {
                'total_negative_reviews': 0,
                'total_positive_reviews': 0,
                'average_rating': 0,
                'common_complaints': [],
                'common_praises': []
            },
            'sources': [],
            'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'search_status': 'success',
            'debug_info': {
                'web_search_available': WEB_SEARCH_AVAILABLE,
                'search_attempts': 0,
                'errors': [],
                'scraped_platforms': []
            }
        }
        
        try:
            # Step 1: Get REAL NIRF ranking
            print("📊 Fetching real NIRF ranking...")
            results['nirf_ranking'] = self.fetch_real_nirf_ranking(university_name)
            
            # Step 2: Search multiple review platforms for REAL data
            print("🔍 Searching real review platforms...")
            self.search_real_review_platforms(university_name, results)
            
            # Step 3: Scrape social media for REAL discussions
            print("📱 Scraping real social media discussions...")
            self.search_real_social_media(university_name, results)
            
            # Step 4: Get REAL news mentions
            print("📰 Fetching real news mentions...")
            self.search_real_news_mentions(university_name, results)
            
            # Step 5: Analyze REAL patterns
            self.analyze_real_review_patterns(results)
            
            # Validation: Ensure we have real data or report failure
            if not results['negative_reviews'] and not results['positive_reviews']:
                results['search_status'] = 'no_data_found'
                results['error'] = 'No real review data found for this university'
                print("⚠️ No real data found")
            else:
                print(f"✅ Real data found: {len(results['negative_reviews'])} negative, {len(results['positive_reviews'])} positive")
            
            return results
            
        except Exception as e:
            print(f"🚨 Critical error in real-time search: {e}")
            return self._return_error(str(e))
    
    def fetch_real_nirf_ranking(self, university_name: str) -> Dict[str, Any]:
        """Fetch REAL NIRF ranking data from official sources"""
        print(f"📊 Fetching real NIRF ranking for: {university_name}")
        
        try:
            ddgs = DDGS()
            
            # Specific NIRF search queries
            nirf_queries = [
                f'site:nirfindia.org "{university_name}"',
                f'NIRF ranking 2024 "{university_name}"',
                f'India ranking "{university_name}" NIRF',
                f'nirfindia.org {university_name} rank'
            ]
            
            for query in nirf_queries:
                try:
                    print(f"🔍 NIRF query: {query}")
                    self.rate_limit()
                    
                    search_results = ddgs.text(query, max_results=10)
                    
                    for result in search_results:
                        # Only process official NIRF results
                        url = result.get('href', '')
                        if 'nirfindia.org' in url or 'nirf' in url.lower():
                            ranking_data = self.extract_real_nirf_data(result, university_name)
                            if ranking_data:
                                print(f"✅ Found real NIRF ranking: {ranking_data['ranking']}")
                                return ranking_data
                
                except Exception as e:
                    print(f"⚠️ Error in NIRF query '{query}': {e}")
                    continue
            
            # If no official NIRF data found, try alternative ranking sources
            return self.fetch_alternative_ranking_data(university_name)
            
        except Exception as e:
            print(f"🚨 Error fetching NIRF ranking: {e}")
            return {
                'ranking': None,
                'error': str(e),
                'year': '2024',
                'category': 'Overall',
                'verified': False,
                'source': 'search_failed'
            }
    
    def extract_real_nirf_data(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract real NIRF ranking from official results"""
        try:
            title = result.get('title', '')
            body = result.get('body', '')
            url = result.get('href', '')
            
            full_text = (title + ' ' + body).lower()
            
            # Check if this result actually mentions the university
            if not any(part.lower() in full_text for part in university_name.split() if len(part) > 2):
                return None
            
            # Extract ranking number
            ranking_patterns = [
                r'rank(?:ed|ing)?\s*(?:at\s*)?(?:#\s*)?(\d+)',
                r'position\s*(\d+)',
                r'(\d+)(?:st|nd|rd|th)\s*rank',
                r'(\d+)(?:st|nd|rd|th)\s*position'
            ]
            
            for pattern in ranking_patterns:
                match = re.search(pattern, full_text)
                if match:
                    ranking = int(match.group(1))
                    if 1 <= ranking <= 1000:  # Valid ranking range
                        return {
                            'ranking': ranking,
                            'year': self.extract_year_from_text(full_text),
                            'category': self.extract_nirf_category(full_text),
                            'source_url': url,
                            'verified': True,
                            'source_title': title,
                            'source': 'official_nirf'
                        }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error extracting NIRF data: {e}")
            return None
    
    def fetch_alternative_ranking_data(self, university_name: str) -> Dict:
        """Fetch ranking from alternative credible sources"""
        try:
            ddgs = DDGS()
            
            alt_queries = [
                f'"{university_name}" ranking India 2024',
                f'"{university_name}" QS ranking world university',
                f'"{university_name}" Times Higher Education ranking'
            ]
            
            for query in alt_queries:
                self.rate_limit()
                search_results = ddgs.text(query, max_results=5)
                
                for result in search_results:
                    ranking_data = self.extract_alternative_ranking(result, university_name)
                    if ranking_data:
                        return ranking_data
            
            return {
                'ranking': None,
                'year': '2024',
                'category': 'Overall',
                'verified': False,
                'source': 'not_found',
                'note': f'No official ranking found for {university_name}'
            }
            
        except Exception as e:
            return {
                'ranking': None,
                'error': str(e),
                'year': '2024',
                'category': 'Overall',
                'verified': False
            }
    
    def search_real_review_platforms(self, university_name: str, results: Dict):
        """Search REAL review platforms with actual scraping"""
        print(f"🎓 Searching real review platforms for: {university_name}")
        
        # Target specific review platforms
        platform_queries = [
            f'site:collegedunia.com "{university_name}" reviews',
            f'site:shiksha.com "{university_name}" reviews',
            f'site:careers360.com "{university_name}" reviews',
            f'site:getmyuni.com "{university_name}" reviews'
        ]
        
        try:
            ddgs = DDGS()
            
            for query in platform_queries:
                try:
                    print(f"🔍 Platform query: {query}")
                    self.rate_limit()
                    
                    search_results = ddgs.text(query, max_results=8)
                    results['debug_info']['search_attempts'] += 1
                    
                    for result in search_results:
                        # Extract and scrape real review data
                        url = result.get('href', '')
                        domain = urlparse(url).netloc.lower()
                        
                        # Try to scrape the actual review page
                        if any(platform in domain for platform in ['collegedunia', 'shiksha', 'careers360', 'getmyuni']):
                            scraped_reviews = self.scrape_review_page(url, university_name)
                            if scraped_reviews:
                                results['negative_reviews'].extend(scraped_reviews['negative'])
                                results['positive_reviews'].extend(scraped_reviews['positive'])
                                results['debug_info']['scraped_platforms'].append(domain)
                                
                                # Add real source
                                results['sources'].append({
                                    'title': result.get('title', f'{domain} Reviews'),
                                    'url': url,
                                    'type': 'review_platform',
                                    'platform': domain,
                                    'search_query': query
                                })
                                
                                print(f"✅ Scraped real data from {domain}")
                
                except Exception as e:
                    error_msg = f"Error in platform query '{query}': {e}"
                    print(f"⚠️ {error_msg}")
                    results['debug_info']['errors'].append(error_msg)
                    continue
                    
        except Exception as e:
            error_msg = f"Error searching review platforms: {e}"
            print(f"🚨 {error_msg}")
            results['debug_info']['errors'].append(error_msg)
    
    def scrape_review_page(self, url: str, university_name: str) -> Optional[Dict]:
        """Scrape actual review content from review platform pages"""
        try:
            print(f"🕷️ Scraping: {url}")
            self.rate_limit()
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ Failed to fetch {url}: {response.status_code}")
                return None
            
            if not BS4_AVAILABLE:
                # Extract reviews from raw HTML using regex
                return self.extract_reviews_from_html(response.text, url, university_name)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            domain = urlparse(url).netloc.lower()
            
            # Platform-specific scraping
            if 'collegedunia' in domain:
                return self.scrape_collegedunia_reviews(soup, url, university_name)
            elif 'shiksha' in domain:
                return self.scrape_shiksha_reviews(soup, url, university_name)
            elif 'careers360' in domain:
                return self.scrape_careers360_reviews(soup, url, university_name)
            elif 'getmyuni' in domain:
                return self.scrape_getmyuni_reviews(soup, url, university_name)
            else:
                return self.scrape_generic_reviews(soup, url, university_name)
                
        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            return None
    
    def extract_reviews_from_html(self, html_content: str, url: str, university_name: str) -> Dict:
        """Extract reviews from raw HTML without BeautifulSoup"""
        reviews = {'negative': [], 'positive': []}
        
        try:
            # Look for review patterns in HTML
            review_patterns = [
                r'<div[^>]*review[^>]*>(.*?)</div>',
                r'<p[^>]*review[^>]*>(.*?)</p>',
                r'class="review[^"]*"[^>]*>(.*?)</',
                r'data-review[^>]*>(.*?)</'
            ]
            
            found_reviews = []
            for pattern in review_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                found_reviews.extend(matches)
            
            # Process found reviews
            for review_html in found_reviews[:10]:  # Limit to 10 reviews
                # Clean HTML tags
                clean_text = re.sub(r'<[^>]+>', ' ', review_html)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if len(clean_text) > 50 and self.is_relevant_to_university(clean_text, university_name):
                    sentiment = self.analyze_review_sentiment(clean_text)
                    
                    review_data = {
                        'content': clean_text[:300],
                        'source': self.extract_domain_name(url),
                        'url': url,
                        'sentiment': sentiment,
                        'review_type': 'scraped_review',
                        'date_found': time.strftime("%Y-%m-%d"),
                        'complaints': self.extract_real_complaints(clean_text),
                        'relevance_score': self.calculate_text_relevance(clean_text, university_name)
                    }
                    
                    if sentiment == 'negative':
                        reviews['negative'].append(review_data)
                    else:
                        reviews['positive'].append(review_data)
            
            print(f"✅ Extracted {len(reviews['negative'])} negative, {len(reviews['positive'])} positive reviews from HTML")
            return reviews
            
        except Exception as e:
            print(f"⚠️ Error extracting from HTML: {e}")
            return {'negative': [], 'positive': []}
    
    def scrape_collegedunia_reviews(self, soup: BeautifulSoup, url: str, university_name: str) -> Dict:
        """Scrape real reviews from CollegeDunia"""
        reviews = {'negative': [], 'positive': []}
        
        try:
            # CollegeDunia-specific selectors
            review_selectors = [
                '.review-card',
                '.review-content',
                '.student-review',
                '[class*="review"]',
                '.comment-content'
            ]
            
            for selector in review_selectors:
                review_elements = soup.select(selector)
                for element in review_elements[:15]:  # Limit reviews
                    text = element.get_text(strip=True)
                    if len(text) > 30 and self.is_relevant_to_university(text, university_name):
                        sentiment = self.analyze_review_sentiment(text)
                        
                        # Extract rating if available
                        rating = self.extract_rating_from_element(element)
                        
                        review_data = {
                            'content': text[:300],
                            'source': 'CollegeDunia',
                            'url': url,
                            'rating': rating,
                            'sentiment': sentiment,
                            'review_type': 'platform_review',
                            'date_found': time.strftime("%Y-%m-%d"),
                            'complaints': self.extract_real_complaints(text),
                            'relevance_score': self.calculate_text_relevance(text, university_name)
                        }
                        
                        if sentiment == 'negative':
                            reviews['negative'].append(review_data)
                        else:
                            reviews['positive'].append(review_data)
            
            print(f"✅ CollegeDunia: {len(reviews['negative'])} negative, {len(reviews['positive'])} positive")
            return reviews
            
        except Exception as e:
            print(f"⚠️ Error scraping CollegeDunia: {e}")
            return {'negative': [], 'positive': []}
    
    def scrape_shiksha_reviews(self, soup: BeautifulSoup, url: str, university_name: str) -> Dict:
        """Scrape real reviews from Shiksha"""
        reviews = {'negative': [], 'positive': []}
        
        try:
            # Shiksha-specific selectors
            review_selectors = [
                '.review-text',
                '.user-review',
                '.review-description',
                '[class*="review"]'
            ]
            
            for selector in review_selectors:
                review_elements = soup.select(selector)
                for element in review_elements[:10]:
                    text = element.get_text(strip=True)
                    if len(text) > 30 and self.is_relevant_to_university(text, university_name):
                        sentiment = self.analyze_review_sentiment(text)
                        
                        review_data = {
                            'content': text[:300],
                            'source': 'Shiksha',
                            'url': url,
                            'sentiment': sentiment,
                            'review_type': 'platform_review',
                            'date_found': time.strftime("%Y-%m-%d"),
                            'complaints': self.extract_real_complaints(text),
                            'relevance_score': self.calculate_text_relevance(text, university_name)
                        }
                        
                        if sentiment == 'negative':
                            reviews['negative'].append(review_data)
                        else:
                            reviews['positive'].append(review_data)
            
            return reviews
            
        except Exception as e:
            print(f"⚠️ Error scraping Shiksha: {e}")
            return {'negative': [], 'positive': []}
    
    def scrape_careers360_reviews(self, soup: BeautifulSoup, url: str, university_name: str) -> Dict:
        """Scrape real reviews from Careers360"""
        reviews = {'negative': [], 'positive': []}
        
        try:
            # Look for common review patterns
            review_elements = soup.find_all(['div', 'p', 'span'], 
                class_=re.compile(r'review|comment|feedback', re.I))
            
            for element in review_elements[:10]:
                text = element.get_text(strip=True)
                if len(text) > 30 and self.is_relevant_to_university(text, university_name):
                    sentiment = self.analyze_review_sentiment(text)
                    
                    review_data = {
                        'content': text[:300],
                        'source': 'Careers360',
                        'url': url,
                        'sentiment': sentiment,
                        'review_type': 'platform_review',
                        'date_found': time.strftime("%Y-%m-%d"),
                        'complaints': self.extract_real_complaints(text),
                        'relevance_score': self.calculate_text_relevance(text, university_name)
                    }
                    
                    if sentiment == 'negative':
                        reviews['negative'].append(review_data)
                    else:
                        reviews['positive'].append(review_data)
            
            return reviews
            
        except Exception as e:
            print(f"⚠️ Error scraping Careers360: {e}")
            return {'negative': [], 'positive': []}
    
    def scrape_getmyuni_reviews(self, soup: BeautifulSoup, url: str, university_name: str) -> Dict:
        """ADDED: Scrape real reviews from GetMyUni"""
        reviews = {'negative': [], 'positive': []}
        
        try:
            # GetMyUni-specific selectors
            review_selectors = [
                '.review-content',
                '.user-review',
                '.student-review',
                '[class*="review"]'
            ]
            
            for selector in review_selectors:
                review_elements = soup.select(selector)
                for element in review_elements[:10]:
                    text = element.get_text(strip=True)
                    if len(text) > 30 and self.is_relevant_to_university(text, university_name):
                        sentiment = self.analyze_review_sentiment(text)
                        
                        review_data = {
                            'content': text[:300],
                            'source': 'GetMyUni',
                            'url': url,
                            'sentiment': sentiment,
                            'review_type': 'platform_review',
                            'date_found': time.strftime("%Y-%m-%d"),
                            'complaints': self.extract_real_complaints(text),
                            'relevance_score': self.calculate_text_relevance(text, university_name)
                        }
                        
                        if sentiment == 'negative':
                            reviews['negative'].append(review_data)
                        else:
                            reviews['positive'].append(review_data)
            
            return reviews
            
        except Exception as e:
            print(f"⚠️ Error scraping GetMyUni: {e}")
            return {'negative': [], 'positive': []}
    
    def scrape_generic_reviews(self, soup: BeautifulSoup, url: str, university_name: str) -> Dict:
        """Generic review scraper for unknown platforms"""
        reviews = {'negative': [], 'positive': []}
        
        try:
            # Look for text that might be reviews
            text_elements = soup.find_all(['p', 'div', 'span'], limit=50)
            
            for element in text_elements:
                text = element.get_text(strip=True)
                if (len(text) > 50 and len(text) < 500 and 
                    self.is_relevant_to_university(text, university_name) and
                    self.looks_like_review(text)):
                    
                    sentiment = self.analyze_review_sentiment(text)
                    
                    review_data = {
                        'content': text[:300],
                        'source': self.extract_domain_name(url),
                        'url': url,
                        'sentiment': sentiment,
                        'review_type': 'scraped_content',
                        'date_found': time.strftime("%Y-%m-%d"),
                        'complaints': self.extract_real_complaints(text),
                        'relevance_score': self.calculate_text_relevance(text, university_name)
                    }
                    
                    if sentiment == 'negative':
                        reviews['negative'].append(review_data)
                    else:
                        reviews['positive'].append(review_data)
            
            return reviews
            
        except Exception as e:
            print(f"⚠️ Error in generic scraping: {e}")
            return {'negative': [], 'positive': []}
    
    def search_real_social_media(self, university_name: str, results: Dict):
        """Search REAL social media discussions"""
        print(f"📱 Searching real social media for: {university_name}")
        
        try:
            ddgs = DDGS()
            
            # Targeted social media queries
            social_queries = [
                f'site:reddit.com "{university_name}" experience',
                f'site:quora.com "{university_name}" review',
                f'"{university_name}" reddit student life',
                f'"{university_name}" quora honest review'
            ]
            
            for query in social_queries:
                try:
                    print(f"🔍 Social query: {query}")
                    self.rate_limit()
                    
                    search_results = ddgs.text(query, max_results=8)
                    results['debug_info']['search_attempts'] += 1
                    
                    for result in search_results:
                        social_data = self.extract_real_social_data(result, university_name)
                        if social_data:
                            if social_data['sentiment'] == 'negative':
                                results['negative_reviews'].append(social_data)
                            else:
                                results['positive_reviews'].append(social_data)
                            
                            # Add real source
                            results['sources'].append({
                                'title': result.get('title', 'Social Media Discussion'),
                                'url': result.get('href', ''),
                                'type': 'social_media',
                                'platform': social_data.get('platform', 'Unknown'),
                                'search_query': query
                            })
                
                except Exception as e:
                    error_msg = f"Error in social query '{query}': {e}"
                    print(f"⚠️ {error_msg}")
                    results['debug_info']['errors'].append(error_msg)
                    continue
                    
        except Exception as e:
            error_msg = f"Error searching social media: {e}"
            print(f"🚨 {error_msg}")
            results['debug_info']['errors'].append(error_msg)
    
    def extract_real_social_data(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract real social media discussion data"""
        try:
            title = result.get('title', '')
            body = result.get('body', '')
            url = result.get('href', '')
            
            # Identify platform
            platform = self.identify_social_platform(url)
            if not platform:
                return None
            
            text_content = (title + ' ' + body).strip()
            
            # Check relevance and length
            if (len(text_content) < 50 or 
                not self.is_relevant_to_university(text_content, university_name)):
                return None
            
            sentiment = self.analyze_review_sentiment(text_content)
            
            return {
                'content': text_content[:300],
                'source': f"{platform} Discussion",
                'url': url,
                'platform': platform,
                'sentiment': sentiment,
                'review_type': 'social_media',
                'date_found': time.strftime("%Y-%m-%d"),
                'complaints': self.extract_real_complaints(text_content),
                'relevance_score': self.calculate_text_relevance(text_content, university_name)
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting social data: {e}")
            return None
    
    def search_real_news_mentions(self, university_name: str, results: Dict):
        """Search for REAL news mentions"""
        print(f"📰 Searching real news mentions for: {university_name}")
        
        try:
            ddgs = DDGS()
            
            # News-specific queries
            news_queries = [
                f'"{university_name}" news 2024',
                f'"{university_name}" controversy scandal',
                f'"{university_name}" problems issues news'
            ]
            
            for query in news_queries:
                try:
                    print(f"🔍 News query: {query}")
                    self.rate_limit()
                    
                    search_results = ddgs.news(query, max_results=10)  # Use news search
                    results['debug_info']['search_attempts'] += 1
                    
                    for result in search_results:
                        news_data = self.extract_real_news_data(result, university_name)
                        if news_data:
                            if news_data['sentiment'] == 'negative':
                                results['negative_reviews'].append(news_data)
                            else:
                                results['positive_reviews'].append(news_data)
                            
                            # Add real source
                            results['sources'].append({
                                'title': result.get('title', 'News Article'),
                                'url': result.get('url', ''),
                                'type': 'news_article',
                                'date': result.get('date', 'Unknown'),
                                'search_query': query
                            })
                
                except Exception as e:
                    error_msg = f"Error in news query '{query}': {e}"
                    print(f"⚠️ {error_msg}")
                    results['debug_info']['errors'].append(error_msg)
                    continue
                    
        except Exception as e:
            error_msg = f"Error searching news: {e}"
            print(f"🚨 {error_msg}")
            results['debug_info']['errors'].append(error_msg)
    
    def extract_real_news_data(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract real news mention data"""
        try:
            title = result.get('title', '')
            body = result.get('body', '')
            url = result.get('url', '')
            date = result.get('date', '')
            
            text_content = (title + ' ' + body).strip()
            
            if (len(text_content) < 30 or 
                not self.is_relevant_to_university(text_content, university_name)):
                return None
            
            sentiment = self.analyze_review_sentiment(text_content)
            severity = self.assess_real_news_severity(text_content)
            
            return {
                'content': text_content[:400],
                'source': self.extract_domain_name(url),
                'url': url,
                'date': date,
                'sentiment': sentiment,
                'severity': severity,
                'review_type': 'news_mention',
                'date_found': time.strftime("%Y-%m-%d"),
                'complaints': self.extract_real_complaints(text_content),
                'relevance_score': self.calculate_text_relevance(text_content, university_name)
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting news data: {e}")
            return None
    
    def analyze_review_sentiment(self, text: str) -> str:
        """Analyze sentiment of review text"""
        text_lower = text.lower()
        
        # Negative sentiment indicators
        negative_words = [
            'bad', 'poor', 'terrible', 'awful', 'horrible', 'worst', 'disappointing',
            'useless', 'waste', 'pathetic', 'regret', 'avoid', 'not recommended',
            'problems', 'issues', 'complaints', 'concerns', 'difficulties',
            'outdated', 'insufficient', 'inadequate', 'limited', 'lack of',
            'unsatisfied', 'disappointed', 'frustrated', 'angry'
        ]
        
        # Positive sentiment indicators
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'best',
            'recommended', 'satisfied', 'happy', 'pleased', 'impressed',
            'quality', 'outstanding', 'fantastic', 'superb', 'brilliant'
        ]
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count and negative_count >= 1:
            return 'negative'
        elif positive_count > negative_count and positive_count >= 1:
            return 'positive'
        else:
            return 'neutral'
    
    def extract_rating_from_element(self, element) -> Optional[str]:
        """Extract rating from review element"""
        try:
            # Look for rating patterns in the element and its children
            rating_patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:out of|/|★)\s*(\d+)',
                r'(\d+(?:\.\d+)?)\s*stars?',
                r'rating[:\s]*(\d+(?:\.\d+)?)'
            ]
            
            element_text = element.get_text()
            for pattern in rating_patterns:
                match = re.search(pattern, element_text, re.IGNORECASE)
                if match:
                    if len(match.groups()) >= 2:
                        return f"{match.group(1)}/{match.group(2)}"
                    else:
                        return f"{match.group(1)}/5"
            
            return None
            
        except Exception as e:
            return None
    
    def is_relevant_to_university(self, text: str, university_name: str) -> bool:
        """Check if text is relevant to the specific university"""
        text_lower = text.lower()
        uni_lower = university_name.lower()
        
        # Create variations of university name
        uni_variations = [
            uni_lower,
            uni_lower.replace('university', '').strip(),
            uni_lower.replace('college', '').strip(),
            uni_lower.replace('institute', '').strip(),
            uni_lower.replace('of', '').strip()
        ]
        
        # Remove very short variations
        uni_variations = [var for var in uni_variations if len(var) > 3]
        
        # Check for direct mentions
        for variation in uni_variations:
            if variation in text_lower:
                return True
        
        # Check for partial matches with university keywords
        uni_keywords = university_name.split()
        uni_keywords = [word.lower() for word in uni_keywords if len(word) > 3]
        
        if len(uni_keywords) >= 2:
            keyword_matches = sum(1 for keyword in uni_keywords if keyword in text_lower)
            return keyword_matches >= 2
        
        return False
    
    def looks_like_review(self, text: str) -> bool:
        """Check if text looks like a review"""
        review_indicators = [
            'student', 'study', 'college', 'university', 'experience',
            'faculty', 'placement', 'infrastructure', 'campus',
            'course', 'degree', 'professor', 'teacher', 'education'
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in review_indicators if indicator in text_lower)
        
        return indicator_count >= 2
    
    def extract_real_complaints(self, text: str) -> List[str]:
        """Extract real complaint categories from text"""
        complaint_keywords = {
            'academics': [
                'faculty', 'teaching', 'professor', 'teacher', 'curriculum',
                'syllabus', 'education', 'academic', 'course', 'study',
                'outdated course', 'poor teaching', 'bad faculty'
            ],
            'infrastructure': [
                'infrastructure', 'building', 'classroom', 'lab', 'library',
                'facility', 'equipment', 'maintenance', 'wifi', 'internet',
                'old building', 'poor infrastructure'
            ],
            'placements': [
                'placement', 'job', 'career', 'company', 'package', 'salary',
                'employment', 'recruiting', 'internship', 'opportunity',
                'poor placement', 'no jobs'
            ],
            'administration': [
                'administration', 'management', 'staff', 'office', 'service',
                'support', 'response', 'bureaucracy', 'process',
                'poor service', 'bad administration'
            ],
            'fees': [
                'fees', 'fee', 'cost', 'expensive', 'money', 'financial',
                'tuition', 'charge', 'payment', 'high fees'
            ],
            'hostel': [
                'hostel', 'accommodation', 'room', 'mess', 'food',
                'residence', 'living', 'staying', 'boarding',
                'poor food', 'bad hostel'
            ]
        }
        
        text_lower = text.lower()
        found_categories = []
        
        for category, keywords in complaint_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches >= 1:
                found_categories.append(category)
        
        return found_categories if found_categories else ['general']
    
    def identify_social_platform(self, url: str) -> Optional[str]:
        """Identify social media platform from URL"""
        if not url:
            return None
        
        url_lower = url.lower()
        
        if 'reddit.com' in url_lower:
            return 'Reddit'
        elif 'quora.com' in url_lower:
            return 'Quora'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'Twitter'
        elif 'facebook.com' in url_lower:
            return 'Facebook'
        elif 'linkedin.com' in url_lower:
            return 'LinkedIn'
        
        return None
    
    def calculate_text_relevance(self, text: str, university_name: str) -> int:
        """Calculate relevance score (1-10)"""
        text_lower = text.lower()
        uni_words = [word.lower() for word in university_name.split() if len(word) > 3]
        
        relevance = 0
        for word in uni_words:
            if word in text_lower:
                relevance += 2
        
        # Bonus for education-related context
        edu_context = ['student', 'college', 'university', 'course', 'degree']
        context_score = sum(1 for ctx in edu_context if ctx in text_lower)
        relevance += min(3, context_score)
        
        return min(10, relevance)
    
    def assess_real_news_severity(self, text: str) -> str:
        """Assess real severity of news content"""
        text_lower = text.lower()
        
        high_severity = [
            'scandal', 'fraud', 'criminal', 'illegal', 'investigation',
            'lawsuit', 'arrested', 'charged', 'violation', 'misconduct'
        ]
        medium_severity = [
            'controversy', 'allegation', 'criticized', 'penalty', 'fine',
            'suspended', 'questioned', 'disputed', 'concerns'
        ]
        
        if any(term in text_lower for term in high_severity):
            return 'high'
        elif any(term in text_lower for term in medium_severity):
            return 'medium'
        else:
            return 'low'
    
    def extract_year_from_text(self, text: str) -> str:
        """Extract year from text"""
        year_match = re.search(r'20(2[0-9])', text)
        return year_match.group(0) if year_match else '2024'
    
    def extract_nirf_category(self, text: str) -> str:
        """Extract NIRF category from text"""
        categories = {
            'Engineering': ['engineering', 'technical', 'technology'],
            'Management': ['management', 'mba', 'business'],
            'Medical': ['medical', 'medicine', 'health'],
            'University': ['university', 'overall'],
            'Pharmacy': ['pharmacy', 'pharmaceutical'],
            'Law': ['law', 'legal']
        }
        
        text_lower = text.lower()
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        return 'Overall'
    
    def extract_alternative_ranking(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract ranking from alternative sources"""
        try:
            title = result.get('title', '')
            body = result.get('body', '')
            url = result.get('href', '')
            
            text = (title + ' ' + body).lower()
            
            # Check relevance
            if not self.is_relevant_to_university(text, university_name):
                return None
            
            # Look for ranking patterns
            ranking_patterns = [
                r'rank(?:ed|ing)?\s*(?:at\s*)?(?:#\s*)?(\d+)',
                r'position\s*(\d+)',
                r'(\d+)(?:st|nd|rd|th)\s*rank'
            ]
            
            for pattern in ranking_patterns:
                match = re.search(pattern, text)
                if match:
                    ranking = int(match.group(1))
                    if 1 <= ranking <= 1000:
                        return {
                            'ranking': ranking,
                            'year': self.extract_year_from_text(text),
                            'category': self.extract_nirf_category(text),
                            'source_url': url,
                            'verified': False,
                            'source_title': title,
                            'source': 'alternative_ranking'
                        }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error extracting alternative ranking: {e}")
            return None
    
    def extract_domain_name(self, url: str) -> str:
        """Extract clean domain name from URL"""
        try:
            if not url:
                return "Unknown Source"
            
            domain = urlparse(url).netloc.lower()
            domain = re.sub(r'^www\.', '', domain)
            
            # Map to readable names
            domain_names = {
                'collegedunia.com': 'CollegeDunia',
                'shiksha.com': 'Shiksha',
                'careers360.com': 'Careers360',
                'getmyuni.com': 'GetMyUni',
                'reddit.com': 'Reddit',
                'quora.com': 'Quora',
                'nirfindia.org': 'NIRF India'
            }
            
            return domain_names.get(domain, domain.split('.')[0].title())
            
        except:
            return "Unknown Source"
    
    def analyze_real_review_patterns(self, results: Dict):
        """Analyze patterns in REAL collected reviews"""
        negative_reviews = results['negative_reviews']
        positive_reviews = results['positive_reviews']
        
        print(f"📊 Analyzing {len(negative_reviews)} negative and {len(positive_reviews)} positive reviews")
        
        # Update totals
        results['review_summary']['total_negative_reviews'] = len(negative_reviews)
        results['review_summary']['total_positive_reviews'] = len(positive_reviews)
        
        if not negative_reviews and not positive_reviews:
            return
        
        # Analyze complaint patterns
        all_complaints = []
        all_praises = []
        total_ratings = []
        
        for review in negative_reviews:
            all_complaints.extend(review.get('complaints', []))
            rating = self.extract_numeric_rating(review.get('rating'))
            if rating:
                total_ratings.append(rating)
        
        for review in positive_reviews:
            all_praises.extend(review.get('complaints', []))  # Positive aspects
            rating = self.extract_numeric_rating(review.get('rating'))
            if rating:
                total_ratings.append(rating)
        
        # Count complaint frequencies
        complaint_counts = {}
        for complaint in all_complaints:
            complaint_counts[complaint] = complaint_counts.get(complaint, 0) + 1
        
        praise_counts = {}
        for praise in all_praises:
            praise_counts[praise] = praise_counts.get(praise, 0) + 1
        
        # Sort by frequency
        results['review_summary']['common_complaints'] = [
            {'category': cat, 'frequency': freq} 
            for cat, freq in sorted(complaint_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        results['review_summary']['common_praises'] = [
            {'category': cat, 'frequency': freq}
            for cat, freq in sorted(praise_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Calculate average rating
        if total_ratings:
            results['review_summary']['average_rating'] = round(sum(total_ratings) / len(total_ratings), 2)
        
        print(f"✅ Pattern analysis complete: {len(complaint_counts)} complaint types, {len(praise_counts)} praise types")
    
    def extract_numeric_rating(self, rating_str: Optional[str]) -> Optional[float]:
        """Extract numeric rating from rating string"""
        if not rating_str:
            return None
        
        try:
            # Handle formats like "3.5/5", "4 out of 5", "3.5★"
            match = re.search(r'(\d+(?:\.\d+)?)', rating_str)
            if match:
                return float(match.group(1))
        except:
            pass
        
        return None
    
    def rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _return_error(self, error_message: str) -> Dict:
        """Return standardized error response"""
        return {
            'university_name': '',
            'nirf_ranking': None,
            'negative_reviews': [],
            'positive_reviews': [],
            'review_summary': {
                'total_negative_reviews': 0,
                'total_positive_reviews': 0,
                'average_rating': 0,
                'common_complaints': [],
                'common_praises': []
            },
            'sources': [],
            'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'search_status': 'error',
            'error': error_message,
            'debug_info': {
                'web_search_available': WEB_SEARCH_AVAILABLE,
                'bs4_available': BS4_AVAILABLE,
                'search_attempts': 0,
                'errors': [error_message]
            }
        }

# Initialize the real-time analyzer
university_analyzer = UniversityReviewAnalyzer()