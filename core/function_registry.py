"""
函数注册和编排系统
每个模块就是一个函数，通过名称注册和调用
支持任意输入输出类型
"""
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import inspect
import requests
import subprocess
import json


@dataclass
class FunctionSpec:
    """函数规范 - 描述函数的输入输出"""
    name: str
    inputs: List[str]  # 输入参数名列表
    outputs: List[str]  # 输出字段名列表
    description: str = ""
    
    def __repr__(self):
        return f"{self.name}({', '.join(self.inputs)}) -> {{{', '.join(self.outputs)}}}"


class FunctionRegistry:
    """函数与工作流注册中心"""
    
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self.specs: Dict[str, FunctionSpec] = {}
        self.workflows: Dict[str, Callable] = {} # 新增：存储工作流
    
    def register(self,
                 name: str,
                 func: Callable,
                 inputs: List[str] = None,
                 outputs: List[str] = None,
                 description: str = "") -> None:
        """
        注册一个函数
        
        Args:
            name: 函数名称
            func: 可调用对象
            inputs: 输入参数名列表
            outputs: 输出字段名列表
            description: 函数描述
        """
        # 如果没有提供inputs，从函数签名自动提取
        if inputs is None:
            sig = inspect.signature(func)
            inputs = list(sig.parameters.keys())
        
        # 如果没有提供outputs，默认为['result']
        if outputs is None:
            outputs = ['result']
        
        self.functions[name] = func
        self.specs[name] = FunctionSpec(name, inputs, outputs, description)
        try:
            print(f"✓ 已注册函数: {self.specs[name]}")
        except UnicodeEncodeError:
            print(f"[OK] 已注册函数: {self.specs[name]}")
    
    def call(self, name: str, **kwargs) -> Any:
        """
        调用注册的函数
        
        Args:
            name: 函数名称
            **kwargs: 函数参数
            
        Returns:
            函数返回值
        """
        if name not in self.functions:
            raise ValueError(f"函数 {name} 未注册")
        
        func = self.functions[name]
        spec = self.specs[name]
        
        # 提取需要的参数
        func_args = {}
        for param in spec.inputs:
            if param in kwargs:
                func_args[param] = kwargs[param]
        
        # 调用函数
        result = func(**func_args)
        
        # 如果返回值不是字典，根据输出规范包装
        if not isinstance(result, dict):
            # 如果只有一个输出字段，使用该字段名
            if len(spec.outputs) == 1:
                result = {spec.outputs[0]: result}
            else:
                # 否则使用默认的"result"
                result = {"result": result}
        
        return result
    
    def list_functions(self) -> List[str]:
        """列出所有注册的函数"""
        return list(self.functions.keys())
    
    def get_spec(self, name: str) -> FunctionSpec:
        """获取函数规范"""
        return self.specs.get(name)

    def register_workflow(self, name: str, workflow: Callable):
        """注册一个工作流"""
        if name in self.workflows:
            try:
                print(f"警告: 工作流 '{name}' 已被覆盖。")
            except UnicodeEncodeError:
                print(f"[WARNING] 工作流 '{name}' 已被覆盖。")
        self.workflows[name] = workflow
        try:
            print(f"✓ 已注册工作流: {name}")
        except UnicodeEncodeError:
            print(f"[OK] 已注册工作流: {name}")

    def get_workflow(self, name: str) -> Optional[Callable]:
        """获取一个已注册的工作流"""
        return self.workflows.get(name)

    def list_workflows(self) -> List[str]:
        """列出所有已注册的工作流"""
        return list(self.workflows.keys())


# 全局注册器
_registry = FunctionRegistry()


def register_function(name: str = None,
                     inputs: List[str] = None,
                     outputs: List[str] = None,
                     description: str = ""):
    """
    装饰器：注册函数
    
    使用方法:
        @register_function(name="text_upper", outputs=["text"])
        def to_upper(text):
            return text.upper()
    """
    def decorator(func):
        func_name = name or func.__name__
        _registry.register(func_name, func, inputs, outputs, description)
        return func
    
    return decorator


def get_registry() -> FunctionRegistry:
    """获取全局注册器"""
    return _registry


def get_registered_function(name: str) -> Callable:
    """
    获取已注册的函数
    
    Args:
        name: 函数名称
        
    Returns:
        注册的函数对象
        
    Raises:
        ValueError: 如果函数未注册
    """
    if name not in _registry.functions:
        raise ValueError(f"函数 {name} 未注册")
    return _registry.functions[name]


def register_workflow(name: str):
    """
    装饰器：注册工作流
    
    使用方法:
        @register_workflow(name="my_workflow")
        def my_workflow_function(arg1, arg2):
            ...
    """
    def decorator(func):
        _registry.register_workflow(name, func)
        return func
    return decorator

