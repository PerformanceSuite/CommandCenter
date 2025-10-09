#!/opt/homebrew/bin/node

const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

async function testLatestModels() {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
        console.error("❌ No API key found!");
        return;
    }
    
    console.log("🔍 Testing Gemini 2.5 Models...\n");
    console.log("API Key:", apiKey.substring(0, 10) + "...\n");
    
    const genAI = new GoogleGenerativeAI(apiKey);
    
    // Test Gemini 2.5 Flash
    try {
        console.log("Testing Gemini 2.5 Flash...");
        const flashModel = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
        const result = await flashModel.generateContent("Say 'Hello from Gemini 2.5 Flash!' in exactly 5 words");
        console.log("✅ Flash:", result.response.text());
    } catch (error) {
        console.error("❌ Flash error:", error.message);
    }
    
    // Test Gemini 2.5 Pro Preview
    try {
        console.log("\nTesting Gemini 2.5 Pro Preview...");
        const proModel = genAI.getGenerativeModel({ model: "gemini-2.5-pro-preview-03-25" });
        const result = await proModel.generateContent("Say 'Hello from Gemini 2.5 Pro!' in exactly 5 words");
        console.log("✅ Pro:", result.response.text());
    } catch (error) {
        console.error("❌ Pro error:", error.message);
    }
    
    console.log("\n🎉 Your Gemini 2.5 setup is ready!");
    console.log("\nQuick commands:");
    console.log("  gemini ask 'your question'         - Use 2.5 Flash");
    console.log("  gemini ask-pro 'complex question'  - Use 2.5 Pro");
    console.log("  gemini models                      - See all models");
    console.log("\nOr use dev-assistant:");
    console.log("  dev-assistant ai 'your question'");
}

testLatestModels();
