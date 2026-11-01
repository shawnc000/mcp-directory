"""Pull MCP server repos from GitHub search (public, unauthenticated OK), merge into data.json with cached metadata.
Filters: topic mcp-server or mcp, stars>=150, not archived, has license. Category by keyword rules."""
import json,urllib.request,urllib.parse,time,os,re
from datetime import datetime, timezone
CATS=[("Browser & Web",r"browser|playwright|scrap|crawl|web|chrome"),("Coding & Dev",r"code|git|ide|cursor|debug|lsp|devtools|sdk"),
("Data & DB",r"sql|postgres|database|db|data|mongo|redis|supabase"),("Cloud & Infra",r"aws|azure|gcp|cloud|kubernetes|k8s|docker|terraform"),
("Docs & Knowledge",r"doc|knowledge|memory|rag|notion|obsidian|search"),("Design & Media",r"figma|draw|design|image|video|audio|blender"),
("Marketing & Social",r"seo|ads|social|xiaohongshu|twitter|tiktok"),("Security",r"secur|pentest|reverse|ida|ghidra"),("Mobile & Devices",r"android|ios|mobile|esp32")]
def cat(t):
    for c,p in CATS:
        if re.search(p,t,re.I): return c
    return "Other"
def search(q,page):
    u="https://api.github.com/search/repositories?"+urllib.parse.urlencode(dict(q=q,sort="stars",per_page=100,page=page))
    r=urllib.request.Request(u,headers={"User-Agent":"dir-bot"})
    if os.getenv("GITHUB_TOKEN"): r.add_header("Authorization","Bearer "+os.environ["GITHUB_TOKEN"])
    return json.load(urllib.request.urlopen(r,timeout=20)).get("items",[])
data={i["repo"]:i for i in json.load(open("data/catalog.json"))}
seen=0
for q in ["topic:mcp-server stars:>=150 archived:false","topic:mcp stars:>=300 archived:false"]:
    for p in (1,2,3):
        for r in search(q,p):
            lic=(r.get("license") or {}).get("spdx_id")
            if not lic or lic=="NOASSERTION": continue
            txt=(r["full_name"]+" "+(r["description"] or "")+" "+" ".join(r.get("topics",[])))
            if "mcp" not in txt.lower(): continue
            e=data.get(r["full_name"],{"name":r["name"],"repo":r["full_name"],"category":cat(txt),"desc":(r["description"] or "")[:200],"desc_zh":""})
            e["meta"]={"stargazers_count":r["stargazers_count"],"pushed_at":r["pushed_at"],"license":{"spdx_id":lic},"topics":r.get("topics",[])}
            url=r.get("html_url")
            if isinstance(url,str) and url.startswith("https://github.com/") and not any(ch.isspace() for ch in url):
                e["source_url"]=url
                e["last_verified_date"]=datetime.now(timezone.utc).strftime("%Y-%m-%d")
            else:
                e["source_url"]=None
                e["last_verified_date"]=None
            data[r["full_name"]]=e; seen+=1
        time.sleep(7)
json.dump(list(data.values()),open("data/catalog.json","w"),ensure_ascii=False,indent=1)
print("seen",seen,"total",len(data))
