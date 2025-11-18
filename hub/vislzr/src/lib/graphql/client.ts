/**
 * urql GraphQL Client Configuration for VISLZR
 *
 * Connects to CommandCenter GraphService backend for graph data queries.
 */

import { Client, cacheExchange, fetchExchange } from 'urql'

export const urqlClient = new Client({
  url: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8000/graphql',
  exchanges: [cacheExchange, fetchExchange],
})
