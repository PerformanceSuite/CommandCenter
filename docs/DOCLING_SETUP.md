# Docling Integration & Setup

## What is Docling?

Docling is an advanced document processing library that powers CommandCenter's RAG (Retrieval Augmented Generation) knowledge base. It converts various document formats into structured, searchable content.

**Supported Formats:**
- PDF documents
- Microsoft Word (.docx)
- PowerPoint (.pptx)
- Markdown (.md)
- HTML files
- Plain text

---

## Installation

### Docker (Automatic - Recommended)

Docling is automatically installed in the Docker backend container via `requirements.txt`:

```txt
docling==1.0.0
```

No manual installation needed! Just run:

```bash
docker-compose up -d
```

### Local Development (Manual)

If running backend locally without Docker:

```bash
cd backend
pip install docling==1.0.0
```

**System Requirements:**
- Python 3.11+
- 2GB+ RAM recommended
- Poppler (for PDF processing)

**Install Poppler:**

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows (via Chocolatey)
choco install poppler
```

---

## How CommandCenter Uses Docling

### Document Processing Pipeline

```
1. Upload Document
   ↓
2. Docling Extracts:
   - Text content
   - Structure (headings, paragraphs)
   - Tables and lists
   - Metadata
   ↓
3. Text Chunking
   - Break into semantic chunks
   - Preserve context
   ↓
4. Embedding Generation
   - Convert chunks to vectors
   - Store in ChromaDB
   ↓
5. RAG Ready
   - Searchable via natural language
   - Context-aware retrieval
```

### Where Docling Runs

**Backend Service** (`app/services/rag_service.py`):

```python
from docling.document_converter import DocumentConverter

class RAGService:
    def __init__(self):
        self.converter = DocumentConverter()

    async def process_document(self, file_path: str):
        # Docling converts document
        result = self.converter.convert(file_path)

        # Extract structured content
        text = result.document.export_to_markdown()

        # Process for RAG
        chunks = self._chunk_text(text)
        embeddings = self._generate_embeddings(chunks)

        # Store in ChromaDB
        self.chroma_collection.add(
            documents=chunks,
            embeddings=embeddings
        )
```

---

## Configuration

### Environment Variables

Docling configuration via `.env`:

```bash
# RAG Storage Paths
RAG_STORAGE_PATH=/app/rag_storage
CHROMADB_PATH=/app/rag_storage/chromadb

# Docling Processing Settings
DOCLING_MAX_FILE_SIZE=50  # MB
DOCLING_TIMEOUT=300        # seconds per file
```

### Advanced Configuration

Create `backend/docling_config.yaml` (optional):

```yaml
# Docling Document Converter Settings
converter:
  # PDF processing
  pdf:
    ocr_enabled: true        # Enable OCR for scanned PDFs
    extract_images: false    # Extract images from PDFs

  # Image processing
  image:
    dpi: 300                 # Image resolution for OCR

  # Performance
  max_workers: 4             # Parallel processing threads

  # Output
  preserve_formatting: true  # Keep original formatting
  extract_tables: true       # Parse tables into structured data
```

---

## Usage Examples

### 1. Upload Research Document

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/knowledge/upload \
  -F "file=@research-paper.pdf" \
  -F "title=AI Music Generation Research" \
  -F "tags=ai,music,research"

# Response
{
  "id": "kb_123",
  "title": "AI Music Generation Research",
  "status": "processing",
  "pages": 15
}
```

### 2. Check Processing Status

```bash
curl http://localhost:8000/api/v1/knowledge/kb_123

# Response
{
  "id": "kb_123",
  "status": "completed",
  "chunks": 42,
  "processed_at": "2025-10-05T15:30:00Z"
}
```

### 3. Query Knowledge Base

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest AI music generation techniques?",
    "limit": 5
  }'

