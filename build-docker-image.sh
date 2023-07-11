
DOCKER_IMAGE_TAG=${$1:-"grafana-plugins-server:0.0.1"}
cmndStr="docker build -t \"${DOCKER_IMAGE_TAG}\" ."
echo "${cmndStr}"
eval "${cmndStr}"
if [ "$?" != "0" ]; then echo '' && echo "Error - Failure during execution of: ${cmndStr}" && echo '' && exit 1; fi
echo "Success - Finished building docker image: ${DOCKER_IMAGE_TAG}"
