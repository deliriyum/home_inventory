import anthropic
import os
import base64
import json
from pathlib import Path

class AIService:
    """Service for AI-powered item analysis using Claude"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def _encode_image(self, image_path):
        """Encode image to base64"""
        with open(image_path, 'rb') as image_file:
            return base64.standard_b64encode(image_file.read()).decode('utf-8')

    def _get_media_type(self, image_path):
        """Determine media type from file extension"""
        ext = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return media_types.get(ext, 'image/jpeg')

    def analyze_item(self, image_path, user_description=None):
        """
        Analyze an item image to identify it, assess condition, and estimate value

        Returns a dict with:
        - item_name
        - confidence (0-1)
        - category
        - description
        - condition_assessment
        - estimated_retail_value
        - value_source
        - repair_needs
        """
        try:
            image_data = self._encode_image(image_path)
            media_type = self._get_media_type(image_path)

            prompt = f"""Analyze this image of an item that needs to be sold.

{"User's description: " + user_description if user_description else ""}

Please provide a detailed analysis in JSON format with the following fields:

1. item_name: What is this item? Be specific (brand, model if identifiable)
2. confidence: Your confidence level in the identification (0.0 to 1.0)
3. category: General category (electronics, furniture, tools, appliances, etc.)
4. description: Detailed description of the item
5. condition_assessment: Current condition and visible issues
6. estimated_retail_value: Approximate current market value in USD
7. value_source: Brief explanation of how you estimated the value
8. repair_needs: List of repairs or improvements needed to make it saleable

Return ONLY valid JSON, no markdown formatting."""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Parse the response
            response_text = message.content[0].text

            # Clean up response if it has markdown code blocks
            if response_text.strip().startswith('```'):
                response_text = response_text.strip()
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            analysis = json.loads(response_text)
            return analysis

        except Exception as e:
            print(f"Error analyzing item: {str(e)}")
            return {
                'item_name': 'Unknown Item',
                'confidence': 0.0,
                'category': 'Unknown',
                'description': 'Could not analyze image',
                'condition_assessment': 'Unable to assess',
                'estimated_retail_value': 0,
                'value_source': 'Analysis failed',
                'repair_needs': []
            }

    def generate_repair_bom(self, item_name, repair_needs, condition_assessment):
        """
        Generate a Bill of Materials for repairs

        Returns a list of items needed for repair with estimated costs
        """
        try:
            prompt = f"""Create a detailed Bill of Materials (BOM) for repairing this item:

Item: {item_name}
Current Condition: {condition_assessment}
Repair Needs: {repair_needs}

Provide a JSON array of repair items with the following fields for each:
- part_name: Name of the part or material
- part_description: What it's for and why it's needed
- estimated_cost: Estimated cost in USD (number)
- quantity: How many needed (number)
- purchase_url: Suggest a generic search term or store name (not a full URL)

Return ONLY valid JSON array, no markdown formatting."""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            response_text = message.content[0].text

            # Clean up response if it has markdown code blocks
            if response_text.strip().startswith('```'):
                response_text = response_text.strip()
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            bom = json.loads(response_text)
            return bom

        except Exception as e:
            print(f"Error generating BOM: {str(e)}")
            return []

    def generate_repair_tutorial(self, item_name, repair_needs, bom):
        """
        Generate step-by-step repair instructions

        Returns a detailed tutorial as markdown text
        """
        try:
            bom_summary = "\n".join([f"- {item['part_name']}" for item in bom]) if bom else "No parts needed"

            prompt = f"""Create a detailed, step-by-step repair tutorial for:

Item: {item_name}
Repairs Needed: {repair_needs}
Parts/Materials Available:
{bom_summary}

Provide:
1. Safety precautions
2. Tools needed
3. Step-by-step instructions (numbered)
4. Tips for success
5. Common pitfalls to avoid

Format as clear, easy-to-follow markdown text."""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3072,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            tutorial = message.content[0].text
            return tutorial

        except Exception as e:
            print(f"Error generating tutorial: {str(e)}")
            return "Tutorial generation failed. Please research repair methods manually."

    def quick_price_check(self, item_name, condition):
        """
        Get a quick price estimate for an item
        """
        try:
            prompt = f"""Provide a current market value estimate for:

Item: {item_name}
Condition: {condition}

Return a JSON object with:
- low_price: Low end of price range (USD)
- high_price: High end of price range (USD)
- average_price: Typical selling price (USD)
- market_info: Brief explanation of the market for this item
- sources: Where to check prices (eBay, Facebook Marketplace, etc.)

Return ONLY valid JSON, no markdown formatting."""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            response_text = message.content[0].text

            # Clean up response if it has markdown code blocks
            if response_text.strip().startswith('```'):
                response_text = response_text.strip()
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            price_info = json.loads(response_text)
            return price_info

        except Exception as e:
            print(f"Error checking price: {str(e)}")
            return {
                'low_price': 0,
                'high_price': 0,
                'average_price': 0,
                'market_info': 'Price check failed',
                'sources': []
            }
