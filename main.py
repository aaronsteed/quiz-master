import questionary
import os
import yaml
from quiz_master.template_engine import TemplateEngine, Chart, Image, Service, Port, Volume, DEFAULT_HOST_PATH, DEFAULT_NFS_PATH

class VolumeBuilder:
    volume: Volume

    def __init__(self):
        self.volume = Volume()

    def with_app_name(self, app_name: str) -> "VolumeBuilder":
        self.volume.app_name = app_name
        return self

    def with_container_path(self, container_path: str) -> "VolumeBuilder":
        self.volume.container_path = container_path
        return self

    def with_nfs_path(self, container_path: str) -> "VolumeBuilder":
        self.volume.nfs_mount_path = f"{DEFAULT_NFS_PATH}/{self.volume.app_name}/{container_path}"
        self.volume.type = "nfs"
        return self

    def with_host_path(self, container_path: str) -> "VolumeBuilder":
        self.volume.host_path = f"{DEFAULT_HOST_PATH}/{self.volume.app_name}/{container_path}"
        self.volume.type = "local-path"
        return self

    def with_volume_mount_name(self, volume_mount_name: str) -> "VolumeBuilder":
        self.volume.volume_mount_name = volume_mount_name
        return self

    def build(self) -> Volume:
        return self.volume


def volume_question(app_name: str) -> Volume:
    volume_builder = VolumeBuilder().with_app_name(app_name)
    container_volume = questionary.text("Volumes the container needs").ask()
    volume_kind = questionary.select("What kind of volume is this?", choices=["local-path", "nfs"]).ask()
    volume_mount_name = questionary.text("What is the name of the volume mount?").ask()
    if volume_kind == "local-path":
        return (volume_builder.
                with_host_path(container_volume)
                .with_container_path(container_volume)
                .with_volume_mount_name(volume_mount_name)
                .build())
    elif volume_kind == "nfs":
        return (volume_builder.
                with_nfs_path(container_volume)
                .with_container_path(container_volume)
                .with_volume_mount_name(volume_mount_name)
                .build())
    return None


def volume_questions(app_name: str) -> list[Volume]:
    volumes = [volume_question(app_name)]
    more_volumes = questionary.confirm("Do you need more volumes?").ask()
    while more_volumes:
        volumes.append(volume_question(app_name))
        more_volumes = questionary.confirm("Do you need more volumes?").ask()
    return volumes


def image_questions() -> Image:
    repository = questionary.text("What repository do you want to use?").ask()
    tag = questionary.text("What tag do you want to use?").ask()
    return Image(repository=repository, tag=tag)


def resolved_k8s_service_name(app_name: str, port_name: str) -> str:
    return f"{app_name}-{port_name}"

def route_questions(service: Service) -> None:

    # detect if routes chart is available
    # check if routes directory exists in current directory
    routes_dir = os.path.join(os.getcwd(), "routes")
    if not os.path.isdir(routes_dir):
        print("No `routes` directory found in the current path; skipping route configuration.")
        return None

    needs_route = questionary.confirm("Do you need routes?").ask()
    if needs_route:
        values_file = os.path.join(routes_dir, "values.yaml")
        if os.path.exists(values_file):
            with open(values_file, "r", encoding="utf-8") as f:
                try:
                    values = yaml.safe_load(f)
                except Exception:
                    print("Failed to parse `values.yaml`; skipping route configuration.")
                    return None

        first_tcp_route = next((port for port in service.ports if port.protocol == "TCP"), None)
        if first_tcp_route is None:
            print("No TCP ports found in the service; skipping route configuration.")
            return None

        name = questionary.text("Route name").ask()
        subdomain = questionary.text("Subdomain").ask()
        auth_enabled = questionary.confirm("Enable auth for this route?").ask()
        service = f"{service.name}-{first_tcp_route.name}"
        port = first_tcp_route.port
        namespace = "default"
        skip_verify = questionary.confirm("Skip TLS verification for this route?").ask()

        route = {
            "name": name,
            "subdomain": subdomain,
            "authEnabled": bool(auth_enabled),
            "service": service,
            "port": int(port)
        }
        if namespace:
            route["namespace"] = namespace
        if skip_verify:
            route["skipVerify"] = True

        values["routes"].append(route)

        with open(values_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(values, f, sort_keys=False, default_flow_style=False)


def port_question(app_name: str) -> Port:
    port_number = questionary.text("what port does the service use").ask()

    port_name = questionary.text("Name for the port number").ask()
    if len(resolved_k8s_service_name(app_name, port_name)) > 15:
        print(f"Warning: The combined length of app name and port name exceeds 15 characters "
              f"({resolved_k8s_service_name(app_name, port_name)}). This may cause issues in Kubernetes.")

    port_type = questionary.select("What type of port do you want to use?", choices=["ClusterIP", "LoadBalancer"]).ask()
    protocol = questionary.select("what protocol do you want to use?", choices=["UDP", "TCP"]).ask()
    return Port(int(port_number), port_name, protocol, port_type)

def service_questions(app_name: str) -> Service:
    ports = [port_question(app_name)]
    needs_more_ports = questionary.confirm("Do you need more ports?").ask()
    while needs_more_ports:
        ports.append(port_question())
        needs_more_ports = questionary.confirm("Do you need more ports?").ask()
    return Service(app_name, ports)

def main():
    chart_name = questionary.text("What is the name of your chart").ask()
    description = questionary.text("What does this service do").ask()
    image = image_questions()
    volumes = volume_questions(chart_name)
    service = service_questions(chart_name)
    route_questions(service)


    chart = Chart(
        name=chart_name,
        description=description,
        image=image,
        volumes=volumes,
        service=service
    )
    # Call templating engine here
    template_engine = TemplateEngine(chart)
    template_engine.render_and_output()


if __name__ == "__main__":
    main()
