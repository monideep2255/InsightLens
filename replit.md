# InsightLens - Document Analysis Platform

## Project Overview
InsightLens is a Flask-based document analysis platform that leverages AI to provide insights from documents including PDFs and EDGAR filings. The application has been migrated from Replit Agent to standard Replit environment.

## Features
- Document upload and analysis
- EDGAR SEC filing search and analysis
- Document comparison functionality
- AI-powered insights generation
- PDF export capabilities
- Admin dashboard
- Document sharing

## Architecture
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL
- **File Storage**: Local uploads directory
- **AI Service**: OpenAI integration
- **Caching**: SQLite-based caching system

## User Preferences
- Production-ready design required
- Security-focused implementation
- Clean separation between client/server

## Recent Changes
- 2025-08-21: Migrated from Replit Agent environment
- 2025-08-21: Set up PostgreSQL database
- 2025-08-21: Fixed environment variable configuration

## Configuration
- Server runs on port 5000 with 0.0.0.0 binding
- Database: PostgreSQL via DATABASE_URL environment variable
- Session security: SESSION_SECRET environment variable
- File uploads: Limited to 16MB, stored in uploads/ directory