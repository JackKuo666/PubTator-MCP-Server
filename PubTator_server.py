from typing import Any, List, Dict, Optional, Union
import asyncio
import logging
from mcp.server.fastmcp import FastMCP
from PubTator_search import PubTator3API

# Initialize PubTator3API instance
api = PubTator3API(max_retries=3, timeout=30)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
mcp = FastMCP("pubmed")



@mcp.tool()
async def export_pubtator_annotations(
    pmids: List[str],
    format: str = "biocjson",
    full_text: bool = False
) -> Union[Dict, str]:
    """
    Export PubTator annotations for a list of PMIDs.

    Args:
        pmids: List of PMIDs to export annotations for
        format: Export format ("pubtator", "biocxml", or "biocjson")
        full_text: Whether to include full text (only for biocxml/biocjson)

    Returns:
        Dictionary or string containing the annotations
    """
    logging.info(f"Exporting PubTator annotations for {len(pmids)} PMIDs in {format} format")
    try:
        result = await asyncio.to_thread(
            api.export_publications,
            pmids,
            "pmid",
            format,
            full_text
        )
        return result
    except Exception as e:
        return {"error": f"Failed to export annotations: {str(e)}"}

@mcp.tool()
async def find_entity_id(
    query: str,
    concept: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict:
    """
    Find entity IDs by free text query.

    Args:
        query: Query text
        concept: Optional entity type ("gene", "disease", "chemical", "species", "mutation")
        limit: Optional limit on number of results

    Returns:
        Dictionary containing entity IDs and information
    """
    logging.info(f"Finding entity IDs for query: {query}, concept: {concept}, limit: {limit}")
    try:
        result = await asyncio.to_thread(
            api.find_entity_id,
            query,
            concept,
            limit
        )
        return result
    except Exception as e:
        return {"error": f"Failed to find entity IDs: {str(e)}"}

@mcp.tool()
async def find_related_entities(
    entity_id: str,
    relation_type: Optional[str] = None,
    target_entity_type: Optional[str] = None
) -> Dict:
    """
    Find entities related to a given entity ID.

    Args:
        entity_id: Entity ID to find relations for
        relation_type: Optional relation type ("treat", "cause", "interact", etc.)
        target_entity_type: Optional target entity type ("gene", "disease", "chemical")

    Returns:
        Dictionary containing related entities and their relationships
    """
    logging.info(f"Finding related entities for: {entity_id}, relation: {relation_type}, target: {target_entity_type}")
    try:
        result = await asyncio.to_thread(
            api.find_related_entities,
            entity_id,
            relation_type,
            target_entity_type
        )
        return result
    except Exception as e:
        return {"error": f"Failed to find related entities: {str(e)}"}

@mcp.tool()
async def search_pubtator(
    query: str,
    max_pages: Optional[int] = None,
    batch_size: int = 100
) -> List[Dict]:
    """
    Search PubTator database with pagination support.

    Args:
        query: Search query (free text/entity ID/relation query)
        max_pages: Optional maximum number of pages to retrieve
        batch_size: Number of results per batch

    Returns:
        List of search result pages
    """
    logging.info(f"Searching PubTator with query: {query}, max_pages: {max_pages}")
    try:
        results = []
        async for page_result in api.search(query, max_pages=max_pages, batch_size=batch_size):
            results.append(page_result)
        return results
    except Exception as e:
        return [{"error": f"Failed to search PubTator: {str(e)}"}]

@mcp.tool()
async def batch_export_from_search(
    query: str,
    format: str = "biocjson",
    max_pages: Optional[int] = 3,
    full_text: bool = False,
    batch_size: int = 100
) -> List[Union[Dict, str]]:
    """
    Search and batch export publications from PubTator.

    Args:
        query: Search query
        format: Export format
        max_pages: Maximum number of search pages
        full_text: Whether to include full text
        batch_size: Number of PMIDs per batch

    Returns:
        List of exported publication batches
    """
    logging.info(f"Batch exporting from search query: {query}, format: {format}")
    try:
        results = []
        async for result in api.batch_export_from_search(
            query,
            format,
            max_pages,
            full_text,
            batch_size
        ):
            results.append(result)
        return results
    except Exception as e:
        return [{"error": f"Failed to batch export: {str(e)}"}]

if __name__ == "__main__":
    logging.info("Starting PubMed MCP server")
    # Initialize and run the server
    mcp.run(transport='stdio')
