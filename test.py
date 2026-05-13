from compose_spec import PyCompose
from systemd_unit_edit import SystemdUnit

yaml = """
services:
  web:
    image: nginx:latest
    ports:
      - 80:80
    environment:
      FOO: bar
volumes:
  data:
"""

unit = SystemdUnit(
    """[Unit]
Description=Test Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/test
"""
)

c = PyCompose.from_yaml(yaml)
print(c.service_names())  # ['web']
print(c.volumes)  # {'data': None}

# Round-trip back to YAML
print(c.to_yaml())

# Convert to Python dict
d = c.to_dict()
print(d)
