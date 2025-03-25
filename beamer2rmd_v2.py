#!/usr/bin/env python3
# filepath: /home/wangzg/Nutstore Files/Nutstore/备课/2025春/面向生物医学科研的绘图技术/beamer2rmd_v2.py
import re
import sys
import os

def beamer_to_rmarkdown(latex_text, widescreen=False):
    """
    Converts a Beamer LaTeX document to an R Markdown (Rmd) presentation format.
    
    Args:
        latex_text (str): The LaTeX document text to convert
        widescreen (bool): Whether to adjust for widescreen presentation (16:9)
    """
    # Extract title, author, and institute from LaTeX
    title_match = re.search(r'\\title\[(.*?)\]{(.*?)}', latex_text)
    author_match = re.search(r'\\author\[(.*?)\]{(.*?)}', latex_text)
    institute_match = re.search(r'\\institute\[(.*?)\]{(.*?)}', latex_text)

    title = title_match.group(2) if title_match else "Untitled Presentation"
    author = author_match.group(2) if author_match else "Unknown Author"
    institute = institute_match.group(2) if institute_match else ""

    # Initialize R Markdown content with widescreen option
    if widescreen:
        rmd_content = f"""---
title: "{title}"
author: "{author}"
date: "`r Sys.Date()`"
output: 
  ioslides_presentation:
    toc: true
    mathjax: true
    widescreen: true
---

"""
    else:
        rmd_content = f"""---
title: "{title}"
author: "{author}"
date: "`r Sys.Date()`"
output: 
  ioslides_presentation:
    toc: true
    mathjax: true
---

"""

    # Convert each \section into a slide title
    latex_text = re.sub(r'\\section{(.*?)}', r'## \1', latex_text)
    
    # Define footnote URL replacer function once
    def footnote_url_replacer(match):
        url = match.group(1).strip()
        # Return HTML link
        return f' <a href="{url}" target="_blank">↗</a>'
    
    # Convert each \frame{...} into a slide
    frames = re.findall(r'\\begin{frame}.*?\{(.*?)\}(.*?)\\end{frame}', latex_text, re.DOTALL)
    for title, content in frames:
        # Process raw content to clean up formatting issues first
        content = content.replace('\n      ', '\n')  # Remove excessive indentation
        
        # Function to handle hyperlinks with error checking
        def href_replacer(match):
            try:
                url = match.group(1)
                text = match.group(2)
                return f'<a href="{url}" target="_blank">{text}</a>'
            except:
                # If there's any issue, return the original text
                return match.group(0)

        # Special case for the format: {~}Content - put Content in vertical center
        if title.strip() == "~" and content.strip():
            # Get the content text for centering
            content_text = content.strip()
            # Create a vertically centered div with the content
            centered_content = f'<div style="display: flex; align-items: center; justify-content: center; height: 400px;">\n<div style="font-size: 36px; text-align: center;">{content_text}</div>\n</div>'
            slide_title = "##"  # Empty title
            content = centered_content
        # Handle other special case: if title is just "~" or "{~}", treat it as empty
        elif title.strip() == "~" or title.strip() == "{~}":
            slide_title = "##"
        else:
            # Process hyperlinks in title - using a more robust pattern
            title = re.sub(r'\\href{(.*?)}{(.*?)}', href_replacer, title)
            
            # Handle any footnotes directly in the title (key change here)
            # Match any footnotes with URLs and put them directly in the title
            footnote_url_match = re.search(r'\\footnote{\\url{([^{}]+)}}', title)
            if footnote_url_match:
                url = footnote_url_match.group(1).strip()
                # Replace the footnote with the HTML link directly in the title
                title = re.sub(r'\\footnote{\\url{[^{}]+}}', f' <a href="{url}" target="_blank">↗</a>', title)
            
            # Handle regular footnotes
            title = re.sub(r'\\footnote{([^{}]+)}', r' <small>\1</small>', title)
            
            slide_title = f"## {title.strip()}" if title.strip() else "##"
            
        # Only process content if it hasn't been pre-processed (for centered slides)
        if not content.startswith('<div style="display: flex;'):
            # Process hyperlinks in content - using a more robust pattern
            content = re.sub(r'\\href{(.*?)}{(.*?)}', href_replacer, content)
            
            # Handle URLs - convert \url{url} to HTML link format
            content = re.sub(r'\\url{([^{}]+)}', r'<a href="\1" target="_blank">\1</a>', content)
            
            # Handle any footnotes that might still be in the content
            content = re.sub(r'\\footnote{\\url{([^{}]+)}}', footnote_url_replacer, content)
            content = re.sub(r'\\footnote{([^{}]+)}', r' <small>\1</small>', content)
            
            # Handle color commands - convert \color{red}{text} to <span style="color:red">text</span>
            content = re.sub(r'\\color{([^}]+)}(.*?)(?=\\|$)', 
                            lambda m: f'<span style="color:{m.group(1)}">{m.group(2)}</span>', 
                            content)
            
            # Handle \textcolor{color}{text} format
            content = re.sub(r'\\textcolor{([^}]+)}{([^}]+)}', 
                            lambda m: f'<span style="color:{m.group(1)}">{m.group(2)}</span>', 
                            content)
            
            # Handle color braces - convert {\color{red} text} to <span style="color:red">text</span>
            content = re.sub(r'{\\color{([^}]+)}([^}]+)}', 
                            lambda m: f'<span style="color:{m.group(1)}">{m.group(2)}</span>', 
                            content)
            
            # Convert \textbullet to bullet character •
            content = re.sub(r'\\textbullet\s*', '• ', content)
            
            # Handle figures and captions
            def figure_replacer(match):
                figure_content = match.group(1).strip()
                
                # Extract caption if present
                caption_match = re.search(r'\\caption{(.*?)}', figure_content)
                caption = caption_match.group(1) if caption_match else ""
                
                # Process the figure content without the caption
                if caption_match:
                    figure_content = figure_content.replace(f'\\caption{{{caption}}}', '')
                
                # Handle centering
                if '\\centering' in figure_content:
                    figure_content = figure_content.replace('\\centering', '<center>')
                    centered = True
                else:
                    centered = False
                
                # Process any images inside the figure
                figure_content = re.sub(r'\\includegraphics(\[.*?\])?{(.*?)}', 
                                     lambda m: image_replacer(m, widescreen), 
                                     figure_content)
                
                # Assemble the final figure with caption
                if caption:
                    caption_html = f'<div style="text-align: center; font-style: italic; margin-top: 8px;">{caption}</div>'
                else:
                    caption_html = ""
                    
                if centered:
                    return f'<center>\n{figure_content.strip()}\n{caption_html}</center>'
                else:
                    return f'{figure_content.strip()}\n{caption_html}'
            
            # Replace \begin{figure}...\end{figure} blocks
            content = re.sub(r'\\begin{figure}(.*?)\\end{figure}', figure_replacer, content, flags=re.DOTALL)
                    
            # Convert LaTeX images to Markdown format, preserving width attributes
            def image_replacer(match, is_widescreen=widescreen):
                options = match.group(1) if match.group(1) else ""
                image_path = match.group(2)
                
                # Extract width information if it exists
                width_match = re.search(r'width=([\d.]+)\\textwidth', options)
                if width_match:
                    width = width_match.group(1).strip()
                    # Convert LaTeX width to percentage (properly handling decimal points)
                    percentage = float(width) * 100
                    
                    # Adjust width for widescreen if needed
                    if is_widescreen:
                        # For widescreen, reduce width by 25% to prevent images from being too wide
                        percentage = percentage * 0.75
                    
                    # Handle PDF files differently - convert to PDF object or PDFs to images if needed
                    if image_path.lower().endswith('.pdf'):
                        return f'<iframe src="{image_path}" width="{percentage:.0f}%" height="500px"></iframe>'
                    else:
                        return f'<img src="{image_path}" width="{percentage:.0f}%">'
                
                # For images without specified width
                # Handle PDF files without width
                if image_path.lower().endswith('.pdf'):
                    # Use smaller default width for widescreen
                    width_pct = "80%" if is_widescreen else "100%"
                    return f'<iframe src="{image_path}" width="{width_pct}" height="500px"></iframe>'
                else:
                    # Use smaller default width for widescreen
                    width_pct = "80%" if is_widescreen else "100%"
                    return f'<img src="{image_path}" width="{width_pct}">'
            
            # Process standalone images
            content = re.sub(r'\\includegraphics(\[.*?\])?{(.*?)}', 
                           lambda m: image_replacer(m, widescreen), 
                           content)
            
            # Handle centered content - convert \begin{center}...\end{center} blocks
            content = re.sub(r'\\begin{center}(.*?)\\end{center}', 
                            lambda m: f'<center>{m.group(1).strip()}</center>', 
                            content, flags=re.DOTALL)
            
            # Also handle standalone center tags
            content = content.replace(r'\begin{center}', '<center>')
            content = content.replace(r'\end{center}', '</center>')
            
            # First, we need to handle nested list environments recursively
            # Convert nested itemize environments first (inside-out approach)
            max_nesting = 5  # Maximum nesting level to attempt
            for _ in range(max_nesting):
                # Process inner-most itemize environments that don't contain other itemize environments
                def nested_itemize_replacer(match):
                    items_text = match.group(1).strip()
                    # Replace \item with unordered list markers at the appropriate indent level
                    items = re.split(r'\\item\s+', items_text)
                    # Remove empty items (usually the first one)
                    items = [item.strip() for item in items if item.strip()]
                    
                    # Create bullet list with each item properly aligned and indented
                    # Use 4 spaces for indentation
                    bullet_list = '\n'.join(f"    - {item}" for item in items)
                    return '\n' + bullet_list + '\n'
                    
                content = re.sub(r'\\begin{itemize}((?:(?!\\begin{itemize}).)*?)\\end{itemize}', 
                                nested_itemize_replacer, 
                                content, 
                                flags=re.DOTALL)
            
            # Process enumerate environments - convert to ordered lists with numbers
            def enumerate_replacer(match):
                items_text = match.group(1).strip()
                # Replace \item with ordered list markers, ensure each item is on its own line
                items = re.split(r'\\item\s+', items_text)
                # Remove empty items (usually the first one)
                items = [item.strip() for item in items if item.strip()]
                
                # Create numbered list with each item properly aligned
                numbered_list = '\n'.join(f"{i+1}. {item}" for i, item in enumerate(items))
                return '\n' + numbered_list + '\n'
                
            content = re.sub(r'\\begin{enumerate}(.*?)\\end{enumerate}', 
                            enumerate_replacer, 
                            content, 
                            flags=re.DOTALL)
            
            # Handle any remaining standalone \item commands
            content = re.sub(r'\\item\s+', '- ', content)
            # For list items that start with a dash
            content = re.sub(r'\\item\s+-\s+', '- ', content)
            
            # Ensure proper paragraph breaks and formatting around HTML tags
            # Adding newlines before and after center tags without extra indentation
            content = re.sub(r'<center>(.*?)</center>', r'\n<center>\n\1\n</center>\n', content, flags=re.DOTALL)
            
            # Make sure images and iframes are on their own line
            content = re.sub(r'(<img .*?>)', r'\n\1\n', content)
            content = re.sub(r'(<iframe .*?</iframe>)', r'\n\1\n', content)
            
            # Fix bullet points after center blocks - remove indentation
            content = re.sub(r'\n\s+(-\s+)', r'\n\1', content)
            content = re.sub(r'\n\s+(•\s+)', r'\n\1', content)
            
            # Clean up multiple consecutive newlines to avoid excessive spacing
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Final attempt to clean up any remaining footnotes - this is a more aggressive approach
            # Make sure we replace remaining footnotes with links directly
            content = re.sub(r'\\footnote\{[^\}]*\\url\{([^\}]+)\}[^\}]*\}', 
                            lambda m: f' <a href="{m.group(1).strip()}" target="_blank">↗</a>', content)
            
        # Add slide to R Markdown - using just one line feed to avoid extra spacing
        rmd_content += f"\n{slide_title}\n{content.strip()}\n"

    return rmd_content


