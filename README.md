# InsightLens - AI-Powered Company Research Assistant

InsightLens is an AI-powered research assistant designed to help users evaluate companies through the lens of value investing principles (Benjamin Graham/Warren Buffett approach). The system processes financial reports from the SEC EDGAR database or uploaded PDF documents and generates structured insight cards with analysis on various aspects of a company, including Business Summary, Moat & Edge, Basic Financial Health, and Management Snapshot. Featuring direct access to 10-K filings for the "Magnificent 7" tech companies and robust caching for efficient API usage.

## Currently Implemented Features

### Phase 1 Core
1. **Multiple Research Methods**
   - SEC EDGAR API integration for 10-K filings
   - PDF file upload with drag-and-drop support
   - "Quick 10-K" feature for Magnificent 7 companies

2. **Content Extraction & Processing**
   - SEC EDGAR API for efficient 10-K filing extraction
   - Smart PDF parsing with optimized processing
   - Headers management for SEC API compliance

3. **AI Analysis**
   - Hugging Face API integration (primary)
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

### Phase 1 Extended
1. **API Infrastructure Improvements**
   - Fixed OpenAI API key refreshing from environment variables
   - Implemented alternate AI providers for reliability
   - Added graceful degradation when API services are unavailable

2. **SEC EDGAR Search Enhancements**
   - Improved company search functionality in SEC EDGAR integration
   - Enhanced retrieval and processing of 10-K filings
   - Added better error handling for SEC API rate limiting

3. **Performance Optimization**
   - Implemented intelligent document sampling for large PDFs
   - Added content fingerprinting for cache lookup
   - Integrated robust caching for AI responses to reduce costs
   - Implemented parallel processing for PDF extraction

4. **Enhanced Error Handling**
   - Added user-friendly error messages for common issues
   - Improved error recovery for API failures
   - Added detailed logging for troubleshooting

5. **User Interface Improvements**
   - Added processing time tracking
   - Implemented clear processing status indicators
   - Improved styling consistency between light/dark modes
   - Enhanced Research Methods card styling in both themes

## Technical Stack

- **Backend**: Python with Flask
- **Frontend**: Bootstrap 5 with custom CSS
- **Database**: PostgreSQL
- **AI Integration**: Hugging Face API (primary), OpenAI API (optional)
- **Document Processing**: PyPDF2, LangChain, BeautifulSoup4
- **Performance**: Parallel processing, content fingerprinting, caching
- **SEC Integration**: EDGAR API with multiple extraction methods
- **Deployment**: Replit

## Project Structure

```
└── InsightLens/
    ├── app.py                 # Flask application configuration
    ├── main.py                # Entry point
    ├── models.py              # Database models
    ├── create_test_pdf.py     # Utility to create test documents
    ├── routes/                # Web route handlers
    │   ├── __init__.py
    │   ├── document_routes.py # Document upload and processing routes
    │   ├── insight_routes.py  # Insight display and status API
    │   └── edgar_routes.py    # SEC EDGAR search and processing
    ├── services/              # Business logic
    │   ├── __init__.py
    │   ├── ai_service.py      # AI provider interface (OpenAI/Hugging Face)
    │   ├── cache_service.py   # Content caching for performance
    │   ├── demo_service.py    # Demo mode without API costs
    │   ├── document_processor.py # Document processing pipeline
    │   ├── edgar_service.py   # SEC EDGAR API integration
    │   ├── open_source_ai.py  # Hugging Face AI integration
    │   ├── pdf_parser.py      # Advanced PDF extraction
    │   └── url_parser.py      # Intelligent URL content extraction
    ├── static/
    │   ├── css/
    │   │   └── custom.css     # Custom styling
    │   └── js/
    │       └── app.js         # Frontend functionality
    ├── templates/             # HTML templates
    │   ├── base.html          # Base template with layout
    │   ├── index.html         # Homepage/upload form
    │   ├── insights.html      # Insight display page
    │   └── edgar_search.html  # SEC search results
    ├── uploads/               # User file uploads
    └── cache/                 # Persistent cache storage
```

## Known Limitations

- Large PDFs (>500 pages) use intelligent sampling for better performance
- API rate limits apply for SEC EDGAR and AI services
- Document processing time varies based on file size and AI provider load
- Analysis quality depends on document content quality and depth
- Demo mode provides sample insights without API costs but with less specificity

## Legal Notice

This tool is designed as a research assistant, not a financial advisor. Always perform your own due diligence before making investment decisions.

## Local Development Setup

1. **Set up environment variables**
   Create a `.env` file with:
   ```
   FLASK_SECRET_KEY=your_random_secret_key
   DATABASE_URL=postgresql://username:password@localhost:5432/insightlens

   # Choose ONE AI provider:

   # Option 1: Hugging Face (recommended)
   HUGGINGFACE_API_KEY=your_huggingface_api_key
   AI_MODEL_TYPE=huggingface
   HUGGINGFACE_MODEL=mistral  # Options: mistral, llama3, deepseek
   
   # Option 2: OpenAI
   # OPENAI_API_KEY=your_openai_api_key
   # AI_MODEL_TYPE=openai
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
