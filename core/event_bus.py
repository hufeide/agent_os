#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件总线

实现发布/订阅模式的事件驱动通信。

作者: Agent OS Team
"""

import asyncio
import threading
from typing import Dict, List, Callable, Optional, Any
from collections import defaultdict
from datetime import datetime

from core.models import Event, EventType


class EventBus:
    """
    事件总线
    
    实现发布/订阅模式，支持事件驱动的异步通信。
    """
    
    def __init__(self):
        """初始化事件总线"""
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._lock = threading.RLock()
        self._running = False
        self._event_queue: asyncio.Queue = None
        self._loop: asyncio.AbstractEventLoop = None
        self._worker_thread: Optional[threading.Thread] = None
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def publish(self, event_type: EventType, data: Dict[str, Any], 
                source: str = "system") -> None:
        """
        发布事件（同步）
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
        """
        event = Event(
            type=event_type,
            data=data,
            source=source
        )
        
        with self._lock:
            self._event_history.append(event)
            
            callbacks = self._subscribers.get(event_type, [])
            for callback in callbacks:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Event callback error: {e}")
    
    async def publish_async(self, event_type: EventType, data: Dict[str, Any],
                       source: str = "system") -> None:
        """
        发布事件（异步）
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
        """
        if not self._running:
            raise RuntimeError("EventBus is not running")
        
        event = Event(
            type=event_type,
            data=data,
            source=source
        )
        
        await self._event_queue.put(event)
    
    def start(self) -> None:
        """
        启动事件总线（异步模式）
        """
        if self._running:
            return
        
        self._running = True
        self._event_queue = asyncio.Queue()
        self._loop = asyncio.new_event_loop()
        
        self._worker_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._worker_thread.start()
        
        print("EventBus started")
    
    def stop(self) -> None:
        """
        停止事件总线
        """
        if not self._running:
            return
        
        self._running = False
        
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        
        print("EventBus stopped")
    
    def _run_event_loop(self) -> None:
        """
        运行事件循环
        """
        asyncio.set_event_loop(self._loop)
        
        async def process_events():
            while self._running:
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0
                    )
                    
                    with self._lock:
                        self._event_history.append(event)
                        callbacks = self._subscribers.get(event.type, [])
                    
                    for callback in callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            print(f"Event callback error: {e}")
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Event processing error: {e}")
        
        self._loop.run_until_complete(process_events())
    
    def get_history(self, event_type: Optional[EventType] = None,
                  limit: int = 100) -> List[Event]:
        """
        获取事件历史
        
        Args:
            event_type: 事件类型（None表示所有类型）
            limit: 最大返回数量
            
        Returns:
            事件列表
        """
        with self._lock:
            if event_type is None:
                return self._event_history[-limit:]
            else:
                return [
                    event for event in self._event_history
                    if event.type == event_type
                ][-limit:]
    
    def clear_history(self) -> None:
        """清空事件历史"""
        with self._lock:
            self._event_history.clear()
    
    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """
        获取订阅者数量
        
        Args:
            event_type: 事件类型（None表示所有类型）
            
        Returns:
            订阅者数量
        """
        with self._lock:
            if event_type is None:
                return sum(len(subs) for subs in self._subscribers.values())
            else:
                return len(self._subscribers.get(event_type, []))


class EventFilter:
    """
    事件过滤器
    
    用于过滤和路由事件。
    """
    
    def __init__(self, event_bus: EventBus):
        """
        初始化事件过滤器
        
        Args:
            event_bus: 事件总线实例
        """
        self.event_bus = event_bus
        self._filters: Dict[str, Callable[[Event], bool]] = {}
    
    def add_filter(self, name: str, filter_func: Callable[[Event], bool]) -> None:
        """
        添加过滤器
        
        Args:
            name: 过滤器名称
            filter_func: 过滤函数（返回True表示通过）
        """
        self._filters[name] = filter_func
    
    def remove_filter(self, name: str) -> None:
        """
        移除过滤器
        
        Args:
            name: 过滤器名称
        """
        if name in self._filters:
            del self._filters[name]
    
    def subscribe_filtered(self, event_type: EventType, callback: Callable[[Event], None],
                      filter_name: Optional[str] = None) -> None:
        """
        订阅带过滤的事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            filter_name: 过滤器名称
        """
        def filtered_callback(event: Event) -> None:
            if filter_name and filter_name in self._filters:
                if not self._filters[filter_name](event):
                    return
            callback(event)
        
        self.event_bus.subscribe(event_type, filtered_callback)
    
    def get_filters(self) -> Dict[str, Callable[[Event], bool]]:
        """
        获取所有过滤器
        
        Returns:
            过滤器字典
        """
        return self._filters.copy()