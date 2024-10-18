# legal-papers-privacy-filtering-
### 网上使用bert的中文模型进行命名识别教程少的可怜,摸索了一周的时间,硬是是把法律文书的人名全部识别出来了,目前可以达到98.9999%(开玩笑的,不过准确率保守估计是有90%以上).注意:这个法律文书目前只是针对裁决书,其他还没测试过

### 使用的模型
bert-base-chinese-ner 下载路径:https://hf-mirror.com/ckiplab/bert-base-chinese-ner (国内镜像,不用魔法也能访问)
下载好,直接放在当前目录下

### 使用步骤
    1.将里面的text改成你的文本,即"text=''' 你的法律文书内容''' "
    2.全局搜索from_pretrained,后面的两处路径都改成模型的决定路径
    3.启动
    4.在当前目录找到一个.docx文件,直接打开
