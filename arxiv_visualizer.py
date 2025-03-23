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
    
    def generate_renders_list_html(self):
        """Generate a HTML file listing all renders in the renders directory"""
        renders_dir = os.path.join(os.path.dirname(__file__), 'renders')
        list_path = os.path.join(renders_dir, "list.html")
        
        # Get all HTML files in the renders directory except main.html and list.html
        html_files = []
        for file in os.listdir(renders_dir):
            if file.endswith(".html") and file not in ["main.html", "list.html"]:
                file_path = os.path.join(renders_dir, file)
                file_time = os.path.getmtime(file_path)
                html_files.append((file, datetime.datetime.fromtimestamp(file_time)))
        
        # Sort by modification time (newest first)
        html_files.sort(key=lambda x: x[1], reverse=True)
        
        # Generate the render items HTML
        render_items = ""
        for file, time in html_files:
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S')
            render_items += f'<li><a href="{file}">{file}</a> <span class="date">{formatted_time}</span></li>\n'
        
        # Load the template
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'render_list.html')
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Replace the placeholder with the actual render items
        html = template.replace('{{render_items}}', render_items)
        
        # Write the HTML file
        with open(list_path, 'w') as f:
            f.write(html)
        
        return list_path
        
    def generate_html(self, output_file="arxiv_papers.html", title="ArXiv AI Security Papers"):
        papers = self.get_all_papers()
        
        if not papers:
            print("No papers to visualize")
            return None
        
        # Ensure renders directory exists
        renders_dir = os.path.join(os.path.dirname(__file__), 'renders')
        os.makedirs(renders_dir, exist_ok=True)
        
        # Prepare both timestamped and main file names
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Handle custom output file name
        if output_file == "arxiv_papers.html":
            timestamped_output = f"arxiv_papers_{timestamp}.html"
        else:
            # Keep custom name but add timestamp
            filename, ext = os.path.splitext(output_file)
            timestamped_output = f"{filename}_{timestamp}{ext}"
        
        # Construct full paths
        timestamped_path = os.path.join(renders_dir, timestamped_output)
        main_path = os.path.join(renders_dir, "main.html")
        
        # Keep original output path for backward compatibility
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        
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
        
        # Save to the original location for backward compatibility
        with open(output_path, 'w') as f:
            f.write(html)
            
        # Save to timestamped file in renders directory
        with open(timestamped_path, 'w') as f:
            f.write(html)
            
        # Also save to main.html in renders directory
        with open(main_path, 'w') as f:
            f.write(html)
            
        # Generate the list.html file with all renders
        list_path = self.generate_renders_list_html()
        
        print(f"HTML visualization generated:")
        print(f"  - Timestamped version: {os.path.abspath(timestamped_path)}")
        print(f"  - Main version: {os.path.abspath(main_path)}")
        print(f"  - History list: {os.path.abspath(list_path)}")
        print(f"  - Original path: {os.path.abspath(output_path)}")
        
        # Return the main.html path as the primary output
        return os.path.abspath(main_path)

def main():
    import sys
    
    output_file = 'arxiv_papers.html'
    open_browser = True
    
    for arg in sys.argv[1:]:
        if arg == "--help":
            print("""
ArXiv Visualizer - Generate visualizations from ArXiv paper data

Usage:
  python arxiv_visualizer.py [options]

Options:
  --output=FILE     Output HTML file (default: arxiv_papers_TIMESTAMP.html in renders/)
  --no-browser      Don't open the HTML file in a browser
  --help            Show this help message

Examples:
  python arxiv_visualizer.py
  python arxiv_visualizer.py --output=custom_name.html
""")
            sys.exit(0)
        elif arg.startswith("--output="):
            output_file = arg.split("=")[1]
        elif arg == "--no-browser":
            open_browser = False
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)
    
    visualizer = ArxivVisualizer()
    
    if visualizer.count_papers() == 0:
        print("No papers found in the database. Run arxiv_collector.py first to gather data.")
        sys.exit(1)
    
    html_file = visualizer.generate_html(output_file=output_file)
    
    if open_browser:
        try:
            webbrowser.open(f"file://{html_file}")
            print(f"Browser opened with the main visualization file")
        except:
            print("Could not automatically open the HTML file in a browser")
    
    render_dir = os.path.join(os.path.dirname(__file__), 'renders')
    print(f"\nTip: For the latest visualization, always use: {os.path.join(render_dir, 'main.html')}")

if __name__ == "__main__":
    main()