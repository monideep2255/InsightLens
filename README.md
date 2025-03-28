# InsightLens - AI-Powered Company Research Assistant

InsightLens is an AI-powered tool that analyzes company documents through the lens of value investing principles (Benjamin Graham/Warren Buffett approach). It processes financial documents from multiple sources (SEC EDGAR API, URLs, or PDF uploads) and generates structured insights about business models, competitive advantages, financial health, and management quality.

## Project Structure

```
└── InsightLens/
    ├── app.py             # Flask application configuration
    ├── main.py            # Entry point for running the application
    ├── models.py          # Database models (Document, Insight, Processing)
    ├── routes/            # Web route handlers
    │   ├── __init__.py
    │   ├── document_routes.py  # Routes for document upload and management
    │   ├── insight_routes.py   # Routes for displaying insights
    │   └── edgar_routes.py     # Routes for SEC EDGAR API integration
    ├── services/          # Business logic services
    │   ├── __init__.py
    │   ├── ai_service.py       # AI insight generation using OpenAI
    │   ├── document_processor.py  # Document processing orchestration
    │   ├── pdf_parser.py       # PDF content extraction
    │   ├── url_parser.py       # URL content extraction
    │   └── edgar_service.py    # SEC EDGAR API integration
    ├── static/            # Static assets
    │   ├── css/
    │   │   └── custom.css      # Custom styles
    │   └── js/
    │       └── app.js          # Client-side JavaScript
    ├── templates/         # HTML templates
    │   ├── base.html           # Base template with common layout
    │   ├── index.html          # Home/upload page
    │   ├── insights.html       # Insights display page
    │   └── edgar_search.html   # SEC EDGAR search page
    └── uploads/           # Storage for uploaded PDF files
```

## Features

### Phase 1 (Implemented)

1. **Multiple Research Methods**
   - SEC EDGAR API integration for 10-K filings (free, preferred option)
   - URL input for company websites with automatic PDF detection
   - PDF file upload with drag-and-drop support
   - Comprehensive "Research Methods" section explaining when to use each approach

2. **Content Extraction & Processing**
   - SEC EDGAR API for efficient 10-K filing extraction
   - Smart PDF parsing with optimized processing for large documents
   - Intelligent sampling of key sections for better performance
   - Web content extraction with automatic PDF link detection
   - Headers management for SEC API compliance

3. **AI Analysis**
   - Integration with OpenAI (GPT-4o model)
   - Custom prompts for each insight category
   - Structured HTML output for each insight

4. **Insight Categories**
   - Business Summary: Core business model and operations
   - Moat & Competitive Edge: Durable advantages and market position
   - Financial Health: Key financial metrics and trends
   - Management Snapshot: Leadership team assessment

5. **User Experience**
   - Responsive design optimized for mobile and tablet devices
   - Dark/light mode toggle with localStorage theme persistence
   - Real-time processing status updates
   - Organized insight cards for easy review
   - Comprehensive error handling and user feedback

## Technical Implementation

### Backend

- **Flask**: Web framework for handling HTTP requests
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Database for storing documents and insights
- **LangChain**: Framework for document processing and text manipulation
- **OpenAI API**: AI model for generating insights (using gpt-4o)
- **Trafilatura**: Library for extracting content from web pages
- **PyPDF2**: Library for PDF processing with intelligent page sampling
- **BeautifulSoup4**: Library for HTML parsing and SEC EDGAR document processing

### Frontend

- **Bootstrap**: Framework for responsive UI components
- **JavaScript**: Client-side interactivity, AJAX requests, and theme toggling
- **Font Awesome**: Icon library for visual elements
- **CSS Variables**: For theme customization (dark/light mode)

### Database Schema

- **Document**: Stores uploaded files, URLs, or SEC EDGAR documents
  - id (Primary Key)
  - filename (for PDFs)
  - url (for web pages or SEC EDGAR URLs)
  - title (document title or company name)
  - content_type ('pdf', 'url', or 'edgar')
  - created_at (timestamp)
  - processed (boolean indicating completion status)

- **Insight**: Stores AI-generated insights with formatted HTML content
  - id (Primary Key)
  - document_id (Foreign Key to Document)
  - category ('business_summary', 'moat', 'financial', 'management')
  - content (HTML formatted insight content)
  - created_at (timestamp of insight generation)

- **Processing**: Tracks document processing status for progress monitoring
  - id (Primary Key)
  - document_id (Foreign Key to Document)
  - status ('pending', 'processing', 'completed', 'failed')
  - error (detailed error message, if applicable)
  - started_at (processing start timestamp)
  - completed_at (processing end timestamp)

## Usage

### SEC EDGAR Search (Recommended Method)
1. Click on "SEC Search" in the navigation menu
2. Enter a company name in the search box
3. Select the company from the search results
4. The system will automatically fetch and analyze the latest 10-K filing
5. View the AI-generated insights organized by category

### URL Analysis
1. Visit the home page
2. Enter a company's website URL in the URL input field
3. Click "Analyze URL"
4. Wait for processing to complete (the system will automatically find and extract PDF annual reports if available)
5. View the AI-generated insights organized by category

### PDF Upload
1. Visit the home page
2. Drag and drop a PDF file or click to browse your files
3. Upload a financial document (annual report, 10-K, etc.)
4. Wait for processing to complete (large PDFs use smart sampling for faster processing)
5. View the AI-generated insights organized by category

## Error Handling

- **Input Validation**
  - PDF file format and size validation
  - URL format and accessibility checking
  - SEC CIK number validation
  
- **Processing Monitoring**
  - Real-time status updates using AJAX
  - Background task tracking in database
  - Timeout handling for long-running processes
  
- **SEC API Compliance**
  - Custom User-Agent headers to prevent 403 errors
  - Rate limiting implementation
  - Error handling for API changes or service disruptions
  
- **PDF Processing Optimization**
  - Fallback to page sampling for large documents
  - Intelligent section extraction
  - Error handling for corrupted PDFs
  
- **AI Service Integration**
  - Error handling for API limits and timeouts
  - Retry logic for transient failures
  - Proper error messages for failed analysis

## Future Enhancements (Planned for Phase 2)

- **User Accounts & History**
  - User registration and authentication
  - Personal document library
  - Saved insights history
  
- **Enhanced Analysis Features**
  - Additional insight categories (e.g., Industry Analysis, Risk Assessment)
  - Competitor comparison
  - Trend analysis over time (multiple reports)
  - Financial ratio calculations
  
- **Productivity Features**
  - Export to PDF/CSV for offline reference
  - Email notifications when processing completes
  - Customizable analysis parameters
  - Batch processing for multiple documents
  
- **Advanced Research Tools**
  - Integration with additional financial data sources
  - Custom questions and answers about the document
  - Highlight important sections of original document
  - Automatic footnote analysis