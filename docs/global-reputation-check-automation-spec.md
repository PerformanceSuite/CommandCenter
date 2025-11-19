# Global Reputation Check Automation Specification
**For CommandCenter Integration**

## Overview
Automated domain reputation monitoring system to check veria.cc (and other domains) across 20+ security and reputation services.

## Target Services

### Tier 1: Critical (Automated)
| Service | API Available | Method | Cost |
|---------|---------------|--------|------|
| VirusTotal | ✅ Yes | REST API | Free tier: 4 req/min |
| MXToolbox | ✅ Yes | REST API | Paid: $99/month |
| URLVoid | ✅ Yes | REST API | Free tier: 1000/day |
| Google Safe Browsing | ✅ Yes | Lookup API v4 | Free |
| Spamhaus | ⚠️ Limited | DNS queries | Free (rate limited) |
| SURBL/URIBL | ⚠️ Limited | DNS queries | Free (rate limited) |
| Barracuda | ⚠️ Limited | DNS queries | Free (rate limited) |
| SORBS | ⚠️ Limited | DNS queries | Free (rate limited) |

### Tier 2: Important (Manual/Semi-Automated)
| Service | API Available | Method | Cost |
|---------|---------------|--------|------|
| Webroot BrightCloud | ❌ No | Web scraping/Manual | N/A |
| Fortinet FortiGuard | ⚠️ Limited | API (enterprise) | Enterprise only |
| Palo Alto Networks | ⚠️ Limited | API (enterprise) | Enterprise only |
| Cloudflare Radar | ✅ Yes | GraphQL API | Free |
| Cisco Talos | ❌ No | Web scraping/Manual | N/A |
| McAfee WebAdvisor | ❌ No | Manual check | N/A |
| Norton Safe Web | ❌ No | Manual check | N/A |
| Sucuri SiteCheck | ✅ Yes | REST API | Free |

## Implementation Plan for CommandCenter

### Phase 1: Core Automation (Week 1)
```typescript
// File: commandcenter/reputation/core.ts
interface ReputationCheck {
  service: string;
  category: string;
  url: string;
  domain: string;
  status: 'clean' | 'listed' | 'error' | 'pending';
  result: string;
  threatScore?: number;
  lastChecked: Date;
  reviewUrl?: string;
  notes: string;
  automated: boolean;
}

class ReputationChecker {
  async checkVirusTotal(domain: string): Promise<ReputationCheck>
  async checkGoogleSafeBrowsing(domain: string): Promise<ReputationCheck>
  async checkURLVoid(domain: string): Promise<ReputationCheck>
  async checkMXToolbox(domain: string): Promise<ReputationCheck>
  async checkDNSBlocklists(domain: string, ip: string): Promise<ReputationCheck[]>
  async checkCloudflareRadar(domain: string): Promise<ReputationCheck>
  async checkSucuri(domain: string): Promise<ReputationCheck>
}
```

### Phase 2: API Integrations

#### VirusTotal API v3
```bash
# Setup
VIRUSTOTAL_API_KEY=your_key_here

# Endpoint
GET https://www.virustotal.com/api/v3/domains/{domain}
```

**Implementation:**
```typescript
async checkVirusTotal(domain: string) {
  const response = await fetch(
    `https://www.virustotal.com/api/v3/domains/${domain}`,
    { headers: { 'x-apikey': process.env.VIRUSTOTAL_API_KEY } }
  );
  const data = await response.json();

  return {
    service: 'VirusTotal',
    category: 'Domain Reputation',
    url: `https://www.virustotal.com/gui/domain/${domain}`,
    domain,
    status: data.data.attributes.last_analysis_stats.malicious > 0 ? 'listed' : 'clean',
    result: `${data.data.attributes.last_analysis_stats.malicious}/90 engines flagged`,
    threatScore: data.data.attributes.reputation || 0,
    lastChecked: new Date(),
    automated: true,
    notes: `Checked by ${data.data.attributes.last_analysis_stats.harmless + data.data.data.attributes.last_analysis_stats.malicious} engines`
  };
}
```

#### Google Safe Browsing API v4
```bash
# Setup
GOOGLE_SAFE_BROWSING_KEY=your_key_here

