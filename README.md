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

### Future Enhancements (Planned for Phase 2)

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

## Technical Implementation

### Backend

- **Flask**: Web framework for handling HTTP requests
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Database for storing documents and insights
- **LangChain**: Framework for document processing and text manipulation
- **AI Integration**:
  - **OpenAI API** (default): Primary AI model for generating insights (using gpt-4o)
  - **Hugging Face API** (alternative): Support for open source models (Mistral, Llama 3, DeepSeek)
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

## AI Model Selection Process

When you click "Analyze with AI" on any document (SEC EDGAR, URL, or PDF), the system follows this process:

1. **Model Selection**: The system checks which AI provider to use based on environment variables:
   - `AI_MODEL_TYPE=openai` (default): Uses OpenAI's GPT-4o model
   - `AI_MODEL_TYPE=huggingface`: Uses models from Hugging Face
   
2. **Hugging Face Model Selection**: If using Hugging Face, the system selects a specific model:
   - `HUGGINGFACE_MODEL=mistral` (default): Uses Mistral model
   - `HUGGINGFACE_MODEL=llama3`: Uses Llama 3 model
   - `HUGGINGFACE_MODEL=deepseek`: Uses DeepSeek model

3. **Document Processing**: The system extracts and preprocesses text content from the document

4. **Insight Generation**: For each insight category (Business Summary, Moat, Financial Health, Management), 
   the system sends customized prompts to the selected AI model

5. **Response Processing**: The system formats and stores the AI responses in the database

## Usage

### SEC EDGAR Search (Recommended Method)
1. Click on "SEC Search" in the navigation menu
2. Enter a company name in the search box (e.g., "Apple" or "Microsoft")
3. Select the company from the search results
4. **Important**: The system will locate the most recent 10-K (annual report) filing. Look for:
   - The filing with "10-K" in the description
   - The most recent date (typically the top result)
   - Avoid selecting other filing types like 10-Q (quarterly reports) or 8-K (current reports)
5. The system will automatically fetch and analyze the selected 10-K filing
6. View the AI-generated insights organized by category

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

## Performance Optimizations

The application has been optimized for better performance and faster processing:

- **Document Content Optimization**
  - Smart content selection for large documents (beginning, middle, end extraction)
  - Content truncation to stay within optimal AI model token limits
  - Intelligent summary generation for large documents before analysis

- **AI Processing Optimizations**
  - Two-stage AI processing for large documents (summary → detailed analysis)
  - Reduced temperature settings for more focused, concise responses
  - Proper prompt engineering to reduce token usage and improve efficiency

- **SEC Edgar Processing**
  - Multiple fallback mechanisms for different SEC document formats
  - Special handling for iXBRL documents with direct text extraction
  - Automatic fallback to SEC TXT format for faster processing

- **PDF Processing**
  - Three-tier processing for different PDF sizes:
    - Full extraction for small documents (<30 pages)
    - Sample every 3rd page for medium-sized documents (30-100 pages)
    - Strategic sampling for large documents (>100 pages)
  - Intelligent page selection focusing on key document sections

- **URL Processing**
  - Enhanced user agent settings to prevent access blocking
  - Multi-stage content extraction with fallbacks
  - Special handlers for problematic domains (Amazon IR, etc.)
  - Automatic handling for 403/401 errors with alternative extraction methods

## Known Limitations

- **OpenAI API Quota**
  - The application relies on OpenAI's API for insight generation
  - Free API keys have limited quota and may encounter "insufficient_quota" errors
  - Consider upgrading to a paid OpenAI plan or switching to Hugging Face models

- **Restricted Websites**
  - Some financial websites (like ir.aboutamazon.com) block scraping attempts
  - Alternative content is provided for these sites with a notice to the user
  - For best results, use SEC EDGAR directly for these companies

- **Large PDF Performance**
  - Very large PDFs (>500 pages) will use intelligent sampling
  - This sampling may miss some content details but captures key sections
  - Analysis quality depends on the document structure and content distribution

- **SEC API Rate Limits**
  - Heavy usage of SEC EDGAR API may trigger rate limiting
  - Implement proper throttling in high-traffic scenarios

- **AI Analysis Limitations**
  - Analysis quality depends on document content quality and relevance
  - Numerical interpretations may vary depending on document context
  - Financial insights require proper context from official documents

## Local Development Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL (local installation or Docker)
- Either one of the following:
  - OpenAI API key (default option for AI-powered analysis)
  - Hugging Face API key (alternative for using open source models)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/insightlens.git
   cd insightlens
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following content:
   ```
   # Required configuration
   FLASK_SECRET_KEY=your_random_secret_key
   DATABASE_URL=postgresql://username:password@localhost:5432/insightlens
   
   # AI model configuration (choose one provider)
   
   # Option 1: OpenAI (default)
   OPENAI_API_KEY=your_openai_api_key
   AI_MODEL_TYPE=openai
   
   # Option 2: Hugging Face (alternative)
   # HUGGINGFACE_API_KEY=your_huggingface_api_key
   # AI_MODEL_TYPE=huggingface
   # HUGGINGFACE_MODEL=mistral  # Options: mistral (default), llama3, deepseek
   ```

5. **Set up the database**
   ```bash
   # Create PostgreSQL database
   createdb insightlens

   # Initialize the database (tables will be created on first run)
   python main.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```
   The application will be available at http://localhost:5000

### Docker Setup (Alternative)

If you prefer using Docker:

1. **Build the Docker image**
   ```bash
   docker build -t insightlens .
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up
   ```