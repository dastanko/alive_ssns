import base64
import os
import subprocess
import sys
import time

import requests

IMAGE_NAME = "postgres:12-alpine"
CONTAINER_NAME = "postgres"


def main(token):
    # pull postgres image, otherwise fails on first run
    subprocess.check_call("docker pull postgres:12-alpine", shell=True, stdout=subprocess.DEVNULL)
    # clean up before running again
    subprocess.run("docker stop postgres && docker rm postgres", check=False, shell=True, stdout=subprocess.DEVNULL)

    # download dump file
    response = requests.get(f"https://hackattic.com/challenges/backup_restore/problem?access_token={token}")
    data = response.json()['dump']
    decode = base64.b64decode(data)
    with open("dump.gz", "wb") as file:
        file.write(decode)

    # uncompress file
    subprocess.check_call(["gzip", "-fd", "dump.gz"])

    # start postgres
    cwd = os.getcwd()
    subprocess.check_call(["docker", "run", "-d", "-v", f"{cwd}:/code",
                           "-e", "POSTGRES_PASSWORD=mysecretpassword", "--name", CONTAINER_NAME, IMAGE_NAME],
                          stdout=subprocess.DEVNULL)

    # wait until postgres starts
    time.sleep(2)

    # restore dump
    subprocess.check_call(["docker", "exec",
                           "-u", "postgres", CONTAINER_NAME, "bash", "-c", "psql -d postgres -f /code/dump "],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # get all alive people
    output = subprocess.check_output(["docker", "exec", "-u", "postgres", CONTAINER_NAME,
                                      "bash", "-c",
                                      "psql -t -U postgres -d postgres -c \"select ssn from criminal_records where status = 'alive';\" | cat"]).decode()

    # submit solution
    solution_response = requests.post(f'https://hackattic.com/challenges/backup_restore/solve?access_token={token}',
                                      json={"alive_ssns": output.split()})
    print(solution_response.json())


if __name__ == '__main__':
    main(sys.argv[1])
