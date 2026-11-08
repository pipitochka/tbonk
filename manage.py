"""One-off administration commands, using the same image and DB configuration."""
import argparse

from app import init_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init-db"])
    parser.parse_args()
    init_db()
    print("Database schema initialized", flush=True)


if __name__ == "__main__":
    main()
