/**
 * GraphCanvas Real-Time Updates Tests
 *
 * Tests WebSocket subscription integration with GraphCanvas component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { GraphCanvas } from '../GraphCanvas';
import { graphWebSocket } from '../../../services/websocket';

// Mock the websocket service
vi.mock('../../../services/websocket', () => ({
  graphWebSocket: {
    isConnected: true,
    connect: vi.fn(),
    subscribe: vi.fn(() => vi.fn()),
    disconnect: vi.fn(),
  },
}));

// Mock ReactFlow since it requires a DOM context
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="react-flow">{children}</div>
  ),
  Background: () => <div data-testid="background" />,
  Controls: () => <div data-testid="controls" />,
  MiniMap: () => <div data-testid="minimap" />,
  useNodesState: (nodes: unknown[]) => [nodes, vi.fn(), vi.fn()],
  useEdgesState: (edges: unknown[]) => [edges, vi.fn(), vi.fn()],
  BackgroundVariant: { Dots: 'dots' },
}));

// Mock LoadingSpinner
vi.mock('../../common/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}));

// Mock GraphNodeTooltip
vi.mock('../GraphNodeTooltip', () => ({
  GraphNodeTooltip: () => null,
}));

describe('GraphCanvas real-time updates', () => {
  const mockNodes = [
    {
      id: 'service:1',
      entity_type: 'service' as const,
      entity_id: 1,
      label: 'Service A',
      metadata: {},
    },
    {
      id: 'service:2',
      entity_type: 'service' as const,
      entity_id: 2,
      label: 'Service B',
      metadata: {},
    },
  ];

  const mockEdges = [
    {
      from_node: 'service:1',
      to_node: 'service:2',
      type: 'dependsOn' as const,
      weight: 1,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (graphWebSocket as unknown as { isConnected: boolean }).isConnected = true;
  });

  it('subscribes to updates when enableRealTime and projectId are set', () => {
    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
      />
    );

    expect(graphWebSocket.subscribe).toHaveBeenCalledWith(
      'entity:updated:proj123',
      expect.any(Function)
    );
  });

  it('does not subscribe when enableRealTime is false', () => {
    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={false}
        projectId="proj123"
      />
    );

    // subscribe is not called for the entity topic when disabled
    expect(graphWebSocket.subscribe).not.toHaveBeenCalledWith(
      'entity:updated:proj123',
      expect.any(Function)
    );
  });

  it('does not subscribe when projectId is missing', () => {
    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
      />
    );

    // subscribe should not be called without projectId
    expect(graphWebSocket.subscribe).not.toHaveBeenCalledWith(
      expect.stringMatching(/^entity:updated:/),
      expect.any(Function)
    );
  });

  it('shows live indicator when connected', () => {
    (graphWebSocket as unknown as { isConnected: boolean }).isConnected = true;

    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
      />
    );

    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('shows connecting indicator when not connected', () => {
    (graphWebSocket as unknown as { isConnected: boolean }).isConnected = false;

    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
      />
    );

    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('does not show indicator when enableRealTime is false', () => {
    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={false}
        projectId="proj123"
      />
    );

    expect(screen.queryByText('Live')).not.toBeInTheDocument();
    expect(screen.queryByText('Connecting...')).not.toBeInTheDocument();
  });

  it('calls onNodeUpdate when update message received', () => {
    const onNodeUpdate = vi.fn();
    let messageHandler: (data: unknown) => void = () => {};

    vi.mocked(graphWebSocket.subscribe).mockImplementation((topic, handler) => {
      if (topic === 'entity:updated:proj123') {
        messageHandler = handler as (data: unknown) => void;
      }
      return vi.fn();
    });

    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
        onNodeUpdate={onNodeUpdate}
      />
    );

    act(() => {
      messageHandler({
        entity_id: 'service:1',
        entity_type: 'service',
        change_type: 'updated',
        data: { health: 80 },
      });
    });

    expect(onNodeUpdate).toHaveBeenCalledWith('service:1', { health: 80 });
  });

  it('calls onNodeCreate when create message received', () => {
    const onNodeCreate = vi.fn();
    let messageHandler: (data: unknown) => void = () => {};

    vi.mocked(graphWebSocket.subscribe).mockImplementation((topic, handler) => {
      if (topic === 'entity:updated:proj123') {
        messageHandler = handler as (data: unknown) => void;
      }
      return vi.fn();
    });

    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
        onNodeCreate={onNodeCreate}
      />
    );

    const newNodeData = {
      id: 'service:3',
      entity_type: 'service',
      label: 'Service C',
    };

    act(() => {
      messageHandler({
        entity_id: 'service:3',
        entity_type: 'service',
        change_type: 'created',
        data: newNodeData,
      });
    });

    expect(onNodeCreate).toHaveBeenCalledWith(newNodeData);
  });

  it('calls onNodeDelete when delete message received', () => {
    const onNodeDelete = vi.fn();
    let messageHandler: (data: unknown) => void = () => {};

    vi.mocked(graphWebSocket.subscribe).mockImplementation((topic, handler) => {
      if (topic === 'entity:updated:proj123') {
        messageHandler = handler as (data: unknown) => void;
      }
      return vi.fn();
    });

    render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
        onNodeDelete={onNodeDelete}
      />
    );

    act(() => {
      messageHandler({
        entity_id: 'service:1',
        entity_type: 'service',
        change_type: 'deleted',
      });
    });

    expect(onNodeDelete).toHaveBeenCalledWith('service:1');
  });

  it('unsubscribes when component unmounts', () => {
    const unsubscribeFn = vi.fn();
    vi.mocked(graphWebSocket.subscribe).mockReturnValue(unsubscribeFn);

    const { unmount } = render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
      />
    );

    unmount();

    expect(unsubscribeFn).toHaveBeenCalled();
  });

  it('resubscribes when projectId changes', () => {
    const { rerender } = render(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj123"
      />
    );

    expect(graphWebSocket.subscribe).toHaveBeenCalledWith(
      'entity:updated:proj123',
      expect.any(Function)
    );

    vi.clearAllMocks();

    rerender(
      <GraphCanvas
        nodes={mockNodes}
        edges={mockEdges}
        enableRealTime={true}
        projectId="proj456"
      />
    );

    expect(graphWebSocket.subscribe).toHaveBeenCalledWith(
      'entity:updated:proj456',
      expect.any(Function)
    );
  });
});
