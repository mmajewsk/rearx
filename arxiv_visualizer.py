#!/usr/bin/env python3
import os
import datetime
import json
import webbrowser
from arxiv_db import ArxivDatabase

class ArxivVisualizer:
    def __init__(self):
        self.db = ArxivDatabase()
    
    def get_all_papers(self):
        return self.db.get_all_papers()
    
    def count_papers(self):
        return self.db.count_papers()
    
    def generate_html(self, output_file="arxiv_papers.html", title="ArXiv AI Security Papers"):
        papers = self.get_all_papers()
        
        if not papers:
            print("No papers to visualize")
            return None
        
        papers_json = []
        for paper in papers:
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
        
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'paper_list.html')
        with open(template_path, 'r') as f:
            template = f.read()
        
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        papers_count = self.count_papers()
        
        html = template.replace('{{title}}', title)
        html = html.replace('{{date}}', current_date)
        html = html.replace('{{count}}', str(papers_count))
        html = html.replace('{{papers_json}}', json.dumps(papers_json, ensure_ascii=False))
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"HTML visualization generated: {os.path.abspath(output_file)}")
        return os.path.abspath(output_file)

def main():
    import sys
    
    output_file = 'arxiv_papers.html'
    
    for arg in sys.argv[1:]:
        if arg == "--help":
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
            sys.exit(0)
        elif arg.startswith("--output="):
            output_file = arg.split("=")[1]
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)
    
    visualizer = ArxivVisualizer()
    
    if visualizer.count_papers() == 0:
        print("No papers found in the database. Run arxiv_collector.py first to gather data.")
        sys.exit(1)
    
    html_file = visualizer.generate_html(output_file=output_file)
    
    try:
        webbrowser.open(f"file://{html_file}")
    except:
        print("Could not automatically open the HTML file in a browser")

if __name__ == "__main__":
    main()