# Response
{
  "results": [
    {
      "text": "Recent advances in AI music generation include...",
      "source": "AI Music Generation Research",
      "page": 3,
      "relevance": 0.95
    }
  ]
}
```

---

## Supported Document Types

### Research Papers (PDF)

**Best for:**
- Academic papers
- Technical specifications
- White papers

**Processing:**
- OCR for scanned documents
- Table extraction
- Citation parsing
- Figure descriptions

**Example:**
```bash
# Upload research paper
curl -X POST http://localhost:8000/api/v1/knowledge/upload \
  -F "file=@JUCE-Framework-Whitepaper.pdf"
```

### Documentation (Markdown)

**Best for:**
- Technical docs
- README files
- GitHub wiki pages

**Processing:**
- Preserves formatting
- Extracts code blocks
- Maintains links
- Parses headers

**Example:**
```bash
# Upload documentation
curl -X POST http://localhost:8000/api/v1/knowledge/upload \
  -F "file=@JUCE-Documentation.md"
```

### Presentations (PowerPoint)

**Best for:**
- Conference presentations
- Technical talks
- Internal presentations

**Processing:**
- Slide-by-slide extraction
- Speaker notes included
- Image descriptions

### Word Documents

**Best for:**
- Reports
- Proposals
- Meeting notes

**Processing:**
- Full text extraction
- Preserves structure
- Table parsing

---

## Performance Optimization

### Document Size Limits

```bash
# .env configuration
DOCLING_MAX_FILE_SIZE=50  # MB per file

# For larger documents, split first:
pdftk large-document.pdf burst output page-%04d.pdf
```

### Processing Time

**Typical processing times:**
- 10-page PDF: ~5 seconds
- 50-page PDF: ~20 seconds
- 200-page PDF: ~60 seconds
- 500-page PDF: ~180 seconds

**Factors affecting speed:**
- Document complexity
- OCR requirement
- Number of images/tables
- Server resources

### Batch Processing

Process multiple documents efficiently:

```python
# Backend example
async def batch_process(files: list):
    tasks = [
        process_document(file)
        for file in files
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Troubleshooting

### Problem: "Docling not found"

**Cause:** Docling not installed

**Fix:**
```bash
# Docker - rebuild backend
docker-compose build backend
docker-compose up -d

# Local - install manually
pip install docling==1.0.0
```

### Problem: "PDF processing failed"

**Cause:** Poppler not installed

**Fix:**
```bash
# macOS
brew install poppler

# Ubuntu
sudo apt-get install poppler-utils

# Verify installation
pdfinfo --version
```

### Problem: "OCR not working"

**Cause:** Tesseract OCR not installed

**Fix:**
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr

# Add language packs if needed
brew install tesseract-lang  # macOS
sudo apt-get install tesseract-ocr-all  # Ubuntu
```

### Problem: "Processing timeout"

**Cause:** Document too large or complex

**Fix:**
```bash
# Increase timeout in .env
DOCLING_TIMEOUT=600  # 10 minutes

# Or split document
pdftk input.pdf cat 1-50 output part1.pdf
pdftk input.pdf cat 51-100 output part2.pdf
```

### Problem: "Low quality OCR results"

**Cause:** Low DPI in scanned PDFs

**Fix:**
```yaml
# docling_config.yaml
converter:
  image:
    dpi: 600  # Increase from default 300
```

---

## Data Storage

### File System Structure

```
rag_storage/
├── uploads/                    # Original uploaded files
│   ├── kb_123_paper.pdf
│   └── kb_124_docs.md
│
├── processed/                  # Docling processed output
│   ├── kb_123_paper.json      # Structured content
│   └── kb_124_docs.json
│
└── chromadb/                   # Vector database
    ├── chroma.sqlite3
    └── embeddings/
```

### Backup Strategy

```bash
# Backup entire RAG storage
docker run --rm \
  -v commandcenter_rag_storage:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/rag-$(date +%Y%m%d).tar.gz /data

# Restore from backup
docker run --rm \
  -v commandcenter_rag_storage:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/rag-20251005.tar.gz -C /
```

---

## Advanced Features

### Custom Document Processors

Extend Docling for custom formats:

```python
# backend/app/services/custom_processor.py
from docling.document_converter import DocumentConverter

class CustomProcessor:
    def __init__(self):
        self.converter = DocumentConverter()

    def process_jupyter_notebook(self, file_path: str):
        """Process Jupyter notebooks"""
        # Custom processing logic
        with open(file_path) as f:
            notebook = json.load(f)

        # Extract cells
        text = "\n\n".join([
            cell['source']
            for cell in notebook['cells']
            if cell['cell_type'] == 'markdown'
        ])

        return text
```

### Metadata Extraction

```python
# Extract rich metadata
result = converter.convert(file_path)

metadata = {
    "title": result.document.metadata.title,
    "author": result.document.metadata.author,
    "pages": len(result.document.pages),
    "tables": len(result.document.tables),
    "created": result.document.metadata.creation_date
}
```

### Table Extraction

```python
# Get structured tables
for table in result.document.tables:
    df = table.to_dataframe()  # Convert to pandas DataFrame
    # Store in database or process further
```

---

## Integration with RAG

### Chunking Strategy

Docling output is chunked for optimal RAG performance:

```python
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Chunk text with overlap for better context preservation

    Args:
        text: Docling-processed text
        chunk_size: Characters per chunk
        overlap: Character overlap between chunks
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks
```

### Embedding Generation

```python
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_embeddings(chunks: list[str]):
    """Generate embeddings for chunks"""
    embeddings = []

    for chunk in chunks:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        )
        embeddings.append(response.data[0].embedding)

    return embeddings
