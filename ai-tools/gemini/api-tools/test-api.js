#!/opt/homebrew/bin/node

const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

async function testGemini() {
    try {
        console.log("🔍 Testing Gemini API key...");
        
        const apiKey = process.env.GEMINI_API_KEY;
        if (!apiKey) {
            console.error("❌ No API key found!");
            return;
        }
        
        console.log("✅ API key found:", apiKey.substring(0, 10) + "...");
        
        const genAI = new GoogleGenerativeAI(apiKey);
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        
        const result = await model.generateContent("Say 'Hello! Your API key is working!' in exactly 5 words.");
        const response = await result.response;
        const text = response.text();
        
        console.log("🎉 Gemini says:", text);
        console.log("\n✅ Everything is working perfectly!");
        
    } catch (error) {
        console.error("❌ Error:", error.message);
        if (error.message.includes("API_KEY_INVALID")) {
            console.error("The API key appears to be invalid. Please check it.");
        }
    }
}

testGemini();
