# src/services/python_service.py
import logging
import aiohttp
import asyncio
import time
from config import ENV

logger = logging.getLogger(__name__)
env = ENV()

class PythonService:
    """Service for handling Python code optimization requests"""
    
    def __init__(self):
        self.api_url = env.api_url
        self.max_retries = env.max_retries
        self.retry_delay = env.retry_delay
    
    async def optimize_code(self, code):
        """
        Send Python code to the optimization API and get results
        
        Args:
            code (str): Python code to optimize
            
        Returns:
            dict: API response with status and data
        """
        logger.info("Sending code to optimization API")
        
        # Request headers
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 Safari/537.36",
            "Origin": "https://www.clouddefense.ai",
            "Referer": "https://www.clouddefense.ai/"
        }
        
        # Request body
        data = {
            "code": code,
            "lang": "python"
        }
        
        # Try the request with retries
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, headers=headers, json=data, timeout=30) as response:
                        logger.info(f"API response status: {response.status}")
                        
                        if response.status == 200:
                            json_response = await response.json()
                            
                            if json_response.get("status") == "success":
                                logger.info("Successfully received optimization results")
                                return self._process_successful_response(json_response)
                            else:
                                logger.error(f"API returned error: {json_response}")
                                return {
                                    "status": "error",
                                    "message": json_response.get("message", "Unknown API error")
                                }
                        
                        elif response.status == 500:
                            logger.warning(f"API error 500 on attempt {attempt + 1}/{self.max_retries}")
                            
                            if attempt < self.max_retries - 1:
                                logger.info(f"Retrying in {self.retry_delay} seconds...")
                                await asyncio.sleep(self.retry_delay)
                                continue
                            else:
                                return {
                                    "status": "error",
                                    "message": f"API server error (500) after {self.max_retries} attempts"
                                }
                        
                        else:
                            logger.error(f"API error: Non-200 response: {response.status}")
                            return {
                                "status": "error", 
                                "message": f"API returned unexpected status code: {response.status}"
                            }
            
            except aiohttp.ClientError as e:
                logger.error(f"Network error on attempt {attempt + 1}/{self.max_retries}: {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    return {
                        "status": "error",
                        "message": f"Network error: {str(e)}"
                    }
            
            except asyncio.TimeoutError:
                logger.error(f"Request timeout on attempt {attempt + 1}/{self.max_retries}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    return {
                        "status": "error",
                        "message": "Request timed out after multiple attempts"
                    }
            
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                return {
                    "status": "error",
                    "message": f"Unexpected error: {str(e)}"
                }
    
    def _process_successful_response(self, response):
        """
        Process a successful API response
        
        Args:
            response (dict): API response data
            
        Returns:
            dict: Processed response
        """
        try:
            # Extract relevant data from response
            data = response.get("data", {})
            
            # Ensure we have the required fields
            if "optimized_code" not in data or "explanation" not in data:
                logger.warning("Missing expected fields in successful response")
                data["optimized_code"] = data.get("optimized_code", "# No optimized code available")
                data["explanation"] = data.get("explanation", "No explanation available")
            
            # Return formatted response
            return {
                "status": "success",
                "data": data
            }
        
        except Exception as e:
            logger.exception(f"Error processing successful response: {e}")
            return {
                "status": "error",
                "message": f"Error processing response: {str(e)}"
            }