# nodes.py
from server import PromptServer
from aiohttp import web
import json

class PromptSelectorNode:
    """提示词选择器节点，用于在ComfyUI中动态选择预定义的提示词"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_pairs": ("STRING", {
                    "multiline": True,
                    "default": '"key1":"value1",\n"key2":"value2",\n"key3":"value3"'
                }),
                # 使用类变量存储的当前keys
                "selected_key": (["key1", "key2", "key3"],),
            },
            # 这样可以为 FUNCTION 提供 node_id 参数
            "hidden": { "node_id": "UNIQUE_ID" }
        }
    
    @classmethod
    def VALIDATE_INPUTS(cls, selected_key):
        return True
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("selected_value",)
    FUNCTION = "process"
    CATEGORY = "Prompt Selector"
    
    @classmethod
    def update_current_keys(cls, data):
        # TODO: 这里可以为不同节点实例设置 selected_key 的可选列表
        print(data)
        return
    
    def __init__(self):
        self.prompt_dict = {}
        self.keys_list = []
        self._last_pairs = None
    
    def escape_newlines_in_strings(self, s: str) -> str:
        """预处理字符串：在双引号内的换行符替换为 \\n，以支持多行值而不破坏 JSON"""
        result = []
        in_string = False
        escaped_quote = False
        i = 0
        while i < len(s):
            char = s[i]
            if char == '"' and not escaped_quote:
                in_string = not in_string
                escaped_quote = False
            elif char == '\\':
                escaped_quote = not escaped_quote
            else:
                escaped_quote = False
            
            if in_string and char == '\n':
                result.append('\\n')
            else:
                result.append(char)
            i += 1
        return ''.join(result)
    
    def parse_prompt_pairs(self, prompt_pairs: str) -> None:
        """解析提示词对字符串并更新可用的keys"""
        self.prompt_dict.clear()
        self.keys_list.clear()
        
        try:
            # 预处理：转义字符串内的换行
            escaped_pairs = self.escape_newlines_in_strings(prompt_pairs)
            # 尝试将输入字符串解析为JSON对象
            prompt_dict = json.loads("{" + escaped_pairs + "}")
            if isinstance(prompt_dict, dict):
                self.prompt_dict = prompt_dict
                self.keys_list = list(prompt_dict.keys())
            else:
                raise ValueError("解析结果不是字典类型")
        except json.JSONDecodeError as e:
            print(f"解析JSON时出错: {str(e)}, 输入: {prompt_pairs}")
        except Exception as e:
            print(f"解析提示词对时出错: {str(e)}, 输入: {prompt_pairs}")
        
        self._last_pairs = prompt_pairs
        
        # 如果没有解析出任何键值对，使用默认值
        if not self.keys_list:
            self.prompt_dict = {"key1": "value1", "key2": "value2", "key3": "value3"}
            self.keys_list = list(self.prompt_dict.keys())
    
    def process(self, prompt_pairs: str, selected_key: str, node_id) -> tuple:
        """处理选择的提示词"""
        try:
            # 解析提示词对并更新可用的keys
            self.parse_prompt_pairs(prompt_pairs)
            
            # 确保选中的key存在，否则使用第一个可用的key
            if selected_key not in self.prompt_dict:
                selected_key = self.keys_list[0] if self.keys_list else "key1"
            
            return (self.prompt_dict.get(selected_key, ""),)
        except Exception as e:
            print(f"处理提示词时出错: {str(e)}")
            return ("",)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "PromptSelector": PromptSelectorNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSelector": "🐱FlyZen提示词选择器"
}

routes = PromptServer.instance.routes

@routes.post('/update_psn_keys')
async def update_psn_keys(request):
    the_data = await request.post()
    PromptSelectorNode.update_current_keys(the_data)
    return web.json_response({})