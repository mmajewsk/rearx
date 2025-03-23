# ArXiv AI Security Paper Tracker

This tool helps track and visualize AI security research papers from ArXiv.org, along with their citation counts from Google Scholar and Twitter mentions.

## Components

1. **arxiv_collector.py** - Searches ArXiv for papers matching keywords, retrieves citation counts from Google Scholar, estimates Twitter mentions, and stores data in TinyDB.
2. **arxiv_visualizer.py** - Generates an interactive HTML visualization with client-side sorting.

## Setup

1. Install required dependencies:
   ```bash
   pip install requests beautifulsoup4 python-dateutil tinydb
   ```

2. Make sure you have a `tags.txt` file with your search keywords (one per line).

## Usage

### 1. Collect Papers

The collector script searches ArXiv, enriches the data with citation counts and Twitter mentions, and stores everything in TinyDB.

```bash
# Basic usage (clears database by default)
python arxiv_collector.py

# Specify number of results
python arxiv_collector.py --max=20

# Use custom keywords file
python arxiv_collector.py --keywords=custom_tags.txt

# Keep existing database entries and add new ones
python arxiv_collector.py --keep-existing
```

### 2. Generate Visualization

The visualizer script creates an interactive HTML page with the papers.

```bash
# Generate HTML with default options
python arxiv_visualizer.py

# Specify custom output file
python arxiv_visualizer.py --output=custom_name.html
```

## Visualization Features

The generated HTML visualization includes:

- **Interactive sorting options**:
  - Sort by publication date (newest first)
  - Sort by citation count (highest first)
  - Sort by Twitter mentions (highest first)

- **Reddit-style layout** for each paper:
  - Rank number
  - Citation count
  - Paper title linked to PDF
  - Publication date and authors
  - Categories and Twitter mention count

## Data Storage

All data is stored in:

- **arxiv_papers.json** - TinyDB database file
- **results/** directory - Contains timestamped JSON and TXT snapshots of search results

## Command-Line Options

### arxiv_collector.py

```
Options:
  --keywords=FILE    Specify keywords file (default: tags.txt)
  --max=NUMBER       Maximum number of results (default: 10)
  --keep-existing    Don't clear the database before adding new papers
  --help             Show this help message
```

### arxiv_visualizer.py

```
Options:
  --output=FILE      Output HTML file (default: arxiv_papers.html)
  --help             Show this help message
```

## Example Workflow

1. Add your keywords to `tags.txt`
2. Run `python arxiv_collector.py --max=20` to collect papers
3. Run `python arxiv_visualizer.py` to generate visualization
4. Open the HTML file in a browser
5. Use the sorting buttons to organize papers by date, citations, or tweets
6. Later, run `python arxiv_collector.py --keep-existing --max=10` to add more papers to your collection