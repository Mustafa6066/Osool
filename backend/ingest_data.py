#!/usr/bin/env python3
"""
Osool Data Ingestion Script
---------------------------
Parses window.egyptianData from data.js and populates the Supabase Vector Store.

Usage:
    python ingest_data.py
"""

import os
import re
import json
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.schema import Document
from supabase import create_client

load_dotenv()

# Configuration
DATA_JS_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "assets", "js", "data.js")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_data_from_js(filepath: str) -> dict:
    """
    Parses the data.js file and extracts the egyptianData object.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove 'window.egyptianData = ' prefix and trailing semicolon/newlines
    # The format is: window.egyptianData = { ... };
    match = re.search(r"window\.egyptianData\s*=\s*(\{.*\})\s*;?", content, re.DOTALL)
    
    if not match:
        raise ValueError("Could not find 'window.egyptianData' object in data.js")
    
    json_str = match.group(1)
    
    # Parse the JSON
    data = json.loads(json_str)
    return data

def create_documents(properties: list) -> list:
    """
    Converts property records into LangChain Documents with rich metadata.
    """
    documents = []
    
    for prop in properties:
        # Create a rich text content for embedding
        # Include key searchable info in the page_content
        content = f"""
Property: {prop.get('title', 'N/A')}
Type: {prop.get('type', 'N/A')}
Location: {prop.get('location', 'N/A')}
Compound: {prop.get('compound', 'N/A')}
Developer: {prop.get('developer', 'N/A')}
Area: {prop.get('area', 0)} sqm
Bedrooms: {prop.get('bedrooms', 0)}
Bathrooms: {prop.get('bathrooms', 0)}
Price: {prop.get('price', 0):,.0f} EGP
Price per sqm: {prop.get('pricePerSqm', 0):,.0f} EGP
Delivery: {prop.get('deliveryDate', 'N/A')}
Sale Type: {prop.get('saleType', 'N/A')}
Description: {prop.get('description', '')}
"""
        # Payment plan info
        payment = prop.get('paymentPlan', {})
        if payment:
            content += f"""
Down Payment: {payment.get('downPayment', 0)}%
Installment Years: {payment.get('installmentYears', 0)}
Monthly Installment: {payment.get('monthlyInstallment', 0):,.0f} EGP
"""

        # Metadata for filtering and display
        metadata = {
            "id": prop.get("id", ""),
            "title": prop.get("title", ""),
            "type": prop.get("type", ""),
            "location": prop.get("location", ""),
            "compound": prop.get("compound", ""),
            "price": prop.get("price", 0),
            "pricePerSqm": prop.get("pricePerSqm", 0),
            "area": prop.get("area", 0),
            "bedrooms": prop.get("bedrooms", 0),
            "bathrooms": prop.get("bathrooms", 0),
            "deliveryDate": prop.get("deliveryDate", ""),
            "saleType": prop.get("saleType", ""),
            "image": prop.get("image", ""),
            "url": prop.get("nawyUrl", ""),
            "developer": prop.get("developer", "")
        }
        
        doc = Document(page_content=content.strip(), metadata=metadata)
        documents.append(doc)
    
    return documents

def ingest_to_supabase(documents: list):
    """
    Embeds documents and upserts to Supabase Vector Store.
    """
    print(f"🔗 Connecting to Supabase: {SUPABASE_URL}")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🧠 Initializing OpenAI Embeddings (text-embedding-3-small)...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    print(f"📤 Upserting {len(documents)} documents to vector store...")
    
    # Use SupabaseVectorStore.from_documents to create/upsert
    # This assumes a 'documents' table exists with proper schema (id, content, metadata, embedding)
    vector_store = SupabaseVectorStore.from_documents(
        documents,
        embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents"
    )
    
    print("✅ Ingestion complete!")
    return vector_store

def main():
    print("=" * 60)
    print("🏠 OSOOL DATA INGESTION PIPELINE")
    print("=" * 60)
    
    # 1. Load Data
    print(f"\n📂 Loading data from: {DATA_JS_PATH}")
    data = load_data_from_js(DATA_JS_PATH)
    
    metadata = data.get("metadata", {})
    properties = data.get("properties", [])
    
    print(f"   - Total Properties: {metadata.get('totalProperties', len(properties))}")
    print(f"   - Last Updated: {metadata.get('lastUpdated', 'N/A')}")
    print(f"   - Source: {metadata.get('dataSource', 'N/A')}")
    
    # 2. Create Documents
    print("\n📄 Creating LangChain Documents...")
    documents = create_documents(properties)
    print(f"   - Created {len(documents)} documents")
    
    # 3. Ingest to Supabase
    print("\n☁️ Ingesting to Supabase Vector Store...")
    ingest_to_supabase(documents)
    
    print("\n🎉 Done! Properties are now searchable via RAG.")

if __name__ == "__main__":
    main()
