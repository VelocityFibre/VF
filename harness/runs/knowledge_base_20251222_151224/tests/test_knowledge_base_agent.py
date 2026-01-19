import os
import json
import pytest
from typing import List, Dict
from agents.knowledge_base.agent import KnowledgeBaseAgent


class TestKnowledgeBaseAgent:
    @pytest.fixture
    def agent(self):
        """Create a KnowledgeBaseAgent for testing"""
        return KnowledgeBaseAgent()

    @pytest.mark.unit
    @pytest.mark.tools
    def test_document_claude_skills_method_exists(self, agent):
        """Verify the document_claude_skills method exists"""
        assert hasattr(agent, 'document_claude_skills'), "Agent missing document_claude_skills method"

    @pytest.mark.unit
    @pytest.mark.tools
    def test_skills_config_json_exists(self, agent):
        """Verify skills_config.json exists and is valid"""
        assert os.path.exists(agent.skills_config_path), f"Skills config not found at {agent.skills_config_path}"
        
        with open(agent.skills_config_path, 'r') as f:
            skills_config = json.load(f)
        
        assert isinstance(skills_config, dict), "skills_config.json must be a dictionary"
        assert len(skills_config) > 0, "skills_config.json must have at least one skill"

    @pytest.mark.unit
    @pytest.mark.tools
    def test_skills_config_schema(self, agent):
        """Verify skills configuration follows expected schema"""
        with open(agent.skills_config_path, 'r') as f:
            skills_config = json.load(f)
        
        for skill_name, skill_config in skills_config.items():
            assert 'description' in skill_config, f"{skill_name} missing description"
            assert 'purpose' in skill_config, f"{skill_name} missing purpose"
            assert 'use_cases' in skill_config, f"{skill_name} missing use_cases"
            assert 'capabilities' in skill_config, f"{skill_name} missing capabilities"
            
            # Test list type fields
            assert isinstance(skill_config['use_cases'], list), f"{skill_name} use_cases must be a list"
            assert isinstance(skill_config['capabilities'], list), f"{skill_name} capabilities must be a list"

    @pytest.mark.integration
    @pytest.mark.tools
    def test_document_claude_skills_returns_markdown(self, agent):
        """Test document_claude_skills generates proper markdown documentation"""
        skills_docs = agent.document_claude_skills()
        
        assert isinstance(skills_docs, dict), "Should return dictionary of markdown docs"
        assert len(skills_docs) > 0, "Should document at least one skill"
        
        for skill_name, markdown_doc in skills_docs.items():
            assert isinstance(markdown_doc, str), f"{skill_name} documentation should be a string"
            assert markdown_doc.startswith(f"# {skill_name.capitalize()} Claude Skill"), "Markdown should have proper header"
            
            # Check for key markdown sections
            assert "## Overview" in markdown_doc, f"Missing Overview in {skill_name} documentation"
            assert "## Purpose" in markdown_doc, f"Missing Purpose in {skill_name} documentation"
            assert "## When to Use" in markdown_doc, f"Missing When to Use in {skill_name} documentation"

    @pytest.mark.integration
    @pytest.mark.tools
    def test_document_specific_skills(self, agent):
        """Test ability to document specific skills"""
        specific_skills = ["database_ops"]
        skills_docs = agent.document_claude_skills(skills_filter=specific_skills)
        
        assert isinstance(skills_docs, dict), "Should return dictionary of markdown docs"
        assert len(skills_docs) == len(specific_skills), "Should return docs only for specified skills"
        
        for skill_name in specific_skills:
            assert skill_name in skills_docs, f"{skill_name} documentation not found"