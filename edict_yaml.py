#   1  10C3   E4ads_v5         Eadsv5             Premium                                                                                                          
#   2  8C7    E8ads_v5         Eadsv5             Premium                                                                                                          
#   3  8C15   E16ads_v5        Eadsv5             Premium                                                                                                          
#   4  8C30   E32ads_v5        Eadsv5             Premium                                                                                                          
#   5  8C60   E64ads_v5        Eadsv5             Premium 
# for split 0 need 476 jobs submit 50 for each -> 250

md = """
  - name: split_{split_idx}_{st}to{ed}
    process_count_per_node: 1
    execution_mode: Basic
    priority: High          
    sla_tier: premium   
    identity: managed
    
    sku: {sku}
    command:
      - cd cccrawl
      - python gendata_main.py --index /mnt/vground/selected_url_from_domain/CCurls_sampled_50pd_split_{split_idx}.json --out-dir /mnt/vground/CCCrawl_Raw --run-name split_0_{st}to{ed} --start {st} --end {ed}
"""

split = 0
sku = "8C60"
template = open("temp.yaml", "r").read()
for st in range(201, 251):
    template += md.format(split_idx=split, sku=sku, st = st, ed = st+1)

open("jobs.yaml", "w").write(template)