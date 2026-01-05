# FS25 Documentation Scraper

A Python web scraper for downloading and organizing the GIANTS Developer Network (GDN) documentation for Farming Simulator 25 into an easily readable offline format.

## Features

- 🔍 **Comprehensive Scraping**: Automatically discovers and downloads all Script, Engine, and Foundation documentation
- 📁 **Organized Output**: Saves files in a structured directory format: `output/{version}/{category}/{item}.md`
- 📝 **Markdown Format**: Clean, readable markdown files that are easy to search and read offline
- ⚡ **Smart Resume**: Skips already downloaded files, allowing you to resume interrupted scraping
- 🛡️ **Error Handling**: Continues scraping even if individual pages fail
- ⏱️ **Rate Limiting**: Respects the server with delays between requests

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Simply run the main script:

```bash
python main.py
```

The scraper will:
1. Fetch the main documentation page
2. Discover all categories (Activatables, AI, Animation, Physics, etc.)
3. Iterate through each category and subcategory
4. Extract the documentation content
5. Save each page as a markdown file in the `output/` directory

## Output Structure

```
output/
├── manifest.json          # Machine-readable index with all file paths
├── INDEX.md              # Human-readable index with links to all files
├── script/
│   ├── Activatables/
│   │   └── VehicleBuyingStationActivatable.md
│   ├── AI/
│   │   ├── AIJobTypeManager.md
│   │   └── ...
│   ├── Animation/
│   └── ...
├── engine/
│   ├── Animation/
│   ├── Physics/
│   │   ├── addForce.md
│   │   └── ...
│   └── ...
└── foundation/
    └── ...
```

### Manifest Files

The scraper generates two index files in the `output/` directory:

1. **manifest.json** - A structured JSON file containing:
   - Metadata (generation timestamp, source URL, total file count)
   - Complete hierarchy of versions, categories, and items
   - Relative paths to all documentation files
   - Perfect for programmatic access or building custom tools

2. **INDEX.md** - A human-readable markdown file with:
   - Table of contents with links to each version
   - Organized listing of all categories and items
   - Direct links to all documentation files
   - Ideal for browsing in a markdown viewer or GitHub

## How It Works

The scraper:

1. **Parses the main page** to extract all category links
2. **Identifies the URL pattern** for both Script classes (`?version=script&category=X&class=Y`) and Engine functions (`?version=engine&category=X&function=Y`)
3. **Extracts content** from the specific DOM element: `#box5 > div.entry > div:nth-child(2)`
4. **Converts to Markdown** using html2text for clean, readable output
5. **Organizes files** by version and category for easy navigation

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- html2text
- lxml

## Notes

- The scraper includes a 0.5-second delay between requests to be respectful to the server
- Already downloaded files are skipped automatically
- Failed downloads are reported but don't stop the scraping process
- All content is saved in UTF-8 encoding

## Example Output

Each markdown file includes:
- Title (class/function name)
- Category and version metadata
- Full documentation content including:
  - Descriptions
  - Function definitions
  - Parameters
  - Code examples
  - Return values

## License

This tool is for personal use to create offline documentation. Please respect GIANTS Software's terms of service and copyright.
