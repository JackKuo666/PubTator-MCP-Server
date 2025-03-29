import asyncio
import logging
from PubTator_server import search_pubtator, export_publications, find_entity_id, find_related_entities, batch_export_from_search

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_tests():
    # Test search_pubtator
    logging.info("Testing search_pubtator...")
    search_results = await search_pubtator("cancer", max_pages=1)
    logging.info(f"Search results: {search_results[:2]}...")

    # Test export_publications
    logging.info("Testing export_publications...")
    if search_results and 'results' in search_results[0]:
        pmids = [str(result['pmid']) for result in search_results[0]['results'][:2]]
        export_result = await export_publications(pmids)
        logging.info(f"Export result: {export_result}")

    # Test find_entity_id
    logging.info("Testing find_entity_id...")
    entity_result = await find_entity_id("p53", concept="gene")
    logging.info(f"Entity result: {entity_result}")

    # Test find_related_entities
    logging.info("Testing find_related_entities...")
    if entity_result and entity_result[0]['id']:
        related_result = await find_related_entities(entity_result[0]['id'], relation_type="treat")
        logging.info(f"Related entities result: {related_result}")

    # Test batch_export_from_search
    logging.info("Testing batch_export_from_search...")
    batch_result = await batch_export_from_search("diabetes", max_pages=1)
    logging.info(f"Batch export result: {batch_result[:2]}...")

if __name__ == "__main__":
    asyncio.run(run_tests())
