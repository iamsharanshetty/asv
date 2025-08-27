# ===========================================
# 📌 Imports
# ===========================================
import os
import re
import json
import time
import textwrap
import requests
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


# ===========================================
# ⚠️ Setup API Keys
# ===========================================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
if not OPENROUTER_API_BASE:
    raise ValueError("OPENROUTER_API_BASE not found in environment variables")

# Initialize LLM
try:
    openrouter_llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct",
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENROUTER_API_BASE,
        temperature=0.1,
        max_tokens=1024,
        # Add headers for OpenRouter using default_headers
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Document Audit API"
        }
    )
    print("✅ Connected to OpenRouter model.")
except Exception as e:
    print(f"🚨 Failed to initialize LLM: {e}")
    raise


# ===========================================
# 📌 Load and Split Documents
# ===========================================
def ingest_and_split_documents(file_path: str) -> list:
    print(f"🔄 Loading and splitting document from: {file_path}")
    if file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=250)
    document_chunks = text_splitter.split_documents(documents)
    print(f"✅ Document split into {len(document_chunks)} chunks.")
    return document_chunks


# ===========================================
# 📌 Ingest Evidence Papers
# ===========================================
def load_evidence_papers():
    """Load evidence papers for claim verification."""
    evidence_urls = [
        "https://arxiv.org/pdf/2508.11042.pdf",
        "https://arxiv.org/pdf/2508.10951.pdf"
    ]
    
    evidence_chunks = []
    for i, url in enumerate(evidence_urls):
        filename = f"evidence_paper_{i+1}.pdf"
        try:
            print(f"Downloading {url} → {filename}")
            # Use requests instead of wget for Windows compatibility
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(response.content)
                loader = PyPDFLoader(filename)
                docs = loader.load()
                splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=250)
                chunks = splitter.split_documents(docs)
                for chunk in chunks:
                    chunk.metadata['source_paper'] = filename
                evidence_chunks.extend(chunks)
                print(f"✅ Loaded {filename} → {len(chunks)} chunks.")
            else:
                print(f"🚨 Failed to download {url}, status code: {response.status_code}")
        except Exception as e:
            print(f"🚨 Error downloading {url}: {e}")
    
    print(f"\n📊 Total evidence chunks: {len(evidence_chunks)}")
    return evidence_chunks

# Initialize evidence chunks
evidence_chunks = load_evidence_papers()


# ===========================================
# 📌 Claim Extraction with OpenRouter
# ===========================================
def extract_claims_openrouter(doc_chunks: list) -> list[dict]:
    print(f"🔄 Extracting claims with OpenRouter from {len(doc_chunks)} chunks...")

    template = """You are an expert auditor. Extract all distinct, verifiable claims from the provided text.
List each claim on a new line starting with a hyphen (-). Do not add explanation.

Text:
"{document_chunk}"

Claims:"""
    prompt = PromptTemplate.from_template(template)
    extraction_chain = prompt | openrouter_llm

    all_claims = []
    for i, chunk in enumerate(doc_chunks):
        try:
            response_text = extraction_chain.invoke({"document_chunk": chunk.page_content}).content
            print(f"\n--- RAW MODEL OUTPUT (Chunk {i}) ---\n{response_text}\n")

            extracted_lines = response_text.split('\n')
            parsed_claims = []
            for line in extracted_lines:
                if line.strip().startswith('-'):
                    cleaned_claim = line.strip()[1:].strip()
                    if cleaned_claim:
                        parsed_claims.append(cleaned_claim)

            for claim_text in parsed_claims:
                all_claims.append({
                    "claim_text": claim_text,
                    "source_context": chunk.page_content,
                    "metadata": {"source": chunk.metadata.get("source", "N/A"), "source_chunk_id": i}
                })
        except Exception as e:
            print(f"⚠️ Error parsing claims from chunk {i}: {e}")
            continue

    print(f"\n✅ Extracted {len(all_claims)} claims.")
    return all_claims


# ===========================================
# 📌 Classify Claims
# ===========================================
def classify_claim_type_openrouter(claim_data: dict) -> dict:
    claim_text = claim_data['claim_text']
    print(f"🤖 Classifying claim: '{claim_text[:50]}...'")

    template = """Classify the following claim into one of these four categories:
- Financial
- Operational
- Legal & Compliance
- Environmental, Social, and Governance (ESG)

Respond with only the category.

Claim: "{claim_text}"
Category:"""
    prompt = PromptTemplate.from_template(template)
    chain = prompt | openrouter_llm
    response = chain.invoke({"claim_text": claim_text}).content.strip()

    valid_categories = ["Financial", "Operational", "Legal & Compliance", "Environmental, Social, and Governance (ESG)"]
    category = response if response in valid_categories else "Operational"

    claim_data['category'] = category
    print(f"✅ Category: {category}")
    return claim_data


# ===========================================
# 📌 Retrieve Evidence (DuckDuckGo + Local Papers)
# ===========================================
search_tool = DuckDuckGoSearchAPIWrapper()

