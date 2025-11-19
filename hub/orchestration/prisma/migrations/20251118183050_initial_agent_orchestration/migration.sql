-- CreateEnum
CREATE TYPE "AgentType" AS ENUM ('LLM', 'RULE', 'API', 'SCRIPT');

-- CreateEnum
CREATE TYPE "RiskLevel" AS ENUM ('AUTO', 'APPROVAL_REQUIRED');

-- CreateEnum
CREATE TYPE "RunStatus" AS ENUM ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'WAITING_APPROVAL');

-- CreateEnum
CREATE TYPE "WorkflowStatus" AS ENUM ('ACTIVE', 'DRAFT', 'ARCHIVED');

-- CreateEnum
CREATE TYPE "ApprovalStatus" AS ENUM ('PENDING', 'APPROVED', 'REJECTED');

-- CreateTable
CREATE TABLE "agents" (
    "id" TEXT NOT NULL,
    "projectId" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "type" "AgentType" NOT NULL,
    "description" TEXT,
    "entryPath" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "riskLevel" "RiskLevel" NOT NULL,
    "registeredAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "agents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "agent_capabilities" (
    "id" TEXT NOT NULL,
    "agentId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "inputSchema" JSONB NOT NULL,
    "outputSchema" JSONB NOT NULL,

    CONSTRAINT "agent_capabilities_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "agent_runs" (
    "id" TEXT NOT NULL,
    "agentId" TEXT NOT NULL,
    "workflowRunId" TEXT,
    "inputJson" JSONB NOT NULL,
    "outputJson" JSONB,
    "status" "RunStatus" NOT NULL,
    "error" TEXT,
    "startedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "finishedAt" TIMESTAMP(3),
    "durationMs" INTEGER,

    CONSTRAINT "agent_runs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflows" (
    "id" TEXT NOT NULL,
    "projectId" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "trigger" JSONB NOT NULL,
    "status" "WorkflowStatus" NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "workflows_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflow_nodes" (
    "id" TEXT NOT NULL,
    "workflowId" TEXT NOT NULL,
    "agentId" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "inputsJson" JSONB NOT NULL,
    "dependsOn" TEXT[],
    "approvalRequired" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "workflow_nodes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflow_runs" (
    "id" TEXT NOT NULL,
    "workflowId" TEXT NOT NULL,
    "trigger" TEXT NOT NULL,
    "contextJson" JSONB NOT NULL,
    "status" "RunStatus" NOT NULL,
    "startedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "finishedAt" TIMESTAMP(3),

    CONSTRAINT "workflow_runs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflow_approvals" (
    "id" TEXT NOT NULL,
    "workflowRunId" TEXT NOT NULL,
    "nodeId" TEXT NOT NULL,
    "status" "ApprovalStatus" NOT NULL,
    "requestedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "respondedAt" TIMESTAMP(3),
    "respondedBy" TEXT,
    "notes" TEXT,

    CONSTRAINT "workflow_approvals_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "agents_projectId_type_idx" ON "agents"("projectId", "type");

-- CreateIndex
CREATE UNIQUE INDEX "agents_projectId_name_key" ON "agents"("projectId", "name");

-- CreateIndex
CREATE UNIQUE INDEX "agent_capabilities_agentId_name_key" ON "agent_capabilities"("agentId", "name");

-- CreateIndex
CREATE INDEX "agent_runs_agentId_status_idx" ON "agent_runs"("agentId", "status");

-- CreateIndex
CREATE INDEX "agent_runs_workflowRunId_idx" ON "agent_runs"("workflowRunId");

-- CreateIndex
CREATE INDEX "workflows_projectId_status_idx" ON "workflows"("projectId", "status");

-- CreateIndex
CREATE UNIQUE INDEX "workflows_projectId_name_key" ON "workflows"("projectId", "name");

-- CreateIndex
CREATE INDEX "workflow_nodes_workflowId_idx" ON "workflow_nodes"("workflowId");

-- CreateIndex
CREATE INDEX "workflow_runs_workflowId_status_idx" ON "workflow_runs"("workflowId", "status");

-- CreateIndex
CREATE INDEX "workflow_runs_startedAt_idx" ON "workflow_runs"("startedAt");

-- CreateIndex
CREATE INDEX "workflow_approvals_workflowRunId_status_idx" ON "workflow_approvals"("workflowRunId", "status");

-- AddForeignKey
ALTER TABLE "agent_capabilities" ADD CONSTRAINT "agent_capabilities_agentId_fkey" FOREIGN KEY ("agentId") REFERENCES "agents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "agent_runs" ADD CONSTRAINT "agent_runs_agentId_fkey" FOREIGN KEY ("agentId") REFERENCES "agents"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "agent_runs" ADD CONSTRAINT "agent_runs_workflowRunId_fkey" FOREIGN KEY ("workflowRunId") REFERENCES "workflow_runs"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "workflow_nodes" ADD CONSTRAINT "workflow_nodes_workflowId_fkey" FOREIGN KEY ("workflowId") REFERENCES "workflows"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "workflow_nodes" ADD CONSTRAINT "workflow_nodes_agentId_fkey" FOREIGN KEY ("agentId") REFERENCES "agents"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "workflow_runs" ADD CONSTRAINT "workflow_runs_workflowId_fkey" FOREIGN KEY ("workflowId") REFERENCES "workflows"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "workflow_approvals" ADD CONSTRAINT "workflow_approvals_workflowRunId_fkey" FOREIGN KEY ("workflowRunId") REFERENCES "workflow_runs"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
