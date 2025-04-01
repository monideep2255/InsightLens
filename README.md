# InsightLens - AI-Powered Company Research Assistant

InsightLens is an AI-powered tool that analyzes company documents through the lens of value investing principles (Benjamin Graham/Warren Buffett approach). It processes financial documents from multiple sources (SEC EDGAR API, URLs, or PDF uploads) and generates structured insights about business models, competitive advantages, financial health, and management quality.

## Currently Implemented Features (Phase 1)

1. **Multiple Research Methods**
   - SEC EDGAR API integration for 10-K filings
   - URL input for company websites with automatic PDF detection
   - PDF file upload with drag-and-drop support
   - "Quick 10-K" feature for Magnificent 7 companies

2. **Content Extraction & Processing**
   - SEC EDGAR API for efficient 10-K filing extraction
   - Smart PDF parsing with optimized processing
   - Web content extraction with PDF link detection
   - Headers management for SEC API compliance

3. **AI Analysis**
   - OpenAI API integration (primary)
   - Hugging Face API support (alternative)
   - Custom prompts for each insight category
   - Structured HTML output for insights

4. **Insight Categories**
   - Business Summary: Core business model and operations
   - Moat & Competitive Edge: Durable advantages and market position
   - Financial Health: Key financial metrics and trends
   - Management Snapshot: Leadership team assessment

5. **User Experience**
   - Dark/light mode toggle
   - Real-time processing status updates
   - Organized insight cards
   - Comprehensive error handling

## Technical Stack

- **Backend**: Python with Flask
- **Frontend**: Bootstrap with custom CSS
- **Database**: PostgreSQL
- **AI Integration**: OpenAI API (default) or Hugging Face API
- **Document Processing**: PyPDF2, Trafilatura, BeautifulSoup4
- **Deployment**: Replit

## Project Structure

```
└── InsightLens/
    ├── app.py             # Flask application configuration
    ├── main.py            # Entry point
    ├── models.py          # Database models
    ├── routes/            # Web route handlers
    │   ├── __init__.py
    │   ├── document_routes.py
    │   ├── insight_routes.py
    │   └── edgar_routes.py
    ├── services/          # Business logic
    │   ├── __init__.py
    │   ├── ai_service.py
    │   ├── document_processor.py
    │   ├── pdf_parser.py
    │   ├── url_parser.py
    │   └── edgar_service.py
    ├── static/
    │   ├── css/
    │   │   └── custom.css
    │   └── js/
    │       └── app.js
    └── templates/         # HTML templates
        ├── base.html
        ├── index.html
        ├── insights.html
        └── edgar_search.html
```

## Known Limitations

- Large PDFs (>500 pages) use intelligent sampling
- Some financial websites block scraping attempts
- API rate limits apply for SEC EDGAR and AI services
- Analysis quality depends on document content quality

## Legal Notice

This tool is designed as a research assistant, not a financial advisor. Always perform your own due diligence before making investment decisions.

## Local Development Setup

1. **Set up environment variables**
   Create a `.env` file with:
   ```
   FLASK_SECRET_KEY=your_random_secret_key
   DATABASE_URL=postgresql://username:password@localhost:5432/insightlens

   # Choose ONE AI provider:

   # Option 1: OpenAI (default)
   OPENAI_API_KEY=your_openai_api_key
   AI_MODEL_TYPE=openai

   # Option 2: Hugging Face
   # HUGGINGFACE_API_KEY=your_huggingface_api_key
   # AI_MODEL_TYPE=huggingface
   # HUGGINGFACE_MODEL=mistral  # Options: mistral, llama3, deepseek
   ```

2. **Initialize the database**
   ```bash
   python recreate_db.py
   ```

3. **Run the application**
   ```bash
   python main.py
   ```
   The application will be available at http://0.0.0.0:5000

## TO-DO Items

### Critical

- [ ] **OpenAI API Authentication Issues**
  - Fix issue with OpenAI API key not being properly refreshed from environment variables
  - Current error: "Incorrect API key provided: sk-proj-*" despite updating environment variables
  - Potential solution: Check if key needs to be in a different format (OpenAI Project API vs Organization API)

- [ ] **SEC EDGAR Search Functionality**
  - Fix company search functionality in SEC EDGAR integration
  - Ensure proper retrieval and processing of 10-K filings
  - Add better error handling for SEC API rate limiting

### Important

- [ ] **Performance Optimization**
  - Improve PDF processing speed for large documents
  - Add caching for API responses to reduce costs

- [ ] **Enhanced Error Handling**
  - Provide more user-friendly error messages
  - Implement graceful degradation when API services are unavailable

### Nice to Have

- [ ] **User Interface Improvements**
  - Add progress indicators for document processing
  - Implement document history view
  - Add filtering options for insights