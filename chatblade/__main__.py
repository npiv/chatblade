from . import cli


def main():
    cli.cli()


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        exit()
