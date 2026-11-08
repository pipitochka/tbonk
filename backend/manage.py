"""One-off administration commands, using the same image and DB configuration."""
import argparse
import logging

from backend.app import init_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init-db"])
    parser.parse_args()
    init_db()
    logging.getLogger("tbonk.admin").info("Database schema initialized")


if __name__ == "__main__":
    main()
