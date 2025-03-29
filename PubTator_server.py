from typing import Any, List, Dict, Optional, Union
import asyncio
import logging
import os
import signal
from mcp.server.fastmcp import FastMCP
from PubTator_search import PubTator3API

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PubTatorMCPServer:
    def __init__(self):
        self.api = PubTator3API(max_retries=3, timeout=30)
        self.mcp = FastMCP("PubTator")
        self.setup_tools()

    def setup_tools(self):
        @self.mcp.tool()
        async def export_pubtator_annotations(
            pmids: List[str],
            format: str = "biocjson",
            full_text: bool = False
        ) -> Union[Dict, str]:
            logging.info(f"Exporting PubTator annotations for {len(pmids)} PMIDs in {format} format")
            try:
                result = await asyncio.to_thread(
                    self.api.export_publications,
                    pmids,
                    "pmid",
                    format,
                    full_text
                )
                return result
            except Exception as e:
                return {"error": f"Failed to export annotations: {str(e)}"}

        @self.mcp.tool()
        async def find_entity_id(
            query: str,
            concept: Optional[str] = None,
            limit: Optional[int] = None
        ) -> Dict:
            logging.info(f"Finding entity IDs for query: {query}, concept: {concept}, limit: {limit}")
            try:
                result = await asyncio.to_thread(
                    self.api.find_entity_id,
                    query,
                    concept,
                    limit
                )
                return result
            except Exception as e:
                return {"error": f"Failed to find entity IDs: {str(e)}"}

        @self.mcp.tool()
        async def find_related_entities(
            entity_id: str,
            relation_type: Optional[str] = None,
            target_entity_type: Optional[str] = None,
            max_results: Optional[int] = None
        ) -> Dict:
            logging.info(f"Finding related entities for: {entity_id}, relation: {relation_type}, target: {target_entity_type}, max_results: {max_results}")
            try:
                result = await asyncio.to_thread(
                    self.api.find_related_entities,
                    entity_id,
                    relation_type,
                    target_entity_type,
                    max_results
                )
                return result
            except Exception as e:
                return {"error": f"Failed to find related entities: {str(e)}"}

        @self.mcp.tool()
        async def search_pubtator(
            query: str,
            max_pages: Optional[int] = None,
            batch_size: int = 100
        ) -> List[Dict]:
            logging.info(f"Searching PubTator with query: {query}, max_pages: {max_pages}")
            try:
                results = []
                search_generator = self.api.search(query, max_pages=max_pages, batch_size=batch_size)
                for page_result in asyncio.as_completed([asyncio.to_thread(lambda: next(search_generator))]):
                    results.append(await page_result)
                    if len(results) == max_pages:
                        break
                return results
            except StopIteration:
                return results
            except Exception as e:
                return [{"error": f"Failed to search PubTator: {str(e)}"}]

        @self.mcp.tool()
        async def batch_export_from_search(
            query: str,
            format: str = "biocjson",
            max_pages: Optional[int] = 3,
            full_text: bool = False,
            batch_size: int = 100
        ) -> Union[Dict, str]:
            logging.info(f"Batch exporting from search query: {query}, format: {format}")
            try:
                export_generator = self.api.batch_export_from_search(
                    query,
                    format,
                    max_pages,
                    full_text,
                    batch_size
                )
                result = await asyncio.to_thread(next, export_generator)
                return result
            except StopIteration:
                return {"message": "No results found"}
            except Exception as e:
                return {"error": f"Failed to batch export: {str(e)}"}

    async def run(self):
        transport = os.environ.get("MCP_TRANSPORT", "tcp")
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8080"))
        if transport == "tcp":
            logging.info(f"Using TCP transport on {host}:{port}")
            await self.mcp.run(transport=transport, host=host, port=port)
        else:
            logging.info("Using stdio transport")
            await self.mcp.run(transport="stdio")

def main():
    logging.info("Starting PubTator MCP server")
    server = PubTatorMCPServer()

    loop = asyncio.get_event_loop()

    def signal_handler():
        logging.info("Shutting down PubTator MCP server")
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        loop.run_until_complete(server.run())
    except Exception as e:
        logging.error(f"Error running PubTator MCP server: {str(e)}")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
