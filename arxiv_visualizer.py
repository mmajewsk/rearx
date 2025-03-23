#!/usr/bin/env python3
"""
ArXiv Visualizer - Generate visualizations from ArXiv paper data stored in TinyDB.

This script handles:
- Loading paper data from TinyDB
- Generating HTML visualizations in a Reddit-like style
- Interactive sorting options directly in the HTML
"""

import os
import re
import datetime
import webbrowser
import json
from arxiv_db import ArxivDatabase

class ArxivVisualizer:
    """Visualization generator for ArXiv papers stored in MongoDB"""
    
    def __init__(self):
        """Initialize with database connection"""
        self.db = ArxivDatabase()
        self.papers = self.db.papers
    
    def get_all_papers(self):
        """Get all papers from the database"""
        return self.db.get_all_papers()
    
    def count_papers(self):
        """Count total papers in the database"""
        return self.db.count_papers()
    
    def generate_html(self, output_file="arxiv_papers.html", title="ArXiv AI Security Papers"):
        """Generate HTML visualization with interactive sorting"""
        # Get all papers
        papers = self.get_all_papers()
        
        if not papers:
            print("No papers to visualize")
            return None
            
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: "Verdana", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #eee;
            color: #222;
        }}
        .container {{
            max-width: 950px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        .header {{
            background-color: #cee3f8;
            border-bottom: 1px solid #5f99cf;
            padding: 10px 20px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 20px;
            color: #369;
        }}
        .filter-options {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
        }}
        .left-options {{
            display: flex;
            gap: 10px;
        }}
        .filter-options button {{
            color: #369;
            text-decoration: none;
            padding: 5px 10px;
            background: none;
            border: none;
            cursor: pointer;
            font-family: inherit;
            font-size: inherit;
        }}
        .filter-options button:hover {{
            text-decoration: underline;
        }}
        .filter-options button.active {{
            font-weight: bold;
            background-color: #e2e2e2;
            border-radius: 3px;
        }}
        .paper-row {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
            line-height: 1.4;
        }}
        .paper-row:hover {{
            background-color: #f8f8f8;
        }}
        .paper-main {{
            display: flex;
            align-items: center;
            cursor: pointer;
        }}
        .rank {{
            flex: 0 0 30px;
            color: #888;
            text-align: right;
            padding-right: 10px;
            font-size: 18px;
        }}
        .votes {{
            flex: 0 0 70px;
            text-align: center;
            padding: 0 10px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        .votes strong {{
            color: #cc3700;
            font-size: 15px;
        }}
        .paper-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        .paper-headline {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
        }}
        .paper-title {{
            color: #0000ff;
            text-decoration: none;
            font-weight: bold;
            font-size: 16px;
            margin-right: 10px;
        }}
        .paper-title:visited {{
            color: #551a8b;
        }}
        .paper-meta {{
            color: #888;
            font-size: 12px;
            margin-top: 4px;
        }}
        .paper-meta a {{
            color: #369;
            text-decoration: none;
        }}
        .paper-meta a:hover {{
            text-decoration: underline;
        }}
        .stats {{
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #888;
        }}
        .twitter-count {{
            color: #1DA1F2;
        }}
        .paper-details {{
            margin-top: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            display: none;
        }}
        .paper-details.show {{
            display: block;
        }}
        .abstract {{
            font-size: 14px;
            line-height: 1.5;
            margin-top: 10px;
            white-space: pre-line;
        }}
        .authors {{
            font-size: 14px;
            margin-top: 5px;
            color: #555;
        }}
        .categories {{
            font-style: italic;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #888;
            padding: 10px;
        }}
        .collapse-icon {{
            margin-left: 5px;
            font-size: 14px;
            transition: transform 0.3s;
        }}
        .collapsed .collapse-icon {{
            transform: rotate(180deg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
        </div>
        <div class="filter-options">
            <div class="left-options">
                <button onclick="sortPapers('date')" class="active" id="sort-date">Recent</button>
                <button onclick="sortPapers('citations')" id="sort-citations">Most Cited</button>
                <button onclick="sortPapers('tweets')" id="sort-tweets">Most Tweeted</button>
            </div>
            <div class="collapse-options">
                <button onclick="expandAll()" id="expand-all">Expand All</button>
                <button onclick="collapseAll()" id="collapse-all">Collapse All</button>
            </div>
        </div>
        
        <div id="papers-container">
"""
        
        # Add papers as JavaScript data
        papers_json = []
        for i, paper in enumerate(papers, 1):
            paper_obj = {
                'arxiv_id': paper.get('arxiv_id', ''),
                'title': paper.get('title', 'Untitled Paper'),
                'authors': paper.get('authors', []),
                'published': paper.get('published', ''),
                'citations': paper.get('citations', 0) or 0,
                'tweets': paper.get('tweets', 0) or 0,
                'paper_link': paper.get('abstract_link', f'https://arxiv.org/abs/{paper.get("arxiv_id", "")}'),
                'categories': paper.get('categories', []),
                'abstract': paper.get('abstract', '')
            }
            papers_json.append(paper_obj)
        
        # Close main HTML container
        html += """
        </div>
        
        <div class="footer">
            Generated on """ + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """ | Data from arXiv.org, Google Scholar, and Twitter
            <br>
            Database contains """ + str(self.count_papers()) + """ papers total.
        </div>
    </div>
    
    <!-- Paper data as JSON -->
    <script>
    // Paper data
    const papers = """ + json.dumps(papers_json, ensure_ascii=False) + """;
    
    // Current sort method
    let currentSort = 'date';
    
    // Format date for display
    function formatDate(dateString) {
        if (!dateString) return "Unknown date";
        const match = dateString.match(/(\d{4}-\d{2}-\d{2})/);
        return match ? match[1] : "Unknown date";
    }
    
    // Format authors for display - compact version
    function formatAuthorsCompact(authors) {
        if (!authors || authors.length === 0) return "Unknown authors";
        if (authors.length > 3) {
            return authors.slice(0, 3).join(', ') + ' et al.';
        }
        return authors.join(', ');
    }
    
    // Format authors for display - full version
    function formatAuthorsFull(authors) {
        if (!authors || authors.length === 0) return "Unknown authors";
        return authors.join(', ');
    }
    
    // Format categories for display
    function formatCategories(categories) {
        if (!categories || categories.length === 0) return "";
        return categories.join(', ');
    }
    
    // Toggle paper details
    function toggleDetails(id) {
        const details = document.getElementById(`paper-details-${id}`);
        const row = document.getElementById(`paper-row-${id}`);
        
        if (details.classList.contains('show')) {
            details.classList.remove('show');
            row.classList.add('collapsed');
        } else {
            details.classList.add('show');
            row.classList.remove('collapsed');
        }
    }
    
    // Expand all paper details
    function expandAll() {
        document.querySelectorAll('.paper-details').forEach(el => {
            el.classList.add('show');
        });
        document.querySelectorAll('.paper-row').forEach(el => {
            el.classList.remove('collapsed');
        });
    }
    
    // Collapse all paper details
    function collapseAll() {
        document.querySelectorAll('.paper-details').forEach(el => {
            el.classList.remove('show');
        });
        document.querySelectorAll('.paper-row').forEach(el => {
            el.classList.add('collapsed');
        });
    }
    
    // Sort papers and update display
    function sortPapers(sortMethod) {
        // Update active button
        document.getElementById('sort-date').classList.remove('active');
        document.getElementById('sort-citations').classList.remove('active');
        document.getElementById('sort-tweets').classList.remove('active');
        document.getElementById('sort-' + sortMethod).classList.add('active');
        
        // Sort papers
        let sortedPapers = [...papers];
        if (sortMethod === 'date') {
            sortedPapers.sort((a, b) => (b.published || '').localeCompare(a.published || ''));
        } else if (sortMethod === 'citations') {
            sortedPapers.sort((a, b) => (b.citations || 0) - (a.citations || 0));
        } else if (sortMethod === 'tweets') {
            sortedPapers.sort((a, b) => (b.tweets || 0) - (a.tweets || 0));
        }
        
        // Update current sort method
        currentSort = sortMethod;
        
        // Generate HTML
        let html = '';
        sortedPapers.forEach((paper, index) => {
            html += `
            <div class="paper-row collapsed" id="paper-row-${index}">
                <div class="paper-main" onclick="toggleDetails(${index})">
                    <div class="rank">${index + 1}</div>
                    <div class="votes">
                        <strong>${paper.citations}</strong>
                        <span>cites</span>
                    </div>
                    <div class="paper-content">
                        <div class="paper-headline">
                            <a href="${paper.paper_link}" class="paper-title" target="_blank" onclick="event.stopPropagation()">${paper.title}</a>
                            <div class="stats">
                                <span class="categories">${formatCategories(paper.categories.slice(0, 3))}</span>
                                <span class="twitter-count">🐦 ${paper.tweets} tweets</span>
                                <span class="collapse-icon">▼</span>
                            </div>
                        </div>
                        <div class="paper-meta">
                            submitted on ${formatDate(paper.published)} by ${formatAuthorsCompact(paper.authors)}
                        </div>
                    </div>
                </div>
                <div class="paper-details" id="paper-details-${index}">
                    <div class="authors"><strong>Authors:</strong> ${formatAuthorsFull(paper.authors)}</div>
                    <div class="abstract"><strong>Abstract:</strong> ${paper.abstract || 'No abstract available'}</div>
                </div>
            </div>
            `;
        });
        
        // Update container
        document.getElementById('papers-container').innerHTML = html;
    }
    
    // Initial sort by date
    document.addEventListener('DOMContentLoaded', function() {
        sortPapers('date');
    });
    </script>
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"HTML visualization generated: {os.path.abspath(output_file)}")
        return os.path.abspath(output_file)

def print_usage():
    """Print usage information"""
    print("""
ArXiv Visualizer - Generate visualizations from ArXiv paper data

Usage:
  python arxiv_visualizer.py [options]

Options:
  --output=FILE     Output HTML file (default: arxiv_papers.html)
  --help            Show this help message

Examples:
  python arxiv_visualizer.py
  python arxiv_visualizer.py --output=custom_name.html
""")

def main():
    """Main entry point for the script"""
    import sys
    
    # Default parameters
    output_file = 'arxiv_papers.html'
    
    # Parse command line arguments
    for arg in sys.argv[1:]:
        if arg == "--help":
            print_usage()
            sys.exit(0)
        elif arg.startswith("--output="):
            output_file = arg.split("=")[1]
        else:
            print(f"Unknown argument: {arg}")
            print_usage()
            sys.exit(1)
    
    # Initialize visualizer
    visualizer = ArxivVisualizer()
    
    # Check if database has papers
    if visualizer.count_papers() == 0:
        print("No papers found in the database. Run arxiv_collector.py first to gather data.")
        sys.exit(1)
    
    # Generate HTML visualization
    html_file = visualizer.generate_html(output_file=output_file)
    
    # Try to open in browser
    try:
        webbrowser.open(f"file://{html_file}")
    except:
        print("Could not automatically open the HTML file in a browser")

if __name__ == "__main__":
    main()