# TODO script up all the below
# docker
'''
   16  # Add Docker's official GPG key:
   17  sudo apt-get update
   18  sudo apt-get install ca-certificates curl
   19  sudo install -m 0755 -d /etc/apt/keyrings
   20  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   21  sudo chmod a+r /etc/apt/keyrings/docker.asc
   22  # Add the repository to Apt sources:
   23  echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
   24    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   25  sudo apt-get update
   26  sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   27  docker build -t streetwarp-web .
   28  sudo groupadd docker
   29  sudo usermod -aG docker $USER
   30  newgrp docker
'''


# caddy
'''
   85  sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
   86  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   87  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
   89  chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   90  sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   91  sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
   92  sudo apt update
   93  sudo apt install caddy
   sudo cp Caddyfile /etc/caddy/Caddyfile
   # copy certs from old server to new one
   ssh olduser@oldserver 'sudo tar -C /var/lib/caddy -czf - .' | sudo tar -C /var/lib/caddy -xzf -
   sudo systemctl restart caddy
'''

# rybbit analytics (follow https://rybbit.com/docs/self-hosting-guides/self-hosting-manual)
'''
cd rybbit
# copy .env from old server
docker compose up -d backend client clickhouse postgres
'''

# ghost
'''
cd ghost-docker
# copy .env from old server
# rsync over old content folder into ~/blog/content
docker compose up -d
'''

# gpx splice redirect
'''
cd gpx-splice-redirect-docker
# copy .env from old server
docker compose up -d
'''

# streetwarp
'''
cd streetwarp-docker
# copy .env from old server
# rsync over old streetwarp videos into ~/streetwarp/video
docker compose up -d
'''

# beszel
'''
# hub
curl -sL https://get.beszel.dev/hub -o /tmp/install-hub.sh && chmod +x /tmp/install-hub.sh && /tmp/install-hub.sh
# agent install via hub, configure as host "localhost" and use the localhost url to connect
'''
