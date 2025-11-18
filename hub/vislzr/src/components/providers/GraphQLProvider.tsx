/**
 * GraphQL Provider Wrapper
 *
 * Wraps the app with urql Client for GraphQL queries.
 */

'use client'

import { Provider } from 'urql'
import { urqlClient } from '@/lib/graphql/client'
import { ReactNode } from 'react'

interface GraphQLProviderProps {
  children: ReactNode
}

export function GraphQLProvider({ children }: GraphQLProviderProps) {
  return <Provider value={urqlClient}>{children}</Provider>
}
