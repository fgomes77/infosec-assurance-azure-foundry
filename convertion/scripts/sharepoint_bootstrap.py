#!/usr/bin/env python3
"""One-time SharePoint bootstrap for the delivery layer (sharepoint/README.md,
functions/delivery/README.md): resolves the ids setup/.env needs, creates
the library folders if missing, and grants the delivery Function's managed
identity the single Sites.Selected WRITE permission on the site.

Graph calls via the signed-in identity (az login / DefaultAzureCredential;
the caller needs Sites.FullControl.All or site-collection admin for the
permission grant). Idempotent; --dry-run prints every call instead.

    python3 sharepoint_bootstrap.py \
        --site-url "https://{tenant}.sharepoint.com/sites/{site}" \
        --library Reports --function-app-id {function-mi-appId} \
        --function-display-name infosec-delivery-fn [--dry-run]

Output: the .env block (SHAREPOINT_SITE_ID, SHAREPOINT_REPORTS_DRIVE_ID,
SHAREPOINT_REPORTS_ROOT_ITEM_ID, SHAREPOINT_DPO_ROOT_ITEM_ID,
SHAREPOINT_ADVISORY_ROOT_ITEM_ID, SHAREPOINT_TEMPLATES_REVIEWS_ITEM_ID).
No secrets are read or written; the permission is bound to the app id.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.microsoft.com/v1.0"
FOLDERS = {                       # env key -> path inside the library
    "SHAREPOINT_REPORTS_ROOT_ITEM_ID": "Reports",
    "SHAREPOINT_DPO_ROOT_ITEM_ID": "Reports/DPO",
    "SHAREPOINT_ADVISORY_ROOT_ITEM_ID": "Advisory",
    "SHAREPOINT_TEMPLATES_REVIEWS_ITEM_ID": "Templates/Reviews",
}


class Graph:
    def __init__(self, dry: bool):
        self.dry = dry
        self.token = None
        if not dry:
            from azure.identity import DefaultAzureCredential
            self.token = DefaultAzureCredential().get_token(
                "https://graph.microsoft.com/.default").token

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        url = path if path.startswith("http") else GRAPH + path
        if self.dry:
            print(f"[dry-run] {method} {url}"
                  + (f" {json.dumps(body)}" if body else ""))
            return {"id": f"{{id:{path.strip('/').split('/')[-1] or 'x'}}}",
                    "value": []}
        req = urllib.request.Request(url, method=method,
                                     data=json.dumps(body).encode() if body else None)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            sys.exit(f"Graph {method} {path} failed: {e.code} {e.read()[:200]!r}")


def ensure_folder(g: Graph, drive: str, path: str) -> str:
    """Create each segment if missing (reuse-if-exists, like the pipeline)."""
    parent = "root"
    item_id = ""
    for seg in path.split("/"):
        found = g.call("GET", f"/drives/{drive}/items/{parent}:/{urllib.parse.quote(seg)}")
        if found.get("id"):
            item_id = found["id"]
        else:
            made = g.call("POST", f"/drives/{drive}/items/{parent}/children",
                          {"name": seg, "folder": {},
                           "@microsoft.graph.conflictBehavior": "fail"})
            item_id = made.get("id", "")
        parent = item_id or parent
    return item_id


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-url", required=True,
                    help="https://{tenant}.sharepoint.com/sites/{site}")
    ap.add_argument("--library", default="Reports",
                    help="document library (drive) name holding Reports/")
    ap.add_argument("--function-app-id", required=True,
                    help="appId of the delivery Function's managed identity")
    ap.add_argument("--function-display-name", default="infosec-delivery-fn")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    u = urllib.parse.urlparse(args.site_url)
    g = Graph(args.dry_run)
    site = g.call("GET", f"/sites/{u.netloc}:{u.path}")
    site_id = site.get("id") or sys.exit("site not found")
    drives = g.call("GET", f"/sites/{site_id}/drives").get("value", [])
    drive = next((d["id"] for d in drives if d.get("name") == args.library),
                 None) or (f"{{id:drive-{args.library}}}" if args.dry_run
                           else sys.exit(f"library {args.library!r} not found"))

    env = {"SHAREPOINT_SITE_ID": site_id, "SHAREPOINT_REPORTS_DRIVE_ID": drive}
    for key, path in FOLDERS.items():
        env[key] = ensure_folder(g, drive, path)

    # Sites.Selected: the ONLY writer on the site is the Function identity
    existing = g.call("GET", f"/sites/{site_id}/permissions").get("value", [])
    already = any(args.function_app_id in json.dumps(p) for p in existing)
    if already:
        print("permission already granted - left unchanged")
    else:
        g.call("POST", f"/sites/{site_id}/permissions", {
            "roles": ["write"],
            "grantedToIdentities": [{"application": {
                "id": args.function_app_id,
                "displayName": args.function_display_name}}]})
        print(f"granted Sites.Selected write to {args.function_display_name}")

    print("\n# add to setup/.env")
    for k, v in env.items():
        print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
