#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过API测试新任务的工作记忆完整性
"""

import requests
import json
import time

def test_new_task_via_api():
    """通过API测试新任务的工作记忆完整性"""
    print("=== 通过API测试新任务的工作记忆完整性 ===\n")
    
    base_url = "http://localhost:8001"
    
    # 检查API服务器状态
    print("检查API服务器状态...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ API服务器正在运行\n")
        else:
            print(f"✗ API服务器状态异常: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器")
        print("  请确保服务器正在运行: python start.py")
        return
    except Exception as e:
        print(f"✗ 连接错误: {e}")
        return
    
    # 创建一个测试任务
    print("创建测试任务...")
    task_data = {
        "name": "测试工作记忆完整性",
        "description": "测试工作记忆是否完整保存Research和Analysis工具结果",
        "type": "research",
        "priority": "high",
        "agent_type": "researcher",
        "params": {
            "question": "What are the key periods in human history?"
        }
    }
    
    try:
        response = requests.post(f"{base_url}/api/tasks", json=task_data, timeout=10)
        print(f"创建任务响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✓ 任务创建成功，任务ID: {task_id}\n")
            
            # 等待任务完成
            print("等待任务完成...")
            max_wait = 60  # 最多等待60秒
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(2)
                wait_time += 2
                
                try:
                    status_response = requests.get(f"{base_url}/api/tasks/{task_id}", timeout=10)
                    if status_response.status_code == 200:
                        task_info = status_response.json()
                        status = task_info.get('status')
                        print(f"  任务状态: {status} (已等待 {wait_time} 秒)")
                        
                        if status == 'completed':
                            print("✓ 任务执行完成\n")
                            break
                        elif status == 'failed':
                            print(f"✗ 任务执行失败\n")
                            break
                except Exception as e:
                    print(f"  检查任务状态时出错: {e}")
            
            # 检查工作记忆
            print("检查工作记忆...")
            agent_id = task_info.get('agent_id', 'researcher_1')
            json_path = f"../agent_contexts/{agent_id}.json"
            
            print(f"工作记忆文件路径: {json_path}")
            
            import os
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    context_data = json.load(f)
                    working_memory = context_data.get('working_memory', [])
                    
                    print(f"工作记忆数量: {len(working_memory)}")
                    print()
                    
                    for i, item in enumerate(working_memory, 1):
                        content = item['content']
                        print(f"{i}. 工作记忆项:")
                        print(f"   长度: {len(content)} 字符")
                        print(f"   内容前300字符: {content[:300]}...")
                        
                        # 检查是否被截断
                        if len(content) < 100 and "调用工具" in content:
                            print(f"   ⚠️ 可能被截断（长度小于100字符）")
                        else:
                            print(f"   ✅ 内容完整")
                        print()
                    
                    # 检查是否有Research和Analysis工具调用
                    research_calls = [item for item in working_memory if "调用工具 Research" in item['content']]
                    analysis_calls = [item for item in working_memory if "调用工具 Analysis" in item['content']]
                    
                    print(f"Research工具调用次数: {len(research_calls)}")
                    print(f"Analysis工具调用次数: {len(analysis_calls)}")
                    print()
                    
                    if research_calls:
                        print("Research工具调用示例:")
                        research_content = research_calls[0]['content']
                        print(f"  长度: {len(research_content)} 字符")
                        print(f"  内容: {research_content[:500]}...")
                        print()
                    
                    if analysis_calls:
                        print("Analysis工具调用示例:")
                        analysis_content = analysis_calls[0]['content']
                        print(f"  长度: {len(analysis_content)} 字符")
                        print(f"  内容: {analysis_content[:500]}...")
                        print()
                    
                    # 总结
                    print("=== 测试总结 ===")
                    if research_calls and len(research_calls[0]['content']) > 100:
                        print("✅ Research工具结果完整保存")
                    else:
                        print("❌ Research工具结果可能被截断")
                    
                    if analysis_calls and len(analysis_calls[0]['content']) > 100:
                        print("✅ Analysis工具结果完整保存")
                    else:
                        print("❌ Analysis工具结果可能被截断")
                    
            else:
                print(f"❌ 工作记忆文件不存在: {json_path}")
        else:
            print(f"✗ 创建任务失败: {response.status_code}")
            print(f"  响应内容: {response.text}")
    
    except Exception as e:
        print(f"✗ 创建任务时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_new_task_via_api()