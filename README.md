*Last Updated: April 9, 2025*

# InsightLens - AI-Powered Company Research Assistant

InsightLens is an AI-powered research assistant designed to help users evaluate companies through the lens of value investing principles (Benjamin Graham/Warren Buffett approach). The system processes financial reports from the SEC EDGAR database or uploaded PDF documents and generates structured insight cards with analysis on various aspects of a company, including Business Summary, Moat & Edge, Basic Financial Health, and Management Snapshot. Featuring direct access to 10-K filings for the "Magnificent 7" tech companies and robust caching for efficient API usage.

## Project Approach & Development Journey

### Initial Planning & Documentation
The project began with comprehensive planning using a Product Requirements Document (PRD) and Technical Specification. This foundational work established:

1. **Background Research**: Explored value investing principles (Graham/Buffett) and identified gaps in existing tools.
2. **Problem Definition**: Recognized the need for an AI-powered tool to streamline document analysis with value investing principles.
3. **User Stories**: Created detailed personas (investors, researchers, students) to guide feature development.
4. **Feature Roadmap**: Structured development into 5 distinct phases:
   - Phase 1: Core Upload & Summarize
   - Phase 2: Value Investing Analysis
   - Phase 3: Scoring Framework
   - Phase 4: Augmented Research
   - Phase 5: AI Recommendations

### Technical Architecture
Working with Replit's AI tools, key technical decisions were made:

1. **Stack Selection**:
   - Python/Flask for robust backend processing
   - Bootstrap for responsive frontend
   - PostgreSQL for data persistence
   - AI Integration via multiple providers

2. **Core Components**:
   - Document processing pipeline
   - AI service abstraction layer
   - Caching system for API efficiency
   - SEC EDGAR integration

### Implementation Strategy
The development followed a methodical approach:

1. **Phase 1 Implementation**:
   - Built core document processing
   - Integrated AI analysis pipeline
   - Created insight card system
   - Implemented caching

2. **Phase 2 Enhancements**:
   - Added value investing lens
   - Developed red flag detection
   - Created biotech analysis mode
   - Enhanced moat analysis

### Testing & Refinement
Each feature underwent thorough testing:

1. **Test Cases**:
   - Document processing accuracy
   - AI analysis quality
   - Edge case handling
   - Performance optimization

2. **Iterative Improvements**:
   - Enhanced prompt engineering
   - Optimized processing pipeline
   - Improved error handling
   - Added comprehensive logging

This systematic approach, combining thorough planning with iterative development and testing, has resulted in a robust tool that effectively merges value investing principles with modern AI capabilities.

## Current UI State (Phase 2)

### Dark Mode
<img src="docs/phase2_screenshots/Phase%202%20dark%20mode.png" alt="InsightLens Dark Mode" width="600"/>
*Dark mode interface showing the main analysis page with value investing and biotech analysis options*

### Light Mode
<img src="docs/phase2_screenshots/Phase%202%20light%20mode.png" alt="InsightLens Light Mode" width="600"/>
*Light mode interface demonstrating the clean, minimal design with all analysis features*

## Legal Notice

This tool is designed as a research assistant, not a financial advisor. Always perform your own due diligence before making investment decisions.

## Currently Implemented Features

### ✨ Phase 1: Upload + Summarize (MVP Core)
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

### ⚖️ Phase 2: Value Investing Lens
1. **Red Flag Detection**
   - Analysis to identify potential warning signs in SEC filings
   - Severity indicators for risk assessment (low, medium, high)

2. **"Would Buffett Invest?" Analysis**
   - Specialized analysis based on Warren Buffett's investment criteria
   - Assessment of value investment principles alignment

3. **Biotech Analysis Mode**
   - Specialized analysis for biotech/pharmaceutical companies
   - Pipeline analysis, regulatory approvals, and clinical trial progress

4. **Enhanced Moat Analysis**
   - Deeper competitive advantage analysis
   - Quantifiable assessment of moat strength
   - Specific competitive advantage identification

5. **Margin of Safety Commentary**
   - Automated price and value assessment
   - Fundamental analysis-based guidance
   - Safety margin evaluation

### Phase 2 Technical Features
1. **API Cost Management**
   - Token usage tracking
   - Monthly budget monitoring and alerts
   - Admin usage statistics dashboard

2. **Industry-Specific Analysis**
   - Specialized templates for Technology, Financial Services, Healthcare/Biotech, and Retail
   - Industry-specific metrics and considerations

3. **Document Comparison**
   - Compare company documents over time
   - Track business model and financial evolution

4. **Export & Sharing**
   - PDF export with professional formatting
   - Shareable analysis links with expiration dates
   - Link management interface

5. **Insight Regeneration**
   - Ability to regenerate individual insight sections
   - Targeted refinement capabilities

## Future Phases

### 📊 Phase 3: Scoring & Evaluation Framework
This phase adds a scoring interface. Users can evaluate companies via sliders and checklists, save results, and export investment memos. This helps apply a consistent methodology across different companies.

Key Features:
- Interactive scorecard (editable sliders/checklist)
- Save & tag companies
- Exportable insights/memos
- Internal dashboard with history

### 🧠 Phase 4: Augmented Research & Comparison
This phase enhances the assistant with autonomous research capabilities. AI agents can fetch data from external sources, monitor changes, and generate comparisons between companies to support deeper strategic decisions.

