"""
函数/能力注册与编排系统（API Registry）
统一以 @register_api 为入口进行注册，inputs/outputs 作为契约源
"""
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import inspect


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
        注册一个函数/能力（API 统一入口）
        
        Args:
            name: 能力名称（点分式）
            func: 可调用对象
            inputs: 输入参数名列表
            outputs: 输出字段名列表
            description: 描述
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
        """列出所有已注册的API名称"""
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




def get_registry() -> FunctionRegistry:
    """获取全局注册器"""
    return _registry




def register_workflow(name: str):
    """
    装饰器：注册工作流
    """
    def decorator(func):
        _registry.register_workflow(name, func)
        return func
    return decorator


def register_api(name: str = None,
                 inputs: List[str] = None,
                 outputs: List[str] = None,
                 description: str = ""):
    """
    装饰器：注册API（统一入口）
    
    使用方法:
        @register_api(name="web_server.restart_project", outputs=["result"])
        def restart_frontend_project(...):
            ...
    """
    def decorator(func):
        func_name = name or func.__name__
        _registry.register(func_name, func, inputs, outputs, description)
        try:
            print(f"✓ 已注册API: {_registry.specs[func_name]}")
        except UnicodeEncodeError:
            print(f"[OK] 已注册API: {_registry.specs[func_name]}")
        return func
    
    return decorator


def get_registered_api(name: str) -> Callable:
    """
    获取已注册的API
    """
    if name not in _registry.functions:
        raise ValueError(f"API {name} 未注册")
    return _registry.functions[name]