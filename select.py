
import json, os
from random import sample
selected = []
domains = 0

for i in range(300):
    fi = "cdx-" + str(i).rjust(5, "0") + ".json"
    os.system(f"/data/home/t2vg-a100-G4-1/zms/azcopy cp 'https://t2vgusw2.blob.core.windows.net/vground/CC-index/{fi}?sv=2021-10-04&st=2024-12-12T08%3A54%3A30Z&se=2024-12-18T08%3A54%3A00Z&skoid=9ec39cf7-c5e4-4f8b-ace5-34448a111cff&sktid=72f988bf-86f1-41af-91ab-2d7cd011db47&skt=2024-12-12T08%3A54%3A30Z&ske=2024-12-18T08%3A54%3A00Z&sks=b&skv=2021-10-04&sr=c&sp=rl&sig=ipVYszoswWt%2FjMVPmLyzvjZNccGrkkcKFacGhSt89BU%3D' './'")
    js = json.load(open(fi))
    domains += len(js)
    for domain, urls in js.items():
        domain_number = len(urls)
        urls_filtered = [(u, v) for u, v in urls.items() if "eng" in v]
        sampled_links = urls_filtered if len(urls_filtered)<=50 else list(sample(urls_filtered, 50))
        for l in sampled_links:
            u, lang = l
            selected.append({
                "url": u,
                "language": lang,
                "domain_scale": domain_number
            })
    os.system(f"rm -f {fi}")

print(list(sample(selected, 50)))
print(len(selected))
print(domains)
open("CCurls_sampled_50pd.json", "w").write(json.dumps(selected))
