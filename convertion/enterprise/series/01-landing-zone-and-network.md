# Step 01 — Landing zone and network

**Objective.** Place the platform in an ENX application landing zone the
workload team owns, with the network the new agent service needs: private
endpoints for Foundry, Key Vault, Storage, Function and Logic Apps; a
**delegated agents subnet** for network-secured agents; private DNS; hub
egress; and the Azure Policy guard-rails (EU-only, `DataZoneStandard`
only, no public network access in `test`/`prod`).

**Owner / effort.** `{group:azure-platform}` with the owner; 3 days.
Countersign: landing-zone lead. **Depends on** 00.

## 1. Target topology

Microsoft's reference is the workload team owning the Foundry resource
inside an *application* landing zone (not a shared business-group Foundry
with delegated projects), the platform team supplying hub firewall, DNS
and connectivity — [GA] https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-landing-zone (2026-06-19).

| Element | `dev` | `test` / `prod` | Kit file |
|---|---|---|---|
| Resource group | `rg-infosec-foundry-dev` | `rg-infosec-foundry-test` / `rg-infosec-foundry` | `setup/provision.sh` creates it from `AZURE_RESOURCE_GROUP` |
| VNet | none (`enablePrivateNetworking=false`) | `{baseName}-vnet` `10.60.0.0/22` → subnets `private-endpoints`, `apps` (Functions / Logic Apps VNet integration), `container-apps` (MCP) — plus **new** `agents` /24 delegated to `Microsoft.App/environments` | `infra/network.bicep` (S-02 adds the subnet) |
| Private DNS zones | — | `cognitiveservices`, `openai`, `aiservices`, `vault`, `blob`, `sites` (+ `search`, `documents` when standard setup) linked to the VNet; forwarders from the hub | `infra/network.bicep` `zoneNames`; `infra/private-endpoint.bicep` |
| Egress | public | hub firewall; agents subnet egress to the tool hosts of step 04 (Atlassian, OneTrust, SecurityScorecard, IAF, ENX gateway) and to Microsoft endpoints | firewall rules (landing zone) |
| Region | `swedencentral` (default) — Agent Service + private VNet supported; every tool available; `italynorth` excluded because file search is unavailable there | `main.bicep` `@allowed` list |

Constraints from the platform (all [GA]):

- For network-secured agents the **Foundry resource must be in the same
  region as its VNet**; Cosmos DB / AI Search / Storage may be elsewhere —
  https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability#common-rollout-pitfalls (2026-09-09).
- BYO VNet: subnet delegated to `Microsoft.App/environments`, **/27
  minimum, /24 recommended** with hosted agents, RFC 1918/6598 ranges;
  **network injection is set at creation and cannot be added later** —
  https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/networking-options (2026-09-09).
- Managed VNet (GA for prompt/hosted agents; Sweden Central, France
  Central, Spain Central, Germany West Central, Italy North, UK South
  listed) is the fallback when the landing zone cannot allocate a /24 —
  https://learn.microsoft.com/en-us/azure/foundry/how-to/managed-virtual-network (2026-08-18).
- A private endpoint secures **inbound** only; agent **egress** (tool
  calls) needs the subnet/managed-VNet isolation — [community-claim]
  https://techcommunity.microsoft.com/blog/azurearchitectureblog/your-private-endpoint-does-not-cover-agent-egress-locking-down-azure-ai-foundry-/4547864 (2026-09-12).
- Some GA features do not fully support isolation (traces and workflows
  listed on the GA page) — verify tracing in step 08 §3 before relying on
  it in `prod`.

## 2. Click-path

**Azure portal.** Resource groups → *Create* (name, region `Sweden
Central`, tags `owner={upn:francisco.gomes}`, `env`, `costCenter`) →
Virtual networks → `{baseName}-vnet` → *Subnets* → add `agents` with
*Subnet delegation* = `Microsoft.App/environments` → Private DNS zones →
verify the six zones are linked → Policy → *Assignments* (§4).
**Foundry portal.** Nothing yet — the Foundry resource is created in step
02 with the network parameters of this step.

## 3. CLI / Bicep

```bash
# landing-zone team, per environment
az group create -n rg-infosec-foundry-test -l swedencentral --tags owner={upn:francisco.gomes} env=test
# what-if of the kit network module alone (no changes applied)
az deployment group what-if -g rg-infosec-foundry-test \
  --template-file infra/network.bicep --parameters baseName=infosecfdrytst location=swedencentral
```

