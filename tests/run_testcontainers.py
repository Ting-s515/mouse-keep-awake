from pathlib import Path

from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage


def main():
    project_root = Path(__file__).resolve().parent.parent
    image_tag = "mouse-keep-awake-tests:local"

    with DockerImage(
        path=str(project_root),
        dockerfile_path="Dockerfile.test",
        tag=image_tag,
    ) as image:
        with DockerContainer(str(image)) as container:
            wrapped = container.get_wrapped_container()
            result = wrapped.wait(timeout=180)
            output = wrapped.logs(stdout=True, stderr=True).decode(
                "utf-8",
                errors="replace",
            )
            print(output, end="")
            if result.get("StatusCode") != 0:
                raise SystemExit(result.get("StatusCode", 1))


if __name__ == "__main__":
    main()
