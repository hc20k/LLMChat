import subprocess
import pkg_resources
import argparse
import os


def yes(response) -> bool:
    return response.lower() == 'y' or not len(response)


def process_reqs(reqs, args):
    for r in reqs:
        try:
            pkg_resources.require(r)
        except pkg_resources.DistributionNotFound as e:
            req = e.req.name
            if not args.y:
                should_install = yes(input(f"Dependency unmet: {req}. Install? [Y/n] "))
                if not should_install:
                    print(f"Skipping {req}...")
                    continue

            print(f"Installing {req}")
            try:
                subprocess.run(["pip", "install", e.req.url if e.req.url else str(req)], check=True)
            except subprocess.CalledProcessError:
                should_continue = yes(input(f"Failed to install {req}! Continue without it? [Y/n] "))
                if not should_continue:
                    exit(1)
        except pkg_resources.VersionConflict as e:
            req = e.req.name
            if not args.y:
                should_install = yes(input(f"Version conflict with {req}! Install required version? [Y/n] "))
                if not should_install:
                    print(f"Skipping {req}...")
                    continue

            print(f"Installing {r}")
            try:
                subprocess.run(["pip", "install", str(r)], check=True)
            except subprocess.CalledProcessError:
                should_continue = yes(input(f"Failed to install {req}! Continue without it? [Y/n] "))
                if not should_continue:
                    exit(1)


def main(args):
    print("Running LLMChat updater...")

    # Check if repo needs update
    if os.path.exists(".git"):
        if (yes(input("Check for repo updates? [Y/n] "))):
            subprocess.run(["git", "pull"], check=True)
    else:
        print("Warning: unable to check for repo updates (.git folder not found)")

    # Check for pip
    try:
        import pip
    except ImportError:
        print("Error: pip isn't installed. Install it from here: https://pip.pypa.io/en/stable/installation/")
        return

    print("Checking necessary requirements...")

    # Read requirements.txt
    with open("requirements.txt", "r") as f:
        reqs = [l.strip() for l in f.readlines()]
        process_reqs(reqs, args)

    if yes(input("Necessary requirements checked! Would you like to install voice support? (Optional) [Y/n] ")):
        with open("optional/voice-requirements.txt", 'r') as f:
            reqs = [l.strip() for l in f.readlines()]
            process_reqs(reqs, args)

        # check ffmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            print(f"Detected {result.stdout}")
        except FileNotFoundError:
            print(f"ffmpeg not installed! Please install it and run this script again.")
            return

        print("Voice requirements checked!")
    
    if yes(input("Would you like to install BLIP dependencies? (Optional if not using image recognition) [Y/n] ")):
        with open("optional/blip-requirements.txt", 'r') as f:
            reqs = [l.strip() for l in f.readlines()]
            process_reqs(reqs, args)

    if yes(input("Would you like to install LLaMA dependencies? (Optional if not using LLaMA LLM) [Y/n] ")):
        with open("optional/llama-requirements.txt", 'r') as f:
            reqs = [l.strip() for l in f.readlines()]
            process_reqs(reqs, args)
    
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("LLMChat updater")
    parser.add_argument("-y", action="store_true",
                        help="Automatically installs unmet dependencies.")
    args = parser.parse_args()
    main(args)
