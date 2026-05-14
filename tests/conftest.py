"""Shared fixtures for the quadlet-compose test suite."""

import pytest


@pytest.fixture
def sample_compose_minimal() -> dict:
    """Minimal compose dict with a single service."""
    return {
        "services": {
            "web": {
                "image": "nginx:latest",
            },
        },
    }


@pytest.fixture
def sample_compose_full() -> dict:
    """Compose dict exercising many service fields."""
    return {
        "name": "myapp",
        "services": {
            "web": {
                "image": "nginx:alpine",
                "container_name": "myapp-web",
                "hostname": "webhost",
                "working_dir": "/app",
                "user": "appuser",
                "environment": {
                    "FOO": "bar",
                    "BAZ": "qux",
                },
                "ports": ["8080:80", "8443:443"],
                "volumes": [
                    {
                        "type": "bind",
                        "source": "/host/path",
                        "target": "/container/path",
                        "read_only": True,
                    },
                    {"type": "volume", "source": "data", "target": "/data"},
                    {"type": "tmpfs", "target": "/tmp"},
                ],
                "networks": ["frontend", "backend"],
                "labels": {"com.example.label": "value"},
                "cap_add": ["NET_ADMIN"],
                "cap_drop": ["MKNOD"],
                "dns": ["8.8.8.8"],
                "dns_search": ["example.com"],
                "extra_hosts": ["myhost:1.2.3.4"],
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost/"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                    "start_period": "40s",
                },
                "logging": {
                    "driver": "json-file",
                    "options": {
                        "max-size": "10m",
                        "max-file": "3",
                    },
                },
                "mem_limit": "512m",
                "pids_limit": 100,
                "shm_size": "64m",
                "tmpfs": ["/run", "/tmp"],
                "devices": ["/dev/sda:/dev/xvda"],
                "group_add": ["dialout"],
                "secrets": ["db_password"],
                "stop_grace_period": "30s",
                "stop_signal": "SIGTERM",
                "init": True,
                "read_only": True,
                "pull_policy": "always",
                "cgroup": "private",
                "ulimits": {
                    "nofile": {"soft": 65536, "hard": 65536},
                    "nproc": 4096,
                },
                "sysctls": {
                    "net.core.somaxconn": "1024",
                },
            },
        },
        "networks": {
            "frontend": {
                "driver": "bridge",
                "ipam": {
                    "driver": "default",
                    "config": [
                        {"subnet": "172.20.0.0/16", "gateway": "172.20.0.1"},
                    ],
                },
            },
            "backend": None,
        },
        "volumes": {
            "data": {
                "driver": "local",
                "labels": {"com.example.volume": "data"},
            },
        },
    }
