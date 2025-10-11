// AgentFlow Setup Wizard JavaScript

let currentStep = 1;
let configuration = {
    project: {},
    agents: [],
    workflow: {},
    claude: {}
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadAgents();
    setupEventListeners();
});

// Load agents from configuration
async function loadAgents() {
    try {
        // In production, this would fetch from the server
        const agents = getDefaultAgents();
        renderAgents(agents);
    } catch (error) {
        console.error('Failed to load agents:', error);
    }
}

// Get default agents configuration
function getDefaultAgents() {
    return {
        core: [
            { id: 'backend', name: 'Backend Agent', description: 'API and server logic' },
            { id: 'frontend', name: 'Frontend Agent', description: 'UI components and state' },
            { id: 'database', name: 'Database Agent', description: 'Schema and migrations' },
            { id: 'testing', name: 'Testing Agent', description: 'Test suites and coverage' },
            { id: 'infrastructure', name: 'Infrastructure Agent', description: 'Docker and CI/CD' }
        ],
        quality: [
            { id: 'ui-ux', name: 'UI/UX Agent', description: 'Visual design review (Opus 4.1)' },
            { id: 'security', name: 'Security Agent', description: 'Vulnerability scanning' },
            { id: 'performance', name: 'Performance Agent', description: 'Optimization and profiling' },
            { id: 'best-practices', name: 'Best Practices Agent', description: 'Code standards' },
            { id: 'dependencies', name: 'Dependencies Agent', description: 'Package management' }
        ],
        specialized: [
            { id: 'documentation', name: 'Documentation Agent', description: 'Docs and comments' },
            { id: 'localization', name: 'Localization Agent', description: 'i18n and translations' },
            { id: 'monitoring', name: 'Monitoring Agent', description: 'Logging and metrics' },
            { id: 'devops', name: 'DevOps Agent', description: 'Pipeline optimization' },
            { id: 'data-validation', name: 'Data Validation Agent', description: 'Schema validation' }
        ]
    };
}

// Render agents in the UI
function renderAgents(agents) {
    renderAgentCategory('coreAgents', agents.core, true);
    renderAgentCategory('qualityAgents', agents.quality, true);
    renderAgentCategory('specializedAgents', agents.specialized, false);
}

function renderAgentCategory(containerId, agents, defaultSelected) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = agents.map(agent => `
        <div class="agent-card ${defaultSelected ? 'selected' : ''}" data-agent="${agent.id}">
            <h4>${agent.name}</h4>
            <p>${agent.description}</p>
        </div>
    `).join('');

    // Add click handlers
    container.querySelectorAll('.agent-card').forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('selected');
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // Step navigation
    document.querySelectorAll('.step').forEach(step => {
        step.addEventListener('click', () => {
            const stepNum = parseInt(step.dataset.step);
            if (stepNum <= currentStep) {
                goToStep(stepNum);
            }
        });
    });

    // Range inputs
    document.getElementById('maxParallel')?.addEventListener('input', (e) => {
        document.getElementById('parallelValue').textContent = e.target.value;
    });

    document.getElementById('reviewThreshold')?.addEventListener('input', (e) => {
        document.getElementById('thresholdValue').textContent = `${e.target.value}/10`;
    });

    document.getElementById('minCoverage')?.addEventListener('input', (e) => {
        document.getElementById('coverageValue').textContent = `${e.target.value}%`;
    });
}

