import asyncio
import logging
import os

import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Currency MCP Server 💵")

class Movie(BaseModel):
    title: str = Field(..., description="The title of the movie")
    logline: str = Field(..., description="The logline of the movie")

@mcp.tool()
def get_exchange_rate(
    currency_from: str = "USD",
    currency_to: str = "EUR",
    currency_date: str = "latest",
):
    """Use this to get current exchange rate.

    Args:
        currency_from: The currency to convert from (e.g., "USD").
        currency_to: The currency to convert to (e.g., "EUR").
        currency_date: The date for the exchange rate or "latest". Defaults to "latest".

    Returns:
        A dictionary containing the exchange rate data, or an error message if the request fails.
    """
    logger.info(
        f"--- 🛠️ Tool: get_exchange_rate called for converting {currency_from} to {currency_to} ---"
    )
    try:
        response = httpx.get(
            f"https://api.frankfurter.app/{currency_date}",
            params={"from": currency_from, "to": currency_to},
        )
        response.raise_for_status()

        data = response.json()
        if "rates" not in data:
            logger.error(f"❌ rates not found in response: {data}")
            return {"error": "Invalid API response format."}
        logger.info(f"✅ API response: {data}")
        return data
    except httpx.HTTPError as e:
        logger.error(f"❌ API request failed: {e}")
        return {"error": f"API request failed: {e}"}
    except ValueError:
        logger.error("❌ Invalid JSON response from API")
        return {"error": "Invalid JSON response from API."}

@mcp.tool()
def store_movie_in_vector_db(movie: Movie):
    
    """Use this to store a movie plot in the vector database.
    Args:
        movie (Movie): The movie to store in the vector database.
    Returns:
        A dictionary containing the movie title and a success message, or an error message if the request fails.
    """
    logger.info(f"--- 🛠️ Tool: store_movie_in_vector_db called for movie {movie.title} ---")
    try:
        return {"message": f"Movie {movie.title} stored in vector database."}
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
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=os.getenv("PORT", "8080"),
        )
    )