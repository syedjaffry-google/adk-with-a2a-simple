import asyncio
import logging
import os

import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from pydantic import BaseModel, Field
import vertexai
from vertexai.preview import rag
import tempfile

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)


PROJECT_ID = os.environ.get('PROJECT_ID', None)
LOCATION = os.environ.get('LOCATION', None)
CORPUS_NAME = os.environ.get('CORPUS_NAME', None)

if not PROJECT_ID or not LOCATION or not CORPUS_NAME:
    raise ValueError("PROJECT_ID, LOCATION, and CORPUS_NAME must be set in the environment variables.")

# Initialize Vertex AI Client
vertexai.init(project=PROJECT_ID, location=LOCATION)

mcp = FastMCP("Movie DB MCP Server 🎬")

@mcp.tool()
def store_movie_in_vector_db(
    title: str, 
    logline: str
):
    
    """Use this to store a movie plot in the vector database.
    Args:
        Title: The title of the movie.
        Logline: The logline of the movie to store in the vector database.
    Returns:
        A dictionary containing the movie title and a success message, or an error message if the request fails.
    """
    logger.info(f"--- 🛠️ Tool: store_movie_in_vector_db called for movie {title} ---")
    try:
        # Create a temp file to upload the logline
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
            f.write(logline)
            temp_file_path = f.name

        try:
            logger.info(f"Uploading logline for {title} to RAG corpus...")
            rag_file = rag.upload_file(
                corpus_name=CORPUS_NAME,
                display_name=f"{title}_logline.txt",
                path=temp_file_path,
                description=f"Logline for movie: {title}",
            )
            logger.info(f"Successfully uploaded to RAG corpus. File name: {rag_file.name}")
            return {
                "message": f"Movie {title} stored in vector database.",
                "rag_file_name": rag_file.name
            }
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except Exception as e:
        logger.error(f"❌ Error storing movie in vector database: {e}")
        return {"error": f"Error storing movie in vector database: {e}"}

@mcp.custom_route("/", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    """GCP Load Balancer health check endpoint."""
    return PlainTextResponse("OK")

if __name__ == "__main__":
    logger.info(f"🚀 MCP server started on port {os.getenv('PORT', '8080')}")
    # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
    port_env = int(os.getenv("PORT", 8080))
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=port_env,
        )
    )