import unittest
from pathlib import Path


class AgentConfigTests(unittest.TestCase):
    def test_openai_agent_exposes_natural_router_as_direct_tool(self):
        config_path = Path(__file__).resolve().parents[1] / "skills" / "chanjet-mcp" / "agents" / "openai.yaml"
        config_text = config_path.read_text(encoding="utf-8")

        self.assertIn("direct_tools:", config_text)
        self.assertIn('- "call_natural"', config_text)
        self.assertIn('- "call_api_smart"', config_text)
        self.assertIn('- "search_api_templates"', config_text)
        self.assertIn('- "call_api_template"', config_text)
        self.assertNotIn("call_tplus_api_smaart", config_text)

