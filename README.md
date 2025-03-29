# PubTator MCP Server
[![smithery badge](https://smithery.ai/badge/@JackKuo666/pubmed-mcp-server)](https://smithery.ai/server/@JackKuo666/pubmed-mcp-server)

🔍 A biomedical literature annotation and relationship mining server based on PubTator3, providing convenient access through the MCP interface.

PubTator MCP Server provides AI assistants with access to the PubTator3 biomedical literature annotation system through the Model Context Protocol (MCP). It allows AI models to programmatically search scientific literature, obtain annotation information, and analyze entity relationships.

🤝 Contribute • 📝 Report Issues

## ✨ Core Features
- 🔎 Literature Annotation Export: Support exporting PubTator annotation results in multiple formats ✅
- 🚀 Entity ID Lookup: Query standard identifiers for biological concepts through free text ✅
- 📊 Relationship Mining: Discover biomedical relationships between entities ✅
- 📄 Literature Search: Support literature retrieval by keywords and entity IDs ✅
- 🧠 Batch Processing: Support batch export of annotation information from search results ✅

## 🚀 Quick Start

### Requirements

- Python 3.10+
- FastMCP library

### Installation

#### Via Smithery

Use [Smithery](https://smithery.ai/server/@JackKuo666/pubmed-mcp-server) to automatically install PubTator Server:

##### Claude

```sh
npx -y @smithery/cli@latest install @JackKuo666/pubmed-mcp-server --client claude --config "{}"
```

##### Cursor

Paste in Settings → Cursor Settings → MCP → Add new server:
- Mac/Linux  
```s
npx -y @smithery/cli@latest run @JackKuo666/pubmed-mcp-server --client cursor --config "{}" 
```

##### Windsurf
```sh
npx -y @smithery/cli@latest install @JackKuo666/pubmed-mcp-server --client windsurf --config "{}"
```

##### CLine
```sh
npx -y @smithery/cli@latest install @JackKuo666/pubmed-mcp-server --client cline --config "{}"
```

#### Manual Installation

1. Clone the repository:
   ```
   git clone https://github.com/JackKuo666/PubTator-MCP-Server.git
   cd PubTator-MCP-Server
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## 📊 Usage

Start the MCP server:

```bash
python PubTator_server.py
```

### Configuration

#### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

(Mac OS)

```json
{
  "mcpServers": {
    "pubtator": {
      "command": "python",
      "args": ["-m", "pubtator-mcp-server"]
      }
  }
}
```

(Windows)

```json
{
  "mcpServers": {
    "pubtator": {
      "command": "C:\\Users\\YOUR\\PATH\\miniconda3\\envs\\mcp_server\\python.exe",
      "args": [
        "D:\\code\\YOUR\\PATH\\PubTator-MCP-Server\\PubTator_server.py"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

#### CLine Configuration
```json
{
  "mcpServers": {
    "pubtator": {
      "command": "bash",
      "args": [
        "-c",
        "source /home/YOUR/PATH/mcp-server-pubtator/.venv/bin/activate && python /home/YOUR/PATH/PubTator_server.py"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## 🛠 API Features

PubTator MCP Server provides the following core features:

### 1. Export Annotations (export_pubtator_annotations)

Export PubTator annotation results for specified PMID literature:
```python
result = await export_pubtator_annotations(
    pmids=["12345678", "87654321"],
    format="biocjson",  # Supported: pubtator, biocxml, biocjson
    full_text=False     # Whether to include full text
)
```

### 2. Entity ID Lookup (find_entity_id)

Query standard identifiers for biological concepts through free text:
```python
result = await find_entity_id(
    query="COVID-19",
    concept="disease",  # Optional: gene, disease, chemical, species, mutation
    limit=10           # Optional: limit number of results
)
```

### 3. Relationship Query (find_related_entities)

Find other entities related to a specified entity:
```python
result = await find_related_entities(
    entity_id="@DISEASE_COVID-19",
    relation_type="treat",    # Optional: treat, cause, interact, etc.
    target_entity_type="chemical"  # Optional: gene, disease, chemical
)
```

### 4. Literature Search (search_pubtator)

Search the PubTator database:
```python
results = await search_pubtator(
    query="COVID-19 treatment",
    max_pages=3,     # Optional: maximum number of pages to retrieve
    batch_size=100   # Number of results per batch
)
```

### 5. Batch Export (batch_export_from_search)

Search and batch export literature annotations:
```python
results = await batch_export_from_search(
    query="COVID-19 treatment",
    format="biocjson",
    max_pages=3,
    full_text=False,
    batch_size=100
)
```

## ⚠️ Usage Limitations

- API request rate limit: maximum 3 requests per second
- When batch exporting, use a reasonable batch_size to avoid request timeout
- For relationship queries, entity IDs must start with "@", e.g., "@DISEASE_COVID-19"

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for research purposes only. Please comply with PubTator's terms of service and use this tool responsibly.
