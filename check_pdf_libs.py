#!/usr/bin/env python3
"""Check PDF processing library availability."""

print("🔍 Checking PDF Processing Libraries")
print("=" * 40)

# Check PyMuPDF
try:
    import fitz
    print("✅ PyMuPDF (fitz) available")
    print(f"   Version: {fitz.version}")
except ImportError as e:
    print("❌ PyMuPDF (fitz) not available")
    print(f"   Error: {e}")

# Check LangChain
try:
    from langchain_community.document_loaders import PyPDFLoader
    print("✅ LangChain available")
except ImportError as e:
    print("❌ LangChain not available")
    print(f"   Error: {e}")

# Check what's in the PDF processor
try:
    from app.services.pdf_processor import PYMUPDF_AVAILABLE
    print(f"✅ PDF Processor reports PyMuPDF available: {PYMUPDF_AVAILABLE}")
except ImportError as e:
    print(f"❌ Cannot import PDF processor: {e}")

# Check what's in the LangChain processor
try:
    from app.services.langchain_pdf_processor import LANGCHAIN_AVAILABLE
    print(f"✅ LangChain Processor reports LangChain available: {LANGCHAIN_AVAILABLE}")
except ImportError as e:
    print(f"❌ Cannot import LangChain processor: {e}")

print("\n💡 Installation commands:")
print("   PyMuPDF: pip install PyMuPDF")
print("   LangChain: pip install langchain langchain-community unstructured")