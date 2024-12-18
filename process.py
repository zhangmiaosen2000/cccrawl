
import os, json




def clean_rules(js):
    for k in ["url", "status", "languages"]:
        if k not in js:
            return False, None, None, None
    if (not js["status"].startswith("2")) or (js["status"] in ["301", "302"]):
        return False, None, None, None
    
    if "http://" in js["url"]:
        domain = js["url"].replace("http://", "").split("/")[0]
    elif "https://" in js["url"]:
        domain = js["url"].replace("https://", "").split("/")[0]
    else:
        return False, None, None, None
    return True, js["url"], js["languages"], domain



URL = "https://data.commoncrawl.org/cc-index/collections/CC-MAIN-2024-46/indexes/"


overall_domain = 6926949
overall_urls = 347915692
overall_max = 115534


for r in range(40, 300):
    fi = "cdx-" + str(r).rjust(5, "0")
    os.system(f"wget {URL}{fi}.gz; gzip -d {fi}.gz")
    ls = open(fi).readlines()
    num = len(ls)
    saved_json = dict() # domain: [url: language]
    for line in ls:
        try:
            info = json.loads(line[line.find('{"url":'):])
        except:
            continue
        kept, url, language, domain = clean_rules(info)
        if not kept:
            continue
        if domain not in saved_json:
            saved_json[domain] = dict()
        saved_json[domain][url] = language  # override
    
    overall_domain += len(saved_json)
    webs = [len(v) for v in saved_json.values()]
    overall_urls += sum(webs)
    overall_max = max([max(webs), overall_max])
    
    # save
    open(f"{fi}.json", "w").write(json.dumps(saved_json))
    # to storage
    os.system(f"/home/t2vg-a100-G4-1/zms/azcopy cp '{fi}.json' 'https://t2vgusw2.blob.core.windows.net/vground/CC-index/?sv=2023-01-03&st=2024-12-10T08%3A32%3A29Z&se=2024-12-16T08%3A48%3A00Z&skoid=9ec39cf7-c5e4-4f8b-ace5-34448a111cff&sktid=72f988bf-86f1-41af-91ab-2d7cd011db47&skt=2024-12-10T08%3A32%3A29Z&ske=2024-12-16T08%3A48%3A00Z&sks=b&skv=2023-01-03&sr=c&sp=racwdxltf&sig=PGuCFAkueapDlodUiFEuuMO1fHaSJWEgqiotVWHmmO4%3D' ")
    os.system(f"rm -f {fi}.json {fi}")

    print(f"tmp index: {r} of 300\nDomain: {overall_domain}\nURL: {overall_urls}\nMax: {overall_max}")








