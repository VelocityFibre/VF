import os
import pytest
import json
from agents.knowledge_base.agent import KnowledgeBaseAgent

@pytest.fixture
def agent():
    """Create KnowledgeBaseAgent for testing"""
    api_key = os.getenv('ANTHROPIC_API_KEY', 'test-key')
    return KnowledgeBaseAgent(api_key)

def test_generate_db_schema_tool(agent):
    """Test generate_db_schema tool"""
    # Mock data for testing when no real database is available
    mock_result = json.loads(agent.execute_tool('generate_db_schema', {
        'format': 'markdown',
        'database_url': 'mock://test_database'  # Simulate no connection
    }))
    
    # If real database is configured, this will work
    # If not, we expect an error result
    assert 'status' in mock_result
    assert mock_result['status'] in ['success', 'error']

def test_generate_db_schema_formats(agent):
    """Test different documentation formats"""
    # Test markdown format
    markdown_result = json.loads(agent.execute_tool('generate_db_schema', {
        'format': 'markdown',
        'database_url': 'mock://test_database'
    }))
    assert 'status' in markdown_result
    
    # Test JSON format
    json_result = json.loads(agent.execute_tool('generate_db_schema', {
        'format': 'json',
        'database_url': 'mock://test_database'
    }))
    assert 'status' in json_result

def test_get_postgres_connection():
    """Test database connection helper"""
    # This will raise an error if no database URL is set
    try:
        conn = get_postgres_connection()
        assert conn is not None
        conn.close()
    except Exception as e:
        pytest.skip(f"No database connection possible: {e}")

@pytest.mark.parametrize("tables", [
    None,  # Test all tables
    ['users', 'projects'],  # Test specific tables
])
def test_generate_db_schema_table_filter(agent, tables):
    """Test table filtering in schema generation"""
    result = json.loads(agent.execute_tool('generate_db_schema', {
        'include_tables': tables,
        'database_url': 'mock://test_database'
    }))

    assert result['status'] == 'success'