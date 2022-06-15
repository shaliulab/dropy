import json
import argparse
from dropy.utils import load_config, save_config()

def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("token", type=str, help="Long term token generated in https://www.dropbox.com/developers/apps/info/")
    args = ap.parse_args()

    config = load_config()


    print(f"Old token: {config['token']}")
    config["token"] = args.token

    save_config(config)

if __name__ == "__main__":
    main()
