
Example usage of grafana-cli: 
```bash
grafana-cli.exe --repo http://localhost:3011/plugins plugins list-remote
```

Set env: `GF_INSTALL_PLUGINS` for grafana container to auto install specified plugins from this server  
Example:  
```bash
docker run -d -p 3000:3000 --name=grafana \
  -e "GF_INSTALL_PLUGINS=grafana-clock-panel, grafana-simple-json-datasource" \
  -e "GF_PLUGIN_REPO=http://grafana-plugins-server:3011/plugins" \
  grafana/grafana-enterprise
```
See reference here: https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/