import fitz  # PyMuPDF
import base64
from typing import Literal
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server for OpenClaw
mcp = FastMCP("OpenClaw_PDF_Extractor")

# Path to the media inbound directory containing all PDFs
MEDIA_INBOUND_PATH = "/home/infonet/.openclaw/media/inbound"

@mcp.tool()
def extract_pdf_content(
    file_name: str, 
    mode: Literal["auto", "text_only", "full"] = "auto"
) -> list:
    """
    Reads a PDF file from the media inbound directory.
    Parameters:
    - file_name: Name of the PDF file (e.g., "document.pdf"). The full path is constructed automatically.
    - mode: Defines the extraction strategy.
        'text_only': Returns only plain text. Fastest and highly saves LLM tokens. Best for books or contracts.
        'auto' (default): Returns text, and explicitly renders a page as an image ONLY if it detects embedded pictures or complex diagrams (graphs, blueprints, circuits).
        'full': Forces rendering of every single page as an image alongside the text. Use when layout is strictly necessary.
    """
    import os
    
    # Construct the full path from the filename
    file_path = os.path.join(MEDIA_INBOUND_PATH, file_name)
    
    try:
        document = fitz.open(file_path)
    except Exception as e:
        return [f"Error: Unable to open PDF file '{file_name}' at '{file_path}'. Details: {str(e)}"]
    
    content_blocks = []
    
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        
        # 1. Always extract Plain Text
        page_text = page.get_text()
        if page_text.strip():
            content_blocks.append(f"\n--- Page {page_num + 1} Text ---\n{page_text}\n")
        
        # 2. Strategy evaluation
        should_render = False
        
        if mode == "full":
            should_render = True
        elif mode == "auto":
            has_images = len(page.get_images()) > 0
            
            # Check for complex vector graphics (charts, schematics).
            # We use a threshold (> 5 paths) to ignore simple decorative lines or basic borders.
            has_complex_vectors = len(page.get_drawings()) > 5 
            
            should_render = has_images or has_complex_vectors
            
        # 3. Image Rendering Process
        if should_render and mode != "text_only":
            # 1.5 zoom is sufficient for OCR and diagram readability while saving tokens
            zoom = 1.5 
            mat = fitz.Matrix(zoom, zoom)
            
            pix = page.get_pixmap(matrix=mat, alpha=False)
            image_bytes = pix.tobytes("png")
            b64_data = base64.b64encode(image_bytes).decode("utf-8")
            
            content_blocks.append({
                "type": "image",
                "data": b64_data,
                "mimeType": "image/png"
            })
        else:
            if mode == "auto":
                content_blocks.append(f"[System Note: Page {page_num + 1} skipped visual render to save tokens (no complex visuals detected).]\n")
                
    return content_blocks

if __name__ == "__main__":
    mcp.run(transport="stdio")