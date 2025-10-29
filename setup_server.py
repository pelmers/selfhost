#!/usr/bin/env python3
"""
Server Setup Script for Self-Hosted Services

This script automates the setup of a complete self-hosted server environment including:
- Docker and Docker Compose installation
- Caddy web server installation and configuration
- Multiple services: Rybbit analytics, Ghost blog, GPX Splice Redirect, Streetwarp
- Beszel monitoring

Usage:
    python3 setup_server.py [options]

Options:
    --skip-docker       Skip Docker installation
    --skip-caddy        Skip Caddy installation
    --skip-shell        Skip Starship and zsh installation
    --skip-services     Skip service deployment
    --skip-monitoring   Skip Beszel monitoring setup
    --dry-run          Show what would be done without executing
    --help             Show this help message

Environment Variables:
    HOME - User home directory (automatically detected)
    USER - Current user (automatically detected)

Before running, ensure you have:
1. .env files copied from old server for each service
2. SSL certificates backed up from old server (/var/lib/caddy)
3. Content directories synced (~/blog/content, ~/streetwarp/video)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ServerSetup:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.script_dir = Path(__file__).parent.absolute()
        self.user = os.environ.get('USER', 'peter')
        self.home = Path.home()
        
        # Service configurations
        self.services = {
            'rybbit': {
                'path': self.script_dir / 'rybbit',
                'compose_services': ['backend', 'client', 'clickhouse', 'postgres'],
                'env_required': True,
                'description': 'Rybbit Analytics Platform'
            },
            'ghost': {
                'path': self.script_dir / 'ghost-docker',
                'compose_services': ['ghost'],
                'env_required': False,
                'description': 'Ghost Blog'
            },
            'gpx-splice-redirect': {
                'path': self.script_dir / 'gpx-splice-redirect-docker',
                'compose_services': ['gpx-splice-redirect'],
                'env_required': True,
                'description': 'GPX Splice Redirect Service'
            },
            'streetwarp': {
                'path': self.script_dir / 'streetwarp-docker',
                'compose_services': ['streetwarp-web'],
                'env_required': True,
                'description': 'Streetwarp Web Application'
            }
        }

    def _log(self, message: str, level: str = 'info') -> None:
        """Internal log method with color coding"""
        colors = {
            'info': Colors.OKBLUE,
            'success': Colors.OKGREEN,
            'warning': Colors.WARNING,
            'error': Colors.FAIL,
            'header': Colors.HEADER
        }
        
        prefix = "[DRY RUN] " if self.dry_run else ""
        color = colors.get(level, Colors.OKBLUE)
        print(f"{color}{prefix}{message}{Colors.ENDC}")

    def info(self, message: str) -> None:
        """Log an info message"""
        self._log(message, 'info')

    def success(self, message: str) -> None:
        """Log a success message"""
        self._log(message, 'success')

    def warn(self, message: str) -> None:
        """Log a warning message"""
        self._log(message, 'warning')

    def error(self, message: str) -> None:
        """Log an error message"""
        self._log(message, 'error')

    def header(self, message: str) -> None:
        """Log a header message"""
        self._log(message, 'header')

    def run_command(self, command: str, description: str = "", check: bool = True, shell: bool = True) -> subprocess.CompletedProcess:
        """Execute a shell command with logging"""
        self.info(f"Running: {description or command}")
        
        if self.dry_run:
            self.warn(f"Would execute: {command}")
            # Return a mock successful result for dry run
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')
        
        try:
            result = subprocess.run(
                command,
                shell=shell,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                self.info(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.error(f"Command failed: {e}")
            if e.stderr:
                self.error(f"Error: {e.stderr}")
            raise

    def check_prerequisites(self) -> bool:
        """Check if the system meets basic requirements"""
        self.header("Checking prerequisites...")
        
        # Check if running on Ubuntu/Debian
        try:
            result = self.run_command("lsb_release -si", check=False)
            if result.returncode != 0:
                self.warn("Could not determine Linux distribution")
            else:
                distro = result.stdout.strip()
                self.info(f"Detected distribution: {distro}")
        except FileNotFoundError:
            self.warn("lsb_release not found, assuming compatible distribution")

        # Check if running as non-root
        if os.geteuid() == 0:
            self.error("ERROR: Do not run this script as root!")
            return False

        # Check sudo access
        try:
            self.run_command("sudo -n true", "Checking sudo access", check=False)
        except subprocess.CalledProcessError:
            self.warn("This script requires sudo access. You may be prompted for your password.")

        return True

    def install_docker(self) -> None:
        """Install Docker and Docker Compose"""
        self.header("Installing Docker...")
        
        # Add Docker's official GPG key
        commands = [
            ("sudo apt-get update", "Updating package list"),
            ("sudo apt-get install -y ca-certificates curl", "Installing prerequisites"),
            ("sudo install -m 0755 -d /etc/apt/keyrings", "Creating keyrings directory"),
            (
                "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
                "Downloading Docker GPG key"
            ),
            ("sudo chmod a+r /etc/apt/keyrings/docker.asc", "Setting GPG key permissions"),
        ]
        
        for cmd, desc in commands:
            self.run_command(cmd, desc)

        # Add Docker repository
        repo_cmd = '''echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'''
        self.run_command(repo_cmd, "Adding Docker repository")

        # Install Docker
        docker_install_commands = [
            ("sudo apt-get update", "Updating package list"),
            (
                "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
                "Installing Docker packages"
            ),
            ("sudo groupadd docker", "Creating docker group (may already exist)"),
            (f"sudo usermod -aG docker {self.user}", "Adding user to docker group"),
        ]

        for cmd, desc in docker_install_commands:
            try:
                self.run_command(cmd, desc)
            except subprocess.CalledProcessError as e:
                if "already exists" in str(e.stderr) or "group 'docker' already exists" in str(e.stderr):
                    self.info(f"Skipping: {desc} (already exists)")
                else:
                    raise

        self.success("Docker installation complete. You may need to log out and back in for group changes to take effect.")

    def install_starship_and_zsh(self) -> None:
        """Install Starship prompt and switch to zsh"""
        self.header("Installing Starship prompt and zsh...")
        
        # Install zsh first
        self.run_command("sudo apt install -y zsh", "Installing zsh")
        
        # Install Starship
        self.run_command("curl -sS https://starship.rs/install.sh | sh", "Installing Starship prompt")
        
        # Copy starship config if it exists
        starship_config_src = self.script_dir / "dotfiles" / "config" / "starship.toml"
        config_dir = self.home / ".config"
        if not self.dry_run:
            config_dir.mkdir(exist_ok=True)
            self.run_command(f"cp {starship_config_src} {config_dir}/starship.toml", "Copying Starship configuration")
        
        # Copy zshrc if it exists
        zshrc_src = self.script_dir / "dotfiles" / ".zshrc"
        zshrc_dst = self.home / ".zshrc"
        if not self.dry_run:
            self.run_command(f"cp {zshrc_src} {zshrc_dst}", "Copying .zshrc configuration")
        
        # Change shell to zsh
        zsh_path = "/usr/bin/zsh"
        self.run_command(f"chsh -s {zsh_path}", f"Changing shell to zsh for user {self.user}")
        
        self.success("Starship and zsh installation complete. You may need to log out and back in for shell changes to take effect.")

    def install_caddy(self) -> None:
        """Install Caddy web server"""
        self.header("Installing Caddy...")
        
        commands = [
            ("sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl", "Installing prerequisites"),
            (
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg",
                "Adding Caddy GPG key"
            ),
            (
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list",
                "Adding Caddy repository"
            ),
            ("sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg", "Setting GPG key permissions"),
            ("sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list", "Setting repository permissions"),
            ("sudo apt update", "Updating package list"),
            ("sudo apt install -y caddy", "Installing Caddy"),
        ]

        for cmd, desc in commands:
            self.run_command(cmd, desc)

        # Copy Caddyfile
        caddyfile_src = self.script_dir / "Caddyfile"
        if caddyfile_src.exists():
            self.info("Copying Caddyfile to /etc/caddy/")
            if not self.dry_run:
                self.run_command(f"sudo cp {caddyfile_src} /etc/caddy/Caddyfile", "Copying Caddyfile")
        else:
            self.warn("Caddyfile not found in current directory")

        self.success("Caddy installation complete.")

    def restore_caddy_certificates(self) -> None:
        """Instructions for restoring Caddy certificates"""
        self.warn("Certificate restoration required:")
        self.info("To restore SSL certificates from your old server, run:")
        self.info("ssh olduser@oldserver 'sudo tar -C /var/lib/caddy -czf - .' | sudo tar -C /var/lib/caddy -xzf -")
        self.info("Then restart Caddy: sudo systemctl restart caddy")

    def check_env_files(self) -> Dict[str, bool]:
        """Check which services have .env files configured"""
        env_status = {}
        
        self.header("Checking environment files...")
        
        for service_name, config in self.services.items():
            if config['env_required']:
                env_file = config['path'] / '.env'
                env_example = config['path'] / '.env.example'
                
                if env_file.exists():
                    env_status[service_name] = True
                    self.info(f"✓ {service_name}: .env file found")
                else:
                    env_status[service_name] = False
                    self.warn(f"✗ {service_name}: .env file missing")
                    if env_example.exists():
                        self.info(f"  Example file available at: {env_example}")
            else:
                env_status[service_name] = True  # No env file required

        return env_status

    def create_required_directories(self) -> None:
        """Create required directories for services"""
        self.header("Creating required directories...")
        
        directories = [
            self.home / "blog" / "content",  # Ghost content
            self.home / "streetwarp" / "video",  # Streetwarp videos
            self.home / "www",  # Static file server
            Path("/var/log/caddy"),  # Caddy logs (requires sudo)
        ]

        for directory in directories:
            if not self.dry_run:
                if str(directory).startswith('/var'):
                    # System directory, use sudo
                    self.run_command(f"sudo mkdir -p {directory}", f"Creating {directory}")
                    self.run_command(f"sudo chown caddy:caddy {directory}", f"Setting ownership of {directory}")
                else:
                    # User directory
                    directory.mkdir(parents=True, exist_ok=True)
                    self.info(f"Created directory: {directory}")
            else:
                self.info(f"Would create directory: {directory}")

    def deploy_service(self, service_name: str) -> bool:
        """Deploy a specific service using docker compose"""
        config = self.services.get(service_name)
        if not config:
            self.error(f"Unknown service: {service_name}")
            return False

        self.header(f"Deploying {config['description']}...")
        
        service_path = config['path']
        if not service_path.exists():
            self.error(f"Service directory not found: {service_path}")
            return False

        # Check for .env file if required
        if config['env_required']:
            env_file = service_path / '.env'
            if not env_file.exists():
                self.error(f"Required .env file missing for {service_name}")
                self.info(f"Copy .env file from old server or create from {service_path}/.env.example")
                return False

        # Change to service directory and run docker compose
        original_cwd = os.getcwd()
        try:
            if not self.dry_run:
                os.chdir(service_path)
            
            # Build and start services
            compose_services = ' '.join(config['compose_services'])
            self.run_command(
                f"docker compose up -d {compose_services}",
                f"Starting {service_name} services"
            )
            
            self.success(f"✓ {config['description']} deployed successfully")
            return True
            
        except Exception as e:
            self.error(f"Failed to deploy {service_name}: {e}")
            return False
        finally:
            if not self.dry_run:
                os.chdir(original_cwd)

    def deploy_all_services(self) -> None:
        """Deploy all configured services"""
        self.header("Deploying all services...")
        
        env_status = self.check_env_files()
        
        for service_name in self.services.keys():
            if env_status.get(service_name, False):
                success = self.deploy_service(service_name)
                if not success:
                    self.warn(f"Service {service_name} deployment failed")
            else:
                self.warn(f"Skipping {service_name} due to missing .env file")

    def setup_beszel_monitoring(self) -> None:
        """Install Beszel monitoring (hub and agent)"""
        self.header("Setting up Beszel monitoring...")
        
        # Install hub
        self.run_command(
            "curl -sL https://get.beszel.dev/hub -o /tmp/install-hub.sh && chmod +x /tmp/install-hub.sh && /tmp/install-hub.sh",
            "Installing Beszel hub"
        )
        
        self.success("Beszel hub installed. Configure the agent through the web interface:")
        self.info("1. Access the Beszel web interface")
        self.info("2. Add agent with host 'localhost'")
        self.info("3. Use localhost URL to connect the agent")

    def show_status(self) -> None:
        """Show the status of all services"""
        self.header("Service Status:")
        
        try:
            # Check Docker services
            result = self.run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", check=False)
            if result.returncode == 0:
                self.info("Docker containers:")
                self.info(result.stdout)
            
            # Check Caddy status
            result = self.run_command("sudo systemctl is-active caddy", check=False)
            caddy_status = result.stdout.strip() if result.returncode == 0 else "unknown"
            self.info(f"Caddy status: {caddy_status}")
            
        except Exception as e:
            self.error(f"Error checking status: {e}")

    def show_next_steps(self) -> None:
        """Show manual steps that need to be completed"""
        self.header("\n" + "="*60)
        self.header("MANUAL STEPS REQUIRED:")
        self.header("="*60)
        
        steps = [
            "1. Copy .env files from old server to each service directory:",
            "   - rybbit/.env",
            "   - gpx-splice-redirect-docker/.env", 
            "   - streetwarp-docker/.env",
            "",
            "2. Restore SSL certificates from old server:",
            "   ssh olduser@oldserver 'sudo tar -C /var/lib/caddy -czf - .' | sudo tar -C /var/lib/caddy -xzf -",
            "",
            "3. Sync content directories from old server:",
            "   rsync -avz olduser@oldserver:~/blog/content/ ~/blog/content/",
            "   rsync -avz olduser@oldserver:~/streetwarp/video/ ~/streetwarp/video/",
            "",
            "4. Start Caddy and restart services:",
            "   sudo systemctl restart caddy",
            "   python3 setup_server.py --skip-docker --skip-caddy --skip-monitoring",
            "",
            "5. Configure Beszel monitoring through web interface",
            "",
            "6. Verify all services are running:",
            "   docker ps",
            "   sudo systemctl status caddy",
        ]
        
        for step in steps:
            if step.startswith(("   ", "  ")):
                self.info(step)
            else:
                self.warn(step)

def main():
    parser = argparse.ArgumentParser(
        description='Automated server setup for self-hosted services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--skip-docker', action='store_true', help='Skip Docker installation')
    parser.add_argument('--skip-caddy', action='store_true', help='Skip Caddy installation')
    parser.add_argument('--skip-shell', action='store_true', help='Skip Starship and zsh installation')
    parser.add_argument('--skip-services', action='store_true', help='Skip service deployment')
    parser.add_argument('--skip-monitoring', action='store_true', help='Skip Beszel monitoring setup')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--status', action='store_true', help='Show current service status')
    parser.add_argument('--service', help='Deploy only a specific service (rybbit, ghost, gpx-splice-redirect, streetwarp)')
    
    args = parser.parse_args()
    
    setup = ServerSetup(dry_run=args.dry_run)
    
    try:
        if args.status:
            setup.show_status()
            return
        
        if args.service:
            if args.service in setup.services:
                setup.deploy_service(args.service)
            else:
                setup.error(f"Unknown service: {args.service}. Available: {', '.join(setup.services.keys())}")
                return
            return
        
        setup.header("Starting server setup...")
        
        if not setup.check_prerequisites():
            return
        
        setup.create_required_directories()
        
        if not args.skip_docker:
            setup.install_docker()
        
        if not args.skip_caddy:
            setup.install_caddy()
            setup.restore_caddy_certificates()
        
        if not args.skip_shell:
            setup.install_starship_and_zsh()
        
        if not args.skip_services:
            setup.deploy_all_services()
        
        if not args.skip_monitoring:
            setup.setup_beszel_monitoring()
        
        setup.show_next_steps()
        setup.success("Setup completed!")
        
    except KeyboardInterrupt:
        setup.warn("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        setup.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()