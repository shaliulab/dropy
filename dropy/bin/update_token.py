import json
import argparse
from dropy.constants import CONFIG_FILE

def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("token", type=str, help="Long term token generated in https://www.dropbox.com/developers/apps/info/")
    args = ap.parse_args()

    with open(CONFIG_FILE, "r") as filehandle:
        data = json.load(filehandle)

    print(f"Old token: {data['token']}")
    data["token"] = args.token

    with open(CONFIG_FILE, "w") as filehandle:
        json.dump(data, filehandle)

if __name__ == "__main__":
    main()
