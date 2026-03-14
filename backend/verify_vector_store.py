#!/usr/bin/env python3
"""
Osool Vector Store Verification Script
---------------------------------------
Verifies that the RAG system is working and data has been ingested.

Usage:
    python verify_vector_store.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def verify():
    print("=" * 60)
    print("🔍 OSOOL VECTOR STORE VERIFICATION")
    print("=" * 60)
    
    # 1. Check Environment
    print("\n1️⃣ Checking Environment Variables...")
    missing = []
    if not SUPABASE_URL: missing.append("SUPABASE_URL")
    if not SUPABASE_KEY: missing.append("SUPABASE_KEY")
    if not OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
    
    if missing:
        print(f"   ❌ Missing: {', '.join(missing)}")
        print("   Please set these in your .env file")
        return False
    print("   ✅ All environment variables set")
    
    # 2. Connect to Supabase
    print("\n2️⃣ Connecting to Supabase...")
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("   ✅ Connected to Supabase")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # 3. Check Documents Table
    print("\n3️⃣ Checking 'documents' table...")
    try:
        result = supabase.table("documents").select("id", count="exact").limit(5).execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        print(f"   ✅ Found {count} documents in vector store")
        
        if count == 0:
            print("   ⚠️ No documents found! Run: python ingest_data.py")
            return False
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        print("   Make sure 'documents' table exists with pgvector extension")
        return False
    
    # 4. Test Vector Search
    print("\n4️⃣ Testing Vector Search...")
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import SupabaseVectorStore
        
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="documents",
            query_name="match_documents"
        )
        
        # Test query
        test_results = vector_store.similarity_search("villa in New Cairo", k=3)
        
        if test_results:
            print(f"   ✅ Vector search working! Found {len(test_results)} results")
            print("\n   📋 Sample Results:")
            for i, doc in enumerate(test_results, 1):
                title = doc.metadata.get('title', 'N/A')[:50]
                price = doc.metadata.get('price', 0)
                print(f"      {i}. {title}... ({price:,.0f} EGP)")
        else:
            print("   ⚠️ No results found for test query")
            
    except Exception as e:
        print(f"   ❌ Vector search failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE - RAG System Ready!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    verify()
