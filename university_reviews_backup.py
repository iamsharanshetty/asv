# university_reviews.py - FIXED AND OPTIMIZED VERSION
import re
import time
import json
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import quote, urlparse
import random
from datetime import datetime, timedelta

# Handle imports with proper error handling
try:
    from fake_useragent import UserAgent
    UA_AVAILABLE = True
    print("✅ UserAgent available")
except ImportError:
    UA_AVAILABLE = False
    print("⚠️ fake-useragent not available, using default user agent")

try:
    from duckduckgo_search import DDGS
    WEB_SEARCH_AVAILABLE = True
    print("✅ DuckDuckGo search available")
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    print("❌ DuckDuckGo search not available - install with: pip install duckduckgo-search")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
    print("✅ BeautifulSoup available")
except ImportError:
    BS4_AVAILABLE = False
    print("❌ BeautifulSoup not available - install with: pip install beautifulsoup4")

class UniversityAnalyzer:
    def __init__(self):
        """Initialize the university analyzer with proper error handling"""
        # Set up user agent
        if UA_AVAILABLE:
            try:
                self.ua = UserAgent()
                user_agent = self.ua.random
            except Exception as e:
                print(f"⚠️ UserAgent error, using fallback: {e}")
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        else:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # Initialize session
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
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 1.0
        
        # Keywords for detecting negative content
        self.serious_negative_keywords = {
            'safety_incidents': [
                'student death', 'suicide', 'accident', 'injury', 'violence', 'assault',
                'safety concern', 'security breach', 'emergency', 'incident', 'died'
            ],
            'academic_issues': [
                'plagiarism', 'cheating', 'academic fraud', 'fake degree',
                'accreditation loss', 'quality concern', 'poor teaching'
            ],
            'financial_problems': [
                'financial crisis', 'bankruptcy', 'fee hike', 'corruption', 
                'embezzlement', 'financial mismanagement', 'overpriced'
            ],
            'faculty_misconduct': [
                'professor misconduct', 'faculty scandal', 'harassment',
                'inappropriate behavior', 'discrimination', 'bias', 'corrupt faculty'
            ],
            'administration_issues': [
                'poor management', 'administration failure', 'policy violation',
                'student protest', 'strike', 'complaint', 'mismanagement'
            ]
        }
        
        # Credible news sources for India
        self.credible_news_domains = [
            'thehindu.com', 'indianexpress.com', 'timesofindia.com',
            'ndtv.com', 'news18.com', 'hindustantimes.com',
            'deccanherald.com', 'tribuneindia.com', 'livemint.com',
            'indiatoday.in', 'outlookindia.com', 'scroll.in',
            'thequint.com', 'firstpost.com', 'theprint.in'
        ]

    def search_university_reviews(self, university_name: str) -> Dict[str, Any]:
        """Main function to search for comprehensive university reviews and negative incidents"""
        print(f"🔍 Starting comprehensive search for: {university_name}")
        
        # Check if web search is available
        if not WEB_SEARCH_AVAILABLE:
            return self._return_service_unavailable_error()
        
        # Initialize results structure
        results = {
            'university_name': university_name,
            'negative_reviews': [],
            'positive_reviews': [],
            'serious_incidents': [],
            'faculty_issues': [],
            'news_articles': [],
            'social_media_mentions': [],
            'review_summary': {
                'total_negative_reviews': 0,
                'total_positive_reviews': 0,
                'serious_incidents_count': 0,
                'faculty_issues_count': 0,
                'common_complaints': [],
                'severity_assessment': 'low'
            },
            'sources': [],
            'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'search_status': 'success',
            'credibility_score': 0
        }
        
        try:
            # Initialize search engine
            ddgs = DDGS()
            
            # Step 1: Search for serious negative incidents
            print("🚨 Searching for serious incidents...")
            self._search_serious_incidents(ddgs, university_name, results)
            
            # Step 2: Search for faculty misconduct
            print("👨‍🏫 Searching for faculty issues...")
            self._search_faculty_issues(ddgs, university_name, results)
            
            # Step 3: Search for news articles
            print("📰 Searching for news articles...")
            self._search_news_articles(ddgs, university_name, results)
            
            # Step 4: Search review platforms
            print("⭐ Searching review platforms...")
            self._search_review_platforms(ddgs, university_name, results)
            
            # Step 5: Search social media mentions
            print("📱 Searching social media...")
            self._search_social_media(ddgs, university_name, results)
            
            # Step 6: Analyze and summarize results
            print("📊 Analyzing results...")
            self._analyze_results(results)
            
            print(f"✅ Search completed: {len(results['negative_reviews'])} negative reviews, {len(results['serious_incidents'])} incidents found")
            
            return results
            
        except Exception as e:
            print(f"🚨 Critical error in search: {str(e)}")
            return self._return_error(str(e), university_name)

    def _search_serious_incidents(self, ddgs, university_name: str, results: Dict):
        """Search for serious negative incidents"""
        incident_queries = [
            f'"{university_name}" student death suicide news',
            f'"{university_name}" campus incident emergency police',
            f'"{university_name}" safety concerns deaths',
            f'"{university_name}" accident injury news',
            f'"{university_name}" violence assault campus',
            f'"{university_name}" controversy scandal exposed'
        ]
        
        for query in incident_queries:
            try:
                print(f"  🔍 Query: {query[:50]}...")
                self._rate_limit()
                
                # Search both web and news
                web_results = list(ddgs.text(query, max_results=8))
                news_results = list(ddgs.news(query, max_results=5))
                
                # Process results
                for result in web_results + news_results:
                    incident = self._extract_serious_incident(result, university_name)
                    if incident:
                        results['serious_incidents'].append(incident)
                        self._add_source(results, result, 'serious_incident')
                        
            except Exception as e:
                print(f"    ⚠️ Query failed: {str(e)}")
                continue

    def _search_faculty_issues(self, ddgs, university_name: str, results: Dict):
        """Search for faculty misconduct and issues"""
        faculty_queries = [
            f'"{university_name}" professor misconduct harassment',
            f'"{university_name}" faculty scandal inappropriate',
            f'"{university_name}" teacher problem complaint',
            f'"{university_name}" staff behavior issues',
            f'"{university_name}" corruption faculty bribery'
        ]
        
        for query in faculty_queries:
            try:
                print(f"  🔍 Query: {query[:50]}...")
                self._rate_limit()
                
                search_results = list(ddgs.text(query, max_results=8))
                
                for result in search_results:
                    faculty_issue = self._extract_faculty_issue(result, university_name)
                    if faculty_issue:
                        results['faculty_issues'].append(faculty_issue)
                        self._add_source(results, result, 'faculty_issue')
                        
            except Exception as e:
                print(f"    ⚠️ Query failed: {str(e)}")
                continue

    def _search_news_articles(self, ddgs, university_name: str, results: Dict):
        """Search for news articles about the university"""
        news_queries = [
            f'"{university_name}" problems issues news',
            f'"{university_name}" controversy news 2024',
            f'"{university_name}" student protest complaints',
            f'"{university_name}" poor quality education',
            f'"{university_name}" placement crisis jobs'
        ]
        
        for query in news_queries:
            try:
                print(f"  🔍 Query: {query[:50]}...")
                self._rate_limit()
                
                news_results = list(ddgs.news(query, max_results=10))
                
                for result in news_results:
                    article = self._extract_news_article(result, university_name)
                    if article:
                        results['news_articles'].append(article)
                        self._add_source(results, result, 'news_article')
                        
            except Exception as e:
                print(f"    ⚠️ Query failed: {str(e)}")
                continue

    def _search_review_platforms(self, ddgs, university_name: str, results: Dict):
        """Search review platforms for negative feedback"""
        review_queries = [
            f'site:collegedunia.com "{university_name}" negative review',
            f'site:shiksha.com "{university_name}" poor rating',
            f'site:careers360.com "{university_name}" bad experience',
            f'"{university_name}" review worst terrible bad'
        ]
        
        for query in review_queries:
            try:
                print(f"  🔍 Query: {query[:50]}...")
                self._rate_limit()
                
                search_results = list(ddgs.text(query, max_results=10))
                
                for result in search_results:
                    review = self._extract_review(result, university_name)
                    if review:
                        if review['sentiment'] == 'negative':
                            results['negative_reviews'].append(review)
                        else:
                            results['positive_reviews'].append(review)
                        self._add_source(results, result, 'review')
                        
            except Exception as e:
                print(f"    ⚠️ Query failed: {str(e)}")
                continue

    def _search_social_media(self, ddgs, university_name: str, results: Dict):
        """Search social media for mentions and discussions"""
        social_queries = [
            f'site:reddit.com "{university_name}" worst experience',
            f'site:quora.com "{university_name}" should avoid',
            f'"{university_name}" twitter complaints problems'
        ]
        
        for query in social_queries:
            try:
                print(f"  🔍 Query: {query[:50]}...")
                self._rate_limit()
                
                search_results = list(ddgs.text(query, max_results=8))
                
                for result in search_results:
                    mention = self._extract_social_mention(result, university_name)
                    if mention:
                        results['social_media_mentions'].append(mention)
                        self._add_source(results, result, 'social_media')
                        
            except Exception as e:
                print(f"    ⚠️ Query failed: {str(e)}")
                continue

    def _extract_serious_incident(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract serious incident information from search result"""
        title = result.get('title', '')
        body = result.get('body', result.get('snippet', ''))
        url = result.get('href', result.get('url', ''))
        
        content = (title + ' ' + body).strip()
        
        # Check relevance
        if not self._is_relevant(content, university_name):
            return None
        
        # Check for serious keywords
        severity_score = self._calculate_severity_score(content)
        if severity_score < 3:  # Only serious incidents
            return None
        
        return {
            'title': title,
            'description': body[:300] + '...' if len(body) > 300 else body,
            'url': url,
            'source': self._extract_domain(url),
            'severity_score': severity_score,
            'incident_type': self._classify_incident_type(content),
            'date_found': time.strftime("%Y-%m-%d"),
            'credibility': self._assess_source_credibility(url)
        }

    def _extract_faculty_issue(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract faculty issue information"""
        title = result.get('title', '')
        body = result.get('body', result.get('snippet', ''))
        url = result.get('href', result.get('url', ''))
        
        content = (title + ' ' + body).strip()
        
        if not self._is_relevant(content, university_name):
            return None
        
        # Check for faculty-related keywords
        if not self._has_faculty_keywords(content):
            return None
        
        return {
            'title': title,
            'description': body[:300] + '...' if len(body) > 300 else body,
            'url': url,
            'source': self._extract_domain(url),
            'issue_type': self._classify_faculty_issue(content),
            'severity': self._assess_faculty_severity(content),
            'date_found': time.strftime("%Y-%m-%d")
        }

    def _extract_news_article(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract news article information"""
        title = result.get('title', '')
        body = result.get('body', result.get('snippet', ''))
        url = result.get('url', result.get('href', ''))
        date = result.get('date', '')
        
        content = (title + ' ' + body).strip()
        
        if not self._is_relevant(content, university_name):
            return None
        
        negativity_score = self._calculate_negativity_score(content)
        
        return {
            'headline': title,
            'summary': body[:400] + '...' if len(body) > 400 else body,
            'url': url,
            'source': self._extract_domain(url),
            'published_date': date,
            'negativity_score': negativity_score,
            'credibility': self._assess_news_credibility(url),
            'date_found': time.strftime("%Y-%m-%d")
        }

    def _extract_review(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract review information"""
        title = result.get('title', '')
        body = result.get('body', result.get('snippet', ''))
        url = result.get('href', result.get('url', ''))
        
        content = (title + ' ' + body).strip()
        
        if not self._is_relevant(content, university_name):
            return None
        
        sentiment = self._analyze_sentiment(content)
        rating = self._extract_rating(content)
        
        return {
            'content': content[:500] + '...' if len(content) > 500 else content,
            'url': url,
            'source': self._extract_domain(url),
            'sentiment': sentiment,
            'rating': rating,
            'complaints': self._extract_complaints(content),
            'date_found': time.strftime("%Y-%m-%d")
        }

    def _extract_social_mention(self, result: Dict, university_name: str) -> Optional[Dict]:
        """Extract social media mention"""
        title = result.get('title', '')
        body = result.get('body', result.get('snippet', ''))
        url = result.get('href', result.get('url', ''))
        
        content = (title + ' ' + body).strip()
        
        if not self._is_relevant(content, university_name):
            return None
        
        platform = self._identify_platform(url)
        negativity = self._calculate_negativity_score(content)
        
        if negativity < 2:  # Only negative mentions
            return None
        
        return {
            'content': content[:400] + '...' if len(content) > 400 else content,
            'url': url,
            'platform': platform,
            'negativity_score': negativity,
            'date_found': time.strftime("%Y-%m-%d")
        }

    # Helper methods
    def _is_relevant(self, content: str, university_name: str) -> bool:
        """Check if content is relevant to the university"""
        content_lower = content.lower()
        uni_lower = university_name.lower()
        
        # Direct match
        if uni_lower in content_lower:
            return True
        
        # Component matching for multi-word university names
        uni_words = [word for word in university_name.split() 
                    if len(word) > 3 and word.lower() not in ['university', 'college', 'institute']]
        
        if len(uni_words) >= 2:
            matches = sum(1 for word in uni_words if word.lower() in content_lower)
            return matches >= 2
        
        return False

    def _calculate_severity_score(self, content: str) -> int:
        """Calculate severity score for incidents"""
        content_lower = content.lower()
        score = 0
        
        # Critical incidents
        critical_words = ['death', 'suicide', 'killed', 'died', 'murder']
        score += sum(5 for word in critical_words if word in content_lower)
        
        # Serious incidents
        serious_words = ['assault', 'violence', 'accident', 'injury', 'emergency']
        score += sum(3 for word in serious_words if word in content_lower)
        
        # Moderate incidents
        moderate_words = ['incident', 'complaint', 'problem', 'issue']
        score += sum(1 for word in moderate_words if word in content_lower)
        
        return min(score, 20)

    def _classify_incident_type(self, content: str) -> str:
        """Classify the type of incident"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['death', 'suicide', 'killed']):
            return 'fatal_incident'
        elif any(word in content_lower for word in ['assault', 'violence', 'attack']):
            return 'violence'
        elif any(word in content_lower for word in ['accident', 'injury']):
            return 'accident'
        elif any(word in content_lower for word in ['harassment', 'misconduct']):
            return 'misconduct'
        else:
            return 'general_incident'

    def _has_faculty_keywords(self, content: str) -> bool:
        """Check if content has faculty-related keywords"""
        content_lower = content.lower()
        faculty_words = ['professor', 'faculty', 'teacher', 'staff', 'instructor', 'principal']
        return any(word in content_lower for word in faculty_words)

    def _classify_faculty_issue(self, content: str) -> str:
        """Classify faculty issue type"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['harassment', 'misconduct', 'inappropriate']):
            return 'misconduct'
        elif any(word in content_lower for word in ['corruption', 'bribery', 'fraud']):
            return 'corruption'
        elif any(word in content_lower for word in ['incompetent', 'poor teaching', 'unqualified']):
            return 'competency'
        else:
            return 'general_complaint'

    def _assess_faculty_severity(self, content: str) -> str:
        """Assess severity of faculty issue"""
        content_lower = content.lower()
        
        high_severity = ['criminal', 'illegal', 'police', 'arrest', 'harassment']
        medium_severity = ['misconduct', 'inappropriate', 'complaint']
        
        if any(word in content_lower for word in high_severity):
            return 'high'
        elif any(word in content_lower for word in medium_severity):
            return 'medium'
        else:
            return 'low'

    def _calculate_negativity_score(self, content: str) -> int:
        """Calculate negativity score"""
        content_lower = content.lower()
        score = 0
        
        high_negative = ['terrible', 'awful', 'worst', 'horrible', 'disaster']
        medium_negative = ['bad', 'poor', 'disappointing', 'unsatisfactory']
        mild_negative = ['issues', 'problems', 'concerns']
        
        score += sum(3 for word in high_negative if word in content_lower)
        score += sum(2 for word in medium_negative if word in content_lower)
        score += sum(1 for word in mild_negative if word in content_lower)
        
        return min(score, 15)

    def _assess_news_credibility(self, url: str) -> str:
        """Assess credibility of news source"""
        if not url:
            return 'unknown'
        
        domain = urlparse(url).netloc.lower()
        
        if any(credible in domain for credible in self.credible_news_domains):
            return 'high'
        elif any(suffix in domain for suffix in ['.edu', '.gov']):
            return 'high'
        else:
            return 'medium'

    def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of review content"""
        content_lower = content.lower()
        
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'disappointing']
        
        pos_count = sum(1 for word in positive_words if word in content_lower)
        neg_count = sum(1 for word in negative_words if word in content_lower)
        
        if neg_count > pos_count:
            return 'negative'
        elif pos_count > neg_count:
            return 'positive'
        else:
            return 'neutral'

    def _extract_rating(self, content: str) -> Optional[str]:
        """Extract rating from content"""
        rating_pattern = r'(\d+(?:\.\d+)?)\s*(?:out of|/)\s*(\d+)|(\d+(?:\.\d+)?)\s*stars?'
        match = re.search(rating_pattern, content, re.IGNORECASE)
        if match:
            if match.group(1) and match.group(2):
                return f"{match.group(1)}/{match.group(2)}"
            else:
                return f"{match.group(3)}/5"
        return None

    def _extract_complaints(self, content: str) -> List[str]:
        """Extract specific complaints from review"""
        content_lower = content.lower()
        complaints = []
        
        complaint_keywords = {
            'poor_teaching': ['poor teaching', 'bad faculty', 'teaching quality'],
            'infrastructure': ['poor infrastructure', 'bad facilities', 'maintenance'],
            'placement': ['poor placement', 'no jobs', 'placement issues'],
            'fees': ['expensive', 'high fees', 'overpriced'],
            'administration': ['poor service', 'bad administration', 'management']
        }
        
        for complaint_type, keywords in complaint_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                complaints.append(complaint_type)
        
        return complaints

    def _identify_platform(self, url: str) -> str:
        """Identify social media platform"""
        if not url:
            return 'unknown'
        
        domain = urlparse(url).netloc.lower()
        
        if 'reddit.com' in domain:
            return 'Reddit'
        elif 'quora.com' in domain:
            return 'Quora'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'Twitter'
        elif 'facebook.com' in domain:
            return 'Facebook'
        else:
            return domain

    def _extract_domain(self, url: str) -> str:
        """Extract clean domain name"""
        if not url:
            return 'Unknown'
        
        try:
            domain = urlparse(url).netloc.lower()
            domain = re.sub(r'^www\.', '', domain)
            return domain.split('.')[0].title()
        except:
            return 'Unknown'

    def _assess_source_credibility(self, url: str) -> str:
        """Assess overall source credibility"""
        if not url:
            return 'unknown'
        
        domain = urlparse(url).netloc.lower()
        
        if any(credible in domain for credible in self.credible_news_domains):
            return 'high'
        elif any(suffix in domain for suffix in ['.edu', '.gov']):
            return 'high'
        elif any(platform in domain for platform in ['reddit.com', 'quora.com']):
            return 'medium'
        else:
            return 'low'

    def _add_source(self, results: Dict, result: Dict, source_type: str):
        """Add source to results"""
        url = result.get('href', result.get('url', ''))
        title = result.get('title', 'Untitled')
        
        # Avoid duplicates
        existing_urls = [source['url'] for source in results['sources']]
        if url not in existing_urls:
            results['sources'].append({
                'title': title,
                'url': url,
                'type': source_type,
                'credibility': self._assess_source_credibility(url),
                'date_found': time.strftime("%Y-%m-%d")
            })

    def _analyze_results(self, results: Dict):
        """Analyze and summarize results"""
        # Update counts
        results['review_summary']['total_negative_reviews'] = len(results['negative_reviews'])
        results['review_summary']['total_positive_reviews'] = len(results['positive_reviews'])
        results['review_summary']['serious_incidents_count'] = len(results['serious_incidents'])
        results['review_summary']['faculty_issues_count'] = len(results['faculty_issues'])
        
        # Extract common complaints
        all_complaints = []
        for review in results['negative_reviews']:
            all_complaints.extend(review.get('complaints', []))
        
        complaint_counts = {}
        for complaint in all_complaints:
            complaint_counts[complaint] = complaint_counts.get(complaint, 0) + 1
        
        results['review_summary']['common_complaints'] = [
            {'type': complaint, 'count': count}
            for complaint, count in sorted(complaint_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Assess overall severity
        serious_count = len(results['serious_incidents'])
        faculty_issues_count = len(results['faculty_issues'])
        negative_count = len(results['negative_reviews'])
        
        if serious_count >= 2 or faculty_issues_count >= 2:
            results['review_summary']['severity_assessment'] = 'high'
        elif serious_count >= 1 or faculty_issues_count >= 1 or negative_count >= 5:
            results['review_summary']['severity_assessment'] = 'medium'
        else:
            results['review_summary']['severity_assessment'] = 'low'
        
        # Calculate credibility score
        total_sources = len(results['sources'])
        if total_sources > 0:
            high_credibility = sum(1 for source in results['sources'] if source['credibility'] == 'high')
            results['credibility_score'] = int((high_credibility / total_sources) * 100)
        else:
            results['credibility_score'] = 0

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        
        self.last_request_time = time.time()

    def _return_service_unavailable_error(self) -> Dict:
        """Return error when service dependencies are not available"""
        return {
            'university_name': '',
            'negative_reviews': [],
            'positive_reviews': [],
            'serious_incidents': [],
            'faculty_issues': [],
            'news_articles': [],
            'social_media_mentions': [],
            'review_summary': {
                'total_negative_reviews': 0,
                'total_positive_reviews': 0,
                'serious_incidents_count': 0,
                'faculty_issues_count': 0,
                'common_complaints': [],
                'severity_assessment': 'unknown'
            },
            'sources': [],
            'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'search_status': 'service_unavailable',
            'error': 'Web search dependencies not available. Please install: pip install duckduckgo-search beautifulsoup4',
            'credibility_score': 0
        }

    def _return_error(self, error_message: str, university_name: str = '') -> Dict:
        """Return standardized error response"""
        return {
            'university_name': university_name,
            'negative_reviews': [],
            'positive_reviews': [],
            'serious_incidents': [],
            'faculty_issues': [],
            'news_articles': [],
            'social_media_mentions': [],
            'review_summary': {
                'total_negative_reviews': 0,
                'total_positive_reviews': 0,
                'serious_incidents_count': 0,
                'faculty_issues_count': 0,
                'common_complaints': [],
                'severity_assessment': 'unknown'
            },
            'sources': [],
            'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'search_status': 'error',
            'error': error_message,
            'credibility_score': 0
        }

# Initialize the analyzer
university_analyzer = UniversityAnalyzer()