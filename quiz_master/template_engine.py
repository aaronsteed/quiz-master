from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
import os
import sys

DEFAULT_HOST_PATH = "/k3s/local-path"
DEFAULT_NFS_PATH = "/volume1/nfs/k3s"

@dataclass(init=False)
class Volume:
    app_name: str
    volume_mount_name: str
    type: str # nfs or local-path
    container_path: str = None
    nfs_mount_path: str = None
    host_path: str = None

    def __init__(self, **kwargs):
        self.app_name = kwargs.get("app_name")
        self.nfs_mount_path = kwargs.get("nfs_mount_path")
        self.host_path = f"{DEFAULT_HOST_PATH}/{self.app_name}"

    def is_host_path(self) -> bool:
        return self.host_path is not None

    def is_nfs_path(self) -> bool:
        return self.nfs_mount_path is not None

@dataclass
class Image:
    repository: str
    tag: str

@dataclass
class Port:
    port: int
    name: str
    protocol: str
    type: str

@dataclass
class Service:
    name: str
    ports: list[Port]

@dataclass
class Chart:
    name: str
    description: str
    image: Image
    volumes: list[Volume]
    service: Service


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    if hasattr(sys, "_MEIPASS"):
        # Running from PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal Python
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def templatable_files():
    appended_files = []
    chart_starter_dir = resource_path('data/chart-starter')
    os.listdir(chart_starter_dir)
    print(chart_starter_dir)
    for root, dirs, files in os.walk(chart_starter_dir):
        for filename in files:
            # Get the relative path from chart-starter to the file
            rel_dir = os.path.relpath(root, chart_starter_dir)
            rel_path = os.path.join(rel_dir, filename) if rel_dir != '.' else filename
            appended_files.append(rel_path)
    print(appended_files)
    return appended_files


class TemplateEngine:
    def __init__(self, chart: Chart):
        self.chart = chart

    def render_and_output(self):
        files = templatable_files()
        template_dir = resource_path('data/chart-starter')
        env = Environment(
            block_start_string='[%',
            block_end_string='%]',
            variable_start_string='[[',
            variable_end_string=']]',
            comment_start_string='[#',
            comment_end_string='#]',
            loader=FileSystemLoader(template_dir))
        for filename in files:
            template = env.get_template(filename)
            output = template.render(chart=self.chart, service=self.chart.service)
            output_path = os.path.join(os.getcwd(), self.chart.name, filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            print(f"Writing {self.chart.name} to {output_path}")
            with open(output_path, 'w') as f:
                f.write(output)
