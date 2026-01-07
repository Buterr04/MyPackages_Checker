import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyBDHO0gEX4nN3IMefqloQ1V7k7ULVtac80"
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage
import base64

def load_image_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# TODO: input images with frontend later
img_base64 = load_image_as_base64("data/damaged-and-intact-packages/damaged/damagedfoodpackagingbox3.jpeg")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 使用 gemini-pro-vision 进行多模态调用
message = HumanMessage(
    content=[
        {
            "type": "text",
            "text": "Check this image and describe if this package is damaged or not. "
            "If it is damaged, tell me where is the damage."
            "combine the damaged areas with the whole package,"
            "give me the percentages"
            "Return ONLY a JSON object with no markdown."
            "JSON format: {\"is_damaged\": true/false, \"damage_location\": \"damaged_percentage\", \"damage_severity\": \"low/medium/high\"}",
        },
        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_base64}"},
    ]
)

vision_result = llm.invoke([message])
print(vision_result.content)

# return vision_result (AI Message)
# must use with (vision_result.content) to get text content