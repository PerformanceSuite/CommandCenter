#!/usr/bin/env node

const { GoogleGenerativeAI } = require("@google/generative-ai");
const fs = require('fs');
const path = require('path');
const readline = require('readline');
require('dotenv').config();

// Check for API key
if (!process.env.GEMINI_API_KEY) {
    console.error("❌ GEMINI_API_KEY not found in .env file");
    console.error("1. Get your API key from: https://makersuite.google.com/app/apikey");
    console.error("2. Copy .env.example to .env");
    console.error("3. Add your API key to the .env file");
    process.exit(1);
}

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0];

async function askGemini(prompt, modelName = "gemini-2.5-flash") {
    try {
        const model = genAI.getGenerativeModel({ model: modelName });
        const result = await model.generateContent(prompt);
        const response = await result.response;
        return response.text();
    } catch (error) {
        console.error("Error:", error.message);
        return null;
    }
}

// Model shortcuts for easy access
const MODELS = {
    'flash': 'gemini-2.5-flash',
    'pro': 'gemini-2.5-pro-preview-03-25',
    'computer-use': 'gemini-2.5-computer-use-preview-10-2025',
    'lite': 'gemini-2.5-flash-lite-preview-06-17'
};

async function codeReview(filePath) {
    try {
        const code = fs.readFileSync(filePath, 'utf8');
        const prompt = `Please review this code and provide feedback on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance improvements
4. Security concerns
5. Suggestions for improvement

Code:
\`\`\`
${code}
\`\`\``;
        
        console.log("🔍 Reviewing code...");
        const response = await askGemini(prompt, "gemini-2.5-flash");
        return response;
    } catch (error) {
        console.error("Error reading file:", error.message);
        return null;
    }
}

async function explainCode(filePath) {
    try {
        const code = fs.readFileSync(filePath, 'utf8');
        const prompt = `Please explain this code in simple terms. What does it do and how does it work?

Code:
\`\`\`
${code}
\`\`\``;
        
        console.log("📖 Explaining code...");
        const response = await askGemini(prompt);
        return response;
    } catch (error) {
        console.error("Error reading file:", error.message);
        return null;
    }
}

async function generateTests(filePath) {
    try {
        const code = fs.readFileSync(filePath, 'utf8');
        const prompt = `Generate comprehensive unit tests for this code. Include edge cases and error scenarios.

Code:
\`\`\`
${code}
\`\`\``;
        
        console.log("🧪 Generating tests...");
        const response = await askGemini(prompt, "gemini-2.5-flash");
        return response;
    } catch (error) {
        console.error("Error reading file:", error.message);
        return null;
    }
}

async function chat() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    
    console.log("💬 Gemini Chat (type 'exit' to quit)");
    console.log("=====================================\n");
    
    const askQuestion = () => {
        rl.question("You: ", async (input) => {
            if (input.toLowerCase() === 'exit') {
                rl.close();
                return;
            }
            
            const response = await askGemini(input);
            console.log("\nGemini:", response, "\n");
            askQuestion();
        });
    };
    
    askQuestion();
}

// Main command handling
async function main() {
    if (!command) {
        console.log(`
🌟 Gemini CLI Tool - Latest 2.5 Models
==========================================

Usage: gemini <command> [options]

Commands:
  ask <prompt>          Ask Gemini a question (uses 2.5 Flash)
  ask-pro <prompt>      Ask using Gemini 2.5 Pro Preview
  review <file>         Get a code review (uses 2.5 Flash)
  explain <file>        Get an explanation of code
  tests <file>          Generate tests for code
  chat                  Start interactive chat mode
  models                List available models

Model Options:
  --model flash         Use Gemini 2.5 Flash (default)
  --model pro          Use Gemini 2.5 Pro Preview
  --model computer-use Use Gemini 2.5 Computer Use Preview
  --model lite         Use Gemini 2.5 Flash Lite Preview

Examples:
  gemini ask "What is recursion?"
  gemini ask-pro "Complex reasoning question"
  gemini review app.js
  gemini explain utils.py
  gemini tests calculator.js
  gemini chat
  gemini models
        `);
        return;
    }

    let response;
    let selectedModel = 'gemini-2.5-flash'; // Default to 2.5 Flash
    
    // Check for model flag
    const modelFlag = args.indexOf('--model');
    if (modelFlag !== -1 && args[modelFlag + 1]) {
        const modelName = args[modelFlag + 1];
        selectedModel = MODELS[modelName] || selectedModel;
    }
    
    switch (command) {
        case 'models':
            console.log("\n🚀 Available Gemini 2.5 Models:");
            console.log("================================\n");
            console.log("🌟 Gemini 2.5 Flash (default)");
            console.log("   Model: gemini-2.5-flash");
            console.log("   Best for: Fast responses, general tasks\n");
            
            console.log("💪 Gemini 2.5 Pro Preview");
            console.log("   Model: gemini-2.5-pro-preview-03-25");
            console.log("   Best for: Complex reasoning, detailed analysis\n");
            
            console.log("🖥️  Gemini 2.5 Computer Use Preview");
            console.log("   Model: gemini-2.5-computer-use-preview-10-2025");
            console.log("   Best for: UI automation, browser control\n");
            
            console.log("⚡ Gemini 2.5 Flash Lite Preview");
            console.log("   Model: gemini-2.5-flash-lite-preview-06-17");
            console.log("   Best for: Lightweight tasks, faster responses\n");
            return;
            
        case 'ask':
            const prompt = args.slice(1).filter((_, i) => i !== modelFlag && i !== modelFlag + 1 - 1).join(' ');
            if (!prompt) {
                console.error("Please provide a prompt");
                return;
            }
            console.log(`Using model: ${selectedModel}`);
            response = await askGemini(prompt, selectedModel);
            break;
            
        case 'ask-pro':
            const proPrompt = args.slice(1).join(' ');
            if (!proPrompt) {
                console.error("Please provide a prompt");
                return;
            }
            console.log("Using Gemini 2.5 Pro Preview...");
            response = await askGemini(proPrompt, 'gemini-2.5-pro-preview-03-25');
            break;
            
        case 'review':
            if (!args[1]) {
                console.error("Please provide a file path");
                return;
            }
            response = await codeReview(args[1]);
            break;
            
        case 'explain':
            if (!args[1]) {
                console.error("Please provide a file path");
                return;
            }
            response = await explainCode(args[1]);
            break;
            
        case 'tests':
            if (!args[1]) {
                console.error("Please provide a file path");
                return;
            }
            response = await generateTests(args[1]);
            break;
            
        case 'chat':
            await chat();
            return;
            
        default:
            console.error(`Unknown command: ${command}`);
            console.log("Run 'gemini' without arguments to see available commands");
            return;
    }
    
    if (response) {
        console.log(response);
    }
}

main();
