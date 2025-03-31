from typing import AsyncGenerator, List, Dict, Optional, Any, Union
import asyncio
import logging
from mcp.server.fastmcp import FastMCP
from pubtator_search import PubTator3API

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
mcp = FastMCP("pubtator")

# Initialize PubTator3API client
client = PubTator3API(max_retries=3, timeout=30)


@mcp.tool()
async def search_pubtator(query: str, max_pages: Optional[int] = 3) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Search for papers on PubTator using a query string.

    Args:
        query: Search query string
        max_pages: Maximum number of pages to retrieve (default: 3)

    Yields:
        Dictionary containing paper information
    """
    try:
        async for page_result in client.search(query, max_pages=max_pages):
            yield page_result
    except Exception as e:
        logging.error(f"An error occurred while searching: {str(e)}")
        yield {"error": f"An error occurred while searching: {str(e)}"}

@mcp.tool()
async def export_publications(ids: List[str], id_type: str = "pmid", format: str = "biocjson", full_text: bool = False) -> Union[Dict, str]:
    logging.info(f"Exporting publications: {ids}, id_type: {id_type}, format: {format}, full_text: {full_text}")
    """
    Export publications from PubTator.

    Args:
        ids: List of publication IDs
        id_type: Type of IDs (pmid or pmcid)
        format: Export format (pubtator, biocxml, or biocjson)
        full_text: Whether to include full text (only for biocxml/biocjson)

    Returns:
        Dictionary or string containing exported publication data
    """
    try:
        result = await asyncio.to_thread(client.export_publications, ids, id_type, format, full_text)
        return result
    except Exception as e:
        return {"error": f"An error occurred while exporting publications: {str(e)}"}

@mcp.tool()
async def find_entity_id(query: str, concept: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    logging.info(f"Finding entity ID for query: {query}, concept: {concept}, limit: {limit}")
    """
    Find entity ID using a free text query.

    Args:
        query: Query text
        concept: Optional, specify biological concept type
        limit: Optional, limit the number of returned results

    Returns:
        Dictionary containing entity IDs
    """
    try:
        result = await asyncio.to_thread(client.find_entity_id, query, concept, limit)
        return result
    except Exception as e:
        return {"error": f"An error occurred while finding entity ID: {str(e)}"}

@mcp.tool()
async def find_related_entities(entity_id: str, relation_type: Optional[str] = None, target_entity_type: Optional[str] = None, max_results: Optional[int] = None) -> Dict[str, Any]:
    logging.info(f"Finding related entities for: {entity_id}, relation_type: {relation_type}, target_entity_type: {target_entity_type}, max_results: {max_results}")
    """
    Find related entities.

    Args:
        entity_id: Entity ID
        relation_type: Optional, specify relation type
        target_entity_type: Optional, specify target entity type
        max_results: Optional, limit the number of returned results

    Returns:
        Dictionary containing related entities
    """
    try:
        result = await asyncio.to_thread(client.find_related_entities, entity_id, relation_type, target_entity_type, max_results)
        return result
    except Exception as e:
        return {"error": f"An error occurred while finding related entities: {str(e)}"}

@mcp.tool()
async def batch_export_from_search(query: str, format: str = "biocjson", max_pages: Optional[int] = 3, full_text: bool = False, batch_size: int = 100) -> List[Union[Dict, str]]:
    logging.info(f"Batch exporting from search: {query}, format: {format}, max_pages: {max_pages}, full_text: {full_text}, batch_size: {batch_size}")
    """
    Search and batch export publications.

    Args:
        query: Search query
        format: Export format
        max_pages: Maximum number of search pages
        full_text: Whether to export full text
        batch_size: Number of PMIDs to process in each batch

    Returns:
        List of dictionaries or strings containing exported publication data
    """
    try:
        results = []
        async for result in client.batch_export_from_search(query, format, max_pages, full_text, batch_size):
            results.append(result)
        return results
    except Exception as e:
        return [{"error": f"An error occurred during batch export: {str(e)}"}]

if __name__ == "__main__":
    logging.info("Starting PubTator MCP server")
    # Initialize and run the server
    mcp.run(transport='stdio')
