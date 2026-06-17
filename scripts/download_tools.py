import urllib.request, json, os, zipfile, io

def download_latest(repo, asset_pattern, dest_dir):
    url = "https://api.github.com/repos/" + repo + "/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "VulnForge"})
    data = json.loads(urllib.request.urlopen(req).read())
    version = data["tag_name"]
    print(repo + ": latest " + version)
    for asset in data["assets"]:
        if asset_pattern in asset["name"] and asset["name"].endswith(".zip"):
            dl_url = asset["browser_download_url"]
            print("  Downloading " + asset["name"] + "...")
            zip_data = urllib.request.urlopen(dl_url).read()
            zf = zipfile.ZipFile(io.BytesIO(zip_data))
            for info in zf.infolist():
                name = os.path.basename(info.filename)
                if name:
                    info.filename = name
                    zf.extract(info, dest_dir)
                    print("  Extracted: " + name)
            return True
    return False

os.makedirs("tools", exist_ok=True)
download_latest("projectdiscovery/nuclei", "windows_amd64", "tools")
download_latest("hahwul/dalfox", "windows_amd64", "tools")
download_latest("ffuf/ffuf", "windows_amd64", "tools")
print("All done!")
