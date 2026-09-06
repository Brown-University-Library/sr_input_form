import subprocess
import sys


def main() -> None:
    """
    Launch browse generation with the current interpreter.
    Called by: the module entry point, docker-compose.yml web command
    """
    subprocess.Popen([sys.executable, 'disa_app/lib/generate_browse_data.py'])


if __name__ == '__main__':
    main()
