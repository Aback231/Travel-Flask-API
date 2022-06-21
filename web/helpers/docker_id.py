import subprocess


def get_docker_id() -> str:
    bash_command = 'cat /etc/hostname'
    output = subprocess.check_output(['bash','-c', bash_command])
    return str(output)