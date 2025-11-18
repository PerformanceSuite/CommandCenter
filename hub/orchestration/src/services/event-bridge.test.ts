import { describe, it, expect, beforeEach, vi } from 'vitest';
import { EventBridge } from './event-bridge';
import prisma from '../db/prisma';
import { NatsClient } from '../events/nats-client';

describe('EventBridge', () => {
  let eventBridge: EventBridge;
  let mockNatsClient: NatsClient;

  beforeEach(async () => {
    // Clean up test data
    await prisma.workflowRun.deleteMany({});
    await prisma.workflowNode.deleteMany({});
    await prisma.workflow.deleteMany({});

    mockNatsClient = new NatsClient();
    eventBridge = new EventBridge(prisma, mockNatsClient);
  });

  describe('matchWorkflows', () => {
    it('should match workflow by exact event pattern', async () => {
      // Create workflow with event trigger
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'file-scanner',
          trigger: {
            type: 'event',
            pattern: 'graph.file.updated',
          },
          status: 'ACTIVE',
        },
      });

      const event = {
        type: 'graph.file.updated',
        payload: { file_path: '/src/test.ts' },
      };

      const matched = await eventBridge['matchWorkflows'](event);

      expect(matched).toHaveLength(1);
      expect(matched[0].id).toBe(workflow.id);
    });

    it('should match workflow by wildcard pattern', async () => {
      // Create workflow with wildcard trigger
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'all-graph-events',
          trigger: {
            type: 'event',
            pattern: 'graph.*',
          },
          status: 'ACTIVE',
        },
      });

      const event = {
        type: 'graph.file.updated',
        payload: {},
      };

      const matched = await eventBridge['matchWorkflows'](event);

      expect(matched).toHaveLength(1);
      expect(matched[0].id).toBe(workflow.id);
    });

    it('should not match draft workflows', async () => {
      await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'draft-workflow',
          trigger: {
            type: 'event',
            pattern: 'graph.file.updated',
          },
          status: 'DRAFT',
        },
      });

      const event = {
        type: 'graph.file.updated',
        payload: {},
      };

      const matched = await eventBridge['matchWorkflows'](event);

      expect(matched).toHaveLength(0);
    });

    it('should match multiple workflows for same event', async () => {
      // Create two workflows for same event
      await prisma.workflow.createMany({
        data: [
          {
            projectId: 1,
            name: 'scanner',
            trigger: {
              type: 'event',
              pattern: 'graph.file.updated',
            },
            status: 'ACTIVE',
          },
          {
            projectId: 1,
            name: 'notifier',
            trigger: {
              type: 'event',
              pattern: 'graph.file.updated',
            },
            status: 'ACTIVE',
          },
        ],
      });

      const event = {
        type: 'graph.file.updated',
        payload: {},
      };

      const matched = await eventBridge['matchWorkflows'](event);

      expect(matched).toHaveLength(2);
    });
  });

  describe('handleEvent', () => {
    it('should create workflow runs for matching workflows', async () => {
      const workflow = await prisma.workflow.create({
        data: {
          projectId: 1,
          name: 'file-scanner',
          trigger: {
            type: 'event',
            pattern: 'graph.file.updated',
          },
          status: 'ACTIVE',
        },
      });

      const event = {
        type: 'graph.file.updated',
        payload: { file_path: '/src/test.ts' },
      };

      await eventBridge['handleEvent'](event);

      // Verify workflow run was created
      const runs = await prisma.workflowRun.findMany({
        where: { workflowId: workflow.id },
      });

      expect(runs).toHaveLength(1);
      expect(runs[0].trigger).toBe('event:graph.file.updated');
      expect(runs[0].status).toBe('PENDING');
    });

    it('should not create runs if no workflows match', async () => {
      const event = {
        type: 'nonexistent.event',
        payload: {},
      };

      await eventBridge['handleEvent'](event);

      const runs = await prisma.workflowRun.findMany({});
      expect(runs).toHaveLength(0);
    });
  });

  describe('patternMatches', () => {
    it('should match exact patterns', () => {
      expect(
        eventBridge['patternMatches']('graph.file.updated', 'graph.file.updated')
      ).toBe(true);
    });

    it('should match single wildcard', () => {
      expect(eventBridge['patternMatches']('graph.file.updated', 'graph.*')).toBe(
        true
      );
      expect(eventBridge['patternMatches']('graph.file.updated', '*.file.*')).toBe(
        true
      );
    });

    it('should match multi-level wildcard', () => {
      expect(eventBridge['patternMatches']('graph.file.updated', 'graph.>')).toBe(
        true
      );
      expect(eventBridge['patternMatches']('a.b.c.d', 'a.>')).toBe(true);
    });

    it('should not match non-matching patterns', () => {
      expect(eventBridge['patternMatches']('graph.file.updated', 'health.*')).toBe(
        false
      );
      expect(eventBridge['patternMatches']('a.b.c', 'a.b')).toBe(false);
    });
  });
});
