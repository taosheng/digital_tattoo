import os
import argparse
import asyncio
import base64
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def test_merge(left_path: str, right_path: str, out_path: str, aggressive: bool, custom_prompt: str = None):
    # Initialize API key
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print("Error: XAI_API_KEY is missing from environment or .env file.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print(f"Reading left image: {left_path}")
    with open(left_path, "rb") as f:
        content1 = f.read()
    print(f"Reading right image: {right_path}")
    with open(right_path, "rb") as f:
        content2 = f.read()

    img1_base64 = base64.b64encode(content1).decode("utf-8")
    img2_base64 = base64.b64encode(content2).decode("utf-8")
    
    # MIME type guessing
    content_type1 = "image/jpeg" if left_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    content_type2 = "image/jpeg" if right_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

    async with httpx.AsyncClient(timeout=120.0) as client:
        print("\n[Step 1] Analyzing BOTH images using grok-4.3 to create a perfect fusion prompt...")
        try:
            vision_payload = {
                "model": "grok-4.3",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "I am providing two images. \n"
                                    "Image 1 (Base): Provides the exact body, clothing, pose, lighting, and background.\n"
                                    "Image 2 (Face): Provides the exact facial features, hair, and head structure.\n\n"
                                    "Your task: Write an extremely detailed, cohesive, and highly descriptive prompt for an image generation AI. "
                                    "This prompt must describe a single, photorealistic photograph. "
                                    "The photograph MUST perfectly recreate the scene, clothing, posture, and background of Image 1. "
                                    "However, the person in the photograph MUST have their face and head described exactly as the person in Image 2. "
                                    "Be very specific about the face structure, eye shape/color, nose, mouth, skin tone, hair style, and facial expression from Image 2. "
                                    "Be very specific about the clothing style, colors, pose, lighting, and background setting from Image 1. "
                                    "Output ONLY the final image generation prompt, nothing else. Do not add conversational text."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type1};base64,{img1_base64}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type2};base64,{img2_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            vision_res = await client.post("https://api.x.ai/v1/chat/completions", headers=headers, json=vision_payload)
            vision_res.raise_for_status()
            vision_data = vision_res.json()
            fusion_prompt = vision_data["choices"][0]["message"]["content"].strip()
            
            print("AI Generated Fusion Prompt:")
            print("-" * 50)
            print(fusion_prompt)
            print("-" * 50)
        except Exception as e:
            print(f"Failed to analyze images and create prompt: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response details: {e.response.text}")
            return

        print("\n[Step 2] Generating merged image using the fusion prompt and LEFT image as reference...")

        if custom_prompt:
            final_prompt = custom_prompt + f"\n\n[Context: {fusion_prompt}]"
            print("Using custom prompt appended with fusion context.")
        else:
            final_prompt = fusion_prompt
            if aggressive:
                final_prompt += " The person's facial features should be extremely charismatic, beautiful, and idealized, standing out as highly attractive while maintaining realistic photography style."
            
        print("\nPrompt being sent to image generation:")
        print("-" * 50)
        print(final_prompt)
        print("-" * 50)

        print("\nSending request to xAI Imagine...")
        try:
            imagine_payload = {
                "model": "grok-imagine-image-quality",
                "prompt": final_prompt,
                "image": f"data:{content_type1};base64,{img1_base64}", # Pass left image as structural reference if xAI supports it
                "aspect_ratio": "1:1",
                "resolution": "1k" 
            }
            
            imagine_res = await client.post("https://api.x.ai/v1/images/generations", headers=headers, json=imagine_payload)
            imagine_res.raise_for_status()
            imagine_data = imagine_res.json()
            merged_image_url = imagine_data["data"][0]["url"]
            
            print(f"\nMerge successful! Image URL: {merged_image_url}")
            
            print(f"Downloading result to {out_path}...")
            res_img = await client.get(merged_image_url)
            res_img.raise_for_status()
            with open(out_path, "wb") as f_out:
                f_out.write(res_img.content)
            print(f"Successfully saved result to {out_path}\n")
            
        except Exception as e:
            print(f"\nAI generation failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response details: {e.response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test xAI Super Merge functionality locally.")
    parser.add_argument("--left", type=str, required=True, help="Path to the left image")
    parser.add_argument("--right", type=str, required=True, help="Path to the right image")
    parser.add_argument("--out", type=str, default="merge_result.jpg", help="Path to save the output image")
    parser.add_argument("--aggressive", action="store_true", help="Use the aggressive/enhanced prompt")
    parser.add_argument("--prompt", type=str, help="Override the default prompt with a custom one for testing")
    
    args = parser.parse_args()
    
    asyncio.run(test_merge(args.left, args.right, args.out, args.aggressive, args.prompt))