Key Features:
- Browser AI agents to fetch additional info
- Public data sourcing (Crunchbase, PubMed, etc.)
- Smart company comparison ("Compare A vs. B")
- Alerts for changes/updates

### 🧾 Phase 5: AI-Powered Recommendation Engine
In this phase, the assistant synthesizes all previous analysis (financial, strategic, scientific, red flags, scoring) to produce an overall investment recommendation.

Key Features:
- Generate AI-based summary recommendation: "Strong Consideration", "Needs Further Review", or "Pass"
- Justification paragraph explaining the decision based on prior insight cards
- Optional toggle: Value Investor Lens vs General Investor Lens
- Include scoring thresholds that influence final output (e.g., red flag presence reduces score weight)
- Allow user overrides with notes for manual adjustments

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
    │   ├── admin_routes.py    # Admin dashboard routes
    │   ├── comparison_routes.py # Document comparison
    │   ├── document_routes.py # Document upload and processing
    │   ├── edgar_routes.py    # SEC EDGAR search and processing
    │   ├── export_routes.py   # PDF export functionality
    │   ├── insight_routes.py  # Insight display and API
    │   └── share_routes.py    # Shareable link management
    ├── services/              # Business logic
    │   ├── __init__.py
    │   ├── ai_service.py      # AI provider interface
    │   ├── cache_service.py   # Content caching
    │   ├── demo_service.py    # Demo mode
    │   ├── document_comparison.py # Compare documents
    │   ├── document_processor.py # Processing pipeline
    │   ├── edgar_service.py   # SEC EDGAR integration
    │   ├── industry_templates.py # Industry-specific analysis
    │   ├── new_prompt_templates.py # Phase 2 prompts
    │   ├── open_source_ai.py  # Hugging Face integration
    │   ├── pdf_export.py      # PDF generation
    │   ├── pdf_parser.py      # PDF extraction
    │   └── url_parser.py      # URL content extraction
    ├── static/
    │   ├── css/
    │   │   └── custom.css     # Custom styling
    │   ├── exports/          # Generated PDF exports
    │   └── js/
    │       └── app.js         # Frontend functionality
    ├── templates/             # HTML templates
    │   ├── admin/
    │   │   └── api_usage.html # API usage dashboard
    │   ├── share/
    │   │   ├── create_link.html
    │   │   ├── expired.html
    │   │   ├── manage_links.html
    │   │   └── shared_insights.html
    │   ├── base.html
    │   ├── comparison.html
    │   ├── comparison_results.html
    │   ├── edgar_search.html
    │   ├── index.html
    │   └── insights.html
    ├── uploads/               # User file uploads
    └── cache/                 # Persistent cache storage
```

## Known Limitations

- Large PDFs (>500 pages) use intelligent sampling for better performance
- API rate limits apply for SEC EDGAR and AI services
- Document processing time varies based on file size and AI provider load
- Analysis quality depends on document content quality and depth
- Demo mode provides sample insights without API costs but with less specificity

## Local Development Setup

1. **Prerequisites**
   - Python 3.11 or higher
   - PostgreSQL database server
   - Python packages listed in pyproject.toml

2. **Install Dependencies**
   ```bash
   pip install -r sample_requirements.txt
   ```

3. **Set up environment variables**
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

4. **Set up PostgreSQL**
   - Create a database named 'insightlens'
   - Update DATABASE_URL in .env with your credentials
   - Initialize database:
     ```bash
     python recreate_db.py
     ```

5. **Run the application**
   Development mode:
   ```bash
   python main.py
   ```
   Production mode:
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```
   The application will be available at http://0.0.0.0:5000

## Deployment

For deployment, we recommend using Replit's deployment options:

1. **Using Replit's Autoscale Deployment**
   - Click the "Deploy" button in your Repl
   - Select "Autoscale" deployment type
   - Configure deployment:
     - Machine: 1vCPU, 2 GiB RAM (default)
     - Max machines: 3 (default)
     - Run command: `gunicorn --bind 0.0.0.0:5000 main:app`
   - Click "Deploy" to publish your application

2. **Using Replit's Reserved VM**
   For long-running, compute-intensive workloads:
   - Click "Deploy" in your Repl
   - Select "Reserved VM"
   - Configure VM size and run command
   - Deploy your application

Key Benefits of Replit Deployment:
- Automatic HTTPS/SSL
- Built-in environment management
- Automatic package installation
- Integrated deployment monitoring
- Easy scaling capabilities
- Zero-configuration PostgreSQL database

### Alternative Deployment Options

1. **Traditional Server Deployment**
   ```bash
   # Install dependencies
   pip install -r sample_requirements.txt

   # Set up environment variables
   export FLASK_SECRET_KEY=your_secret_key
   export DATABASE_URL=postgresql://username:password@localhost:5432/insightlens

   # Initialize database
   python recreate_db.py

   # Run with Gunicorn
   gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
   ```

2. **Docker Deployment**
   ```bash
   # Build the Docker image
   docker compose -f docker-compose.sample.yml build

   # Start the services
   docker compose -f docker-compose.sample.yml up -d
   ```

   The application will be available at http://localhost:5000

3. **Production Considerations**
   - Use a production-grade database
   - Configure proper logging
   - Set up monitoring
   - Implement backup strategies
   - Use HTTPS in production
   - Consider using a reverse proxy (nginx/Apache)

For most users, we recommend using Replit's deployment options for the best development experience and easiest maintenance.