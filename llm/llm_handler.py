#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM处理器

支持vllm API的LLM处理器。

作者: Agent OS Team
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException


@dataclass
class LLMConfig:
    """LLM配置"""
    api_url: str
    model_name: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0


class LLMHandler:
    """
    LLM处理器
    
    支持vllm API的LLM调用
    """
    
    def __init__(self, config: LLMConfig):
        """
        初始化LLM处理器
        
        Args:
            config: LLM配置
        """
        self.config = config
        self.api_url = config.api_url.rstrip('/')
        self.model_name = config.model_name
        self.session = requests.Session()
        
        if config.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {config.api_key}"
            })
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> str:
        """
        聊天对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            响应文本
        """
        url = f"{self.api_url}/v1/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }
        
        return self._call_api(url, payload)
    
    def complete(self, 
                prompt: str, 
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None) -> str:
        """
        文本补全
        
        Args:
            prompt: 提示文本
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            补全文本
        """
        url = f"{self.api_url}/v1/completions"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }
        
        return self._call_api(url, payload)
    
    def generate_json(self,
                     prompt: str,
                     schema: Dict[str, Any],
                     temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        生成JSON格式响应
        
        Args:
            prompt: 提示文本
            schema: JSON schema
            temperature: 温度参数
            
        Returns:
            JSON响应
        """
        messages = [
            {
                "role": "system",
                "content": f"你是一个JSON生成助手。请严格按照以下JSON schema格式返回响应：\n{json.dumps(schema, ensure_ascii=False)}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = self.chat(messages, temperature)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return self._extract_json(response)
    
    def _call_api(self, url: str, payload: Dict[str, Any]) -> str:
        """
        调用API
        
        Args:
            url: API URL
            payload: 请求负载
            
        Returns:
            响应文本
        """
        print(f"[LLM调试] 调用API: {url}")
        print(f"[LLM调试] 模型: {payload.get('model')}")
        print(f"[LLM调试] 温度: {payload.get('temperature')}")
        print(f"[LLM调试] 最大tokens: {payload.get('max_tokens')}")
        
        for attempt in range(self.config.max_retries):
            try:
                print(f"[LLM调试] 第{attempt + 1}次尝试...")
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                print(f"[LLM调试] API响应状态码: {response.status_code}")
                print(f"[LLM调试] API响应keys: {list(data.keys())}")
                
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    print(f"[LLM调试] Choice keys: {list(choice.keys())}")
                    if "message" in choice:
                        content = choice["message"]["content"]
                        print(f"[LLM调试] 返回内容长度: {len(content)}")
                        return content
                    elif "text" in choice:
                        content = choice["text"]
                        print(f"[LLM调试] 返回内容长度: {len(content)}")
                        return content
                
                print(f"[LLM调试] 警告: API响应中没有找到choices")
                return ""
                
            except RequestException as e:
                print(f"[LLM调试] 请求异常: {e}")
                if attempt < self.config.max_retries - 1:
                    print(f"[LLM调试] 等待{self.config.retry_delay}秒后重试...")
                    time.sleep(self.config.retry_delay)
                    continue
                raise Exception(f"LLM API调用失败: {str(e)}")
            except Exception as e:
                print(f"[LLM调试] 异常: {e}")
                if attempt < self.config.max_retries - 1:
                    print(f"[LLM调试] 等待{self.config.retry_delay}秒后重试...")
                    time.sleep(self.config.retry_delay)
                    continue
                raise Exception(f"LLM响应解析失败: {str(e)}")
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取JSON
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            解析后的JSON对象
        """
        try:
            cleaned_text = text.strip()
            
            # 移除markdown代码块标记
            if cleaned_text.startswith("```"):
                # 找到第一个换行符
                first_newline = cleaned_text.find("\n")
                if first_newline != -1:
                    # 移除开头的 ```json 或 ```
                    cleaned_text = cleaned_text[first_newline:].strip()
                    
                    # 移除结尾的 ```
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3].strip()
            
            # 提取JSON部分
            start = cleaned_text.find("{")
            end = cleaned_text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = cleaned_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始文本: {text[:200]}...")
        except Exception as e:
            print(f"提取JSON时发生错误: {e}")
            print(f"原始文本: {text[:200]}...")
        
        return {}
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        try:
            url = f"{self.api_url}/health"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息
        """
        try:
            url = f"{self.api_url}/v1/models"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return {}


def create_llm_handler(api_url: str = None,
                       model_name: str = None,
                       **kwargs) -> LLMHandler:
    """
    创建LLM处理器
    
    Args:
        api_url: API URL
        model_name: 模型名称
        **kwargs: 其他配置参数
        
    Returns:
        LLM处理器实例
    """
    api_url = api_url or os.getenv("LLM_API_URL", "http://192.168.1.159:19000")
    model_name = model_name or os.getenv("LLM_MODEL_NAME", "Qwen3Coder")
    
    config = LLMConfig(
        api_url=api_url,
        model_name=model_name,
        api_key=kwargs.get("api_key") or os.getenv("LLM_API_KEY"),
        temperature=kwargs.get("temperature", 0.7),
        max_tokens=kwargs.get("max_tokens", 2000),
        timeout=kwargs.get("timeout", 60),
        max_retries=kwargs.get("max_retries", 3),
        retry_delay=kwargs.get("retry_delay", 1.0)
    )
    
    return LLMHandler(config)


if __name__ == "__main__":
    print("LLM处理器测试")
    print("=" * 50)
    
    handler = create_llm_handler()
    
    print(f"API URL: {handler.api_url}")
    print(f"Model: {handler.model_name}")
    print()
    
    print("健康检查...")
    health = handler.health_check()
    print(f"健康状态: {'✓ 正常' if health else '✗ 异常'}")
    print()
    
    print("获取模型信息...")
    model_info = handler.get_model_info()
    print(json.dumps(model_info, indent=2, ensure_ascii=False))
    print()
    
    print("测试对话...")
    try:
        messages = [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ]
        response = handler.chat(messages)
        print(f"响应: {response}")
    except Exception as e:
        print(f"错误: {e}")