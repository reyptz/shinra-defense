"""
Honeypot Container Management
Manages Docker/Podman containers for honeypot provisioning
"""
import docker
from docker.errors import DockerException, APIError
from typing import Optional, Dict, List
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HoneypotContainerManager:
    """Manages honeypot containers using Docker/Podman"""
    
    def __init__(self, use_podman: bool = False):
        """
        Initialize container manager
        
        Args:
            use_podman: If True, use Podman instead of Docker
        """
        try:
            if use_podman:
                # Connect to Podman socket via DockerClient
                # docker.from_env() n'accepte pas de paramètre 'environment'.
                self.client = docker.DockerClient(
                    base_url="unix:///run/podman/podman.sock"
                )
            else:
                self.client = docker.from_env()
            
            logger.info("Connected to container runtime successfully")
        except DockerException as e:
            logger.error(f"Failed to connect to container runtime: {e}")
            raise
    
    def create_smb_honeypot(
        self, 
        name: str, 
        port: int = 445, 
        network: str = "bridge"
    ) -> Optional[str]:
        """
        Create an SMB honeypot container
        
        Args:
            name: Container name
            port: Port to expose
            network: Docker network
            
        Returns:
            Container ID or None on failure
        """
        try:
            container = self.client.containers.run(
                image="crazymax/samba:latest",
                name=name,
                ports={"445/tcp": port},
                environment={
                    "TZ": "UTC",
                    "SMB_WORKGROUP": "WORKGROUP",
                    "SMB_SHARE": "honeypot",
                    "SMB_SHARE_PATH": "/data",
                },
                volumes={
                    "/tmp/honeypot-data": {"bind": "/data", "mode": "rw"}
                },
                detach=True,
                network=network,
                auto_remove=False
            )
            
            logger.info(f"SMB honeypot created: {container.id}")
            return container.id
        except APIError as e:
            logger.error(f"Failed to create SMB honeypot: {e}")
            return None
    
    def create_ssh_honeypot(
        self, 
        name: str, 
        port: int = 22, 
        network: str = "bridge"
    ) -> Optional[str]:
        """
        Create an SSH honeypot container
        
        Args:
            name: Container name
            port: Port to expose
            network: Docker network
            
        Returns:
            Container ID or None on failure
        """
        try:
            container = self.client.containers.run(
                image="dtagdevsec/cowrie:latest",
                name=name,
                ports={"2222/tcp": port},
                environment={
                    "COWRIE_TELNET_ENABLED": "false",
                },
                detach=True,
                network=network,
                auto_remove=False
            )
            
            logger.info(f"SSH honeypot created: {container.id}")
            return container.id
        except APIError as e:
            logger.error(f"Failed to create SSH honeypot: {e}")
            return None
    
    def create_http_honeypot(
        self, 
        name: str, 
        port: int = 80, 
        network: str = "bridge"
    ) -> Optional[str]:
        """
        Create an HTTP honeypot container
        
        Args:
            name: Container name
            port: Port to expose
            network: Docker network
            
        Returns:
            Container ID or None on failure
        """
        try:
            container = self.client.containers.run(
                image="honeypot/honeytrap:latest",
                name=name,
                ports={"80/tcp": port},
                detach=True,
                network=network,
                auto_remove=False
            )
            
            logger.info(f"HTTP honeypot created: {container.id}")
            return container.id
        except APIError as e:
            logger.error(f"Failed to create HTTP honeypot: {e}")
            return None
    
    def stop_container(self, container_id: str) -> bool:
        """
        Stop a container by ID
        
        Args:
            container_id: Container ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            logger.info(f"Container stopped: {container_id}")
            return True
        except APIError as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False
    
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """
        Remove a container by ID
        
        Args:
            container_id: Container ID
            force: Force removal
            
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Container removed: {container_id}")
            return True
        except APIError as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False
    
    def get_container_stats(self, container_id: str) -> Optional[Dict]:
        """
        Get container statistics
        
        Args:
            container_id: Container ID
            
        Returns:
            Dictionary with stats or None on failure
        """
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            return {
                "container_id": container_id,
                "status": container.status,
                "cpu_usage": stats["cpu_stats"]["cpu_usage"]["total_usage"],
                "memory_usage": stats["memory_stats"]["usage"],
                "network_rx": stats["networks"]["eth0"]["rx_bytes"] if "networks" in stats else 0,
                "network_tx": stats["networks"]["eth0"]["tx_bytes"] if "networks" in stats else 0,
            }
        except APIError as e:
            logger.error(f"Failed to get stats for container {container_id}: {e}")
            return None
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> Optional[str]:
        """
        Get container logs
        
        Args:
            container_id: Container ID
            tail: Number of lines from the end
            
        Returns:
            Log string or None on failure
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail)
            return logs.decode('utf-8')
        except APIError as e:
            logger.error(f"Failed to get logs for container {container_id}: {e}")
            return None
    
    def list_active_honeypots(self) -> List[Dict]:
        """
        List all active honeypot containers
        
        Returns:
            List of container information dictionaries
        """
        try:
            containers = self.client.containers.list(all=True)
            honeypots = []
            
            for container in containers:
                # Check if container name contains honeypot keywords
                name = container.name.lower()
                if any(keyword in name for keyword in ['honeypot', 'cowrie', 'samba', 'honeytrap']):
                    honeypots.append({
                        "id": container.id,
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else str(container.image.id),
                        "created": container.attrs["Created"],
                    })
            
            return honeypots
        except APIError as e:
            logger.error(f"Failed to list containers: {e}")
            return []
    
    def cleanup_old_honeypots(self, max_age_hours: int = 24) -> int:
        """
        Remove honeypots older than specified age
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of containers removed
        """
        removed_count = 0
        try:
            containers = self.client.containers.list(all=True)
            now = datetime.utcnow()
            
            for container in containers:
                created_str = container.attrs["Created"]
                created = datetime.strptime(created_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                age_hours = (now - created).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    if self.remove_container(container.id, force=True):
                        removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old honeypots")
            return removed_count
        except APIError as e:
            logger.error(f"Failed to cleanup old honeypots: {e}")
            return 0


# Factory function for creating specific honeypots
def create_honeypot(honeypot_type: str, name: str, port: int, use_podman: bool = False) -> Optional[str]:
    """
    Factory function to create a honeypot of specified type
    
    Args:
        honeypot_type: Type of honeypot (smb, ssh, http)
        name: Container name
        port: Port to expose
        use_podman: Use Podman instead of Docker
        
    Returns:
        Container ID or None on failure
    """
    manager = HoneypotContainerManager(use_podman=use_podman)
    
    if honeypot_type.lower() == "smb":
        return manager.create_smb_honeypot(name, port)
    elif honeypot_type.lower() == "ssh":
        return manager.create_ssh_honeypot(name, port)
    elif honeypot_type.lower() == "http":
        return manager.create_http_honeypot(name, port)
    else:
        logger.error(f"Unknown honeypot type: {honeypot_type}")
        return None