Shared delta **S-02** (literal text for `infra/network.bicep`): add
`agents: '10.60.1.0/24'            // snet-agents (delegated to Microsoft.App/environments)`
to the `var subnets = { … }` object (the free /24 between `snet-apps` and
`snet-aca` in the kit's `10.60.0.0/22` plan), and this entry to the
`vnet.properties.subnets` array after the `container-apps` subnet:

```bicep
      {
        name: 'snet-agents'
        properties: {
          addressPrefix: subnets.agents
          delegations: [ { name: 'foundry-agents', properties: { serviceName: 'Microsoft.App/environments' } } ]
        }
      }
```
plus the output `output agentsSubnetId string = vnet.properties.subnets[3].id`.
`infra/main.bicep` passes `agentsSubnetId` to the Foundry resource in step
02 §B (network-injection block). If the landing zone assigns a different
address space, keep the /24 size — /27 is the platform minimum.

## 4. Azure Policy assignments (RG scope; `test` and `prod`)

| Policy | Id / kind | Effect | Why |
|---|---|---|---|
| Azure AI Services resources should restrict network access | built-in `037eea7a…` | Deny | no public Foundry endpoint — [GA] https://learn.microsoft.com/en-us/azure/ai-services/policy-reference (2026-07-13) |
| Azure AI Services resources should use Azure Private Link | built-in `d6759c02…` | Audit | evidence for DORA Art. 9(4)(b) |
| Allowed locations | built-in | Deny outside the EU list of `main.bicep` | residency |
| **Deny GlobalStandard deployments** | custom (JSON below) | Deny | inference must stay in the EU Data Zone; the Q&A guidance recommends exactly this policy — [community-claim] https://learn.microsoft.com/en-us/answers/questions/5966351/azure-ai-foundry-modified-abuse-monitoring-eu-data (2026-08-04) |

```json
{
  "mode": "All",
  "displayName": "InfoSec Foundry - deny GlobalStandard model deployments",
  "policyRule": {
    "if": {
      "allOf": [
        { "field": "type", "equals": "Microsoft.CognitiveServices/accounts/deployments" },
        { "field": "Microsoft.CognitiveServices/accounts/deployments/sku.name", "in": [ "GlobalStandard", "GlobalProvisionedManaged", "GlobalBatch" ] }
      ]
    },
    "then": { "effect": "deny" }
  },
  "parameters": {}
}
```
`az policy definition create -n infosec-foundry-deny-global-sku --rules policy.json --mode All`
then `az policy assignment create -n deny-global-sku --policy infosec-foundry-deny-global-sku --scope $(az group show -n rg-infosec-foundry --query id -o tsv)`.

## 5. Values captured into `setup/.env`

| Variable | Value |
|---|---|
| `AZURE_RESOURCE_GROUP` | per environment |
| `AZURE_LOCATION` | `swedencentral` |
| (parameters, not env) `enablePrivateNetworking=true`, `publicNetworkAccess=Disabled` in `main.parameters.prod.json` / `.test.json` | already present for prod |

## 6. Verification

| # | Check | Pass when |
|---|---|---|
| V1 | `infra/validate.sh --what-if rg-infosec-foundry-test` with `PARAMS=main.parameters.test.json` | no errors; guard module passes (`publicNetworkAccess=Disabled` requires private networking) |
| V2 | `az network vnet subnet show … -n agents --query delegations[0].serviceName` | `Microsoft.App/environments`; prefix is a /24 |
| V3 | Private DNS zones linked (`az network private-dns link vnet list`) | six (or eight with standard setup) zones linked |
| V4 | `az policy state list --resource-group …` after a deliberate test deployment of a `GlobalStandard` SKU in `dev` | denied |
| V5 | Hub firewall: from the `apps` subnet, TLS to the step-04 tool hosts succeeds; to arbitrary internet fails (test VM or Function `curl`) | as expected |

**Rollback.** Delete the RG (`dev`), or `az deployment group what-if` of
the previous commit and redeploy (`test`/`prod`); policy assignments are
removed with `az policy assignment delete`. **ISMS evidence.** what-if
output, subnet/DNS listings, policy compliance report — ISO 27001:2022
A.8.20–A.8.22 (network security, segregation), A.5.23 (cloud services);
DORA Art. 9(3)–(4); NIS2 Art. 21(2)(e).

## Sources
- [GA] Landing-zone architecture — https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-landing-zone (2026-06-19)
- [GA] Networking options — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/networking-options (2026-09-09)
- [GA] Managed VNet — https://learn.microsoft.com/en-us/azure/foundry/how-to/managed-virtual-network (2026-08-18)
- [GA] Isolation pitfalls — https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability#common-rollout-pitfalls (2026-09-09)
- [GA] Regions / tool matrix — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions#supported-regions (2026-09-07)
- [GA] Azure Policy built-ins — https://learn.microsoft.com/en-us/azure/ai-services/policy-reference (2026-07-13)
- [community-claim] Private endpoint vs agent egress — https://techcommunity.microsoft.com/blog/azurearchitectureblog/your-private-endpoint-does-not-cover-agent-egress-locking-down-azure-ai-foundry-/4547864 (2026-09-12)
- [community-claim] EU residency / policy guidance — https://learn.microsoft.com/en-us/answers/questions/5966351/azure-ai-foundry-modified-abuse-monitoring-eu-data (2026-08-04)
