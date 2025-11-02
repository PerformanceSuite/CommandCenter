async function fetchJSON(pathname: string) {
  const res = await fetch(pathname, { cache: 'no-store' });
  return res.json();
}

export default async function Home() {
  const registry = await fetchJSON('/api/registry');
  const events = await fetchJSON('/api/events/recent');
  return (
    <main className="space-y-8">
      <section>
        <h2 className="text-xl font-medium mb-2">Discovered Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(registry.tools || []).map((t: any) => (
            <div key={t.id} className="rounded-2xl p-4 bg-neutral-900 border border-neutral-800">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold">{t.id}</div>
                  <div className="text-xs text-neutral-400">{t.version}</div>
                </div>
                <div className="text-xs">
                  {t.endpoints?.web && <a href={t.endpoints.web} className="underline mr-2">web</a>}
                  {t.endpoints?.api && <a href={t.endpoints.api} className="underline">api</a>}
                </div>
              </div>
              <div className="mt-2 text-xs text-neutral-400">categories: {(t.categories||[]).join(', ')}</div>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2 className="text-xl font-medium mb-2">Recent Events</h2>
        <div className="space-y-2">
          {events.items?.slice(0, 20).map((e: any, i: number) => (
            <div key={i} className="rounded-xl p-3 bg-neutral-900 border border-neutral-800 text-xs">
              <div className="text-neutral-400">{e.ts}</div>
              <div className="font-mono">{e.topic}</div>
              <pre className="whitespace-pre-wrap text-[11px] mt-1">{JSON.stringify(e.payload, null, 2)}</pre>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}

const projects = await fetchJSON('/api/projects');

<section>
  <h2 className="text-xl font-medium mb-2">Project Instances</h2>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
    {(projects.projects || []).map((p: any) => (
      <div key={p.instanceId} className="rounded-2xl p-4 bg-neutral-900 border border-neutral-800">
        <div className="font-semibold">{p.name || p.instanceId}</div>
        <div className="text-xs text-neutral-400">{p.projectId} • env={p.env}</div>
        <div className="text-xs text-neutral-400 mt-1">
          tools: {(p.tools||[]).join(", ")}
        </div>
      </div>
    ))}
  </div>
</section>
