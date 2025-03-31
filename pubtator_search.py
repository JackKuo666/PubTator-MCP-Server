import requests
import json
import time
from typing import List, Dict, Optional, Union, Generator

class PubTator3API:
    BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
    ANNOTATE_URL = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful"
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PubTator3API Python Client/2.1",
            "Accept": "application/json"
        })
        self.request_delay = 0.34  # Comply with the 3 requests/second limit
        self.max_retries = max_retries
        self.timeout = timeout
        self._last_request_time = 0
    
    def _rate_limited_request(self, method, *args, **kwargs):
        """Request method with rate limiting and retry mechanism"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        
        kwargs['timeout'] = self.timeout
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, *args, **kwargs)
                self._last_request_time = time.time()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(min(2 ** attempt, 10))  # Exponential backoff strategy
    
    # ------------------------- Core Functionality -------------------------
    def export_publications(
        self,
        ids: List[str],
        id_type: str = "pmid",
        format: str = "biocjson",
        full_text: bool = False
    ) -> Union[Dict, str]:
        """
        导出一组文献的标注结果
        
        参数:
            ids: 文献ID列表(pmids或pmcids)
            id_type: ID类型，可以是"pmid"或"pmcid"
            format: 返回格式("pubtator", "biocxml"或"biocjson")
            full_text: 是否获取全文(仅适用于biocxml/biocjson格式)
        
        返回:
            标注结果(JSON字典或XML字符串)
        """
        if not ids:
            raise ValueError("IDs list cannot be empty")
        
        if id_type not in ["pmid", "pmcid"]:
            raise ValueError("id_type must be 'pmid' or 'pmcid'")
        if format not in ["pubtator", "biocxml", "biocjson"]:
            raise ValueError("format must be one of: pubtator, biocxml, biocjson")
        
        try:
            if id_type == "pmcid":
                url = f"{self.BASE_URL}/publications/pmc_export/{format}"
            else:
                url = f"{self.BASE_URL}/publications/export/{format}"
            
            params = {f"{id_type}s": ",".join(ids)}
            if full_text and format != "pubtator":
                params["full"] = "true"
            
            response = self._rate_limited_request("GET", url, params=params)
            response.raise_for_status()
            
            if format == "biocjson":
                result = response.json()
                # 处理不同的返回结构
                if isinstance(result, list):
                    return {"documents": result}  # Standardize to documents key
                return result
            return response.text
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to export publications: {str(e)}")
    
    def find_entity_id(
        self,
        query: str,
        concept: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        通过自由文本查询查找生物概念的标识符
        
        参数:
            query: 查询文本
            concept: 可选，指定生物概念类型
                     (如"gene", "disease", "chemical", "species", "mutation")
            limit: 可选，限制返回结果数量
        
        返回:
            包含实体ID的JSON字典
        """
        url = f"{self.BASE_URL}/entity/autocomplete/"
        params = {"query": query}
        
        if concept:
            if concept not in ["gene", "disease", "chemical", "species", "mutation"]:
                raise ValueError("Invalid concept type")
            params["concept"] = concept
        if limit:
            params["limit"] = limit
        
        response = self._rate_limited_request("GET", url, params=params)
        response.raise_for_status()
        return response.json()
    
    def find_related_entities(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        target_entity_type: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> Dict:
        """
        查找相关实体
        
        参数:
            entity_id: 实体ID(通过find_entity_id获取)
            relation_type: 可选，指定关系类型
                          (如"treat", "cause", "interact", "associate")
            target_entity_type: 可选，指定目标实体类型
                               (如"gene", "disease", "chemical")
            max_results: 可选，限制返回结果的最大数量
        
        返回:
            相关实体结果的JSON字典
        """
        url = f"{self.BASE_URL}/relations"
        # 确保实体ID格式正确
        if not entity_id.startswith("@"):
            raise ValueError("Invalid entity ID format, should start with '@', e.g., '@CHEMICAL_remdesivir' or '@DISEASE_Neoplasms'")
        params = {"e1": entity_id}
        
        valid_relations = ["treat", "cause", "cotreat", "convert", "compare",
                          "interact", "associate", "positive_correlate",
                          "negative_correlate", "prevent", "inhibit",
                          "stimulate", "drug_interact"]
        
        if relation_type:
            if relation_type not in valid_relations and relation_type != "ANY":
                raise ValueError("Invalid relation type")
            params["type"] = relation_type
        if target_entity_type:
            if target_entity_type not in ["gene", "disease", "chemical", "variant"]:
                raise ValueError("Invalid target entity type")
            params["e2"] = target_entity_type
        if max_results:
            params["limit"] = max_results
        
        response = self._rate_limited_request("GET", url, params=params)
        response.raise_for_status()
        return response.json()
    
    
    
    # ------------------------- Enhanced Search Functionality -------------------------
    def search(
        self,
        query: str,
        page: int = 1,
        max_pages: Optional[int] = None,
        batch_size: int = 100
    ) -> Generator[Dict, None, None]:
        """增强的搜索功能，支持自动分页和错误重试
        
        参数:
            query: 查询内容(自由文本/实体ID/关系查询)
            page: 起始页码
            max_pages: 最大获取页数(None表示无限制)
            batch_size: 每批处理的PMID数量
        
        返回:
            生成器，逐页产生搜索结果
        """
        current_page = page
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while max_pages is None or current_page <= max_pages:
            try:
                url = f"{self.BASE_URL}/search/"
                params = {"text": query, "page": current_page}
                
                response = self._rate_limited_request("GET", url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("results"):
                    break
                    
                consecutive_errors = 0  # 重置错误计数
                yield data
                current_page += 1
                
            except requests.exceptions.RequestException as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    raise Exception(f"Search terminated after {max_consecutive_errors} consecutive request failures")
                time.sleep(min(2 ** consecutive_errors, 10))  # 指数退避
                continue
            
            except json.JSONDecodeError:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    raise Exception(f"Search terminated after {max_consecutive_errors} consecutive response parsing failures")
                time.sleep(min(2 ** consecutive_errors, 10))
                continue
    
    def search_relations(
        self,
        entity1: str,
        relation_type: str = "ANY",
        entity2: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        专门的关系查询方法
        
        参数:
            entity1: 第一个实体ID
            relation_type: 关系类型(ANY/treat/cause等)
            entity2: 第二个实体ID或类型(如"DISEASE")
            max_pages: 最大获取页数
        
        返回:
            生成器，逐页产生关系搜索结果
        """
        if entity2 is None:
            query = f"relations:{relation_type}|{entity1}"
        else:
            query = f"relations:{relation_type}|{entity1}|{entity2}"
            
        yield from self.search(query, max_pages=max_pages)
    
    def extract_pmids_from_results(self, results: Dict) -> List[str]:
        """
        从搜索结果中提取PMID列表
        
        参数:
            results: 单页搜索结果
            
        返回:
            PMID列表
        """
        return [str(result["pmid"]) for result in results.get("results", []) if "pmid" in result]
    
    def batch_export_from_search(
        self,
        query: str,
        format: str = "biocjson",
        max_pages: Optional[int] = 3,
        full_text: bool = False,
        batch_size: int = 100
    ) -> Generator[Union[Dict, str], None, None]:
        """搜索并批量导出文献，支持分批处理和错误重试
        
        参数:
            query: 搜索查询
            format: 导出格式
            max_pages: 最大搜索页数
            full_text: 是否导出全文
            batch_size: 每批处理的PMID数量
            
        返回:
            生成器，产生导出的文献内容
        """
        try:
            all_pmids = []
            for page_result in self.search(query, max_pages=max_pages):
                page_pmids = self.extract_pmids_from_results(page_result)
                all_pmids.extend(page_pmids)
                
                # 分批处理以避免URL过长和内存占用
                while len(all_pmids) >= batch_size:
                    batch = all_pmids[:batch_size]
                    try:
                        # 确保所有PMID都是字符串类型
                        batch = [str(pmid) for pmid in batch]
                        result = self.export_publications(
                            batch,
                            "pmid",
                            format,
                            full_text
                        )
                        yield result
                        all_pmids = all_pmids[batch_size:]
                    except requests.exceptions.RequestException as e:
                        # 处理导出失败的情况
                        print(f"批量导出失败(批次大小:{len(batch)}): {str(e)}")
                        # 减小批次大小重试
                        if batch_size > 10:
                            batch_size = batch_size // 2
                            continue
                        raise
            
            # 处理剩余的PMID
            if all_pmids:
                try:
                    # 确保所有剩余的PMID都是字符串类型
                    all_pmids = [str(pmid) for pmid in all_pmids]
                    result = self.export_publications(
                        all_pmids,
                        "pmid",
                        format,
                        full_text
                    )
                    yield result
                except requests.exceptions.RequestException as e:
                    print(f"处理剩余PMID失败(数量:{len(all_pmids)}): {str(e)}")
                    raise
                    
        except Exception as e:
            raise Exception(f"批量导出过程中发生错误: {str(e)}")

if __name__ == "__main__":
    import argparse
    import logging
    from datetime import datetime
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 命令行参数
    parser = argparse.ArgumentParser(description='PubTator3API Test Program')
    parser.add_argument('--test', choices=['all', 'export', 'entity', 'relation', 'annotate', 'search'],
                        default='all', help='Select test case to run')
    args = parser.parse_args()
    
    try:
        api = PubTator3API(max_retries=3, timeout=30)
        
        def test_export_publications():
            logger.info("Testing export publications functionality...")
            pmids = ["25359968", "25359969"]
            result = api.export_publications(pmids, format="biocjson")
            logger.info(f"Successfully exported {len(pmids)} publications")
            return result
        
        def test_find_entity_id():
            logger.info("Testing find entity ID functionality...")
            query = "diabetes"
            result = api.find_entity_id(query, concept="disease", limit=5)
            logger.info(f"Successfully found entity: {query}")
            return result
        
        def test_find_related_entities():
            logger.info("Testing find related entities functionality...")
            entity_id = "@DISEASE_Diabetes_Mellitus"  # Use correct entity ID format
            result = api.find_related_entities(
                entity_id,
                relation_type="treat",
                target_entity_type="chemical"
            )
            logger.info(f"Successfully found entities related to {entity_id}")
            return result
        
        
        
        def test_search():
            logger.info("Testing search functionality...")
            query = "diabetes treatment"
            results = []
            for page_result in api.search(query, max_pages=2):
                results.append(page_result)
            logger.info(f"Successfully searched: {query}")
            return results
        
        # 执行测试
        test_funcs = {
            'export': test_export_publications,
            'entity': test_find_entity_id,
            'relation': test_find_related_entities,
            'search': test_search
        }
        
        if args.test == 'all':
            for name, func in test_funcs.items():
                # 执行所有测试用例
                try:
                    logger.info(f"\nExecuting test: {name}")
                    result = func()
                    logger.info(f"Test successful: {name}\n")
                except Exception as e:
                    logger.error(f"Test failed {name}: {str(e)}\n")
        else:
            try:
                result = test_funcs[args.test]()
                logger.info(f"Test successful: {args.test}")
            except Exception as e:
                logger.error(f"Test failed {args.test}: {str(e)}")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Network request error: {e}")
    except ValueError as e:
        logger.error(f"Parameter error: {e}")
    except Exception as e:
        logger.error(f"Unknown error: {e}")
    finally:
        api.session.close()
