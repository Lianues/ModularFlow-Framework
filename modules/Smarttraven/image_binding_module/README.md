# 图像绑定模块 (Image Binding Module)

这个模块用于实现文件与PNG图片的绑定与提取功能。它可以将世界书、正则、角色卡、预设、用户配置等文件隐藏地嵌入到PNG图片中，并在需要时从图片中提取这些文件。

## 功能特点

- 支持将多个文件嵌入到同一张PNG图片中
- 自动检测文件类型并添加标签
- 支持从图片中提取所有或指定类型的文件
- 检查图片是否包含嵌入的文件
- 获取图片中嵌入的文件信息（不提取文件内容）
- 使用PNG数据块的方式嵌入文件，不影响图片的正常显示

## 使用方法

### 导入模块

```python
from modules.SmartTavern.image_binding_module import ImageBindingModule
```

### 初始化

```python
image_binding = ImageBindingModule()
```

### 将文件嵌入到图片中

```python
# 将多个文件嵌入到图片中
output_path = image_binding.embed_files_to_image(
    image_path="path/to/image.png",
    file_paths=[
        "path/to/world_book.json",
        "path/to/character.json",
        "path/to/preset.json",
        "path/to/regex.json",
        "path/to/personas.json"
    ],
    output_path="path/to/output.png"  # 可选，默认为原图片路径加上_embedded后缀
)

print(f"文件已嵌入到图片中: {output_path}")
```

### 从图片中提取文件

```python
# 提取所有文件
extracted_files = image_binding.extract_files_from_image(
    image_path="path/to/image_with_embedded_files.png",
    output_dir="path/to/output_directory"  # 可选，默认为exports目录
)

print(f"已提取 {len(extracted_files)} 个文件:")
for file_info in extracted_files:
    print(f"- {file_info['name']} ({file_info['type']}): {file_info['path']}")

# 只提取特定类型的文件
from modules.SmartTavern.image_binding_module.variables import FILE_TYPE_TAGS

character_files = image_binding.extract_files_from_image(
    image_path="path/to/image_with_embedded_files.png",
    filter_types=[FILE_TYPE_TAGS["CHARACTER"]]  # 只提取角色卡
)
```

### 获取图片中嵌入的文件信息

```python
# 获取图片中嵌入的文件信息（不提取文件内容）
files_info = image_binding.get_embedded_files_info("path/to/image.png")

if files_info:
    print(f"图片包含 {len(files_info)} 个嵌入文件:")
    for info in files_info:
        print(f"- {info['name']} ({info['type']}), 大小: {info['size']} 字节")
else:
    print("图片不包含嵌入文件")
```

### 检查图片是否包含嵌入文件

```python
# 检查图片是否包含嵌入文件
has_embedded_files = image_binding.is_image_with_embedded_files("path/to/image.png")
print(f"图片是否包含嵌入文件: {has_embedded_files}")
```

## 文件类型标签

模块自动根据文件名和路径识别以下文件类型：

- `WB`: 世界书 (World Book)
- `RG`: 正则规则 (Regex)
- `CH`: 角色卡 (Character)
- `PS`: 预设 (Preset)
- `UC`: 用户信息 (personas)
- `OT`: 其他类型 (Other)

## 技术实现

该模块使用PNG图片的自定义数据块来存储文件数据。PNG格式允许在不影响图片显示的情况下，添加自定义的数据块。这些数据块可以包含任意数据，并且在图片被正常显示或编辑时不会被损坏或删除（除非使用特定工具）。

具体实现：
1. 将要嵌入的文件内容编码为Base64字符串
2. 将文件元数据（名称、类型、大小等）和内容组织成JSON格式
3. 压缩JSON数据以减小体积
4. 创建自定义PNG数据块，将压缩后的数据写入
5. 在PNG的IEND块（图片结束标记）之前插入自定义数据块
6. 提取时，查找并解析自定义数据块，还原文件内容

## 限制

- 单个文件的最大大小限制为10MB
- 仅支持PNG格式的图片
- 部分图片编辑软件可能会在编辑过程中删除自定义数据块