// Navigation functions
function nextStep() {
    if (validateCurrentStep()) {
        saveStepData();
        if (currentStep < 4) {
            goToStep(currentStep + 1);
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        goToStep(currentStep - 1);
    }
}

function goToStep(step) {
    // Update sections
    document.querySelectorAll('.wizard-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`step${step}`).classList.add('active');

    // Update navigation
    document.querySelectorAll('.step').forEach((s, index) => {
        s.classList.remove('active', 'completed');
        if (index + 1 < step) {
            s.classList.add('completed');
        } else if (index + 1 === step) {
            s.classList.add('active');
        }
    });

    currentStep = step;

    // Special actions for step 4
    if (step === 4) {
        showReview();
    }
}

// Validation
function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            const projectName = document.getElementById('projectName').value;
            if (!projectName) {
                alert('Please enter a project name');
                return false;
            }
            return true;
        case 2:
            const selectedAgents = document.querySelectorAll('.agent-card.selected');
            if (selectedAgents.length === 0) {
                alert('Please select at least one agent');
                return false;
            }
            return true;
        default:
            return true;
    }
}

// Save step data
function saveStepData() {
    switch (currentStep) {
        case 1:
            configuration.project = {
                name: document.getElementById('projectName').value,
                type: document.getElementById('projectType').value,
                path: document.getElementById('projectPath').value,
                description: document.getElementById('description').value,
                technologies: Array.from(document.querySelectorAll('input[name="tech"]:checked'))
                    .map(cb => cb.value)
            };
            break;
        case 2:
            configuration.agents = Array.from(document.querySelectorAll('.agent-card.selected'))
                .map(card => card.dataset.agent);
            configuration.workflow.maxParallel = document.getElementById('maxParallel').value;
            break;
        case 3:
            configuration.workflow = {
                ...configuration.workflow,
                branchStrategy: document.getElementById('branchStrategy').value,
                mergeStrategy: document.getElementById('mergeStrategy').value,
                reviewThreshold: document.getElementById('reviewThreshold').value,
                minCoverage: document.getElementById('minCoverage').value,
                testing: Array.from(document.querySelectorAll('input[name="testing"]:checked'))
                    .map(cb => cb.value)
            };
            configuration.claude = {
                useOpus41: document.querySelector('input[value="opus41"]')?.checked,
                useVision: document.querySelector('input[value="vision"]')?.checked,
                parallel: document.querySelector('input[value="parallel"]')?.checked
            };
            break;
    }
}

// Show review
function showReview() {
    // Project review
    const projectReview = document.getElementById('projectReview');
    projectReview.innerHTML = `
        <div class="review-item">
            <span>Name:</span>
            <strong>${configuration.project.name}</strong>
        </div>
        <div class="review-item">
            <span>Type:</span>
            <strong>${configuration.project.type}</strong>
        </div>
        <div class="review-item">
            <span>Technologies:</span>
            <strong>${configuration.project.technologies.join(', ') || 'None selected'}</strong>
        </div>
    `;

    // Agents review
    const agentsReview = document.getElementById('agentsReview');
    agentsReview.innerHTML = `
        <div class="review-item">
            <span>Total Agents:</span>
            <strong>${configuration.agents.length}</strong>
        </div>
        <div class="review-item">
            <span>Agents:</span>
            <strong>${configuration.agents.join(', ')}</strong>
        </div>
        <div class="review-item">
            <span>Max Parallel:</span>
            <strong>${configuration.workflow.maxParallel}</strong>
        </div>
    `;

    // Workflow review
    const workflowReview = document.getElementById('workflowReview');
    workflowReview.innerHTML = `
        <div class="review-item">
            <span>Branch Strategy:</span>
            <strong>${configuration.workflow.branchStrategy}</strong>
        </div>
        <div class="review-item">
            <span>Merge Strategy:</span>
            <strong>${configuration.workflow.mergeStrategy}</strong>
        </div>
        <div class="review-item">
            <span>Review Threshold:</span>
            <strong>${configuration.workflow.reviewThreshold}/10</strong>
        </div>
        <div class="review-item">
            <span>Min Coverage:</span>
            <strong>${configuration.workflow.minCoverage}%</strong>
        </div>
    `;
}

