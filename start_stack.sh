
compose_file=$1
echo docker run -d --name grafana-plugins-server --restart always -p 3011:3011 grafana-plugins-server:0.0.1
cmndStr=""
# Check if compose plugin is installed
if docker compose version >/dev/null 2>&1; then cmndStr="docker compose"; fi


