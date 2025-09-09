import questionary
from dataclasses import dataclass

DEFAULT_HOST_PATH = "/k3s/local-path"
DEFAULT_NFS_PATH = "/volume1/nfs/k3s"

@dataclass(init=False)
class Volume:
    app_name: str
    volume_mount_name: str
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

class VolumeBuilder:
    volume: Volume

    def __init__(self):
        self.volume = Volume()

    def with_app_name(self, app_name: str) -> "VolumeBuilder":
        self.volume.app_name = app_name
        return self

    def with_nfs_path(self, container_path: str) -> "VolumeBuilder":
        self.volume.nfs_mount_path = f"{DEFAULT_NFS_PATH}/{self.volume.app_name}/{container_path}"
        return self

    def with_host_path(self, container_path: str) -> "VolumeBuilder":
        self.volume.host_path = f"{DEFAULT_HOST_PATH}/{self.volume.app_name}/{container_path}"
        return self

    def with_volume_mount_name(self, app_name: str, volume_mount_name: str) -> "VolumeBuilder":
        self.volume.volume_mount_name = f"{app_name}-{volume_mount_name}"
        return self

    def build(self) -> Volume:
        return self.volume


def volume_question(app_name: str) -> Volume:
    volume_builder = VolumeBuilder().with_app_name(app_name)
    container_volume = questionary.text("Volumes the container needs").ask()
    volume_kind = questionary.select("What kind of volume is this?", choices=["host", "nfs"]).ask()
    volume_mount_name = questionary.text("What is the name of the volume mount?").ask()
    if volume_kind == "host":
        return (volume_builder.
                with_host_path(container_volume)
                .with_volume_mount_name(app_name, volume_mount_name)
                .build())
    elif volume_kind == "nfs":
        return (volume_builder.
                with_nfs_path(container_volume)
                .with_volume_mount_name(app_name, volume_mount_name)
                .build())

def volume_questions(app_name: str) -> list[Volume]:
    volumes = []
    volumes.append(volume_question(app_name))
    more_volumes = questionary.confirm("Do you need more volumes?").ask()
    while more_volumes:
        volumes.append(volume_question(app_name))
        more_volumes = questionary.confirm("Do you need more volumes?").ask()
    return volumes


@dataclass
class Image:
    repository: str
    tag: str

def image_questions() -> Image:
    repository = questionary.text("What repository do you want to use?").ask()
    tag = questionary.text("What tag do you want to use?").ask()
    return Image(repository=repository, tag=tag)

@dataclass
class Port:
    port: int
    name: str
    protocol: str

@dataclass
class Service:
    name: str
    ports: list[Port]

def port_question() -> Port:
    port_number = questionary.text("what port does the service use").ask()
    port_name = questionary.text("Name for the port number").ask()
    protocol = questionary.select("what protocol do you want to use?", choices=["http", "udp", "tcp"]).ask()
    return Port(port_number, port_name, protocol)

def service_questions(app_name: str) -> Service:
    ports = []
    ports.append(port_question())
    needs_more_ports = questionary.confirm("Do you need more ports?").ask()
    while needs_more_ports:
        ports.append(port_question())
        needs_more_ports = questionary.confirm("Do you need more ports?").ask()
    return Service(app_name, ports)

def main():
    value = questionary.text("What is the name of your chart").ask()
    image = image_questions()
    volumes = volume_questions(value)
    service = service_questions(value)

    print(service)
    print(image)
    print(volumes)
    print(value)

if __name__ == "__main__":
    main()