```

### ChromaDB Storage

```python
import chromadb

chroma_client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
collection = chroma_client.get_or_create_collection("research")

# Store processed documents
collection.add(
    documents=chunks,
    embeddings=embeddings,
    metadatas=[{"source": "paper.pdf", "page": i} for i in range(len(chunks))],
    ids=[f"chunk_{i}" for i in range(len(chunks))]
)

# Query
results = collection.query(
    query_texts=["What is JUCE?"],
    n_results=5
)
```

---

## Monitoring

### Processing Logs

```bash
# View Docling processing logs
docker-compose logs -f backend | grep docling

# Example output
[INFO] Docling: Processing paper.pdf
[INFO] Docling: Extracted 42 pages
[INFO] Docling: Found 7 tables
[INFO] Docling: Generated 128 chunks
[INFO] Docling: Completed in 15.3s
```

### Metrics

Track Docling performance:

```python
# backend/app/routers/knowledge.py
import time

@router.post("/upload")
async def upload_document(file: UploadFile):
    start = time.time()

    # Process with Docling
    result = await rag_service.process_document(file)

    duration = time.time() - start

    # Log metrics
    logger.info(f"Processed {file.filename} in {duration:.2f}s")

    return {
        "id": result.id,
        "duration": duration,
        "chunks": len(result.chunks)
    }
```

---

## Best Practices

### 1. Document Preparation

**Before uploading:**
- ✅ Remove sensitive information
- ✅ Ensure PDFs are not password-protected
- ✅ Use descriptive filenames
- ✅ Add relevant tags

### 2. Optimal Formats

**Preferred:**
- PDF with embedded text (not scanned)
- Markdown with clear structure
- DOCX with styles

**Avoid:**
- Scanned PDFs without OCR
- Images of text
- Complex layouts

### 3. Size Management

```bash
# Check document size before upload
ls -lh research-paper.pdf

# Compress large PDFs
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=compressed.pdf input.pdf
```

### 4. Regular Maintenance

```bash
# Clean up old processed files (example)
find rag_storage/processed -mtime +90 -delete

# Optimize ChromaDB
docker-compose exec backend python -c "
from app.services.rag_service import rag_service
rag_service.optimize_index()
"
```

---

## References

- [Docling Documentation](https://github.com/DS4SD/docling)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

## Getting Help

- Docling Issues: https://github.com/DS4SD/docling/issues
- CommandCenter Issues: https://github.com/PerformanceSuite/CommandCenter/issues
- RAG Configuration: See [CONFIGURATION.md](./CONFIGURATION.md)

---

**Next Steps:**
- [Configuration Guide](./CONFIGURATION.md)
- [API Documentation](./API.md)
- [Data Isolation](./DATA_ISOLATION.md)