def retrieve_evidence_openrouter(claim_data: dict) -> dict:
    claim_text = claim_data['claim_text']
    print(f"🔎 Retrieving evidence for: '{claim_text[:50]}...'")

    template = """Generate 5 distinct and specific search queries to verify this claim:
Claim: "{claim_text}"

Queries:"""
    prompt = PromptTemplate.from_template(template)
    chain = prompt | openrouter_llm
    response = chain.invoke({"claim_text": claim_text}).content

    queries = [re.sub(r'^\d+\.\s*', '', q).strip() for q in response.split('\n') if q.strip()]
    print(f"Generated {len(queries)} queries.")

    all_results = []
    found_in_papers = False

    # Search in local evidence papers
    for query in queries:
        key_terms = set(re.findall(r'\b\w+\b', query.lower()))
        local_results = []
        for chunk in evidence_chunks:
            content_lower = chunk.page_content.lower()
            score = sum(1 for term in key_terms if term in content_lower)
            if score > 0:
                local_results.append({
                    "source_query": query,
                    "retrieved_content": chunk.page_content,
                    "source": chunk.metadata.get('source_paper', 'Local Paper'),
                    "relevance_score": score
                })
        if local_results:
            found_in_papers = True
            all_results.extend(local_results)

    if not found_in_papers:
        print("⚠️ No evidence in papers → falling back to web search.")
        for query in queries:
            try:
                result_text = search_tool.run(query)
                if result_text and "No good DuckDuckGo Search Result" not in result_text:
                    all_results.append({
                        "source_query": query,
                        "retrieved_content": result_text,
                        "source": "Web",
                        "relevance_score": 0
                    })
            except Exception as e:
                print(f"⚠️ Web search error: {e}")

    if not all_results:
        claim_data['evidence'] = "No reliable evidence was found."
        return claim_data

    # Keep top 3 evidence
    sorted_results = sorted(all_results, key=lambda x: x['relevance_score'], reverse=True)
    claim_data['evidence'] = sorted_results[:3]
    print("✅ Evidence collected.")
    return claim_data


# ===========================================
# 📌 Evaluate Claims
# ===========================================
def evaluate_claim_openrouter(claim_data: dict) -> dict:
    claim_text = claim_data['claim_text']
    evidence = claim_data['evidence']
    print(f"⚖️ Evaluating claim: '{claim_text[:50]}...'")

    if not evidence or isinstance(evidence, str):
        claim_data.update({
            'verdict': 'Insufficient Evidence',
            'evidence_summary': 'No relevant evidence found.',
            'verdict_reasoning': 'The search did not yield enough evidence.'
        })
        return claim_data

    template = """You are an impartial auditor. Evaluate the claim using the evidence below.
Verdict must be one of: 'Confirmed', 'Plausible', 'Contradicted', 'Insufficient Evidence'.

Claim: "{claim_text}"

Evidence:
{evidence_json}

Respond in JSON with keys: "verdict", "evidence_summary", "verdict_reasoning".
JSON:"""
    prompt = PromptTemplate.from_template(template)
    chain = prompt | openrouter_llm
    response = chain.invoke({
        "claim_text": claim_text,
        "evidence_json": json.dumps(evidence, indent=2)
    }).content

    try:
        result_dict = json.loads(response)
        claim_data.update(result_dict)
    except:
        claim_data.update({
            'verdict': 'Evaluation Error',
            'evidence_summary': 'Failed to parse model JSON.',
            'verdict_reasoning': response
        })

    print(f"✅ Verdict: {claim_data.get('verdict')}")
    return claim_data


# ===========================================
# 📌 Chain the Pipeline
# ===========================================
def run_pipeline(file_path):
    """
    Main pipeline function to process a document and generate audit report.
    
    Args:
        file_path (str): Path to the document to be audited
        
    Returns:
        dict: Audit report with claims and their evaluations
    """
    try:
        if not file_path or not os.path.exists(file_path):
            return {"error": "Invalid file path or file does not exist"}

        print(f"🚀 Starting audit pipeline for: {file_path}")
        start_time = time.time()

        # Step 1: Load and split document
        doc_chunks = ingest_and_split_documents(file_path)
        if not doc_chunks:
            return {"error": "Failed to process document"}

        # Step 2: Extract claims
        claims = extract_claims_openrouter(doc_chunks)
        if not claims:
            return {"error": "No claims found in document", "claims": []}

        # Step 3: Process each claim
        processed_claims = []
        for i, claim in enumerate(claims):
            print(f"\n🔄 Processing claim {i+1}/{len(claims)}")
            try:
                # Classify claim type
                claim = classify_claim_type_openrouter(claim)
                
                # Retrieve evidence
                claim = retrieve_evidence_openrouter(claim)
                
                # Evaluate claim
                claim = evaluate_claim_openrouter(claim)
                
                processed_claims.append(claim)
            except Exception as e:
                print(f"⚠️ Error processing claim {i+1}: {e}")
                claim['error'] = str(e)
                processed_claims.append(claim)

        end_time = time.time()
        processing_time = end_time - start_time

        # Generate summary report
        report = {
            "summary": {
                "total_claims": len(processed_claims),
                "processing_time_seconds": round(processing_time, 2),
                "document_name": os.path.basename(file_path),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "claims": processed_claims
        }

        print(f"\n✅ Audit finished in {processing_time:.2f} seconds.")
        print(f"📊 Processed {len(processed_claims)} claims.")

        # Save report to file
        try:
            report_file_name = f"audit_report_{os.path.basename(file_path)}.json"
            with open(report_file_name, 'w') as f:
                json.dump(report, f, indent=4)
            print(f"📂 Report saved to '{report_file_name}'")
        except Exception as e:
            print(f"⚠️ Failed to save report: {e}")

        return report

    except Exception as e:
        error_msg = f"Pipeline error: {str(e)}"
        print(f"🚨 {error_msg}")
        return {"error": error_msg}
