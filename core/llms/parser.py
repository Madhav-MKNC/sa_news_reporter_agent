import re
import json
from core.colored import cprint, Colors


# Output parser
class Parser:
    def __init__(self):
        pass

    def __extract_json_from_text(self, text: str) -> dict:
        """
        Extracts the first valid JSON block from text.
        
        Args:
            text (str): Raw text containing JSON.
            
        Returns:
            dict: Parsed JSON object.
            
        Raises:
            ValueError: If JSON is not found or is invalid.
        """
        # Remove leading/trailing square brackets (if present)
        text = text.strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1].strip()

        # Match JSON inside a fenced code block
        fenced_pattern = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
        fenced_match = fenced_pattern.search(text)

        if fenced_match:
            json_str = fenced_match.group(1).strip()
        else:
            # Match standalone JSON object
            standalone_pattern = re.compile(r"(\{.*?\})", re.DOTALL)
            standalone_match = standalone_pattern.search(text)

            if standalone_match:
                json_str = standalone_match.group(1).strip()
            else:
                raise ValueError("Invalid JSON format: No JSON found.")

        # Parse and return JSON as a dict
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format: Failed to parse JSON.")

    def __is_valid_data(self, response: dict, expected_keys: set) -> bool:
        if not isinstance(response, dict):
            return False

        if set(response.keys()) != expected_keys:
            return False

        return True

    # The following is a dummpy method
    def get_what(self, raw_input: str) -> dict:
        expected_keys = {
            'what'
        }

        try:
            response_json = self.__extract_json_from_text(raw_input)
        except Exception as e:
            cprint(f"[PARSER] Error extracting JSON: {e}", color=Colors.Text.RED)
            response_json = {
                "what": ""
            }

        if not self.__is_valid_data(response=response_json, expected_keys=expected_keys):
            cprint("[PARSER] Invalid JSON format: Missing expected keys or invalid value types.", color=Colors.Text.RED)
            response_json = {
                "what": ""
            }

        return response_json
    
    # The following is a dummpy method
    def get_news_json(self, raw_input: str) -> dict:
        expected_keys = {
            'headline_str',
            'content_str',
            'tags_list'
        }

        try:
            response_json = self.__extract_json_from_text(raw_input)
        except Exception as e:
            cprint(f"[PARSER] Error extracting JSON: {e}", color=Colors.Text.RED)
            response_json = {
                'headline_str': '',
                'content_str': '',
                'tags_list': []
            }

        if not self.__is_valid_data(response=response_json, expected_keys=expected_keys):
            cprint("[PARSER] Invalid JSON format: Missing expected keys or invalid value types.", color=Colors.Text.RED)
            response_json = {
                'headline_str': '',
                'content_str': '',
                'tags_list': []
            }

        return response_json
    