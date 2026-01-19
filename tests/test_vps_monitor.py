"""
Tests for VPS Monitor Agent

Test coverage for SSH-based monitoring functionality including:
- CPU usage parsing
- Memory usage parsing
- Disk usage parsing
- Network statistics
- Load average parsing
- Service status checking
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Import the agent
sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "vps-monitor"))
from agent import SSHVPSClient, VPSMonitorAgent


class TestSSHVPSClient:
    """Test SSH VPS Client functionality"""

    @pytest.fixture
    def vps_client(self, mock_vps_hostname):
        """Create a VPS client instance for testing"""
        return SSHVPSClient(mock_vps_hostname)

    # CPU Usage Tests
    def test_get_cpu_usage_success(self, vps_client):
        """Test successful CPU usage parsing"""
        # Arrange
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "12.4"
            }

            # Act
            result = vps_client.get_cpu_usage()

            # Assert
            assert result['cpu_percent'] == 12.4
            assert result['status'] == 'normal'

    def test_get_cpu_usage_high(self, vps_client):
        """Test CPU usage with warning threshold"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "85.5"
            }

            result = vps_client.get_cpu_usage()

            assert result['cpu_percent'] == 85.5
            assert result['status'] == 'warning'

    def test_get_cpu_usage_critical(self, vps_client):
        """Test CPU usage with critical threshold"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "95.2"
            }

            result = vps_client.get_cpu_usage()

            assert result['cpu_percent'] == 95.2
            assert result['status'] == 'critical'

    def test_get_cpu_usage_parse_error(self, vps_client):
        """Test CPU usage parsing error handling"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "invalid"
            }

            result = vps_client.get_cpu_usage()

            assert 'error' in result
            assert 'Failed to parse CPU usage' in result['error']

    def test_get_cpu_usage_ssh_failure(self, vps_client):
        """Test CPU usage when SSH command fails"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": False,
                "error": "Connection timeout"
            }

            result = vps_client.get_cpu_usage()

            assert 'error' in result

    # Memory Usage Tests
    def test_get_memory_usage_success(self, vps_client):
        """Test successful memory usage parsing"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "total=8192 used=2867 free=5325 percent=35.0"
            }

            result = vps_client.get_memory_usage()

            assert result['total'] == 8192
            assert result['used'] == 2867
            assert result['free'] == 5325
            assert result['percent'] == 35.0
            assert result['status'] == 'normal'

    def test_get_memory_usage_warning(self, vps_client):
        """Test memory usage with warning threshold"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "total=8192 used=7372 free=820 percent=90.0"
            }

            result = vps_client.get_memory_usage()

            assert result['percent'] == 90.0
            assert result['status'] == 'warning'

    def test_get_memory_usage_critical(self, vps_client):
        """Test memory usage with critical threshold"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "total=8192 used=7864 free=328 percent=96.0"
            }

            result = vps_client.get_memory_usage()

            assert result['percent'] == 96.0
            assert result['status'] == 'critical'

    # Disk Usage Tests
    def test_get_disk_usage_success(self, vps_client):
        """Test successful disk usage parsing"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "size=100G used=24G available=76G percent=24%"
            }

            result = vps_client.get_disk_usage()

            assert result['size'] == '100G'
            assert result['used'] == '24G'
            assert result['available'] == '76G'
            assert result['percent'] == '24%'
            assert result['percent_num'] == 24.0
            assert result['status'] == 'normal'

    def test_get_disk_usage_warning(self, vps_client):
        """Test disk usage with warning threshold"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "size=100G used=85G available=15G percent=85%"
            }

            result = vps_client.get_disk_usage()

            assert result['percent_num'] == 85.0
            assert result['status'] == 'warning'

    # Network Stats Tests
    def test_get_network_stats_success(self, vps_client):
        """Test successful network statistics parsing"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "rx_bytes=155914567890 tx_bytes=96012345678"
            }

            result = vps_client.get_network_stats()

            assert 'rx_bytes' in result
            assert 'tx_bytes' in result
            assert 'rx_bytes_raw' in result
            assert 'tx_bytes_raw' in result
            assert isinstance(result['rx_bytes'], float)
            assert isinstance(result['tx_bytes'], float)

    # Load Average Tests
    def test_get_load_average_success(self, vps_client):
        """Test successful load average parsing"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "1min=0.45 5min=0.67 15min=0.52"
            }

            result = vps_client.get_load_average()

            assert result['1min'] == 0.45
            assert result['5min'] == 0.67
            assert result['15min'] == 0.52

    # Service Status Tests
    def test_get_services_status_all_running(self, vps_client):
        """Test service status when all services running"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "nginx=running\nneon-agent=running\npostgresql=running\ndocker=running"
            }

            result = vps_client.get_services_status()

            assert len(result) == 4
            assert all(svc['healthy'] for svc in result)

    def test_get_services_status_some_stopped(self, vps_client):
        """Test service status with some services stopped"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "nginx=running\nneon-agent=running\npostgresql=stopped\ndocker=stopped"
            }

            result = vps_client.get_services_status()

            assert len(result) == 4
            running = [svc for svc in result if svc['healthy']]
            stopped = [svc for svc in result if not svc['healthy']]
            assert len(running) == 2
            assert len(stopped) == 2

    # System Info Tests
    def test_get_system_info_success(self, vps_client):
        """Test successful system information retrieval"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "hostname=srv1092611\nos=Ubuntu 24.04 LTS\nkernel=6.14.0-35-generic\nuptime=up 3 days, 14 hours"
            }

            result = vps_client.get_system_info()

            assert result['hostname'] == 'srv1092611'
            assert result['os'] == 'Ubuntu 24.04 LTS'
            assert result['kernel'] == '6.14.0-35-generic'
            assert 'uptime' in result

    # Top Processes Tests
    def test_get_top_processes_success(self, vps_client):
        """Test successful top processes retrieval"""
        with patch.object(vps_client, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = {
                "success": True,
                "stdout": "1234|45.2|12.3|nginx\n5678|23.1|8.4|python3\n9012|12.5|5.2|node"
            }

            result = vps_client.get_top_processes(limit=3)

            assert len(result) == 3
            assert result[0]['pid'] == '1234'
            assert result[0]['cpu'] == '45.2'
            assert result[0]['command'] == 'nginx'


class TestVPSMonitorAgent:
    """Test VPS Monitor Agent (Claude integration)"""

    @pytest.fixture
    def vps_agent(self, mock_vps_hostname, mock_anthropic_api_key):
        """Create VPS Monitor Agent for testing"""
        return VPSMonitorAgent(mock_vps_hostname, mock_anthropic_api_key)

    def test_agent_initialization(self, vps_agent):
        """Test agent initializes correctly"""
        assert vps_agent.vps is not None
        assert vps_agent.anthropic is not None
        assert vps_agent.conversation_history == []
        assert vps_agent.model == "claude-3-5-haiku-20241022"

    def test_define_tools(self, vps_agent):
        """Test that agent defines all expected tools"""
        tools = vps_agent.define_tools()

        assert len(tools) == 9
        tool_names = [tool['name'] for tool in tools]
        assert 'get_system_info' in tool_names
        assert 'get_cpu_usage' in tool_names
        assert 'get_memory_usage' in tool_names
        assert 'get_disk_usage' in tool_names
        assert 'get_top_processes' in tool_names
        assert 'get_network_stats' in tool_names
        assert 'get_load_average' in tool_names
        assert 'get_services_status' in tool_names
        assert 'get_full_health_report' in tool_names

    def test_execute_tool_get_cpu_usage(self, vps_agent):
        """Test tool execution for CPU usage"""
        with patch.object(vps_agent.vps, 'get_cpu_usage') as mock_cpu:
            mock_cpu.return_value = {"cpu_percent": 15.3, "status": "normal"}

            result = vps_agent.execute_tool('get_cpu_usage', {})
            result_dict = eval(result)  # Parse JSON string

            assert result_dict['cpu_percent'] == 15.3
            assert result_dict['status'] == 'normal'

    def test_execute_tool_unknown(self, vps_agent):
        """Test execution of unknown tool"""
        result = vps_agent.execute_tool('unknown_tool', {})
        result_dict = eval(result)

        assert 'error' in result_dict
        assert 'Unknown tool' in result_dict['error']

    def test_clear_history(self, vps_agent):
        """Test conversation history clearing"""
        # Add some history
        vps_agent.conversation_history.append({"role": "user", "content": "test"})
        vps_agent.conversation_history.append({"role": "assistant", "content": "response"})

        assert len(vps_agent.conversation_history) == 2

        # Clear history
        vps_agent.clear_history()

        assert len(vps_agent.conversation_history) == 0