# Endpoint
POST https://safebrowsing.googleapis.com/v4/threatMatches:find?key={API_KEY}
```

**Implementation:**
```typescript
async checkGoogleSafeBrowsing(domain: string) {
  const response = await fetch(
    `https://safebrowsing.googleapis.com/v4/threatMatches:find?key=${process.env.GOOGLE_SAFE_BROWSING_KEY}`,
    {
      method: 'POST',
      body: JSON.stringify({
        client: { clientId: 'veria-reputation-checker', clientVersion: '1.0.0' },
        threatInfo: {
          threatTypes: ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE'],
          platformTypes: ['ANY_PLATFORM'],
          threatEntryTypes: ['URL'],
          threatEntries: [{ url: `http://${domain}/` }]
        }
      })
    }
  );

  const data = await response.json();

  return {
    service: 'Google Safe Browsing',
    category: 'Transparency Report',
    url: 'https://transparencyreport.google.com/safe-browsing/search',
    domain,
    status: data.matches ? 'listed' : 'clean',
    result: data.matches ? 'Unsafe content detected' : 'No unsafe contents found',
    lastChecked: new Date(),
    automated: true,
    notes: data.matches ? `Threats: ${data.matches.map(m => m.threatType).join(', ')}` : 'Clean'
  };
}
```

#### URLVoid API
```typescript
async checkURLVoid(domain: string) {
  const response = await fetch(
    `https://api.urlvoid.com/api1000/${process.env.URLVOID_API_KEY}/host/${domain}/`
  );
  const data = await response.json();

  return {
    service: 'URLVoid',
    category: 'Multi-Engine Check',
    url: `https://www.urlvoid.com/scan/${domain}/`,
    domain,
    status: data.detections.count > 0 ? 'listed' : 'clean',
    result: `${data.detections.count}/${data.detections.engines.length} engines flagged`,
    threatScore: data.detections.count,
    lastChecked: new Date(),
    automated: true,
    notes: `Checks ${data.detections.engines.length} blocklist engines`
  };
}
```

#### DNS Blocklist Checks
```typescript
async checkDNSBlocklists(domain: string, ip: string) {
  const blocklists = [
    { name: 'Spamhaus DBL', zone: 'dbl.spamhaus.org', type: 'domain' },
    { name: 'Spamhaus ZEN', zone: 'zen.spamhaus.org', type: 'ip' },
    { name: 'SURBL', zone: 'multi.surbl.org', type: 'domain' },
    { name: 'URIBL', zone: 'multi.uribl.com', type: 'domain' },
    { name: 'Barracuda', zone: 'b.barracudacentral.org', type: 'domain' },
    { name: 'SORBS', zone: 'dnsbl.sorbs.net', type: 'ip' }
  ];

  const results: ReputationCheck[] = [];

  for (const bl of blocklists) {
    const query = bl.type === 'ip'
      ? `${ip.split('.').reverse().join('.')}.${bl.zone}`
      : `${domain}.${bl.zone}`;

    try {
      const lookup = await dns.promises.resolve4(query);
      results.push({
        service: bl.name,
        category: bl.type === 'ip' ? 'IP Blocklist' : 'DNS Blocklist',
        url: `https://www.spamhaus.org/lookup/` // Generic lookup URL
        domain,
        status: 'listed',
        result: `Listed: ${lookup[0]}`,
        lastChecked: new Date(),
        automated: true,
        notes: 'Domain/IP found on blocklist'
      });
    } catch (err) {
      if (err.code === 'ENOTFOUND') {
        results.push({
          service: bl.name,
          category: bl.type === 'ip' ? 'IP Blocklist' : 'DNS Blocklist',
          url: `https://www.spamhaus.org/lookup/`,
          domain,
          status: 'clean',
          result: 'Not listed',
          lastChecked: new Date(),
          automated: true,
          notes: 'No listing found'
        });
      } else {
        results.push({
          service: bl.name,
          category: bl.type === 'ip' ? 'IP Blocklist' : 'DNS Blocklist',
          url: `https://www.spamhaus.org/lookup/`,
          domain,
          status: 'error',
          result: err.message,
          lastChecked: new Date(),
          automated: true,
          notes: 'Query error'
        });
      }
    }
  }

  return results;
}
```

### Phase 3: Scheduled Monitoring

```typescript
// File: commandcenter/reputation/scheduler.ts
import { CronJob } from 'cron';

class ReputationMonitor {
  private checker: ReputationChecker;