// Deploy workflow
async function deployWorkflow() {
    const deployOption = document.querySelector('input[name="deploy"]:checked').value;
    const statusDiv = document.getElementById('deploymentStatus');
    
    statusDiv.classList.add('active');
    statusDiv.innerHTML = '<div class="status-item"><span class="status-icon loading">⟳</span> Generating configuration...</div>';

    try {
        // Simulate deployment steps
        await simulateDeployment(statusDiv, deployOption);
        
        // Success message
        statusDiv.innerHTML += '<div class="status-item"><span class="status-icon success">✓</span> AgentFlow deployed successfully!</div>';
        
        // Download configuration
        downloadConfiguration();
        
    } catch (error) {
        statusDiv.innerHTML += `<div class="status-item"><span class="status-icon error">✗</span> Error: ${error.message}</div>`;
    }
}

// Simulate deployment process
async function simulateDeployment(statusDiv, option) {
    const steps = [
        'Validating configuration...',
        'Creating project structure...',
        'Setting up git worktrees...',
        'Configuring agents...',
        'Initializing workflows...'
    ];

    for (const step of steps) {
        await new Promise(resolve => setTimeout(resolve, 500));
        statusDiv.innerHTML += `<div class="status-item"><span class="status-icon success">✓</span> ${step}</div>`;
    }

    if (option === 'run') {
        statusDiv.innerHTML += '<div class="status-item"><span class="status-icon loading">⟳</span> Starting agents...</div>';
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

// Download configuration files
function downloadConfiguration() {
    // Generate shell script
    const shellScript = generateShellScript();
    downloadFile('agentflow-config.sh', shellScript);

    // Generate JSON config
    const jsonConfig = JSON.stringify(configuration, null, 2);
    downloadFile('agentflow.json', jsonConfig);

    // Generate README
    const readme = generateReadme();
    downloadFile('AGENTFLOW_README.md', readme);
}

// Generate shell script
function generateShellScript() {
    return `#!/bin/bash
# AgentFlow Configuration
# Generated: ${new Date().toISOString()}

# Project Configuration
export PROJECT_NAME="${configuration.project.name}"
export PROJECT_TYPE="${configuration.project.type}"
export PROJECT_PATH="${configuration.project.path || '.'}"

# Agent Configuration
export AGENTS="${configuration.agents.join(' ')}"
export MAX_PARALLEL=${configuration.workflow.maxParallel}

# Workflow Configuration
export BRANCH_STRATEGY="${configuration.workflow.branchStrategy}"
export MERGE_STRATEGY="${configuration.workflow.mergeStrategy}"
export REVIEW_THRESHOLD=${configuration.workflow.reviewThreshold}
export MIN_COVERAGE=${configuration.workflow.minCoverage}

# Claude Configuration
export CLAUDE_MODEL="claude-opus-4-1-20250805"
export USE_VISION=${configuration.claude.useVision}

# Run AgentFlow
cd "$(dirname "$0")"
./scripts/agentflow.sh --project "$PROJECT_NAME" --agents $MAX_PARALLEL
`;
}

// Generate README
function generateReadme() {
    return `# AgentFlow Configuration for ${configuration.project.name}

## Project Details
- **Type**: ${configuration.project.type}
- **Technologies**: ${configuration.project.technologies.join(', ')}
- **Description**: ${configuration.project.description}

## Active Agents
${configuration.agents.map(agent => `- ${agent}`).join('\n')}

## Workflow Settings
- **Branch Strategy**: ${configuration.workflow.branchStrategy}
- **Merge Strategy**: ${configuration.workflow.mergeStrategy}
- **Review Threshold**: ${configuration.workflow.reviewThreshold}/10
- **Min Coverage**: ${configuration.workflow.minCoverage}%

## Quick Start

1. Make the script executable:
   \`\`\`bash
   chmod +x agentflow-config.sh
   \`\`\`

2. Run AgentFlow:
   \`\`\`bash
   ./agentflow-config.sh
   \`\`\`

3. Monitor progress:
   \`\`\`bash
   tail -f .agentflow/logs/*.log
   \`\`\`

Generated by AgentFlow on ${new Date().toLocaleString()}
`;
}

// Download file utility
function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}
