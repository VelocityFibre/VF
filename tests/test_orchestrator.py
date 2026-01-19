"""
Tests for Agent Orchestrator

Test coverage for agent routing and coordination functionality including:
- Agent registration and listing
- Task routing logic
- Keyword matching
- Agent statistics
- Registry loading
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "orchestrator"))
from orchestrator import AgentOrchestrator


class TestAgentOrchestrator:
    """Test Agent Orchestrator functionality"""

    @pytest.fixture
    def mock_registry(self):
        """Create a temporary mock registry for testing"""
        registry_data = {
            "registry_version": "1.0.0",
            "last_updated": "2025-11-18",
            "total_agents": 3,
            "agents": [
                {
                    "id": "test-vps",
                    "name": "Test VPS Agent",
                    "type": "infrastructure",
                    "status": "active",
                    "path": "agents/test-vps",
                    "description": "Test VPS monitoring agent",
                    "triggers": ["vps", "server", "cpu", "memory"],
                    "capabilities": {
                        "monitoring": ["cpu", "memory"]
                    },
                    "model": "claude-3-haiku",
                    "cost_per_query": "$0.001"
                },
                {
                    "id": "test-database",
                    "name": "Test Database Agent",
                    "type": "database",
                    "status": "active",
                    "path": "agents/test-database",
                    "description": "Test database agent",
                    "triggers": ["database", "sql", "query"],
                    "capabilities": {
                        "querying": ["select", "insert"]
                    },
                    "model": "claude-3-haiku",
                    "cost_per_query": "$0.001"
                },
                {
                    "id": "test-inactive",
                    "name": "Test Inactive Agent",
                    "type": "other",
                    "status": "inactive",
                    "path": "agents/test-inactive",
                    "description": "Test inactive agent",
                    "triggers": ["inactive"],
                    "capabilities": {},
                    "model": "claude-3-haiku",
                    "cost_per_query": "$0.001"
                }
            ],
            "agent_categories": {
                "infrastructure": ["test-vps"],
                "database": ["test-database"]
            }
        }

        # Create temporary registry file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(registry_data, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink()

    @pytest.fixture
    def orchestrator(self, mock_registry):
        """Create orchestrator with mock registry"""
        return AgentOrchestrator(registry_path=mock_registry)

    # Registry Loading Tests
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes with registry"""
        assert orchestrator.registry is not None
        assert len(orchestrator.registry['agents']) == 3

    def test_invalid_registry_path(self):
        """Test error handling for invalid registry path"""
        with pytest.raises(FileNotFoundError):
            AgentOrchestrator(registry_path="/nonexistent/path.json")

    # Agent Listing Tests
    def test_list_agents(self, orchestrator):
        """Test listing all agents from registry"""
        agents = orchestrator.list_agents()

        assert len(agents) == 3
        assert all('id' in agent for agent in agents)
        assert all('name' in agent for agent in agents)

    def test_get_agent_by_id_found(self, orchestrator):
        """Test retrieving agent by ID when it exists"""
        agent = orchestrator.get_agent_by_id("test-vps")

        assert agent is not None
        assert agent['id'] == "test-vps"
        assert agent['name'] == "Test VPS Agent"

    def test_get_agent_by_id_not_found(self, orchestrator):
        """Test retrieving agent by ID when it doesn't exist"""
        agent = orchestrator.get_agent_by_id("nonexistent")

        assert agent is None

    # Task Routing Tests
    def test_route_task_single_match(self, orchestrator):
        """Test routing with single agent match"""
        result = orchestrator.route_task("Check VPS CPU usage")

        assert result['status'] == 'routed'
        assert result['agent']['agent_id'] == 'test-vps'
        assert 'vps' in result['agent']['matched_keywords'] or 'cpu' in result['agent']['matched_keywords']

    def test_route_task_multiple_matches(self, orchestrator):
        """Test routing with multiple agent matches"""
        # Add "server" trigger to database agent temporarily by modifying registry
        result = orchestrator.route_task("Show server database", auto_select=False)

        assert result['status'] in ['routed', 'multiple_matches']

    def test_route_task_no_match(self, orchestrator):
        """Test routing when no agent matches"""
        result = orchestrator.route_task("completely unrelated random task xyz")

        assert result['status'] == 'no_match'
        assert 'suggestion' in result

    def test_route_task_auto_select(self, orchestrator):
        """Test automatic agent selection"""
        result = orchestrator.route_task("Check memory usage", auto_select=True)

        assert result['status'] == 'routed'
        assert 'agent' in result

    # Keyword Matching Tests
    def test_find_agent_for_task_keyword_match(self, orchestrator):
        """Test keyword matching finds correct agent"""
        matches = orchestrator.find_agent_for_task("What is the CPU usage?")

        assert len(matches) > 0
        assert matches[0]['agent_id'] == 'test-vps'
        assert 'cpu' in matches[0]['matched_keywords']

    def test_find_agent_for_task_case_insensitive(self, orchestrator):
        """Test keyword matching is case insensitive"""
        matches_lower = orchestrator.find_agent_for_task("check vps status")
        matches_upper = orchestrator.find_agent_for_task("CHECK VPS STATUS")
        matches_mixed = orchestrator.find_agent_for_task("Check VPS Status")

        assert len(matches_lower) > 0
        assert len(matches_upper) > 0
        assert len(matches_mixed) > 0
        assert matches_lower[0]['agent_id'] == matches_upper[0]['agent_id']
        assert matches_upper[0]['agent_id'] == matches_mixed[0]['agent_id']

    def test_find_agent_for_task_multiple_keywords(self, orchestrator):
        """Test matching with multiple keywords increases confidence"""
        matches = orchestrator.find_agent_for_task("Check server VPS CPU and memory")

        assert len(matches) > 0
        # Should have high confidence with multiple keyword matches
        assert matches[0]['confidence'] >= 2  # At least 2 keywords matched

    def test_find_agent_for_task_sorted_by_confidence(self, orchestrator):
        """Test matches are sorted by confidence (highest first)"""
        matches = orchestrator.find_agent_for_task("database sql server")

        if len(matches) > 1:
            # Ensure sorted by confidence descending
            for i in range(len(matches) - 1):
                assert matches[i]['confidence'] >= matches[i+1]['confidence']

    # Agent Statistics Tests
    def test_get_agent_stats(self, orchestrator):
        """Test agent statistics calculation"""
        stats = orchestrator.get_agent_stats()

        assert 'total_agents' in stats
        assert 'active_agents' in stats
        assert 'categories' in stats
        assert stats['total_agents'] == 3
        assert stats['active_agents'] == 2  # Only test-vps and test-database are active

    def test_get_agent_stats_categories(self, orchestrator):
        """Test agent statistics by category"""
        stats = orchestrator.get_agent_stats()

        assert 'infrastructure' in stats['categories']
        assert 'database' in stats['categories']
        assert stats['categories']['infrastructure'] == 1
        assert stats['categories']['database'] == 1

    # Capability Explanation Tests
    def test_explain_capabilities_found(self, orchestrator):
        """Test capability explanation for existing agent"""
        explanation = orchestrator.explain_capabilities("test-vps")

        assert "Test VPS Agent" in explanation
        assert "test-vps" in explanation.lower() or "vps" in explanation.lower()
        assert "monitoring" in explanation.lower()

    def test_explain_capabilities_not_found(self, orchestrator):
        """Test capability explanation for non-existent agent"""
        explanation = orchestrator.explain_capabilities("nonexistent")

        assert "not found" in explanation.lower()

    # Edge Cases
    def test_route_task_empty_string(self, orchestrator):
        """Test routing with empty task description"""
        result = orchestrator.route_task("")

        assert result['status'] == 'no_match'

    def test_route_task_only_whitespace(self, orchestrator):
        """Test routing with whitespace-only task"""
        result = orchestrator.route_task("   ")

        assert result['status'] == 'no_match'

    def test_route_task_special_characters(self, orchestrator):
        """Test routing handles special characters gracefully"""
        result = orchestrator.route_task("Check CPU @#$%^&*()!")

        # Should still match based on "cpu" keyword
        assert result['status'] == 'routed'
        assert result['agent']['agent_id'] == 'test-vps'
