# InsightLens Test Plan

This document outlines the testing procedures for the InsightLens application, with a focus on the new features implemented in Phase 2.

## 1. PDF Export Functionality

### Test Case 1.1: Basic PDF Export
- **Objective**: Verify that the PDF export feature properly generates a PDF with all insight sections
- **Steps**:
  1. Upload a sample 10-K document or use Quick 10-K access
  2. Wait for analysis to complete
  3. Click "Export to PDF" button in the Actions dropdown
  4. Open the downloaded PDF file
- **Expected Result**: PDF contains all insight sections with proper formatting and styling

### Test Case 1.2: PDF Content Validation
- **Objective**: Confirm PDF content matches web interface content
- **Steps**:
  1. Open a completed analysis in the web interface
  2. Export to PDF
  3. Compare content in each section between PDF and web interface
- **Expected Result**: Content in PDF should match web interface exactly (minus HTML formatting)

### Test Case 1.3: PDF Compatibility
- **Objective**: Verify PDF compatibility across different PDF readers
- **Steps**:
  1. Generate a PDF export
  2. Open in Adobe Reader, Browser PDF viewer, and other common readers
- **Expected Result**: PDF displays correctly in all readers with proper formatting

## 2. Shareable Links Feature

### Test Case 2.1: Create Shareable Link
- **Objective**: Verify creation of shareable links
- **Steps**:
  1. Open a completed analysis
  2. Click "Create Shareable Link" in Actions dropdown
  3. Complete the form (with/without name, with/without expiration)
  4. Submit the form
- **Expected Result**: System creates link and redirects to manage links page showing the new link

### Test Case 2.2: Access Shared Analysis
- **Objective**: Verify that shared links provide access to analysis
- **Steps**:
  1. Create a shareable link
  2. Open the link in a different browser or incognito window
- **Expected Result**: Analysis displays correctly with all insights, in read-only mode with shared view banner

### Test Case 2.3: Link Expiration
- **Objective**: Verify that expired links are properly handled
- **Steps**:
  1. Create a link with a short expiration (1 day)
  2. Change system date to simulate expiration
  3. Try to access the link
- **Expected Result**: System shows "link expired" page and prevents access

### Test Case 2.4: Link Deactivation
- **Objective**: Verify ability to deactivate links
- **Steps**:
  1. Create a shareable link
  2. Go to manage links page
  3. Click deactivate button for the link
  4. Try to access the link
- **Expected Result**: System shows "link expired or deactivated" page and prevents access

### Test Case 2.5: Link Management
- **Objective**: Test the link management interface
- **Steps**:
  1. Create multiple links with different names/expirations
  2. Go to manage links page
- **Expected Result**: All links are displayed with correct details (name, creation date, expiration, status)

## 3. Regenerate Specific Insights

### Test Case 3.1: Regenerate Business Summary
- **Objective**: Verify ability to regenerate specific insights
- **Steps**:
  1. Open a completed analysis
  2. Click the regenerate button on the Business Summary card
  3. Confirm the regeneration prompt
- **Expected Result**: System regenerates only the Business Summary section and displays new content

### Test Case 3.2: Regenerate Multiple Sections
- **Objective**: Verify ability to regenerate multiple sections independently
- **Steps**:
  1. Open a completed analysis
  2. Regenerate Financial Health section
  3. Regenerate Competitive Moat section
- **Expected Result**: Each section regenerates independently without affecting others

### Test Case 3.3: Regenerate Special Analysis Sections
- **Objective**: Verify regeneration of specialized analysis sections
- **Steps**:
  1. Open an analysis that includes Red Flags, Buffett Analysis, or Biotech Analysis
  2. Regenerate one of these specialized sections
- **Expected Result**: System regenerates only the selected specialized section correctly

## 4. Document Comparison Feature

### Test Case 4.1: Compare Two Documents
- **Objective**: Verify basic comparison functionality
- **Steps**:
  1. Analyze two documents from the same company (e.g., 10-Ks from different years)
  2. Add both to comparison via "Add to Comparison" option
  3. View the comparison results
- **Expected Result**: System displays a side-by-side comparison highlighting differences

### Test Case 4.2: Compare Different Company Types
- **Objective**: Test comparison across different company types
- **Steps**:
  1. Analyze documents from companies in different sectors (e.g., tech vs. retail)
  2. Perform comparison
- **Expected Result**: System correctly identifies and highlights industry-specific differences

## 5. Error Handling

### Test Case 5.1: API Failure Recovery
- **Objective**: Verify system recovery from API failures
- **Steps**:
  1. Simulate an API failure (if possible, temporarily disable API access)
  2. Attempt document analysis
- **Expected Result**: System properly handles the error, displays appropriate message, and attempts recovery or fallback

### Test Case 5.2: Invalid Document Handling
- **Objective**: Test system response to invalid documents
- **Steps**:
  1. Upload an invalid document (e.g., corrupted PDF, non-10-K document)
  2. Attempt analysis
- **Expected Result**: System detects invalid content and provides clear error message

## 6. Integration Testing

### Test Case 6.1: End-to-End Document Analysis
- **Objective**: Verify complete workflow from upload to analysis to export
- **Steps**:
  1. Upload a 10-K document
  2. Wait for analysis to complete
  3. View all insight sections
  4. Export to PDF
  5. Create a shareable link
  6. Access the shared link
- **Expected Result**: Complete workflow functions without errors, with all features working together seamlessly

### Test Case 6.2: API Cost Management
- **Objective**: Verify API usage tracking and budget management
- **Steps**:
  1. Perform multiple document analyses
  2. Access the admin dashboard to view API usage statistics
- **Expected Result**: System accurately tracks and displays token usage and cost information


## Test Execution Instructions

For each test case:
1. Record the test date and tester name
2. Note the test environment details (browser, OS)
3. Document any deviations from expected results
4. Take screenshots of key screens for documentation
5. Rate the severity of any issues (Critical, High, Medium, Low)

## Bug Reporting Format

If issues are found, report them using this format:
- **Bug ID**: [Unique identifier]
- **Test Case**: [Related test case]
- **Description**: [Brief description of the issue]
- **Steps to Reproduce**: [Detailed steps]
- **Expected vs. Actual Result**: [What should happen vs. what did happen]
- **Severity**: [Critical/High/Medium/Low]
- **Screenshots/Evidence**: [Attach relevant visuals]
- **Environment**: [Browser, OS, etc.]
