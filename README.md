# InsightLens - AI-Powered Company Research Assistant

InsightLens is an AI-powered tool that analyzes company documents through the lens of value investing principles. It processes uploaded PDF documents or website URLs and generates structured insights about business models, competitive advantages, financial health, and management quality.

## Project Structure

```
└── InsightLens/
    ├── app.py             # Flask application configuration
    ├── main.py            # Entry point for running the application
    ├── models.py          # Database models (Document, Insight, Processing)
    ├── routes/            # Web route handlers
    │   ├── __init__.py
    │   ├── document_routes.py  # Routes for document upload and management
    │   └── insight_routes.py   # Routes for displaying insights
    ├── services/          # Business logic services
    │   ├── __init__.py
    │   ├── ai_service.py       # AI insight generation using OpenAI
    │   ├── document_processor.py  # Document processing orchestration
    │   ├── pdf_parser.py       # PDF content extraction
    │   └── url_parser.py       # URL content extraction
    ├── static/            # Static assets
    │   ├── css/
    │   │   └── custom.css      # Custom styles
    │   └── js/
    │       └── app.js          # Client-side JavaScript
    ├── templates/         # HTML templates
    │   ├── base.html           # Base template with common layout
    │   ├── index.html          # Home/upload page
    │   └── insights.html       # Insights display page
    └── uploads/           # Storage for uploaded PDF files
```

## Features

### Phase 1 (Implemented)

1. **Document Upload**
   - PDF file upload with drag-and-drop support
   - URL input for web page analysis
   - Validation for file formats and URLs

2. **Content Extraction**
   - PDF parsing using LangChain and PyPDF2
   - Web content extraction using Trafilatura

3. **AI Analysis**
   - Integration with OpenAI (GPT-4o model)
   - Custom prompts for each insight category
   - Structured HTML output for each insight

4. **Insight Categories**
   - Business Summary: Core business model and operations
   - Moat & Competitive Edge: Durable advantages and market position
   - Financial Health: Key financial metrics and trends
   - Management Snapshot: Leadership team assessment

5. **User Interface**
   - Responsive design using Bootstrap
   - Real-time processing status updates
   - Organized insight cards for easy review
   - Error handling and user feedback

## Technical Implementation

### Backend

- **Flask**: Web framework for handling HTTP requests
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Database for storing documents and insights
- **LangChain**: Framework for document processing and text manipulation
- **OpenAI API**: AI model for generating insights
- **Trafilatura**: Library for extracting content from web pages

### Frontend

- **Bootstrap**: Framework for responsive UI components
- **JavaScript**: Client-side interactivity and AJAX requests
- **Font Awesome**: Icon library for visual elements

### Database Schema

- **Document**: Stores uploaded files or URLs
  - id (Primary Key)
  - filename (for PDFs)
  - url (for web pages)
  - title
  - content_type ('pdf' or 'url')
  - created_at
  - processed (boolean)

- **Insight**: Stores AI-generated insights
  - id (Primary Key)
  - document_id (Foreign Key)
  - category ('business_summary', 'moat', 'financial', 'management')
  - content (HTML)
  - created_at

- **Processing**: Tracks document processing status
  - id (Primary Key)
  - document_id (Foreign Key)
  - status ('pending', 'processing', 'completed', 'failed')
  - error (if any)
  - started_at
  - completed_at

## Usage

1. Visit the home page
2. Choose between PDF upload or URL input
3. Submit a document for analysis
4. Wait for processing to complete
5. View the generated insights organized by category

## Error Handling

- Validation for PDF files and URLs
- Processing status tracking
- Detailed error messages for failed operations
- Graceful fallback for AI service errors

## Future Enhancements (Planned)

- User accounts and document history
- Additional insight categories
- Export to PDF/CSV
- Customizable analysis parameters
- Batch processing for multiple documents