### Key Features:

1. **Multiple Operation Modes**:
   - **Simple Mode**: Downloads PDFs directly from a single page
   - **Navigation Mode**: Follows links to discover PDFs on multiple pages

2. **Flexible Configuration**:
   - Interactive setup wizard that guides you through configuration
   - Save and load configurations for different websites
   - Command-line options for automation

3. **Smart PDF Detection**:
   - Detects PDFs not just by extension but also by content type and link text
   - Handles relative and absolute URLs automatically

4. **Intelligent Navigation**:
   - Controls depth of link following (how many clicks deep to go)
   - Stays within the same domain
   - Customizable patterns for which links to follow or ignore

### How to Use It:

1. Install the required libraries:
   ```
   pip install requests beautifulsoup4
   ```

2. Save the script as `flexible_pdf_scraper.py`

3. Run the script:
   ```
   python flexible_pdf_scraper.py
   ```

4. Follow the interactive prompts:
   - For the Niš eServis site (http://www.eservis.ni.rs/materijalizasg/), you would enter that URL
   - Choose Navigation Mode (option 2) since you'll likely need to browse through multiple pages
   - Set a reasonable depth (2 or 3) to control how many levels of links to follow

### For the Niš eServis Site Specifically:

The site example (http://www.eservis.ni.rs/materijalizasg/) appears to be a document repository for Niš city. Here's how I'd recommend setting it up:

1. Base URL: `http://www.eservis.ni.rs/materijalizasg/`
2. Mode: Navigation Mode
3. Depth: 2 or 3
4. Follow pattern: (leave empty to follow all links)
5. Ignore pattern: `facebook|twitter|login|kontakt`

### Command-Line Quick Use:

If you just want to quickly scrape a site without going through the interactive setup:

```
python flexible_pdf_scraper.py --url http://www.eservis.ni.rs/materijalizasg/
```
