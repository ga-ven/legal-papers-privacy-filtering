import datetime
import re

from docx import Document
from transformers import BertForTokenClassification, BertTokenizerFast
from transformers import pipeline


# 合并ner相同类型的实体
def merge_entities(predictions):
    merged_entities = {}
    current_entity = None

    for pred in predictions:
        entity_type = pred['entity']
        start = pred['start']
        end = pred['end']
        word = pred['word']
        base_entity_type = entity_type.split('-')[1]  # 获取基础实体类型

        # 处理 B- 开头的实体
        if entity_type.startswith('B-'):
            # 如果当前存在实体，将其添加到合并字典中
            if current_entity:
                if current_entity['entity_type'] not in merged_entities:
                    merged_entities[current_entity['entity_type']] = []
                merged_entities[current_entity['entity_type']].append(current_entity)
            # 开始新的实体
            current_entity = {
                'start': start,
                'end': end,
                'entity_type': base_entity_type,
                'entity_text': word
            }

        # 处理 I- 和 E- 实体
        elif entity_type.startswith('I-') or entity_type.startswith('E-'):
            if current_entity and current_entity['entity_type'] == base_entity_type:
                # 更新当前实体的结束位置和文本
                current_entity['end'] = end
                current_entity['entity_text'] += word
            else:
                # 如果当前实体不匹配，需创建一个新的实体
                if current_entity:
                    if current_entity['entity_type'] not in merged_entities:
                        merged_entities[current_entity['entity_type']] = []
                    merged_entities[current_entity['entity_type']].append(current_entity)
                # 初始化一个新实体
                current_entity = {
                    'start': start,
                    'end': end,
                    'entity_type': base_entity_type,
                    'entity_text': word
                }

        # 处理 S- 实体
        elif entity_type.startswith('S-'):
            if base_entity_type not in merged_entities:
                merged_entities[base_entity_type] = []
            merged_entities[base_entity_type].append({
                'start': start,
                'end': end,
                'entity_type': base_entity_type,
                'entity_text': word
            })

    # 添加最后一个当前实体到合并字典
    if current_entity:
        if current_entity['entity_type'] not in merged_entities:
            merged_entities[current_entity['entity_type']] = []
        merged_entities[current_entity['entity_type']].append(current_entity)

    return merged_entities


# 定义全局变量
replacement_map = {}
used_chars = set()  # 用于跟踪已使用的字符
replacement_counter = 0  # 用于动态分配字符


def replace_in_text(ner_example, text):
    global replacement_map, used_chars, replacement_counter  # 声明全局变量

    # # 首先优先替换文本中已存在的替代字符
    # for entity_name, replacement_char in replacement_map.items():
    #     text = text.replace(entity_name, replacement_char)

    # 处理 NER 识别结果
    for entity_list in ner_example.values():
        # 遍历字典的值
        for ner in entity_list:  # 遍历每个实体列表
            entity_name = ner['entity_text']
            # 针对组织名和人名的处理
            if ner['entity_type'] in ['PERSON']:
                # 如果已经处理过这个实体，直接使用映射中的替代字符
                if entity_name not in replacement_map:
                    # 为人名分配一个新的符号
                    while True:
                        if ner['entity_type'] == 'PERSON':
                            replacement_char = chr(65 + replacement_counter) + '某'  # 生成 A某, B某, C某
                        # elif ner['entity_type'] == 'ORG':  # 处理人名
                        #     replacement_char = chr(65 + replacement_counter) + '组织' # 生成 A组织, B组织, C组织

                        replacement_counter += 1
                        if replacement_char not in used_chars:
                            used_chars.add(replacement_char)
                            break

                    replacement_map[entity_name] = replacement_char

                # 输出当前的替换信息
                print(f"将 '{entity_name}' 替换为 '{replacement_map[entity_name]}'")

        # # 执行替换
        # print(f"当前实体集合为{entity_list}")
        # if replacement_map.get(entity_name) is not None:
        #     start_index = ner['start']
        #     end_index = ner['end']
        #     # 替换文本中的对应部分
        #     text = text[:start_index] + replacement_map.get(entity_name) + text[end_index:]

        for entity_name, replacement_char in replacement_map.items():
            text = text.replace(entity_name, replacement_char)

    # 输出替换后的文本
    return text


# 加载模型和tokenizer
tokenizer = BertTokenizerFast.from_pretrained(r'D:\pythonproject\legal_desensitization\ckiplab\bert-base-chinese-ner')
#使用这个也行 AutoModelForTokenClassification
model = BertForTokenClassification.from_pretrained(
    r'D:\pythonproject\legal_desensitization\ckiplab\bert-base-chinese-ner')

nlp = pipeline("ner", model=model, tokenizer=tokenizer)

# 输入长文本
text = '''
陈平飞    公司员工
叶宏天   广东明日律师事务所律师
李  飞   广东明日律师事务所律师
宋晶晶  广东明日律师事务所实习律师
陈东复明  广东明日律师事务所实习律师
李  明  广东明日律师事务所实习律师
以上为示例
可以将上面替换成你自己的文本内容
'''


# 处理每个段落的内容
def process_paragraph(para):
    # 从右往左查找第一个空格
    last_space_index = para.rfind(' ')
    if last_space_index != -1 and  len(para) - last_space_index - 1 > 1:
        # 替换第一个空格为逗号
        para = para[:last_space_index] + ',' + para[last_space_index + 1:]

    # 去掉其他空格
    para = para.replace(' ', '')

    return para


# 按段落划分文本
paragraphs = text.split('\n')
paragraphs = [process_paragraph(para) for para in paragraphs]  # 去除空段落
print('段落文本内容', paragraphs)

# 初始化结果列表
all_ner_results = []
# 最终脱密后的文本
final_text = ''
# 打印每个段落的NER结果
for idx, para in enumerate(paragraphs):
    # 去掉所有空格
    para = re.sub(r'\s+', '', para)
    # idx为段落的索引 para为每个段落的文本
    print(f"Paragraph {idx + 1}: {para}")
    # 每个段落的ner结果
    para_ner = nlp(para)
    print('每个段落的ner结果：', para_ner)
    # 合并相同类型ner结果
    merge_ner_results = merge_entities(para_ner)
    print('合并相同类型的ner', merge_ner_results)
    # 加密后的文本
    encryption_text = replace_in_text(merge_ner_results, para)
    print('当前映射表的内容', replacement_map)
    print('脱密后的文本', encryption_text)
    final_text += encryption_text + '\n'  # 加密文本汇总
    all_ner_results.extend(merge_ner_results)  # 将结果添加到总结果中

print('最终的NER结果:', all_ner_results)
# 加密后的文本
print('加密后的文本:', final_text)
print('映射表', replacement_map)

# 保存脱密后的文件
# 创建一个 Document 对象
doc = Document()
doc.add_paragraph(final_text)
current_time = datetime.datetime.now().strftime('%y_%m_%d_%H_%M')
file_name = f'法律文书脱密{current_time}.docx'

# 保存文件
try:
    doc.save(file_name)
    print(f"文件 '{file_name}' 已保存。")
except Exception as e:
    print(f"保存文件时发生错误: {e}")
