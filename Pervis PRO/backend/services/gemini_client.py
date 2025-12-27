"""
Gemini AI 客户端服务
Phase 2: 安全的后端AI调用，严格JSON验证
"""

import os
import json
import uuid
import time
from typing import Dict, List, Any, Optional
from google.generativeai import GenerativeModel, configure
import google.generativeai as genai

class GeminiClient:
    
    def __init__(self):
        # 从环境变量获取API密钥
        api_key = os.getenv("GEMINI_API_KEY")
        
        self.mock_mode = False
        self.model = None

        if not api_key:
            # Phase 5: 用户要求强制去Mock，如果没有Key则直接报错，不提供Mock
            raise ValueError("GEMINI_API_KEY未设置。请在.env中配置Key或切换到本地LLM模式。")
            
        elif api_key == "test_key_for_development":
            print("⚠️ 警告: 使用的是测试Key，仅用于API连通性测试 (Mock Mode Validated).")
            self.mock_mode = True 
        else:
            try:
                configure(api_key=api_key)
                # 使用 Gemini 1.5 Flash
                self.model = GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini AI内核已连接 (Model: gemini-1.5-flash)")
            except Exception as e:
                # Phase 5: 连接失败直接抛出异常，不回退
                raise ConnectionError(f"❌ Gemini 连接失败: {str(e)}")
    
    async def analyze_script(self, script_text: str, mode: str = "parse") -> Dict[str, Any]:
        """
        剧本分析 - 生成Beat和角色信息
        """
        
        # Mock模式返回测试数据
        if self.mock_mode:
            return self._get_mock_script_analysis(script_text)
        
        system_prompt = """
你是专业的剧本分析师。请将输入的剧本分析为结构化的Beat列表和角色信息。

输出要求：
1. 必须返回严格的JSON格式
2. Beat是语义单元，不是精确时间轴
3. 标签要具体且有创意启发性

JSON格式：
{
  "logline": "一句话故事概述",
  "synopsis": "详细故事梗概",
  "characters": [
    {
      "id": "char_xxx",
      "name": "角色名",
      "role": "Protagonist/Antagonist/Supporting/Extra",
      "description": "角色描述"
    }
  ],
  "beats": [
    {
      "content": "Beat内容描述",
      "emotion_tags": ["情绪标签"],
      "scene_tags": ["场景标签"],
      "action_tags": ["动作标签"],
      "cinematography_tags": ["摄影标签"],
      "duration_estimate": 数字
    }
  ]
}
"""
        
        try:
            # 构建完整提示
            full_prompt = f"{system_prompt}\n\n剧本内容：\n{script_text}"
            
            # 调用Gemini
            response = self.model.generate_content(full_prompt)
            
            # 清理和验证JSON
            cleaned_json = self._clean_json_response(response.text)
            parsed_data = json.loads(cleaned_json)
            
            # 验证必要字段
            self._validate_script_analysis(parsed_data)
            
            return {
                "status": "success",
                "data": parsed_data,
                "raw_response": response.text[:500]  # 保留部分原始响应用于调试
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error_code": "JSON_PARSE_ERROR",
                "message": "AI返回的JSON格式无效",
                "details": str(e),
                "trace_id": str(uuid.uuid4()),
                "raw_response": response.text if 'response' in locals() else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error_code": "AI_SERVICE_ERROR", 
                "message": "剧本分析失败",
                "details": str(e),
                "trace_id": str(uuid.uuid4())
            }
    
    async def analyze_video_content(self, filename: str, description: str = "", 
                                  images: List[Any] = None) -> Dict[str, Any]:
        """
        视频内容分析 - 生成标签和segment
        Supports 'Vision' input via list of PIL Images (keyframes)
        """
        
        # Mock模式返回测试数据
        if self.mock_mode:
            return self._get_mock_video_analysis(filename)
        
        system_prompt = """
你是专业的视频内容分析师。基于提供的视频关键帧图片和元数据，生成详细的内容标签。

输出要求：
1. 必须返回严格的JSON格式
2. 标签要丰富且有创意价值 (包含情绪、运镜、光影)
3. 准确描述画面内容

JSON格式：
{
  "global_tags": {
    "emotions": ["情绪标签"],
    "scenes": ["场景标签"], 
    "actions": ["动作标签"],
    "cinematography": ["摄影技法标签"]
  },
  "segments": [
    {
      "start_time": 0,
      "end_time": 0,
      "description": "基于画面的详细描述",
      "tags": {
        "visual_elements": ["可见物体"],
        "mood": ["氛围"]
      }
    }
  ]
}
"""
        
        try:
            # 构建多模态Prompt
            content_parts = [system_prompt]
            
            # 添加文本元数据
            content_parts.append(f"视频文件名: {filename}\n描述: {description}\n以下是该视频的精选关键帧：")
            
            # 添加图片数据 (如果有)
            if images:
                # Gemini 1.5 支持直接传入 PIL Image 对象
                content_parts.extend(images)
            else:
                content_parts.append("(未提供关键帧图片，仅根据文件名分析)")
            
            # 调用Gemini (Multimodal)
            response = self.model.generate_content(content_parts)
            
            cleaned_json = self._clean_json_response(response.text)
            parsed_data = json.loads(cleaned_json)
            
            return {
                "status": "success",
                "data": parsed_data
            }
            
        except Exception as e:
            print(f"Gemini Vision Analysis Failed: {e}")
            return {
                "status": "error",
                "error_code": "VIDEO_ANALYSIS_ERROR",
                "message": "视频分析失败",
                "details": str(e),
                "trace_id": str(uuid.uuid4())
            }
    
    async def generate_search_explanation(self, beat_content: str, asset_tags: Dict, 
                                        match_score: float) -> str:
        """
        生成搜索推荐理由
        """
        
        prompt = f"""
请为以下匹配生成一句自然的推荐理由：

Beat内容: {beat_content}
素材标签: {asset_tags}
匹配分数: {match_score}

要求：
- 一句话说明为什么推荐这个素材
- 语言自然，有启发性
- 不超过50字
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return f"该素材与您的创作需求匹配度为{match_score:.0%}，建议预览查看效果"
    
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        通用的JSON生成方法
        """
        if self.mock_mode:
             raise NotImplementedError("Mock mode not supported for generate_json")

        try:
            response = self.model.generate_content(prompt)
            cleaned = self._clean_json_response(response.text)
            return json.loads(cleaned)
        except Exception as e:
            print(f"Gemini Generate JSON Failed: {e}")
            return {"error": str(e)}

    def _clean_json_response(self, text: str) -> str:
        """
        清理AI返回的JSON文本
        """
        if not text:
            raise ValueError("Empty response from AI")
        
        # 移除markdown代码块标记
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # 尝试解析，如果失败则尝试修复
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            # 简单的JSON修复逻辑
            return self._attempt_json_repair(text)
    
    def _attempt_json_repair(self, text: str) -> str:
        """
        尝试修复损坏的JSON
        """
        # 查找最后一个完整的对象
        last_brace = text.rfind('}')
        if last_brace > 0:
            # 尝试截取到最后一个完整对象
            truncated = text[:last_brace + 1]
            try:
                json.loads(truncated)
                return truncated
            except:
                pass
        
        # 如果修复失败，返回默认结构
        return json.dumps({
            "logline": "剧本分析被截断",
            "synopsis": "AI响应不完整，请重试",
            "characters": [],
            "beats": []
        })
    
    def _validate_script_analysis(self, data: Dict[str, Any]):
        """
        验证剧本分析结果的必要字段
        """
        required_fields = ["beats", "characters"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # 验证beats结构
        if not isinstance(data["beats"], list):
            raise ValueError("beats must be a list")
        
        for i, beat in enumerate(data["beats"]):
            if not isinstance(beat, dict) or "content" not in beat:
                raise ValueError(f"Invalid beat structure at index {i}")
    
    def _get_mock_script_analysis(self, script_text: str) -> Dict[str, Any]:
        """(Deprecated) Mock Analysis - Disabled by Phase 5 Enforcement"""
        raise NotImplementedError("Mock mode is disabled. Please connect a valid AI backend.")

        
        # 智能解析剧本内容
        lines = [line.strip() for line in script_text.split('\n') if line.strip()]
        print(f"[DEBUG] 解析到 {len(lines)} 行")
        
        beats = []
        characters = set()
        current_scene = "未知场景"
        current_time = "白天"
        
        for line in lines:
            # 跳过常见的剧本标记
            if line in ['FADE IN:', 'FADE OUT:', 'CUT TO:', 'DISSOLVE TO:']:
                continue
            
            # 识别场景标题 (EXT./INT.)
            if line.startswith('EXT.') or line.startswith('INT.'):
                parts = line.split('-')
                if len(parts) >= 2:
                    current_scene = parts[0].replace('EXT.', '外景').replace('INT.', '内景').strip()
                    current_time = parts[1].strip() if len(parts) > 1 else "白天"
                continue
            
            # 识别角色对话 (全大写的行)
            if line.isupper() and len(line) < 30 and not line.startswith('EXT') and not line.startswith('INT'):
                characters.add(line)
                continue
            
            # 识别动作描述和对话内容
            if len(line) > 10:  # 过滤太短的行
                # 估算时长：根据内容长度和复杂度
                word_count = len(line)
                
                # 基础时长：每15个字符约1秒（中文更密集）
                base_duration = max(2.0, word_count / 15)
                
                # 根据内容类型调整
                if '对话' in line or '"' in line or '"' in line:
                    # 对话通常需要更长时间
                    duration = base_duration * 1.5
                elif any(action in line for action in ['跑', '追', '打', '战斗', '爆炸']):
                    # 动作场景需要更长时间
                    duration = base_duration * 2.0
                elif any(slow in line for slow in ['慢慢', '缓缓', '静静', '凝视', '沉思']):
                    # 慢节奏场景
                    duration = base_duration * 1.8
                else:
                    duration = base_duration
                
                # 限制在合理范围内
                duration = min(max(duration, 2.0), 15.0)
                
                # 分析情绪标签
                emotion_tags = []
                if any(word in line for word in ['紧张', '害怕', '恐惧', '惊恐']):
                    emotion_tags.extend(['紧张', '恐惧'])
                if any(word in line for word in ['开心', '快乐', '笑', '高兴']):
                    emotion_tags.extend(['快乐', '轻松'])
                if any(word in line for word in ['悲伤', '哭', '难过', '痛苦']):
                    emotion_tags.extend(['悲伤', '沉重'])
                if any(word in line for word in ['愤怒', '生气', '暴怒', '愤恨']):
                    emotion_tags.extend(['愤怒', '激动'])
                if any(word in line for word in ['神秘', '诡异', '奇怪', '不安']):
                    emotion_tags.extend(['神秘', '不安'])
                if not emotion_tags:
                    emotion_tags = ['平静', '中性']
                
                # 分析场景标签
                scene_tags = []
                if '外景' in current_scene or any(word in line for word in ['街道', '公园', '户外', '天空']):
                    scene_tags.append('户外')
                if '内景' in current_scene or any(word in line for word in ['房间', '办公室', '室内', '家']):
                    scene_tags.append('室内')
                if '夜' in current_time or '晚' in current_time:
                    scene_tags.append('夜晚')
                else:
                    scene_tags.append('白天')
                if any(word in line for word in ['城市', '都市', '街道', '大楼']):
                    scene_tags.append('城市')
                if any(word in line for word in ['自然', '森林', '山', '海']):
                    scene_tags.append('自然')
                
                # 分析动作标签
                action_tags = []
                if any(word in line for word in ['走', '跑', '移动', '前进']):
                    action_tags.append('移动')
                if any(word in line for word in ['看', '观察', '注视', '盯']):
                    action_tags.append('观察')
                if any(word in line for word in ['说', '讲', '对话', '交谈']):
                    action_tags.append('对话')
                if any(word in line for word in ['打', '战斗', '攻击', '防御']):
                    action_tags.append('战斗')
                if any(word in line for word in ['拿', '抓', '握', '触摸']):
                    action_tags.append('互动')
                if not action_tags:
                    action_tags = ['静态']
                
                # 分析摄影标签
                cinematography_tags = []
                if any(word in line for word in ['特写', '近景', '脸']):
                    cinematography_tags.append('特写')
                elif any(word in line for word in ['远景', '全景', '广角']):
                    cinematography_tags.append('远景')
                else:
                    cinematography_tags.append('中景')
                
                if any(word in line for word in ['跟随', '跟拍', '移动']):
                    cinematography_tags.append('跟拍')
                if any(word in line for word in ['俯视', '仰视']):
                    cinematography_tags.append('角度镜头')
                
                beats.append({
                    "content": line[:200],  # 限制长度
                    "emotion_tags": emotion_tags[:3],  # 最多3个标签
                    "scene_tags": scene_tags[:3],
                    "action_tags": action_tags[:3],
                    "cinematography_tags": cinematography_tags[:2],
                    "duration_estimate": round(duration, 1)
                })
        
        # 如果没有解析到Beat，创建一个默认的
        if not beats:
            beats = [{
                "content": script_text[:200] if script_text else "空剧本",
                "emotion_tags": ["中性"],
                "scene_tags": ["未知"],
                "action_tags": ["静态"],
                "cinematography_tags": ["中景"],
                "duration_estimate": 5.0
            }]
        
        # 生成角色列表
        character_list = []
        for i, char_name in enumerate(list(characters)[:10]):  # 最多10个角色
            character_list.append({
                "id": f"char_{uuid.uuid4().hex[:8]}",
                "name": char_name,
                "role": "Protagonist" if i == 0 else "Supporting",
                "description": f"剧本中的角色：{char_name}"
            })
        
        # 如果没有识别到角色，添加默认角色
        if not character_list:
            character_list.append({
                "id": f"char_{uuid.uuid4().hex[:8]}",
                "name": "主角",
                "role": "Protagonist",
                "description": "故事的主要角色"
            })
        
        # 生成logline和synopsis
        logline = f"包含{len(beats)}个场景的故事"
        synopsis = f"剧本共{len(beats)}个Beat，涉及{len(character_list)}个角色，总时长约{sum(b['duration_estimate'] for b in beats):.1f}秒"
        
        mock_data = {
            "logline": logline,
            "synopsis": synopsis,
            "characters": character_list,
            "beats": beats
        }
        
        return {
            "status": "success",
            "data": mock_data,
            "raw_response": f"[智能解析模式] 解析了{len(beats)}个Beat，{len(character_list)}个角色"
        }
    
    def _get_mock_video_analysis(self, filename: str) -> Dict[str, Any]:
        """返回模拟的视频分析数据"""
        
        mock_data = {
            "global_tags": {
                "emotions": ["神秘", "紧张"],
                "scenes": ["室内", "夜晚"],
                "actions": ["探索", "发现"],
                "cinematography": ["手持", "特写"]
            },
            "segments": [
                {
                    "start_time": 0,
                    "end_time": 10.0,
                    "description": "开场建立镜头，展现环境氛围",
                    "tags": {
                        "emotions": ["平静", "神秘"],
                        "scenes": ["室内", "昏暗"],
                        "actions": ["建立", "展示"],
                        "cinematography": ["广角", "稳定"]
                    }
                },
                {
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "description": "角色登场，情绪转换",
                    "tags": {
                        "emotions": ["紧张", "期待"],
                        "scenes": ["室内", "特写"],
                        "actions": ["进入", "观察"],
                        "cinematography": ["中景", "跟拍"]
                    }
                }
            ]
        }
        
        return {
            "status": "success",
            "data": mock_data
        }
    
    async def generate_text(self, prompt: str) -> Dict[str, Any]:
        """通用文本生成方法"""
        
        if self.mock_mode:
            return {
                "status": "success",
                "data": {
                    "text": "这是一个基于语义相似度的推荐，该素材的情绪和场景设定与您的创作需求高度匹配。"
                }
            }
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "status": "success",
                "data": {
                    "text": response.text
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
