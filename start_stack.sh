
compose_file=$1
cmndStr=""
# Check if compose plugin is installed
if docker compose version >/dev/null 2>&1; then cmndStr="docker compose"
else cmndStr="docker-compose"; fi

if [ ! -z "${compose_file}" ]; then cmndStr="${cmndStr} -f \"${compose_file}\""; fi
cmndStr="${cmndStr} -d"

echo "Executing: ${cmndStr}"
eval $cmndStr