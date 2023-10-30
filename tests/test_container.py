from calendar import c
import os
import shutil
import time
from contextlib import contextmanager
import pytest
import docker
import redis_record


# Define a Docker client for interacting with the Docker daemon
docker_client = docker.from_env()
docker_path = os.path.dirname(os.path.dirname(__file__))
RECORDING_DIR = os.path.abspath(os.path.join(docker_path, "test-recordings"))

@contextmanager
def docker_container(*a, **kw):
    container_name = kw.get('name', None)
    if container_name:
        try:
            ex_container = docker_client.containers.get(container_name)
            print("Existing container:", ex_container.name)
            yield ex_container
            return
        except docker.errors.NotFound:
            pass
    container = docker_client.containers.run(*a, detach=True, **kw)
    try:
        print("Started container:", container.name)
        yield container
    finally:
        print("Stopping container:", container.name)
        container.stop()
        container.remove()


@pytest.fixture(scope="module")
def redis_record_image():
    tag = 'redis-record:test'
    # Build the Docker image from a Dockerfile
    image, _ = docker_client.images.build(path=docker_path, tag=tag)
    yield image


@pytest.fixture(scope="module")
def redis_container():
    with docker_container(
        "redis:latest",
        name="redis",
        restart_policy={"Name": "unless-stopped"},
        ports={"6379/tcp": 6379, "8001/tcp": 8001},
    ) as container:
        yield container


@pytest.fixture(scope="module")
def record_container(redis_record_image, redis_container, record_dir):
    networks = list(redis_container.attrs['NetworkSettings']['Networks'].keys())
    with docker_container(
        redis_record_image.tags[0],
        name="redis-record",
        network=networks[0],
        environment={"PYTHONUNBUFFERED": "1"},
        volumes={record_dir: {"bind": "/src/recordings", "mode": "rw"}},
        restart_policy={"Name": "unless-stopped"},
    ) as container:
        yield container


@pytest.fixture(scope="module")
def replay_container(redis_record_image, redis_container, record_dir):
    networks = list(redis_container.attrs['NetworkSettings']['Networks'].keys())
    with docker_container(
        redis_record_image.tags[0],
        name="redis-replay",
        command="-m redis_record.replay",
        network=networks[0],
        environment={"PYTHONUNBUFFERED": "1"},
        volumes={record_dir: {"bind": "/src/recordings", "mode": "rw"}},
        restart_policy={"Name": "unless-stopped"},
    ) as container:
        yield container


@pytest.fixture(scope="module")
def containers(redis_container, record_container, replay_container):
    yield [record_container, replay_container, redis_container]


@pytest.fixture(scope="module")
def record_commands():
    with redis_record.Commands() as cmds:
        yield cmds

@pytest.fixture(scope="module")
def record_dir():
    try:
        os.makedirs(RECORDING_DIR, exist_ok=True)
        yield RECORDING_DIR
    finally:
        # shutil.rmtree(RECORDING_DIR)
        pass


def test_reader_writer():
    pass



def test_record(containers, record_commands, record_dir):
    time.sleep(2)
    record_name = "asdf"
    stream_id = 'test'
    print("start")
    record_commands.start(record_name)
    time.sleep(1)
    print("data")
    data = []
    for i in range(50):
        x, t = record_commands.add_fake(stream_id, i)
        data.append(x)
        print(i, t, x)
        time.sleep(0.001)
    print("stop")
    time.sleep(0.01)
    print(record_commands.stop())
    time.sleep(5)

    print("replay")
    t0 = time.time()
    record_commands.replay(record_name)
    print("read")
    data2, cursor = read_until(record_commands, stream_id, t0, len(data))
    print("stop")
    record_commands.stop_replay()

    print(data)
    print(data2)
    assert data == data2


def read_until(record_commands, stream_id, t0, n):
    data2 = []
    cursor = {stream_id: f'{t0*1000:.0f}-0'}
    while True:
        x, cursor = record_commands.read(cursor)
        time.sleep(0.0005)
        if not x:
            print("no data", cursor, len(data2))
            time.sleep(1)
        for sid, xs in x:
            if not xs:
                print("no data in", sid, len(data2))
                time.sleep(1)
            for t, d in xs:
                print(t, len(data2), n)
                data2.append(d[b'd'])
            if len(data2) >= n:
                return data2, cursor

if __name__ == '__main__':
    pytest.main()