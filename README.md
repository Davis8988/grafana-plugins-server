# Usage Instructions:

Set envs for grafana container:

1. `GF_INSTALL_PLUGINS` - for grafana container to auto install specified plugins from this server  
2. `GF_PLUGIN_REPO` - Address of this **grafana plugins server** followed by **'/plugins'** (E.g http://grafana-plugins-server:3011/plugins)

<u>Example</u>:  

```bash
docker run -d -p 3000:3000 --name=grafana \
  -e "GF_PLUGIN_REPO=http://grafana-plugins-server:3011/plugins" \
  -e "GF_INSTALL_PLUGINS=grafana-clock-panel, grafana-simple-json-datasource" \
  grafana/grafana-enterprise
```
See reference here: https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/



# Example usage of grafana-cli: 

```bash
grafana-cli.exe --repo http://localhost:3011/plugins plugins list-remote
```