  // Run daily at 2 AM UTC
  startDailyCheck() {
    new CronJob('0 2 * * *', async () => {
      const results = await this.runFullCheck('veria.cc');
      await this.saveResults(results);
      await this.notifyIfIssues(results);
    }).start();
  }

  // Run weekly comprehensive check with manual services
  startWeeklyCheck() {
    new CronJob('0 3 * * 0', async () => {
      const results = await this.runFullCheck('veria.cc');
      await this.generateReport(results);
      await this.emailReport(results);
    }).start();
  }

  async runFullCheck(domain: string): Promise<ReputationCheck[]> {
    const ip = await this.resolveDomain(domain);

    return Promise.all([
      this.checker.checkVirusTotal(domain),
      this.checker.checkGoogleSafeBrowsing(domain),
      this.checker.checkURLVoid(domain),
      this.checker.checkMXToolbox(domain),
      ...await this.checker.checkDNSBlocklists(domain, ip),
      this.checker.checkCloudflareRadar(domain),
      this.checker.checkSucuri(domain),
    ]);
  }
}
```

### Phase 4: Export & Reporting

```typescript
// File: commandcenter/reputation/export.ts
class ReputationReporter {
  async generateCSV(results: ReputationCheck[]): Promise<string> {
    const headers = [
      'Service Name',
      'Category',
      'URL',
      'Domain',
      'Status',
      'Result',
      'Threat Score',
      'Last Checked',
      'Review URL',
      'Notes'
    ];

    const rows = results.map(r => [
      r.service,
      r.category,
      r.url,
      r.domain,
      r.status,
      r.result,
      r.threatScore?.toString() || 'N/A',
      r.lastChecked.toISOString(),
      r.reviewUrl || 'N/A',
      r.notes
    ]);

    return [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
  }

  async generateHTML(results: ReputationCheck[]): Promise<string> {
    // Generate styled HTML report
  }

  async generateJSON(results: ReputationCheck[]): Promise<string> {
    return JSON.stringify(results, null, 2);
  }
}
```

## Cost Analysis

### Free Tier (Recommended for MVP)
- VirusTotal: 4 requests/min (sufficient for daily checks)
- Google Safe Browsing: Unlimited (with reasonable use)
- URLVoid: 1000 requests/day
- Cloudflare Radar: Free
- Sucuri: Free
- DNS Blocklists: Free (rate limited)

**Total Cost: $0/month**

### Paid Tier (For Scale)
- VirusTotal Premium: $500/month (unlimited)
- MXToolbox API: $99/month
- Custom DNS resolver: $10/month (avoid rate limits)

**Total Cost: ~$609/month**

## Directory Structure

```
commandcenter/
├── src/
│   └── reputation/
│       ├── core.ts              # ReputationChecker class
│       ├── scheduler.ts         # CronJob monitoring
│       ├── export.ts            # CSV/HTML/JSON export
│       ├── integrations/
│       │   ├── virustotal.ts
│       │   ├── google.ts
│       │   ├── urlvoid.ts
│       │   ├── mxtoolbox.ts
│       │   ├── cloudflare.ts
│       │   └── dns-blocklists.ts
│       └── types.ts             # TypeScript interfaces
├── docs/
│   └── reputation-checks/
│       └── veria-cc-2025-11-18.csv
└── .env.example
    VIRUSTOTAL_API_KEY=
    GOOGLE_SAFE_BROWSING_KEY=
    URLVOID_API_KEY=
    MXTOOLBOX_API_KEY=
```

## CLI Usage

```bash
# Run manual check
commandcenter reputation check veria.cc

# Run and export
commandcenter reputation check veria.cc --export csv --output ./docs/

# Start monitoring (daemon mode)
commandcenter reputation monitor veria.cc --interval daily

# Generate report from previous check
commandcenter reputation report veria.cc --format html
```

## Next Steps

1. **Week 1**: Implement core checker with VirusTotal + Google Safe Browsing
2. **Week 2**: Add DNS blocklist checks + URLVoid integration
3. **Week 3**: Build scheduler and notification system
4. **Week 4**: Create export/reporting functionality
5. **Week 5**: Deploy to CommandCenter production

## Success Metrics

- ✅ Check 15+ reputation sources automatically
- ✅ Daily monitoring with <5 min runtime
- ✅ Alert if any service flags domain
- ✅ Weekly CSV export to docs/
- ✅ 99.9% uptime for monitoring service
