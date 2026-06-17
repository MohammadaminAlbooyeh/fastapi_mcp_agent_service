# MCP Tools

## Available Tools

### database_tool
Database query and CRUD operations.
- `execute_query(sql)` - Execute raw SQL
- `insert_record(table, data)` - Insert a record
- `update_record(table, id, data)` - Update a record
- `delete_record(table, id)` - Delete a record
- `list_records(table, filters)` - List records

### file_tool
File system operations.
- `read_file(path)` - Read file contents
- `write_file(path, content)` - Write to file
- `list_files(directory)` - List directory contents
- `delete_file(path)` - Delete a file
- `file_exists(path)` - Check if file exists

### search_tool
Web and semantic search.
- `web_search(query)` - Search the web
- `semantic_search(query, index)` - Semantic search
- `similarity_search(text, top_k)` - Similarity search

### api_tool
External API calls.
- `http_request(method, url, headers, body)` - HTTP request
- `call_rest_api(endpoint, params)` - REST API call
- `call_graphql(query, variables)` - GraphQL query

### calculator_tool
Math and calculations.
- `execute(expression)` - Evaluate math expression
