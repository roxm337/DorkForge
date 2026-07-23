"""Allow `python -m dorkforge` to launch CLI or GUI."""
import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("gui", "--gui"):
        from dorkforge.ui.main_window import main as gui_main
        gui_main()
    else:
        from dorkforge.cli import cli
        cli()


if __name__ == "__main__":
    main()