def main():
    """
    Process command line arguments and convert LaTeX file to RMarkdown.
    Usage: beamer2rmd_v2.py [--widescreen] input.tex [output.Rmd]
    If output file is not specified, it will use the same name as input but with .Rmd extension.
    """
    # Check if input file was provided
    if len(sys.argv) < 2:
        print("Usage: beamer2rmd_v2.py [--widescreen] input.tex [output.Rmd]")
        sys.exit(1)
    
    # Get all arguments
    args = sys.argv[1:]
    
    # Check for widescreen flag
    widescreen = False
    if "--widescreen" in args:
        widescreen = True
        args.remove("--widescreen")
    
    # Handle input and output files
    if len(args) > 0:
        # If there's only 1 argument left, it's the input file
        # If there are 2 or more, the last one could be the output file
        if len(args) > 1 and args[-1].lower().endswith('.rmd'):
            input_file = ' '.join(args[:-1])
            output_file = args[-1]
        else:
            # All arguments are part of the input filename
            input_file = ' '.join(args)
            # Use the same name as input but change extension to .Rmd
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.Rmd"
    else:
        print("Error: No input file specified.")
        print("Usage: beamer2rmd_v2.py [--widescreen] input.tex [output.Rmd]")
        sys.exit(1)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    print(f"Converting {input_file} to {output_file} (Widescreen: {widescreen})...")
    
    # Read the LaTeX file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            latex_text = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Convert to RMarkdown
    rmd_text = beamer_to_rmarkdown(latex_text, widescreen)
    
    # Write the output file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rmd_text)
        print(f"Conversion successful! Output saved to {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


# This allows the script to be run directly from the command line
if __name__ == "__main__":
    main()