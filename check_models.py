import google.generativeai as genai

genai.configure(api_key="AIzaSyD952mhQGB06f6GEJKU5ayuB1y3ek_8SxI")  

print("\n✅ Available Gemini Models for your account:\n")

for m in genai.list_models():
    print(m.name, " | ", m.supported_generation_methods)
