/**
 * VISLZR Home Page - Project Selector
 */

'use client'

import Link from 'next/link'

export default function Home() {
  // TODO: Fetch projects from GraphQL API
  const projects = [
    { id: 1, name: 'CommandCenter', description: 'AI Operating System for Knowledge Work' },
    { id: 2, name: 'Hub', description: 'Multi-project management system' },
  ]

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="w-full max-w-4xl">
        <header className="mb-12 text-center">
          <h1 className="mb-4 text-5xl font-bold text-gray-900">VISLZR</h1>
          <p className="text-xl text-gray-600">
            Interactive Graph Visualization for CommandCenter Projects
          </p>
        </header>

        <div className="grid gap-6 md:grid-cols-2">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/project/${project.id}`}
              className="group rounded-xl border-2 border-gray-200 bg-white p-6 shadow-lg transition-all hover:border-blue-500 hover:shadow-xl"
            >
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900 group-hover:text-blue-600">
                  {project.name}
                </h2>
                <svg
                  className="h-6 w-6 text-gray-400 transition-transform group-hover:translate-x-1 group-hover:text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
              <p className="text-gray-600">{project.description}</p>
              <div className="mt-4 flex gap-2">
                <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                  Graph View
                </span>
                <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
                  Real-time
                </span>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-12 rounded-xl border-2 border-gray-200 bg-white p-8 shadow-lg">
          <h3 className="mb-4 text-xl font-bold text-gray-900">Features</h3>
          <ul className="grid gap-3 md:grid-cols-2">
            <li className="flex items-start gap-2">
              <svg className="mt-1 h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-gray-700">Interactive graph visualization</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="mt-1 h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-gray-700">Real-time updates via SSE</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="mt-1 h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-gray-700">Code review & audit triggers</span>
            </li>
            <li className="flex items-start gap-2">
              <svg className="mt-1 h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-gray-700">Custom node visualizations</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
