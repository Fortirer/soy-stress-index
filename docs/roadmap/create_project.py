"""Create labels, milestones, issues and a GitHub Project (v2) for Turgor.
Usage: python3 create_project.py issues.json  (token in ~/.ghflow/tok)"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OWNER, REPO = "Fortirer", "soy-stress-index"
TOKEN = (Path.home() / ".ghflow" / "tok").read_text().strip()
plan = json.loads(Path(sys.argv[1]).read_text())
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
     "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"}


def rest(method, path, data=None, ok=(200, 201)):
    req = urllib.request.Request(f"https://api.github.com{path}", method=method, headers=H,
                                 data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 422 and "already_exists" in body:
            return None
        raise SystemExit(f"{method} {path} -> {e.code} {body[:300]}")


def gql(query, **variables):
    req = urllib.request.Request("https://api.github.com/graphql", method="POST", headers=H,
                                 data=json.dumps({"query": query, "variables": variables}).encode())
    with urllib.request.urlopen(req) as r:
        out = json.loads(r.read())
    if out.get("errors"):
        raise SystemExit(f"GraphQL error: {out['errors']}")
    return out["data"]


base = f"/repos/{OWNER}/{REPO}"
for lab in plan["labels"]:
    rest("POST", f"{base}/labels", lab)
print("labels ok")

existing = {m["title"]: m["number"] for m in rest("GET", f"{base}/milestones?state=all&per_page=100")}
ms = {}
for m in plan["milestones"]:
    ms[m["title"]] = existing.get(m["title"]) or rest("POST", f"{base}/milestones", m)["number"]
print("milestones ok")

have = {i["title"]: i for i in rest("GET", f"{base}/issues?state=all&per_page=100") if "pull_request" not in i}
issues = []
for it in plan["issues"]:
    if it["title"] in have:
        issues.append(have[it["title"]])
        continue
    i = rest("POST", f"{base}/issues", {"title": it["title"], "body": it["body"], "labels": it["labels"],
                                         "milestone": ms[it["milestone"]]})
    if it.get("state") == "closed":
        rest("PATCH", f"{base}/issues/{i['number']}", {"state": "closed", "state_reason": "completed"})
        i["state"] = "closed"
    issues.append(i)
    print("issue", i["number"], it["title"][:60])
    time.sleep(1)

owner_id = gql("query($l:String!){user(login:$l){id}}", l=OWNER)["user"]["id"]
repo_id = gql("query($o:String!,$n:String!){repository(owner:$o,name:$n){id}}", o=OWNER, n=REPO)["repository"]["id"]
proj = gql("""mutation($o:ID!,$t:String!,$r:ID!){createProjectV2(input:{ownerId:$o,title:$t,repositoryId:$r}){projectV2{id number url}}}""",
           o=owner_id, t=plan["project_title"], r=repo_id)["createProjectV2"]["projectV2"]
gql("""mutation($p:ID!,$d:String!){updateProjectV2(input:{projectId:$p,shortDescription:$d,readme:$d}){projectV2{id}}}""",
    p=proj["id"], d=plan["project_description"])
fields = gql("""query($p:ID!){node(id:$p){... on ProjectV2{fields(first:30){nodes{... on ProjectV2SingleSelectField{id name options{id name}}}}}}}""",
             p=proj["id"])["node"]["fields"]["nodes"]
status = next(f for f in fields if f and f.get("name") == "Status")
opt = {o["name"]: o["id"] for o in status["options"]}
for i in issues:
    item = gql("""mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}""",
               p=proj["id"], c=i["node_id"])["addProjectV2ItemById"]["item"]["id"]
    target = "Done" if i["state"] == "closed" else "Todo"
    if target in opt:
        gql("""mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}""",
            p=proj["id"], i=item, f=status["id"], o=opt[target])
print("PROJECT", proj["url"], "items", len(issues))
