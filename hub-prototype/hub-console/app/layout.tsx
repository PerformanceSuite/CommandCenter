export const metadata = { title: 'CommandCenter Hub', description: 'Local Hub Console' }
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-neutral-950 text-neutral-200">
        <div className="max-w-6xl mx-auto p-6">
          <header className="mb-6">
            <h1 className="text-2xl font-semibold">CommandCenter Hub — Console</h1>
            <p className="text-sm text-neutral-400">Local only. Reads snapshots and registry files.</p>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
